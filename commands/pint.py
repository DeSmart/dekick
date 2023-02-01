"""
Runs pint
"""
import sys
from argparse import ArgumentParser, Namespace
from typing import Union

from rich.console import Console
from rich.traceback import install

from commands.docker_compose import docker_compose
from lib.logger import install_logger
from lib.misc import get_flavour_container
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.settings import CURRENT_UID

install()
console = Console()


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
    install_logger(parser.log_level, parser.log_filename)
    sys.exit(pint(args=args, raise_exception=False)["returncode"])


def pint(
    args: list,
    env: Union[dict, None] = None,
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = True,
):
    """It runs pint in a container

    Args:
        args (list): _description_
        env (Union[dict, None], optional): additional env added on top of default one. Defaults to None.
        raise_exception (bool, optional): raise exception if something goes wrong. Defaults to True.
        raise_error (bool, optional): raise error if something goes wrong. Defaults to True.
        capture_output (bool, optional): capture output to return value. Defaults to False.
    """

    container = get_flavour_container()

    cmd = "run"
    args = ["--rm", "--user", CURRENT_UID, container, "pint"] + args

    return docker_compose(
        cmd=cmd,
        args=args,
        env=env,
        raise_exception=raise_exception,
        raise_error=raise_error,
        capture_output=capture_output,
    )
