import io
import json
import os
import re
import time
from pathlib import Path
from random import Random
from typing import Optional

import numpy as np
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode
from telegram import InputMediaPhoto, Update
from telegram.ext import ContextTypes

from base.debug import eprint
from base.format import escaped
from base.log import logger


async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.message
    try:
        assert context.args
        rd = Random(int(time.time()))
        await update.message.reply_text(f'Choose: {rd.randint(1, int(context.args[0]))}')
    except:
        await update.message.reply_text('Usage: /roll [total]')


async def callpolice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.effective_chat
    rd = Random(int(time.time()))
    emoji = '👮🚔🚨🚓'
    text = ''.join([emoji[rd.randint(0, 3)]
                   for _ in range(rd.randint(10, 100))])
    await update.effective_chat.send_message(text)


dig = np.array([
    [1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1,
        0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1],
    [1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1,
        1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0,
        1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0,
        1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1,
        0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1,
        0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0,
        1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1],
    [0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1,
        1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0,
        1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0,
        0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1],
]) * 255


def generator_register(id: str, tm: str) -> Optional[str]:
    try:
        pic = f'./tmp/{id}_{tm}.png'
        if not os.path.exists(pic):
            tmp = f'./tmp/{int(time.time())}.png'
            qrcode.make(id).save(tmp)  # type: ignore
            bg = np.array(Image.open('template/template.jpg').convert('L'))
            tmp = np.array(Image.open(tmp).convert('L'))[40:-45, 40:-45]
            tmp = np.array(Image.fromarray(tmp).resize((41, 41)))
            bg[14:55, 25:66] = tmp
            points = [29, 35, 41, 47, 53, 59]
            edit = [int(_) for _ in tm]
            for i in range(6):
                x, y, d = 55, points[i], edit[i]
                bg[x:x+7, y:y+4] = dig[d].reshape(7, 4)
            Image.fromarray(bg).save(pic)
        return pic
    except Exception as e:
        eprint(e)


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.message
    args = context.args
    logger.info(f'\\register {update.message.chat_id} {json.dumps(args)}')

    try:
        assert args
        assert len(args) == 2
        assert len(re.findall(r'^\d{10}$', args[0])) == 1
        assert len(re.findall(r'^\d{6}$', args[1])) == 1

        pic = generator_register(args[0], args[1])
        assert pic is not None
        await update.message.reply_photo(open(pic, 'rb'))
        Path(pic).unlink()
    except:
        await update.message.reply_text('Usage: /register [StudentID] [Month]\nExample: /register 1994990239 202102')


users = {}


async def yue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message and update.message.from_user
    user_id = update.message.from_user.id
    user_name = update.message.from_user.name
    users[user_id] = user_name
    await update.message.reply_text('约😘')


async def gu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message and update.message.from_user
    user_id = update.message.from_user.id
    if user_id in users:
        del users[user_id]
    await update.message.reply_text('不约😭')


async def fan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    if len(users) == 0:
        await update.message.reply_text('没人约😭')
        return
    info = ' '.join([f'[{escaped(user_name)}](tg://user?id={user_id})'
                     for user_id, user_name in users.items()])
    await update.message.reply_markdown_v2(info)


async def san(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    global users
    users = {}
    await update.message.reply_text('散🎉')


async def payme_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message and update.message.from_user
    user_id = update.message.from_user.id
    folder = Path(f'./data/pay/{user_id}')
    folder.mkdir(exist_ok=True)
    try:
        file = await update.message.photo[-1].get_file()
        buf = await file.download_as_bytearray()
        for res in decode(Image.open(io.BytesIO(buf))):
            url: str = res.data.decode()
            if url.startswith('https://qr.alipay.com/'):
                with (folder / 'ali.png').open('wb') as f:
                    f.write(buf)
                await update.message.reply_text('检测到：Alipay 收款码')
                return
            elif url.startswith('wxp://'):
                with (folder / 'wx.png').open('wb') as f:
                    f.write(buf)
                await update.message.reply_text('检测到：Wechat 收款码')
                return
            elif url.startswith('https://qr.95516.com/'):
                with (folder / 'uni.png').open('wb') as f:
                    f.write(buf)
                await update.message.reply_text('检测到：UnionPay 收款码')
                return
            else:
                await update.message.reply_text('Unsupported QRCode')
                logger.warning(url)
                return
    except Exception as e:
        await update.message.reply_text('QRCode not found')
        eprint(e)


async def payme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message and update.message.from_user
    user_id = update.message.from_user.id
    folder = Path(f'./data/pay/{user_id}')
    if not (folder.exists() and len(list(folder.iterdir()))):
        await update.message.reply_text('No QRCodes found, send to me first!')
        return
    images = [InputMediaPhoto(file.open('rb')) for file in folder.iterdir()]
    await update.message.reply_media_group(images)
