from base.caiyun import daily_weather
from base.config import channel, group
from base.format import escaped
from commands.info import info_daily


def weather_report(context):
    text = daily_weather(context.job.context)
    context.bot.send_message(chat_id=group,   text=text)
    context.bot.send_message(chat_id=channel, text=text)


def daily_report(context):
    text = 'Today Info:'
    today = info_daily()
    for source in today.keys():
        text += '\n \\- %s' % escaped(source)
        for news in today[source]:
            text += '\n[%s](%s)' % (escaped(news['title']), news['url'])
    context.bot.send_message(
        chat_id=group, text=text, parse_mode='MarkdownV2', disable_web_page_preview=True)
