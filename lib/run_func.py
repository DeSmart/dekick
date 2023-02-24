import logging
import sys
import time
from typing import Union

from rich.traceback import install

from lib.logger import get_log_filename, log_exception
from lib.settings import C_END, C_ERROR, C_FILE
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

    out = None

    try:
        if func_args is not None:
            out = func(**func_args)
        else:
            out = func()
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

    if out is not None and out["success"] is not True:
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
