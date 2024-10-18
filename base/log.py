import sys
import logging
import colorlog
from base.config import config

BASIC_FORMAT = '%(asctime)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s'
COLOR_FORMAT = '%(log_color)s%(asctime)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s'
DATE_FORMAT = None
basic_formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
color_formatter = colorlog.ColoredFormatter(COLOR_FORMAT, DATE_FORMAT)


class MaxFilter:
    def __init__(self, max_level):
        self.max_level = max_level

    def filter(self, record):
        if record.levelno <= self.max_level:
            return True


chlr = logging.StreamHandler(stream=sys.stdout)
chlr.setFormatter(color_formatter)
chlr.setLevel('INFO')
chlr.addFilter(MaxFilter(logging.INFO))

ehlr = logging.StreamHandler(stream=sys.stderr)
ehlr.setFormatter(color_formatter)
ehlr.setLevel('WARNING')

fhlr = logging.handlers.TimedRotatingFileHandler(
    config['BOT']['logpath'] + 'server', when='H', interval=1, backupCount=24*7)
fhlr.setFormatter(basic_formatter)
fhlr.setLevel('DEBUG')

logger = logging.getLogger()
logger.setLevel('NOTSET')
logger.addHandler(fhlr)

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
logger.addHandler(chlr)
logger.addHandler(ehlr)
