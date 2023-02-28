"""Logging module for Dekick""" ""
import logging
from sys import stdout
from typing import Union

from lib.fs import chown, touch
from lib.settings import (
    C_CMD,
    C_CODE,
    C_END,
    C_FILE,
    get_function_time_end,
    get_function_time_start,
    is_profiler_mode,
    show_elapsed_time,
)
from lib.spinner import create_spinner, set_spinner_mode

LOG_FILE_NAME = ""
CURRENT_LOG_LEVEL = ""


def install_logger(level: str = "", filename: str = ""):
    """Installs the logger and sets the log level and filenam"""
    function_start = get_function_time_start()

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
        log_format = f"{C_CMD}%(asctime)s{C_END} {C_CODE}%(levelname)s{C_END}: {C_FILE}[%(module)s:%(funcName)s:%(lineno)d]{C_END} %(message)s"
    elif level == "DEBUG":
        log_format = "%(asctime)s %(levelname)s: [%(module)s:%(funcName)s:%(lineno)d] %(message)s"

    config = {
        "filename": filename,
        "force": True,
        "encoding": "utf-8",
        "level": level,
        "format": log_format,
        "datefmt": "[%Y-%m-%d %X]",
    }

    # # Special mode - log all to stdout
    if filename == "stdout":
        config["stream"] = stdout
        del config["filename"]
        set_spinner_mode("null")
    else:
        touch(filename)
        chown(filename)

    logging.basicConfig(**config)

    spinner.succeed()
    function_end = get_function_time_end()
    elapsed_time = function_end - function_start
    if is_profiler_mode():
        show_elapsed_time(elapsed_time)


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
