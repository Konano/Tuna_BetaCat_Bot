import logging

from telegram import Bot

from base.debug import try_except


def init(_bot: Bot):
    global bot
    bot = _bot


"""
Using "msg" instead of "message" to avoid conflict with the message module in the python-telegram-bot package.
"""


@try_except(level=logging.DEBUG, return_value=False)
async def delete_msg(chat_id: str | int, message_id: int, **kwargs):
    """
    Delete a message.
    Return True if successful, False otherwise.
    """
    await bot.delete_message(chat_id=chat_id, message_id=message_id, **kwargs)


@try_except(level=logging.DEBUG, return_value=False)
async def edit_msg_text(chat_id: str | int, message_id: int, text: str, **kwargs):
    """
    Edit the text of a message.
    Return True if successful, False otherwise.
    """
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, **kwargs)


@try_except(level=logging.DEBUG, return_value=False)
async def send_msg(chat_id: str | int, text: str, **kwargs):
    """
    Send a message.
    Return True if successful, False otherwise.
    """
    await bot.send_message(chat_id=chat_id, text=text, **kwargs)


@try_except(level=logging.DEBUG, return_value=False)
async def edit_msg_media(chat_id: str | int, message_id: int, media, **kwargs):
    """
    Edit the media of a message.
    Return True if successful, False otherwise.
    """
    await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, **kwargs)
