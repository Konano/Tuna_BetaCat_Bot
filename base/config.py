import configparser

config = configparser.RawConfigParser()
config.read('config.ini')

accessToken = config['BOT']['accesstoken']

group = config['BOT'].getint('group')
channel = config['BOT'].getint('channel')
pipe = config['BOT'].getint('pipe')

logFile = config['BOT']['logpath'] + 'server'

heartbeatURL = config['BOT'].get('heartbeat')

caiyunToken = config['CAIYUN']['token']

webhookConfig = {
    'listen': config['WEBHOOK']['listen'],
    'port': int(config['WEBHOOK']['port']),
    'cert': config['WEBHOOK']['cert'],
    'webhook_url': config['WEBHOOK']['webhook_url'],
    'secret_token': config['WEBHOOK']['secret_token']
}
