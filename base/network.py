import asyncio
import functools
import json
import logging
from asyncio.exceptions import TimeoutError
from http.cookies import Morsel
from io import BytesIO
from pathlib import Path
from typing import Optional

import aiohttp
from aiohttp.client_exceptions import ContentTypeError

from base.debug import archive, eprint


class ErrorAfterAttempts(Exception):
    pass


class ErrorStatusCode(Exception):
    def __init__(self, status_code: int, content: str | bytes, *args, **kwargs):
        self.status_code = status_code
        self.archive = archive(content)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f'{self.status_code}:{self.archive}'

    def __repr__(self):
        return f'ErrorStatusCode ({self.status_code}:{self.archive})'


def attempt(times: int):
    def decorate(func):
        @functools.wraps(func)
        async def wrap(*args, **kwargs):
            for _ in range(times):
                try:
                    return await func(*args, **kwargs)
                except (ErrorStatusCode, TimeoutError, ContentTypeError, AssertionError) as e:
                    eprint(e, logging.DEBUG)
                except Exception as e:
                    raise e
                await asyncio.sleep(5)
            else:
                raise ErrorAfterAttempts(f'Network error in {times} attempts')
        return wrap
    return decorate


# ==================== GET ====================


@attempt(3)
async def get(url: str, timeout: float = 30, **kwargs) -> bytes:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('GET', url, timeout=_timeout, **kwargs) as r:
        content = await r.read()
    return content


@attempt(3)
async def get_redirect(url: str, timeout: float = 30, **kwargs) -> Optional[str]:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('GET', url, timeout=_timeout, allow_redirects=False, **kwargs) as r:
        if r.status in (301, 302):
            return r.headers['Location']
    return None


@attempt(3)
async def get_noreturn(url: str, timeout: float = 30, **kwargs) -> None:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('GET', url, timeout=_timeout, **kwargs) as r:
        await r.read()


@attempt(3)
async def get_str(url: str, timeout: float = 30, **kwargs) -> str:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('GET', url, timeout=_timeout, **kwargs) as r:
        content = await r.text()
    if r.status != 200:
        raise ErrorStatusCode(r.status, content)
    return content


@attempt(3)
async def get_json(url: str, timeout: float = 30, **kwargs) -> dict | list:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('GET', url, timeout=_timeout, **kwargs) as r:
        data = await r.json()
    return data


@attempt(3)
async def get_dict(url: str, timeout: float = 30, **kwargs) -> dict:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('GET', url, timeout=_timeout, **kwargs) as r:
        data = await r.json()
    assert isinstance(data, dict), f'Expect dict, but got {type(data)}'
    return data


@attempt(3)
async def get_photo(url: str, timeout: float = 30, **kwargs) -> bytes:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('GET', url, timeout=_timeout, **kwargs) as r:
        content = await r.read()
    assert len(content) >= 1024, f'Photo size is too small: {
        len(content)}, it may be wrong.'
    return content


# ==================== POST ====================

@attempt(3)
async def post(url: str, data=None, timeout: float = 30, **kwargs) -> bytes:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('POST', url, data=data, timeout=_timeout, **kwargs) as r:
        content = await r.read()
    return content


@attempt(3)
async def post_json(url: str, data=None, timeout: float = 30, **kwargs) -> dict | list:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('POST', url, data=data, timeout=_timeout, **kwargs) as r:
        data = await r.json()
    return data


@attempt(3)
async def post_dict(url: str, data=None, timeout: float = 30, **kwargs) -> dict:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('POST', url, data=data, timeout=_timeout, **kwargs) as r:
        data = await r.json()
    assert isinstance(data, dict), f'Expect dict, but got {type(data)}'
    return data


@attempt(3)
async def post_status(url: str, data=None, timeout: float = 30, **kwargs) -> tuple[str, int]:
    _timeout = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.request('POST', url, data=data, timeout=_timeout, **kwargs) as r:
        content = await r.text()
        status = r.status
    return content, status


# ==================== SESSION ====================


def m2d(morsel: Morsel) -> dict:
    cookie = dict()
    cookie["basic"] = morsel.__dict__
    cookie["extra"] = dict(morsel.items())
    return cookie


def d2m(cookie: dict) -> Morsel:
    morsel = Morsel()
    dict.update(morsel, cookie["extra"])
    morsel.__dict__.update(cookie["basic"])
    return morsel


class Session:
    def __init__(self, cookie_file: str, timeout: float = 30, **kwargs):
        self.cookie_file = cookie_file
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.kwargs = kwargs
        self.session = aiohttp.ClientSession()
        self.inited = False

    async def init(self):
        assert self.inited is False, 'Session has been inited'
        self.inited = True
        self.session = aiohttp.ClientSession(
            timeout=self.timeout, **self.kwargs)
        try:
            self.load_cookie()
        except Exception as e:
            eprint(e, msg=f'Failed to load cookie: {
                   self.cookie_file}', stacklevel=1)

    @property
    def cookie_jar(self):
        return self.session.cookie_jar

    def __del__(self):
        self.inited and self.save_cookie()  # type: ignore

    def load_cookie(self, cookie_file: Optional[str] = None):
        if cookie_file is None:
            cookie_file = self.cookie_file
        cookies = json.load(Path(cookie_file).open("r"))
        cookies = [(cookie["basic"]["_key"], d2m(cookie))
                   for cookie in cookies]
        self.cookie_jar.update_cookies(cookies)

    def save_cookie(self, cookie_file: Optional[str] = None):
        if cookie_file is None:
            cookie_file = self.cookie_file
        cookies = [m2d(cookie) for cookie in self.cookie_jar]
        json.dump(cookies, Path(cookie_file).open("w"),
                  ensure_ascii=False, indent=4, default=str)

    def output_cookie(self):
        for name, cookies in self.cookie_jar._cookies.items():  # type: ignore
            print(name)
            print(cookies)
        print()

    @attempt(3)
    async def get(self, url: str, **kwargs) -> bytes:
        not self.inited and await self.init()  # type: ignore
        async with self.session.request('GET', url, **kwargs) as r:
            content = await r.read()
        return content

    @attempt(3)
    async def get_headers(self, url: str, field: list[str], **kwargs) -> list[tuple[str, str]]:
        not self.inited and await self.init()  # type: ignore
        async with self.session.request('GET', url, **kwargs) as r:
            headers = r.headers
        return list(filter(lambda x: x[0].lower() in field, headers.items()))
        # if field is not None:
        #     return list(filter(lambda x: x[0].lower() in field, headers.items()))
        # return headers

    @attempt(3)
    async def get_json(self, url: str, **kwargs) -> dict | list:
        not self.inited and await self.init()  # type: ignore
        async with self.session.request('GET', url, **kwargs) as r:
            data = await r.json()
        return data

    @attempt(3)
    async def get_dict(self, url: str, **kwargs) -> dict:
        not self.inited and await self.init()  # type: ignore
        async with self.session.request('GET', url, **kwargs) as r:
            data = await r.json()
        assert isinstance(data, dict), f'Expect dict, but got {type(data)}'
        return data

    @attempt(3)
    async def post_json(self, url: str, data, **kwargs) -> dict | list:
        not self.inited and await self.init()  # type: ignore
        async with self.session.request('POST', url, data=data, **kwargs) as r:
            data = await r.json()
        return data

    @attempt(3)
    async def post_dict(self, url: str, data, **kwargs) -> dict:
        not self.inited and await self.init()  # type: ignore
        async with self.session.request('POST', url, data=data, **kwargs) as r:
            data = await r.json()
        assert isinstance(data, dict), f'Expect dict, but got {type(data)}'
        return data


# ==================== OTHER ====================


async def rss(url: str, timeout: float = 30, **kwargs):
    content = await get(url, timeout=timeout, **kwargs)
    if not content.startswith(b'<?xml'):
        if b"Error message: this route is empty" in content:
            return feedparser.FeedParserDict(entries=[])
    return feedparser.parse(BytesIO(content))
