"""
Runs yarn
"""
import logging
import sys
from argparse import ArgumentParser, Namespace
from typing import Union

from rich.traceback import install

from commands.docker_compose import docker_compose
from lib.logger import install_logger
from lib.misc import get_flavour_container
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import C_CMD, C_END, CURRENT_UID

install()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """
    parser.set_defaults(func=main)
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse library
        args (list):
    """
    parser_default_funcs(parser)
    exit_code = 0

    if parser.log_filename:
        install_logger(parser.log_level, parser.log_filename)
        exit_code = ui_yarn(args=args)
    else:
        exit_code = yarn(args=args, raise_exception=False, capture_output=False)[
            "returncode"
        ]

    sys.exit(exit_code)


def ui_yarn(**kwargs):
    """UI wrapper for docker_compose"""

    def wrapper(**kwargs):
        yarn(raise_exception=True, **kwargs)

    args = kwargs["args"][0] if "args" in kwargs else ""

    return run_func(
        text=f"Running yarn {C_CMD}{args}{C_END}", func=wrapper, func_args=kwargs
    )


def yarn(
    args: list,
    env: Union[dict, None] = None,
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = True,
):
    """It runs yarn in a container

    Args:
        args (list): _description_
        env (Union[dict, None], optional): additional env added on top of default one. Defaults to None.
        raise_exception (bool, optional): raise exception if something goes wrong. Defaults to True.
        raise_error (bool, optional): raise error if something goes wrong. Defaults to True.
        capture_output (bool, optional): capture output to return value. Defaults to False.
    """
    logging.info("Running yarn(%s)", args)

    container = get_flavour_container()

    cmd = "run"
    args = [
        "--rm",
        "-e",
        "HOME=/tmp",
        "--user",
        CURRENT_UID,
        container,
        "yarn",
    ] + args

    return docker_compose(
        cmd=cmd,
        args=args,
        env=env,
        raise_exception=raise_exception,
        raise_error=raise_error,
        capture_output=capture_output,
    )
