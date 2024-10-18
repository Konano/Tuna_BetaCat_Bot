import json
import traceback

from telegram.error import BadRequest

from base.config import channel, config, group
from base.crawler import request
from base.format import escaped
from base.log import logger

start_probability = 0.8
stop_probability = 0.1
start_precipitation = 0.03
stop_precipitation = 0.005
rain_2h = rain_60 = rain_15 = rain_0 = False

try:
    with open('data/realtime.json', 'r') as file:
        realtime = json.load(file)
except:
    realtime = {'newmsg': True, 'msgid': None, 'text': None}
    with open('data/realtime.json', 'w') as file:
        json.dump(realtime, file)

try:
    with open('data/caiyun.json', 'r') as file:
        caiyunData = json.load(file)
    alerts = {}
    if caiyunData['result']['alert']['status'] == 'ok':
        for each in caiyunData['result']['alert']['content']:
            if each['request_status'] == 'ok' and each['alertId'] not in alerts:
                alerts[each['alertId']] = each
except:
    caiyunData = None
    alerts = {}

caiyunFailedCount = 0


def deal_precipitation(str):

    intensity = float(str)
    if intensity == 0:
        return '无'
    elif intensity < 0.031:
        return '毛毛雨'
    elif intensity < 0.25:
        return '小雨'
    elif intensity < 0.35:
        return '中雨'
    elif intensity < 0.48:
        return '大雨'
    else:
        return '暴雨'


def deal_skycon(str):

    switch = {
        'CLEAR_DAY': '晴',
        'CLEAR_NIGHT': '晴',
        'PARTLY_CLOUDY_DAY': '多云',
        'PARTLY_CLOUDY_NIGHT': '多云',
        'CLOUDY': '阴',
        'LIGHT_HAZE': '轻度雾霾',
        'MODERATE_HAZE': '中度雾霾',
        'HEAVY_HAZE': '重度雾霾',
        'HAZE': '雾霾',
        'LIGHT_RAIN': '小雨',
        'MODERATE_RAIN': '中雨',
        'HEAVY_RAIN': '大雨',
        'STORM_RAIN': '暴雨',
        'RAIN': '雨',
        'FOG': '雾',
        'LIGHT_SNOW': '小雪',
        'MODERATE_SNOW': '中雪',
        'HEAVY_SNOW': '大雪',
        'STORM_SNOW': '暴雪',
        'SNOW': '雪',
        'WIND': '大风',
        'DUST': '浮尘',
        'SAND': '沙尘',
        'THUNDER_SHOWER': '雷阵雨',
        'HAIL': '冰雹',
        'SLEET': '雨夹雪'
    }
    try:
        return switch[str]
    except KeyError:
        return str


def level_windspeed(str):

    speed = float(str)
    if speed <= 0.2:
        return 'Lv 0'
    elif speed <= 1.5:
        return 'Lv 1'
    elif speed <= 3.3:
        return 'Lv 2'
    elif speed <= 5.4:
        return 'Lv 3'
    elif speed <= 7.9:
        return 'Lv 4'
    elif speed <= 10.7:
        return 'Lv 5'
    elif speed <= 13.8:
        return 'Lv 6'
    elif speed <= 17.1:
        return 'Lv 7'
    elif speed <= 20.7:
        return 'Lv 8'
    elif speed <= 24.4:
        return 'Lv 9'
    elif speed <= 28.4:
        return 'Lv 10'
    elif speed <= 32.6:
        return 'Lv 11'
    elif speed <= 36.9:
        return 'Lv 12'
    elif speed <= 41.4:
        return 'Lv 13'
    elif speed <= 46.1:
        return 'Lv 14'
    elif speed <= 50.9:
        return 'Lv 15'
    elif speed <= 56.0:
        return 'Lv 16'
    elif speed <= 61.2:
        return 'Lv 17'
    else:
        return 'Lv >17'


def dir_diff(a, b):
    c = a - b
    if c > 180:
        c -= 360
    if c < -180:
        c += 360
    return c


def dir_diff_abs(a, b):
    if a < b:
        a, b = b, a
    return min(a - b, 360 - (a - b))


def wind_direction(str):

    dir = float(str)
    dir_val = [0, 45, 90, 135, 180, 225, 270, 315]
    dir_desc = ['正北', '东北', '正东', '东南', '正南', '西南', '正西', '西北']
    dir_bias = ['西东', '北东', '北南', '东南', '东西', '南西', '南北', '西北']

    main_dir = 0
    for i in range(1, 8):
        if dir_diff_abs(dir, dir_val[i]) < dir_diff_abs(dir, dir_val[main_dir]):
            main_dir = i
    str = dir_desc[main_dir]
    if dir_diff(dir, dir_val[main_dir]) < 0:
        str += '偏' + dir_bias[main_dir][:1]
    else:
        str += '偏' + dir_bias[main_dir][-1:]
    return str


def alert_type(str):

    switchA = {
        '01': '台风',
        '02': '暴雨',
        '03': '暴雪',
        '04': '寒潮',
        '05': '大风',
        '06': '沙尘暴',
        '07': '高温',
        '08': '干旱',
        '09': '雷电',
        '10': '冰雹',
        '11': '霜冻',
        '12': '大雾',
        '13': '霾',
        '14': '道路结冰',
        '15': '森林火灾',
        '16': '雷雨大风'
    }
    switchB = {
        '01': '蓝色预警',
        '02': '黄色预警',
        '03': '橙色预警',
        '04': '红色预警'
    }

    try:
        return switchA[str[:2]] + switchB[str[-2:]]
    except KeyError:
        return str + '(UnknownCode)'


def update_newmsg():
    global realtime
    realtime['newmsg'] = True
    with open('data/realtime.json', 'w') as file:
        json.dump(realtime, file)


def alert_now():

    alerts = []
    if caiyunData['result']['alert']['status'] == 'ok':
        for each in caiyunData['result']['alert']['content']:
            if each['request_status'] == 'ok':
                alerts.append(alert_type(each['code']))
    return alerts


def caiyun_temp_min():
    temp_min = 999.99
    for i in range(12):
        temp_min = min(temp_min, float(
            caiyunData['result']['hourly']['temperature'][i]['value']))
    return temp_min


def caiyun_temp_max():
    temp_max = -999.99
    for i in range(12):
        temp_max = max(temp_max, float(
            caiyunData['result']['hourly']['temperature'][i]['value']))
    return temp_max


def caiyun_humi_avg():
    humi_avg = 0.0
    for i in range(12):
        humi_avg += float(caiyunData['result']
                          ['hourly']['humidity'][i]['value'])
    return round(humi_avg / 12, 2)


def caiyun_wind_avg():
    wind_avg = 0.0
    for i in range(12):
        wind_avg += float(caiyunData['result']['hourly']['wind'][i]['speed'])
    return round(wind_avg / 12, 1)


def caiyun_visi_avg():
    visi_avg = 0.0
    for i in range(12):
        visi_avg += float(caiyunData['result']
                          ['hourly']['visibility'][i]['value'])
    return round(visi_avg / 12, 2)


def caiyun_aqi_avg():
    aqi_avg = 0.0
    for i in range(12):
        aqi_avg += float(caiyunData['result']['hourly']
                         ['air_quality']['aqi'][i]['value']['chn'])
    return int(aqi_avg / 12)


def daily_weather(dayornight):

    if dayornight == 'day':
        return \
            '天气：{}\n'.format(caiyunData['result']['hourly']['description']) + \
            '温度：{}~{}℃\n'.format(caiyun_temp_min(), caiyun_temp_max()) + \
            '湿度：{}%\n'.format(int(caiyun_humi_avg()*100)) + \
            '风速：{}m/s ({})\n'.format(caiyun_wind_avg(), level_windspeed(caiyun_wind_avg())) + \
            '能见度：{}km\n'.format(caiyun_visi_avg()) + \
            '今日日出：{}\n'.format(caiyunData['result']['daily']['astro'][0]['sunrise']['time']) + \
            '今日日落：{}\n'.format(caiyunData['result']['daily']['astro'][0]['sunset']['time']) + \
            'AQI：{}\n'.format(caiyun_aqi_avg()) + \
            '紫外线：{}\n'.format(caiyunData['result']['daily']['life_index']['ultraviolet'][0]['desc']) + \
            '舒适度：{}\n'.format(caiyunData['result']['daily']['life_index']['comfort'][0]['desc']) + \
            ('现挂预警信号：{}\n'.format(' '.join(alert_now())) if alert_now() != [] else '')
    else:
        return \
            '天气：{}\n'.format(caiyunData['result']['hourly']['description']) + \
            '温度：{}~{}℃\n'.format(caiyun_temp_min(), caiyun_temp_max()) + \
            '湿度：{}%\n'.format(int(caiyun_humi_avg()*100)) + \
            '风速：{}m/s ({})\n'.format(caiyun_wind_avg(), level_windspeed(caiyun_wind_avg())) + \
            '能见度：{}km\n'.format(caiyun_visi_avg()) + \
            '明日日出：{}\n'.format(caiyunData['result']['daily']['astro'][1]['sunrise']['time']) + \
            '明日日落：{}\n'.format(caiyunData['result']['daily']['astro'][1]['sunset']['time']) + \
            'AQI：{}\n'.format(caiyun_aqi_avg()) + \
            ('现挂预警信号：{}\n'.format(' '.join(alert_now())) if alert_now() != [] else '')


def realtime_report(bot, text):
    try:
        global realtime
        if realtime['newmsg']:
            try:
                bot.delete_message(chat_id=group, message_id=realtime['msgid'])
            except BadRequest as e:
                logger.debug(e)
            realtime['text'] = text
            realtime['msgid'] = bot.send_message(
                chat_id=group, text=text).message_id
            realtime['newmsg'] = False
        elif realtime['text'] != text:
            realtime['text'] = text
            bot.edit_message_text(chat_id=group, text=text,
                                  message_id=realtime['msgid'])
        with open('data/realtime.json', 'w') as file:
            json.dump(realtime, file)
    except Exception as e:
        logger.debug(traceback.format_exc())
        logger.error(e)


def forecast_rain(bot):

    assert caiyunData['result']['minutely']['status'] == 'ok'

    probability_2h = caiyunData['result']['minutely']['probability']
    global rain_2h
    if max(probability_2h) < stop_probability and rain_2h == True:
        rain_2h = False
        logger.info('rain_2h T to F')
    if max(probability_2h) > start_probability and rain_2h == False:
        rain_2h = True
        realtime_report(bot, '未来两小时内可能会下雨。')
        logger.info('rain_2h F to T')

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
        realtime_report(bot, caiyunData['result']['forecast_keypoint'])


def caiyun(context):

    global caiyunData, caiyunFailedCount
    try:
        caiyunData = json.loads(request('https://api.caiyunapp.com/v2.6/{}/{},{}/weather.json?lang=zh_CN&alert=true'
                                        .format(config['CAIYUN']['token'], config['CAIYUN']['longitude'], config['CAIYUN']['latitude'])))

        assert caiyunData['status'] == 'ok'

        with open('data/caiyun.json', 'w') as file:
            json.dump(caiyunData, file)

        caiyunFailedCount = 0

    except:
        logger.debug(traceback.format_exc())
        caiyunFailedCount += 1
        if caiyunFailedCount == 1 or caiyunFailedCount % 5 == 0:
            logger.warning(
                f'Failed to get data from CaiYun. ({caiyunFailedCount})')
        return

    forecast_rain(context.bot)

    if caiyunData['result']['alert']['status'] == 'ok':
        for each in caiyunData['result']['alert']['content']:
            if each['request_status'] == 'ok' and each['alertId'] not in alerts:
                context.bot.send_message(chat_id=group,   text='*{}*\n\n{}'.format(
                    escaped(each['title']), escaped(each['description'])), parse_mode='MarkdownV2')
                context.bot.send_message(chat_id=channel, text='*{}*\n\n{}'.format(
                    escaped(each['title']), escaped(each['description'])), parse_mode='MarkdownV2')
                alerts[each['alertId']] = each
