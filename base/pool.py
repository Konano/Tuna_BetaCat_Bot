import json
import traceback
from datetime import datetime, timedelta

from telegram import Message
from telegram.ext import ContextTypes

from base.config import group
from base.log import logger

try:
    with open('data/msgpool.json', 'r') as file:
        msg_pool = json.load(file)
    for x in msg_pool:
        x[0] = datetime.fromisoformat(x[0])
except:
    msg_pool = []


def add_pool(msg: Message) -> None:
    if msg.chat.id == group:
        msg_pool.append((msg.date, msg.chat.id, msg.message_id))


async def auto_delete(context: ContextTypes.DEFAULT_TYPE) -> None:
    tot = 0
    for x in msg_pool:
        if x[0] < datetime.now(x[0].tzinfo) - timedelta(days=1):
            tot += 1
            try:
                await context.bot.delete_message(chat_id=x[1], message_id=x[2])
            except Exception as e:
                if 'Message to delete not found' not in str(e):
                    logger.warning(traceback.format_exc())
                pass
        else:
            break
    del msg_pool[:tot]
    with open('data/msgpool.json', 'w') as file:
        json.dump(msg_pool, file, default=str)
