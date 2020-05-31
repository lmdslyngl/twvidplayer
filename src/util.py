
import logging
from logging.handlers import SysLogHandler
import json
from functools import lru_cache


class TwPlayerException(Exception):
    pass


def init_logger() -> None:
    config = load_config()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    syslog_handler = SysLogHandler((config["syslog_host"], config["syslog_port"]))
    root_logger.addHandler(syslog_handler)

    formatter = logging.Formatter("%(name)s %(message)s")
    syslog_handler.setFormatter(formatter)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.disabled = True


def get_logger() -> logging.Logger:
    return logging.getLogger("twtlplayer")


@lru_cache(maxsize=1)
def load_config() -> dict:
    with open("config.json", "r") as f:
        return json.load(f)
