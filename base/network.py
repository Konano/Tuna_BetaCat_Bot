import asyncio
import functools
import logging
from asyncio.exceptions import TimeoutError
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
                except TimeoutError as e:
                    eprint(e, logging.DEBUG, print_trace=False)
                except (ErrorStatusCode, ContentTypeError, AssertionError) as e:
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
