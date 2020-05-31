
import logging
from logging.handlers import SysLogHandler


class TwPlayerException(Exception):
    pass


def init_logger() -> None:
    root_logger = logging.getLogger()

    syslog_handler = SysLogHandler(("liva.local", 20514))
    root_logger.addHandler(syslog_handler)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.disabled = True


def get_logger() -> logging.Logger:
    return logging.getLogger("twtlplayer")
