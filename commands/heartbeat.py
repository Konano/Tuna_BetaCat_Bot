from telegram.ext import ContextTypes

from base import network
from base.config import heartbeatURL
from base.log import logger


async def send_heartbeat(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug('heartbeat')
    await network.get(url=heartbeatURL)
