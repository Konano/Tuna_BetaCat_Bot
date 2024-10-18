import json
import logging
import os
from datetime import datetime, timedelta
from typing import cast

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pytz import timezone
from telegram import Bot, InputMediaPhoto, Message, Update
from telegram.ext import ContextTypes

from base.config import channel, config, group
from base.debug import try_except
from base.format import escaped
from base.log import logger
from base.message import delete_msg, edit_msg_media
from base.pool import add_pool
from base.weather import CaiyunAPIError, caiyun_api, daily_weather, now_weather

matplotlib.use('Agg')

if not os.path.exists('./tmp/'):
    os.makedirs('./tmp/')

# ==================== data ====================


try:
    caiyunData = json.load(open('data/caiyun.json', 'r'))
except Exception:
    caiyunData = {}


@try_except(level=logging.DEBUG, return_value=False, exclude=(CaiyunAPIError))
async def weather_update():
    """更新彩云天气数据"""
    global caiyunData
    caiyunData = await caiyun_api(config['CAIYUN']['longitude'], config['CAIYUN']['latitude'])
    with open('data/caiyun.json', 'w') as file:
        json.dump(caiyunData, file)


# ==================== rain ====================

start_probability = 0.8
stop_probability = 0.2
start_precipitation = 0.03
stop_precipitation = 0.01
rain_2h = rain_60 = rain_15 = rain_0 = False
rainfall = False
alert_text = ''

try:
    weather_msgid = json.load(
        open('data/weather_msgid.json', 'r'))
except Exception:
    weather_msgid = 0


async def forecast_rain(bot: Bot):
    """根据两小时内的降雨预测发出预警"""
    if caiyunData == {} or caiyunData['result']['minutely']['status'] != 'ok':
        return

    global rain_2h
    probability_2h = caiyunData['result']['minutely']['probability']
    if max(probability_2h) < stop_probability and rain_2h == True:
        rain_2h = False
        logger.debug('rain_2h T to F')
    if max(probability_2h) > start_probability and rain_2h == False:
        rain_2h = True
        logger.debug('rain_2h F to T')
        # await rain_alert(bot, '未来两小时内可能会下雨。')

    global rain_60, rain_15, rain_0
    changed = False
    precipitation = caiyunData['result']['minutely']['precipitation_2h']
    if (precipitation[60] < stop_precipitation and rain_60 == True) or (precipitation[60] > start_precipitation and rain_60 == False):
        rain_60 = not rain_60
        changed = True
    if (precipitation[15] < stop_precipitation and rain_15 == True) or (precipitation[15] > start_precipitation and rain_15 == False):
        rain_15 = not rain_15
        changed = True
    if (precipitation[0] < stop_precipitation and rain_0 == True) or (precipitation[0] > start_precipitation and rain_0 == False):
        rain_0 = not rain_0
        changed = True

    if changed:
        await rain_alert(bot, caiyunData['result']['forecast_keypoint'])

    global rainfall
    rainfall = rain_2h or rain_60 or rain_15 or rain_0


async def rain_alert(bot: Bot, text: str):
    """降雨预警"""
    global alert_text, weather_msgid
    if alert_text == text:
        return
    alert_text = text
    await delete_msg(group, weather_msgid)
    msg: Message = await bot.send_message(chat_id=group, text=text)
    weather_msgid = msg.message_id
    with open('data/weather_msgid.json', 'w') as file:
        json.dump(weather_msgid, file)


# ==================== alert ====================

try:
    alert_info = json.load(
        open('data/alert_info.json', 'r'))
except Exception:
    alert_info = {}


async def alert_info_update(bot: Bot):
    """更新预警信息"""
    if caiyunData == {} or caiyunData['result']['alert']['status'] != 'ok':
        return

    modified = False
    alertIds = [each['alertId']
                for each in caiyunData['result']['alert']['content']]
    for id in list(alert_info.keys()):
        if id not in alertIds:
            await delete_msg(group, alert_info[id]['msgid'])
            del alert_info[id]
    for each in caiyunData['result']['alert']['content']:
        if each['request_status'] == 'ok' and each['alertId'] not in alert_info:
            text = '*%s*\n\n%s' % (escaped(each['title']),
                                   escaped(each['description']))
            msg = await bot.send_message(chat_id=group, text=text,
                                         parse_mode='MarkdownV2')
            # mark_autodel(msg)
            each['msgid'] = msg.message_id
            alert_info[each['alertId']] = each
            modified = True
    if modified:
        with open('data/alert_info.json', 'w') as file:
            json.dump(alert_info, file)


# ==================== pic ====================

@try_except(level=logging.WARNING)
def temperature_graph():
    """未来 24 小时气温折线图"""
    pic = f'./tmp/temperature.png'
    logger.debug(f'file {pic} created')

    temperature: list[float] = []
    datetimes: list[str] = []
    for x in caiyunData['result']['hourly']['temperature'][:25]:
        dt = datetime.fromisoformat(x['datetime'])
        if datetime.now(timezone("Asia/Shanghai")) - timedelta(hours=1) <= dt:
            temperature.append(x['value'])
            datetimes.append(str(dt.hour))
        if len(temperature) == 24:
            break
    plt.figure(figsize=(6, 3))
    plt.plot(np.array(datetimes), np.array(temperature), linewidth=0)

    for i in range(len(datetimes)):
        plt.axvline(x=i, color='gray', linestyle='dashed', linewidth=0.5)

    z = np.polyfit(np.arange(len(temperature)), np.array(temperature), 8)
    p = np.poly1d(z)
    t = np.arange(0, len(temperature) - 1 + 0.1, 0.1)
    plt.plot(t, p(t), color='red', linewidth=1)

    plt.title('Temperature within 24 hours')
    plt.savefig(pic)
    plt.close()  # Close the figure to avoid the warning
    return pic


@try_except(level=logging.WARNING)
def precipitation_graph():
    """未来 2 小时降雨概率折线图"""
    pic = f'./tmp/precipitation.png'
    logger.debug(f'file {pic} created')

    precipitation = caiyunData['result']['minutely']['precipitation_2h']
    plt.figure(figsize=(6, 3))
    plt.plot(np.arange(120), np.array(precipitation))
    plt.ylim(bottom=0)
    if plt.axis()[3] > 0.03:
        plt.hlines(0.03, 0, 120, colors=['skyblue'], linestyles='dashed')
    if plt.axis()[3] > 0.25:
        plt.hlines(0.25, 0, 120, colors=['blue'], linestyles='dashed')
    if plt.axis()[3] > 0.35:
        plt.hlines(0.35, 0, 120, colors=['orange'], linestyles='dashed')
    if plt.axis()[3] > 0.48:
        plt.hlines(0.48, 0, 120, colors=['darkred'], linestyles='dashed')

    plt.title('Probability of precipitation within 2 hours')
    plt.savefig(pic)
    plt.close()  # Close the figure to avoid the warning
    return pic


@try_except(level=logging.WARNING)
def mixed_graph():
    """将未来 2 小时降雨概率折线图和未来 24 小时气温折线图合并"""
    pic = pic_temp = temperature_graph()
    if max(caiyunData['result']['minutely']['precipitation_2h']) > 0:
        pic_rain = precipitation_graph()
        pic = f'./tmp/mixed.png'
        logger.debug(f'file {pic} created')
        img_rain = Image.open(pic_rain)
        img_temp = Image.open(pic_temp)
        width, height = img_rain.size
        img_combined = Image.new('RGB', (width, height * 2))
        img_combined.paste(img_rain, (0, 0))
        img_combined.paste(img_temp, (0, height))
        img_combined.save(pic)
    return pic


# ==================== weather report ====================

try:
    weather_report_msgid = json.load(
        open('data/weather_report_msgid.json', 'r'))
except Exception:
    weather_report_msgid = {'group': 0, 'channel': 0}


async def weather_report(context: ContextTypes.DEFAULT_TYPE):
    """定时发送或者更新天气预报"""
    assert context.job
    hour = cast(int, context.job.data)
    text = daily_weather(caiyunData, hour)
    if hour == 6 or hour == 18:
        await delete_msg(group, weather_report_msgid['group'])
        await delete_msg(channel, weather_report_msgid['channel'])
        pic = mixed_graph()
        msg = await context.bot.send_photo(group, open(pic, 'rb'), text)
        weather_report_msgid['group'] = msg.message_id
        msg = await context.bot.send_photo(channel, open(pic, 'rb'), text)
        weather_report_msgid['channel'] = msg.message_id
        with open('data/weather_report_msgid.json', 'w') as file:
            json.dump(weather_report_msgid, file)
    else:
        pic = mixed_graph()
        pic = InputMediaPhoto(media=open(pic, 'rb'), caption=text)
        await edit_msg_media(group, weather_report_msgid['group'], pic)
        await edit_msg_media(channel, weather_report_msgid['channel'], pic)


# ==================== poll ====================

remain_minutes = 0


async def weather_poll(context: ContextTypes.DEFAULT_TYPE):
    """定时更新天气数据"""
    # 如果降雨则更新粒度为 5mins
    # 如果不降雨则更新粒度为 15mins
    global remain_minutes
    remain_minutes -= 1
    if remain_minutes <= 0:
        if await weather_update():
            await forecast_rain(context.bot)
            await alert_info_update(context.bot)
            remain_minutes = 5 if rainfall else 15
        else:
            # 如果更新失败则 2mins 后重试
            remain_minutes = 2
        logger.debug(f'next update: {remain_minutes} mins')


# ==================== realtime ====================

async def realtime_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """实时天气预报"""
    assert update.message
    await weather_update()
    if caiyunData != {} and caiyunData['result']['realtime']['status'] == 'ok':
        text = now_weather(caiyunData)
        await update.message.reply_text(text)
    else:
        await update.message.reply_text('天气数据获取失败')


async def realtime_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """实时降雨预报"""
    assert update.message
    await weather_update()
    if caiyunData == {} or caiyunData['result']['minutely']['status'] != 'ok':
        await update.message.reply_text('天气数据获取失败')
        return

    pic = precipitation_graph()
    if pic is None:
        await update.message.reply_text('图表生成错误')
        return

    msg = await update.message.reply_photo(
        photo=open(pic, 'rb'),
        caption=caiyunData['result']['forecast_keypoint']
    )
    add_pool(msg)
