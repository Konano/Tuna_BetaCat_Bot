import json

from telegram import Update
from telegram.ext import ContextTypes

try:
    with open('data/mute.json', 'r') as file:
        muted = json.load(file)
except:
    muted = []


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_chat
    if not context.args:
        await update.effective_chat.send_message('Usage: /mute [source]')
        return
    for each in context.args:
        if each not in muted:
            muted.append(each)
    with open('data/mute.json', 'w') as file:
        json.dump(muted, file)
    await update.effective_chat.send_message('Muted: ' + ' '.join(context.args))


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_chat
    if not context.args:
        await update.effective_chat.send_message('Usage: /unmute [source]')
        return
    for each in context.args:
        muted.remove(each)
    with open('data/mute.json', 'w') as file:
        json.dump(muted, file)
    await update.effective_chat.send_message('Unmuted: ' + ' '.join(context.args))


async def mute_show(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_chat
    text = '\n'.join(['Muted list:'] + muted)
    await update.effective_chat.send_message(text)
