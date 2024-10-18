import logging
from datetime import datetime

import sentry_sdk
from sentry_sdk.integrations.logging import SentryHandler

from base.config import config

SENTRY_INIT = False


def sentry_init():
    global SENTRY_INIT
    if SENTRY_INIT:
        return
    SENTRY_INIT = True

    if config['SENTRY'].get('dsn') is None:
        return

    sentry_sdk.init(
        dsn=config['SENTRY']['dsn'],
        release=datetime.now().strftime('%Y-%m-%d'),
        attach_stacktrace=True,
    )

    shlr = SentryHandler()
    shlr.setLevel('WARNING')
    logging.getLogger().addHandler(shlr)
    logging.getLogger(__name__).addHandler(shlr)
