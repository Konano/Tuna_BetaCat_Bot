import configparser
import logging
import sys
import traceback
from datetime import datetime, time, timedelta
from logging import Filter
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

from pytz import timezone
from telegram import Chat, Message, Update
from telegram.error import Forbidden, TelegramError
from telegram.ext import (Application, CommandHandler, ContextTypes, JobQueue,
                          MessageHandler, Updater, filters)

from base.caiyun import caiyun
from base.config import accessToken, group, pipe, webhookConfig
from base.log import logger
from base.mute import mute, mute_show, unmute
from base.pool import auto_delete
from commands.daily import daily_report, weather_report
from commands.gadget import (callpolice, fan, gu, new_message, payme,
                             payme_upload, register, roll, san, yue)
from commands.heartbeat import send_heartbeat
from commands.info import info
from commands.weather import forecast, forecast_hourly, weather


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error for debuging."""
    logger.error("Exception while handling an update: %s", context.error)
    logger.debug(msg="The traceback of the exception:", exc_info=context.error)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    logger.debug(update_str)


def main():
    """Start the bot."""
    app = Application.builder().token(accessToken).build()

    app.add_error_handler(error_handler)

    f_group = filters.Chat(group)
    f_pipe = filters.Chat(pipe)

    assert app.job_queue
    job: JobQueue = app.job_queue
    tz = timezone("Asia/Shanghai")  # local_tz
    jk = {"misfire_grace_time": None}  # job_kwargs

    groupCommands = []
    allCommands = []  # TODO

    # ===== weather =====
    # app.add_handler(CommandHandler('weather', weather))
    # allCommands.append(('weather', '清华目前的天气', 61))
    # app.add_handler(CommandHandler('forecast', forecast))
    # allCommands.append(('forecast', '清华降雨分钟级预报', 62))
    # app.add_handler(CommandHandler('forecast_hourly', forecast_hourly))
    # allCommands.append(('forecast_hourly', '清华天气小时级预报', 63))
    # job.run_repeating(caiyun, interval=60*5, first=0, job_kwargs=jk)
    # for hour in range(24):
    #     job.run_daily(weather_report, time=time(hour, 0, 0, tzinfo=tz),
    #                   data=hour, name='weather_report')
    # app.add_handler(MessageHandler(f_group & filters.TEXT, new_message))

    # ===== info =====
    # app.add_handler(CommandHandler('mute', mute, filters=f_group))
    # groupCommands.append(('mute', '屏蔽发布源', 71))
    # app.add_handler(CommandHandler('unmute', unmute, filters=f_group))
    # groupCommands.append(('unmute', '解除屏蔽发布源', 72))
    # app.add_handler(CommandHandler('mute_list', mute_show, filters=f_group))
    # groupCommands.append(('mute_list', '列出所有被屏蔽的发布源', 73))
    # app.add_handler(MessageHandler(
    #     f_pipe & filters.UpdateType.CHANNEL_POST, info))
    # job.run_daily(daily_report, time=time(23, 0, 0, tzinfo=tz))

    # ===== gadget =====
    app.add_handler(CommandHandler('roll', roll))
    allCommands.append(('roll', '从 1 开始的随机数', 81))
    app.add_handler(CommandHandler('callpolice', callpolice))
    allCommands.append(('callpolice', '在线报警', 82))
    # app.add_handler(CommandHandler('washer', washer))
    # allCommands.append(('washer', '洗衣机在线状态', 83))
    app.add_handler(CommandHandler('register', register))
    allCommands.append(('register', '一键注册防止失学', 84))

    # app.add_handler(CommandHandler('hitreds', hitreds, filters=(~f_group)))
    # allCommands.append(('hitreds', '一键打红人', 101))
    # app.add_handler(CommandHandler('spankreds', hitreds, filters=(~f_group)))
    # allCommands.append(('spankreds', '给红人来一巴掌', 102))
    # job.run_daily(hitreds_init, time=time(0, 0, 0, tzinfo=tz))

    # ===== yue =====
    app.add_handler(CommandHandler('payme', payme, filters=f_group))
    groupCommands.append(('payme', '显示你的收款码', 121))
    app.add_handler(CommandHandler('fan', fan, filters=f_group))
    groupCommands.append(('fan', '发起约饭', 122))
    app.add_handler(CommandHandler('yue', yue, filters=f_group))
    groupCommands.append(('yue', '约~', 123))
    app.add_handler(CommandHandler('buyue', gu, filters=f_group))
    groupCommands.append(('buyue', '不约~', 124))
    app.add_handler(CommandHandler('san', san, filters=f_group))
    groupCommands.append(('san', '饭饱散伙', 125))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.PHOTO, payme_upload))

    # ===== other =====
    job.run_repeating(send_heartbeat, interval=60, first=0, job_kwargs=jk)
    job.run_repeating(auto_delete, interval=60, first=30, job_kwargs=jk)

    logger.info('bot start')
    app.run_webhook(**webhookConfig)


if __name__ == '__main__':
    main()
