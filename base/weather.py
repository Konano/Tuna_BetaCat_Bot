import json

from base import network
from base.config import caiyunToken

# ==================== function ====================


class CaiyunAPIError(Exception):
    pass


def level_rain(intensity: str | float) -> str:
    """降雨量等级"""
    intensity = float(intensity)
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


def level_windspeed(speed: str | float) -> str:
    """风速等级"""
    speed = float(speed)
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
        return 'Lv 17+'


def type_alert(alert: str) -> str:
    """预警类型"""
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
        '16': '雷雨大风',
        '18': '沙尘'
    }
    switchB = {
        '01': '蓝色预警',
        '02': '黄色预警',
        '03': '橙色预警',
        '04': '红色预警'
    }
    try:
        return switchA[alert[:2]] + switchB[alert[-2:]]
    except KeyError:
        return alert + '(UnknownCode)'


def type_skycon(skycon: str) -> str:
    """天气类型"""
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
        return switch[skycon]
    except KeyError:
        return skycon


def wind_direction(dir: str | float) -> str:
    """风向"""

    def dir_diff(a: float, b: float) -> float:
        c = a - b
        c = c - 360 if c > 180 else c
        c = c + 360 if c < -180 else c
        return c

    def dir_diff_abs(a: float, b: float) -> float:
        a, b = max(a, b), min(a, b)
        return min(a - b, 360 - (a - b))

    dir = float(dir)
    dir_val = [0, 45, 90, 135, 180, 225, 270, 315]
    dir_desc = ['正北', '东北', '正东', '东南', '正南', '西南', '正西', '西北']
    dir_bias = ['西东', '北东', '北南', '东南', '东西', '南西', '南北', '西北']

    main_dir = 0
    for i in range(1, 8):
        if dir_diff_abs(dir, dir_val[i]) < dir_diff_abs(dir, dir_val[main_dir]):
            main_dir = i
    if dir_diff(dir, dir_val[main_dir]) < 0:
        return dir_desc[main_dir] + '偏' + dir_bias[main_dir][0]
    else:
        return dir_desc[main_dir] + '偏' + dir_bias[main_dir][1]


# ==================== alert ====================


def alert_now(data: dict) -> list[str]:
    """
    获取当前预警信息
    """

    data = data['result']['alert']
    alerts = []
    if data['status'] == 'ok':
        alerts = [type_alert(each['code'])
                  for each in data['content'] if each['request_status'] == 'ok']
    return alerts

# ==================== weather ====================


def temp_min(data) -> float:
    return min(float(hour['value'])
               for hour in data['result']['hourly']['temperature'][:12])


def temp_max(data) -> float:
    return max(float(hour['value'])
               for hour in data['result']['hourly']['temperature'][:12])


def humi_avg(data) -> float:
    humi_sum = sum(float(hour['value'])
                   for hour in data['result']['hourly']['humidity'][:12])
    return round(humi_sum / 12, 2)


def wind_avg(data) -> float:
    wind_sum = sum(float(hour['speed'])
                   for hour in data['result']['hourly']['wind'][:12])
    return round(wind_sum / 12, 1)


def vis_avg(data) -> float:
    vis_sum = sum(float(hour['value'])
                  for hour in data['result']['hourly']['visibility'][:12])
    return round(vis_sum / 12, 2)


def aqi_avg(data) -> int:
    aqi_sum = sum(float(hour['value']['chn'])
                  for hour in data['result']['hourly']['air_quality']['aqi'][:12])
    return int(aqi_sum / 12)


def daily_weather(data: dict, hour: int, more: bool = True) -> str:
    """
    获取日间或晚间天气信息
    :param hour: 当前小时
    """
    if 6 <= hour < 18:
        infos = [
            '天气：{}'.format(data['result']['hourly']['description']),
            '白天气温：{}~{}℃'.format(data['result']['daily']['temperature_08h_20h'][0]
                                 ['min'], data['result']['daily']['temperature_08h_20h'][0]['max']),
            '近12小时气温：{}~{}℃'.format(temp_min(data), temp_max(data)),
            '湿度：{}%'.format(int(humi_avg(data)*100)),
            '风速：{}m/s ({})'.format(wind_avg(data),
                                   level_windspeed(wind_avg(data))),
            '能见度：{}km'.format(vis_avg(data)),
            '今日日出：{}'.format(data['result']['daily']
                             ['astro'][0]['sunrise']['time']),
            '今日日落：{}'.format(data['result']['daily']
                             ['astro'][0]['sunset']['time']),
            'AQI：{}'.format(aqi_avg(data)),
            '紫外线：{}'.format(data['result']['daily']
                            ['life_index']['ultraviolet'][0]['desc']),
            '舒适度：{}'.format(data['result']['daily']
                            ['life_index']['comfort'][0]['desc']),
            ('现挂预警信号：{}'.format(' '.join(alert_now(data)))
             if alert_now(data) != [] else ''),
        ]
    else:
        infos = [
            '天气：{}'.format(data['result']['hourly']['description']),
            '夜间气温：{}~{}℃'.format(data['result']['daily']['temperature_20h_32h'][0]
                                 ['min'], data['result']['daily']['temperature_20h_32h'][0]['max']),
            '近12小时气温：{}~{}℃'.format(temp_min(data), temp_max(data)),
            '湿度：{}%'.format(int(humi_avg(data)*100)),
            '风速：{}m/s ({})'.format(wind_avg(data),
                                   level_windspeed(wind_avg(data))),
            '能见度：{}km'.format(vis_avg(data)),
            '明日日出：{}'.format(data['result']['daily']
                             ['astro'][1]['sunrise']['time']),
            '明日日落：{}'.format(data['result']['daily']
                             ['astro'][1]['sunset']['time']),
            'AQI：{}'.format(aqi_avg(data)),
            '紫外线：{}'.format(data['result']['daily']
                            ['life_index']['ultraviolet'][0]['desc']),
            '舒适度：{}'.format(data['result']['daily']
                            ['life_index']['comfort'][0]['desc']),
            ('现挂预警信号：{}'.format(' '.join(alert_now(data)))
             if alert_now(data) != [] else ''),
        ]
    if more:
        return '\n'.join(infos)
    else:
        return '\n'.join(infos[0:2] + infos[3:5] + infos[-1:])


def now_weather(data: dict) -> str:
    """
    获取当前天气信息
    """
    text = ''
    text += '清华当前天气：{}\n'.format(
        type_skycon(data['result']['realtime']['skycon']))
    text += '温度：{}℃\n'.format(
        data['result']['realtime']['temperature'])
    if 'apparent_temperature' in data['result']['realtime']:
        text += '体感：{}℃\n'.format(
            data['result']['realtime']['apparent_temperature'])
    text += '湿度：{}%\n'.format(
        int(float(data['result']['realtime']['humidity']) * 100))
    text += '风向：{}\n'.format(
        wind_direction(data['result']['realtime']['wind']['direction']))
    text += '风速：{}m/s ({})\n'.format(
        data['result']['realtime']['wind']['speed'],
        level_windspeed(data['result']['realtime']['wind']['speed']))
    if data['result']['realtime']['precipitation']['local']['status'] == 'ok':
        text += '降水：{}\n'.format(
            level_rain(data['result']['realtime']['precipitation']['local']['intensity']))
    text += '能见度：{}km\n'.format(
        data['result']['realtime']['visibility'])
    text += 'PM2.5：{}\n'.format(
        data['result']['realtime']['air_quality']['pm25'])
    text += 'AQI：{} ({})\n'.format(
        data['result']['realtime']['air_quality']['aqi']['chn'],
        data['result']['realtime']['air_quality']['description']['chn'])
    text += '紫外线：{}\n'.format(
        data['result']['realtime']['life_index']['ultraviolet']['desc'])
    text += '舒适度：{}\n'.format(
        data['result']['realtime']['life_index']['comfort']['desc'])
    alert_signal = alert_now(data)
    if alert_signal != []:
        text += '现挂预警信号：{}\n'.format(' '.join(alert_signal))
    return text


async def caiyun_api(longitude, latitude):
    """
    获取彩云天气数据
    """
    url = 'https://api.caiyunapp.com/v2.6/%s/%s,%s/weather.json?lang=zh_CN&alert=true' % (
        caiyunToken, longitude, latitude)
    data = await network.get_dict(url, timeout=5)
    if data.get('status') != 'ok':
        raise CaiyunAPIError(f'彩云天气 API 返回错误: {json.dumps(data)}')
    return data
