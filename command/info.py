import json
import traceback

from telegram import Update
from telegram.ext import ContextTypes

import base.mute as mt
from base.config import group
from base.format import escaped
from base.log import logger
from base.webvpn import webvpn

try:
    with open('data/today.json', 'r') as file:
        today = json.load(file)
except:
    today = {}


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.channel_post and update.channel_post.text
    try:
        rev = json.loads(update.channel_post.text)
        logger.info(rev)
        data = rev['data']

        if rev['type'] == 'newinfo':
            url = data['url']
            today[url] = data
            today[url]['msgid'] = None
            if data['source'] not in mt.muted:
                text = 'Info %s\n[%s](%s) [\\(webvpn\\)](%s)' % (escaped(
                    data['source']), escaped(data['title']), data['url'], webvpn(data['url']))
                msg = await context.bot.send_message(
                    chat_id=group, text=text, parse_mode='MarkdownV2', disable_web_page_preview=True)
                today[url]['msgid'] = msg.message_id

        elif rev['type'] == 'delinfo':
            url = data
            if url in today.keys():
                if today[url]['msgid'] is not None:
                    await context.bot.delete_message(chat_id=group, message_id=today[url]['msgid'])
                del today[url]

        with open('data/today.json', 'w') as file:
            json.dump(today, file)

    except Exception as e:
        logger.error(e)
        logger.debug(traceback.format_exc())


def info_daily(clear=True):
    ret = {}
    for info in today.values():
        if info['source'] not in ret.keys():
            ret[info['source']] = []
        ret[info['source']].append(info)
    if clear:
        today.clear()
        with open('data/today.json', 'w') as file:
            json.dump(today, file)
    return ret


async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    text = 'Today Info:'
    today = info_daily()
    for source in today.keys():
        text += '\n \\- %s' % escaped(source)
        for news in today[source]:
            text += '\n[%s](%s)' % (escaped(news['title']), news['url'])
    await context.bot.send_message(
        chat_id=group, text=text, parse_mode='MarkdownV2', disable_web_page_preview=True)
