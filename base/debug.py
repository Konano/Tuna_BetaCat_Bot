import asyncio
import functools
import logging
import traceback
from datetime import datetime
from typing import Callable, Optional

from base.log import logger


class IgnoreWarning(Exception):
    pass


def exception_desc(e: Exception) -> str:
    """
    Return exception description.
    """
    if str(e) != '':
        return f'{e.__class__.__module__}.{e.__class__.__name__} ({e})'
    return f'{e.__class__.__module__}.{e.__class__.__name__}'


def eprint(e: Exception, level: int = logging.WARNING, msg: Optional[str] = None, stacklevel: int = 2) -> None:
    """
    Print exception with traceback.
    """
    if not (isinstance(level, int) and level in logging._levelToName):
        level = logging.WARNING

    if msg is not None:
        logger.log(level, msg, stacklevel=stacklevel)

    exception_str = f'Exception: {exception_desc(e)}'
    logger.log(level, exception_str, stacklevel=stacklevel)

    logger.debug(traceback.format_exc(), stacklevel=stacklevel)


def try_except(level: int = logging.WARNING, msg: Optional[str] = None, return_value: bool = True, exclude=(IgnoreWarning)) -> Callable:
    """
    Try to execute the function.
    If an exception is raised, log it in debug level and return True/False or Return/None.
    """
    def decorate(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrap_async(*args, **kwargs):
                try:
                    ret = await func(*args, **kwargs)
                    return ret if return_value else True
                except exclude as e:
                    eprint(e, logging.DEBUG, msg, stacklevel=3)
                    return None if return_value else False
                except Exception as e:
                    eprint(e, level, msg, stacklevel=3)
                    return None if return_value else False
            return wrap_async
        else:
            @functools.wraps(func)
            def wrap(*args, **kwargs):
                try:
                    ret = func(*args, **kwargs)
                    return ret if return_value else True
                except exclude as e:
                    eprint(e, logging.DEBUG, msg, stacklevel=3)
                    return None if return_value else False
                except Exception as e:
                    eprint(e, level, msg, stacklevel=3)
                    return None if return_value else False
            return wrap
    return decorate


def archive(content: str | bytes, suffix: Optional[str] = None) -> str:
    """
    Archive content to file.
    """
    now = str(datetime.now()).replace(' ', '_').replace(':', '-')
    filepath = f'log/archive/{now}' + (f'.{suffix}' if suffix else '')
    if isinstance(content, str):
        open(filepath, 'w').write(content)
    elif isinstance(content, bytes):
        open(filepath, 'wb').write(content)
    else:
        raise TypeError('content must be str or bytes')
    return filepath
