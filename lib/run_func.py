import logging
import re
import sys
import time
from math import inf
from typing import Union

from rich.traceback import install

from lib.logger import get_log_filename, log_exception
from lib.settings import (
    C_CODE,
    C_END,
    C_ERROR,
    C_FILE,
    C_TIME,
    TERMINAL_COLUMN_WIDTH,
    get_seconds_since_dekick_start,
    is_profiler_mode,
)
from lib.spinner import DEFAULT_SPINNER_MODE, create_spinner

install()

# pylint: disable=too-many-branches
def run_func(
    text: str,
    func=None,
    func_args: Union[None, dict] = None,
    terminate: bool = True,
) -> bool:
    """Run function with spinner

    Args:
        text (str): _description_
        func (_type_, optional): _description_. Defaults to None.
        func_args (Union[None, dict], optional): _description_. Defaults to None.
        terminate (bool, optional): _description_. Defaults to True.

    Returns:
        bool: _description_
    """
    logging.debug(locals())

    logging.info(text)
    spinner = create_spinner(text=text)

    spinner.start()

    if func is None:
        time.sleep(0.25)
        spinner.succeed()
        return True

    out = {}

    try:
        function_start = get_seconds_since_dekick_start()
        if func_args is not None:
            out = func(**func_args)
        else:
            out = func()
        if out is None: # pylint: disable=using-constant-test
            out = {}
        if "text" not in out:
            out["text"] = text
        if "text" in out and out["text"] == "":
            out["text"] = text
        function_end = get_seconds_since_dekick_start()
        elapsed_time = function_end - function_start
        if is_profiler_mode() :
            logging.debug("function elapsed time: %s", f"{elapsed_time:.2f}")
            out["text"] = out["text"] + get_elapsed_time((out["text"]), elapsed_time)

    except Exception as error:  # pylint: disable=broad-except

        log_file = get_log_filename()
        authentication_error = "403 Forbidden"
        error_text = str(error.args[0])
        def find_text_in_error_message(error_message, text_to_find):
            """
            This function takes an error message and a text to find, and returns True
            if the text is present in the error message, and False otherwise.
            """
            if text_to_find in str(error_message):
                return True
            else:
                return False
        if find_text_in_error_message(error_text, authentication_error):
            fail_text = (
            f"{C_ERROR}Failed{C_END}. You may not have permission to access this repository. "
            + "Please, check it!"
        )
        else:
            fail_text = (
            f"{C_ERROR}Failed{C_END}. Please see {C_FILE}{log_file}{C_END}"
            + " for more information"
        )

        if DEFAULT_SPINNER_MODE == "halo":
            fail_text = (
                f"{text} {C_ERROR}failed{C_END}. Please see {C_FILE}{log_file}{C_END}"
                + " for more information"
            )

        spinner.fail(text=fail_text)

        logging.error("Error message: %s", error.args[0])
        log_exception(error)

        if terminate is True:
            sys.exit(1)

    if "success" in out and out["success"] is not True:
        logging.debug(out)

        if "type" in out and out["type"] == "warn":
            logging.warning(out["text"])
            spinner.warn(text=out["text"])
        else:
            logging.error(out["text"])
            spinner.fail(text=out["text"])

        if terminate is True:
            logging.debug("Terminating DeKick with exit code 1")
            sys.exit(1)
        else:
            return False

    if out is not None and "text" in out and out["text"] != "":
        logging.info(out["text"])
        spinner.succeed(text=out["text"])
    else:
        spinner.succeed()

    if out is not None and "func" in out:
        logging.debug("Calling another function from run_func() with args: %s", out)

        if "func_args" in out:
            return out["func"](**out["func_args"])

        return out["func"]()

    return True


def get_elapsed_time(text: str, elapsed_time: int) -> str:
    """Show elapsed time"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    elapsed_time_formatted = f"{elapsed_time}s"
    result = ansi_escape.sub('', text)
    text_length = len(result)
    right_margin = 5
    checks = [
        (0, 1, C_TIME, "< 1s"),
        (1, 10, C_TIME, elapsed_time_formatted),
        (10, 30, C_CODE, elapsed_time_formatted),
        (30, inf, C_ERROR, elapsed_time_formatted),
    ]
    for check in checks:
        if check[0] <= elapsed_time < check[1]:
            return f" {check[2]}{check[3]}{C_END}".rjust(
                (TERMINAL_COLUMN_WIDTH + right_margin) - text_length, " "
            )
    return ""

