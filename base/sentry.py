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

    if 'SENTRY' not in config or config['SENTRY'].get('dsn') is None:
        return

    sentry_sdk.init(
        dsn=config['SENTRY']['dsn'],
        release=datetime.now().strftime('%Y-%m-%d'),
        attach_stacktrace=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        _experiments={
            # Set continuous_profiling_auto_start to True
            # to automatically start the profiler on when
            # possible.
            "continuous_profiling_auto_start": True,
        },
    )

    shlr = SentryHandler()
    shlr.setLevel('WARNING')
    logging.getLogger().addHandler(shlr)
    logging.getLogger(__name__).addHandler(shlr)
