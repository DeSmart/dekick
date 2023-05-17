"""Logging module for Dekick""" ""
import logging
from os import path
from sys import stdout
from typing import Union

from lib.fs import chown, touch
from lib.settings import C_CMD, C_CODE, C_END, C_FILE, DEKICK_PATH
from lib.spinner import create_spinner, set_spinner_mode

LOG_FILE_NAME = ""
CURRENT_LOG_LEVEL = ""


class MyFormatter(logging.Formatter):
    """Custom formatter to add modulefilename to log record"""

    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def format(self, record):
        if not hasattr(record, "module"):
            record.module = ""  # Set a default value for modulefilename
        return super().format(record)


class LoggerFilter(logging.Filter):
    """Custom filter to add modulefilename to log record"""

    def filter(self, record):
        record.module = path.abspath(record.pathname).replace(DEKICK_PATH + "/", "")
        return True


def install_logger(level: str = "", filename: str = ""):
    """Installs the logger and sets the log level and filenam"""

    filename = "dekick.log" if filename == "" else filename
    level = "INFO" if level == "" else level

    set_log_level(level)
    set_log_filename(filename)
    spinner = create_spinner(
        f"Logging to {C_CODE}{filename}{C_END} (level {C_CMD}{level}{C_END})"
    )

    spinner.start()

    log_format = "%(asctime)s %(levelname)s: %(message)s"
    if filename == "stdout":
        log_format = f"{C_CMD}%(asctime)s{C_END} {C_CODE}%(levelname)s{C_END}: {C_FILE}[%(module)s:%(lineno)d]{C_END} %(message)s"
    elif level == "DEBUG":
        log_format = "%(asctime)s %(levelname)s: [%(module)s:%(lineno)d] %(message)s"

    if filename == "stdout":
        handler = logging.StreamHandler(stream=stdout)
    elif filename:
        handler = logging.FileHandler(filename, mode="w", encoding="utf-8")
    else:
        handler = logging.StreamHandler()

    handler.addFilter(LoggerFilter())
    formatter = MyFormatter(log_format, datefmt="[%Y-%m-%d %H:%M:%S]")
    handler.setFormatter(formatter)

    config = {
        "force": True,
        "level": level,
        "format": log_format,
        "handlers": [handler],
    }

    # # Special mode - log all to stdout
    if filename == "stdout":
        set_spinner_mode("null")
    else:
        touch(filename)
        chown(filename)

    logging.basicConfig(**config)

    spinner.succeed()


def set_log_filename(filename: Union[str, None]):
    """Sets the current log filename"""
    global LOG_FILE_NAME  # pylint: disable=global-statement
    LOG_FILE_NAME = filename


def get_log_filename() -> str:
    """Returns the current log filename"""
    return LOG_FILE_NAME


def get_log_level() -> str:
    """Returns the current log level"""
    return CURRENT_LOG_LEVEL


def set_log_level(level: str):
    """Sets the current log level"""
    global CURRENT_LOG_LEVEL  # pylint: disable=global-statement
    CURRENT_LOG_LEVEL = level


def log_exception(exception: Exception):
    """Logs an exception"""
    if get_log_level() == "DEBUG":
        logging.exception(exception)
