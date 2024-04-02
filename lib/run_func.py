import logging
import re
import sys
import time
from math import inf
from subprocess import CalledProcessError
from typing import Union

from rich.traceback import install

from lib.logger import get_log_filename, log_exception
from lib.settings import (
    C_CMD,
    C_CODE,
    C_END,
    C_ERROR,
    C_FILE,
    C_TIME,
    TERMINAL_COLUMN_WIDTH,
    get_seconds_since_dekick_start,
)
from lib.spinner import create_spinner

install()

# pylint: disable=too-many-branches


def run_func(
    text: str,
    func=None,
    func_args: Union[None, dict] = None,
    terminate: bool = True,
    show_elapsed_time=True,
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
        time.sleep(0.1)
        spinner.succeed()
        return True

    out = {}
    out_text = ""

    try:
        function_start = get_seconds_since_dekick_start(1)
        if func_args is not None:
            out = func(**func_args)
        else:
            out = func()
        if out is None:  # pylint: disable=using-constant-test
            out = {}

        if "text" not in out:
            out_text = text
        if "text" in out:
            out_text = text if out["text"] == "" else out["text"]

        function_end = get_seconds_since_dekick_start(1)
        elapsed_time = round(function_end - function_start, 1)
        if show_elapsed_time:
            out_text = out_text + get_elapsed_time((out_text), elapsed_time)

    except CalledProcessError as error:
        log_file = get_log_filename()
        lines = error.output.rstrip().splitlines()
        lines = [
            "  " + line
            for line in lines
            if not re.match("\\s+Container .* Running", line)
        ]
        output_formatted = "\n".join(lines)
        fail_text = f"{text} {C_ERROR}failed{C_END}\n\n{output_formatted}\n\n  "
        spinner.fail(text=fail_text)
        log_exception(error)

        if terminate is True:
            sys.exit(1)

    except Exception as error:  # pylint: disable=broad-except
        log_file = get_log_filename()
        fail_text = (
            f"{text} {C_ERROR}failed{C_END}\n  {error}\n\n  "
            + f"Enable debug mode by adding {C_CMD}--log-level DEBUG{C_END} "
            + f"and look into {C_FILE}{log_file}{C_END} "
            + "for more information about the error"
        )
        spinner.fail(text=fail_text)

        logging.error(error.args[0])
        log_exception(error)

        if terminate is True:
            sys.exit(1)

    out_text_debug = (
        str(out["text"]).strip().replace("\n", " ") if "text" in out else ""
    )

    if "success" in out and out["success"] is not True:
        logging.debug("%s output: %s", text, out_text_debug)

        if "type" in out and out["type"] == "warn":
            logging.warning(out_text_debug)
            spinner.warn(text=out_text)
        else:
            logging.error(out_text_debug)
            spinner.fail(text=out_text)

        if terminate is True:
            logging.debug("Terminating DeKick with exit code 1")
            sys.exit(1)
        else:
            if out is not None and "func" in out:
                logging.debug(
                    "Calling another function from run_func() with args: %s", out
                )

                if "func_args" in out:
                    return out["func"](**out["func_args"])

                return out["func"]()

            return False

    if out is not None and "text" in out and out["text"] != "":
        logging.info(out_text_debug)
    if out is not None and out_text != "":
        spinner.succeed(text=out_text)
    else:
        spinner.succeed()

    if out is not None and "func" in out:
        logging.debug("Calling another function from run_func() with args: %s", out)

        if "func_args" in out:
            return out["func"](**out["func_args"])

        return out["func"]()

    return True


def get_elapsed_time(text: str, elapsed_time: float) -> str:
    """Show elapsed time"""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    result = ansi_escape.sub("", text).replace("\n", "")
    text_length = len(result)

    elapsed_time_formatted = (
        ""
        if elapsed_time < 1
        else (
            f"{int(elapsed_time)}s"
            if elapsed_time.is_integer()
            else f"{elapsed_time:.1f}s"
        )
    )

    right_margin = 5
    colors = [
        (0, 10, C_TIME),
        (10, 30, C_CODE),
        (30, inf, C_ERROR),
    ]
    for check in colors:
        if check[0] <= elapsed_time < check[1]:
            return f" {check[2]}{elapsed_time_formatted}{C_END}".rjust(
                (TERMINAL_COLUMN_WIDTH + right_margin) - text_length, " "
            )
    return ""
