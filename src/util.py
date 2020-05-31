
import logging
from logging.handlers import SysLogHandler


class TwPlayerException(Exception):
    pass


def init_logger() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)


    syslog_handler = SysLogHandler(("liva.local", 20514))
    root_logger.addHandler(syslog_handler)

    formatter = logging.Formatter("%(name)s %(message)s")
    syslog_handler.setFormatter(formatter)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.disabled = True


def get_logger() -> logging.Logger:
    return logging.getLogger("twtlplayer")
