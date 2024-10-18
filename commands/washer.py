# import requests
# import json

# from base.log import logger
# from base.pool import add_pool


# def washer_status(obj):
#     return f"{obj['tower']}{obj['floorName']}{obj['macUnionCode']} {obj['status']}"


# def get_washer(query):
#     try:
#         res = requests.get(
#             f'https://washer.thu.services/?s={query}&j', timeout=(5, 10))
#     except requests.exceptions.RequestException:
#         return '网络错误。'

#     ret = json.loads(res.content.decode('utf-8'))['result']
#     reply = [washer_status(x) for x in ret]
#     if reply == []:
#         return '查询无结果，请检查参数是否正确。'
#     elif len(reply) > 20:
#         return '\n'.join(reply[:20]) + '\n...'
#     else:
#         return '\n'.join(reply)


# def washer(update, context):

#     logger.info('\\washer {} '.format(
#         update.message.chat_id) + json.dumps(context.args))

#     if len(context.args) == 0:
#         args = '紫荆2号楼'
#     else:
#         args = ''.join(context.args)

#     msg = context.bot.send_message(
#         update.message.chat_id, 'checking...', reply_to_message_id=update.message.message_id)
#     text = get_washer(args)
#     context.bot.delete_message(update.message.chat_id, msg.message_id)
#     msg = context.bot.send_message(update.message.chat_id, text,
#                                    reply_to_message_id=update.message.message_id)
#     add_pool(msg)
