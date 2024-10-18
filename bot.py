import configparser
import logging
import sys
import traceback
from datetime import datetime, time, timedelta
from logging import Filter
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

from pytz import timezone
from telegram import (BotCommandScopeChat, BotCommandScopeDefault, Chat,
                      Message, Update)
from telegram.error import Forbidden, TelegramError
from telegram.ext import (Application, CommandHandler, ContextTypes, JobQueue,
                          MessageHandler, Updater, filters)

from base import message
from base.config import accessToken, group, pipe, webhookConfig
from base.log import logger
from base.mute import mute, mute_show, unmute
from base.pool import auto_delete
from command.gadget import (callpolice, fan, gu, payme, payme_upload, register,
                            roll, san, yue)
from command.heartbeat import send_heartbeat
from command.info import daily_report, info
from command.weather import (realtime_forecast, realtime_weather, weather_poll,
                             weather_report)


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
    message.init(app.bot)

    f_group = filters.Chat(group)
    f_pipe = filters.Chat(pipe)

    assert app.job_queue
    job: JobQueue = app.job_queue
    tz = timezone("Asia/Shanghai")  # local_tz
    jk = {"misfire_grace_time": None}  # job_kwargs

    groupCommands = []
    allCommands = []

    # ===== weather =====
    # 定期获取天气数据
    job.run_repeating(weather_poll, interval=60, first=0, job_kwargs=jk)
    # 当前位置天气
    app.add_handler(CommandHandler('weather', realtime_weather))
    allCommands.append(('weather', '此时清华的天气', 45))
    # 当前位置降雨概率
    app.add_handler(CommandHandler('forecast', realtime_forecast))
    allCommands.append(('forecast', '此时清华的降雨概率', 46))
    # 天气预报以及更新
    for hour in range(24):
        job.run_daily(weather_report, time=time(hour, 0, 0, tzinfo=tz),
                      data=hour, name='weather_report')

    # ===== info =====
    app.add_handler(CommandHandler('mute', mute, filters=f_group))
    groupCommands.append(('mute', '屏蔽发布源', 71))
    app.add_handler(CommandHandler('unmute', unmute, filters=f_group))
    groupCommands.append(('unmute', '解除屏蔽发布源', 72))
    app.add_handler(CommandHandler('mute_list', mute_show, filters=f_group))
    groupCommands.append(('mute_list', '列出所有被屏蔽的发布源', 73))
    app.add_handler(MessageHandler(
        f_pipe & filters.UpdateType.CHANNEL_POST, info))
    job.run_daily(daily_report, time=time(23, 0, 0, tzinfo=tz))

    # ===== gadget =====
    app.add_handler(CommandHandler('roll', roll))
    allCommands.append(('roll', '从 1 开始的随机数', 81))
    app.add_handler(CommandHandler('callpolice', callpolice))
    allCommands.append(('callpolice', '在线报警', 82))
    app.add_handler(CommandHandler('register', register))
    allCommands.append(('register', '一键注册防止失学', 83))

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

    # Add commands into menu
    groupCommands += allCommands
    groupCommands = sorted(groupCommands, key=lambda x: x[2])
    groupCommands = [(x[0], x[1]) for x in groupCommands]
    allCommands = sorted(allCommands, key=lambda x: x[2])
    allCommands = [(x[0], x[1]) for x in allCommands]

    async def set_commands(context: ContextTypes.DEFAULT_TYPE):
        await context.bot.set_my_commands(allCommands, scope=BotCommandScopeDefault())
        await context.bot.set_my_commands(groupCommands, scope=BotCommandScopeChat(group))
    job.run_once(set_commands, when=0, job_kwargs=jk)

    logger.info('bot start')
    app.run_webhook(**webhookConfig)


if __name__ == '__main__':
    main()
