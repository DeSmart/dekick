import logging
import sys
import time
from typing import Union

from rich.traceback import install

from lib.logger import get_log_filename, log_exception
from lib.settings import (
    C_CODE,
    C_END,
    C_ERROR,
    C_FILE,
    C_TIME,
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
            out["text"] = out["text"] + get_elapsed_time(elapsed_time)

    except Exception as error:  # pylint: disable=broad-except

        log_file = get_log_filename()
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


def get_elapsed_time(elapsed_time) -> str:
    """Show elapsed time"""
    if elapsed_time < 1:
        return " "
    if elapsed_time >1 and elapsed_time < 10:
        return (" ") + f"{C_TIME}{elapsed_time:.1f}s{C_END}"
    if elapsed_time > 10 and elapsed_time < 30:
        return (" ") + f"{C_CODE}{elapsed_time:.1f}s{C_END}"
    if elapsed_time > 30:
        return (" ") + f"{C_ERROR}{elapsed_time:.1f}s{C_END}"

    return (" ") + f"{C_TIME}{elapsed_time:.1f}s{C_END}"
