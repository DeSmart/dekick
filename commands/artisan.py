"""
Runs artisan
"""
import sys
from argparse import ArgumentParser, Namespace
from typing import Union

from rich.traceback import install

from commands.docker_compose import docker_compose
from lib.logger import install_logger
from lib.misc import get_flavour_container
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import C_CMD, C_CODE, C_END, CURRENT_UID

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
    install_logger(parser.log_level, parser.log_filename)
    sys.exit(artisan(args=args, raise_exception=False)["returncode"])


# pylint: disable=too-many-arguments, dangerous-default-value
def artisan(
    args: list,
    env: Union[dict, None] = None,
    docker_env: dict = {},
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = False,
):
    """It runs artisan in a container

    Args:
        args (list): _description_
        env (Union[dict, None], optional): additional env added on top of default one. Defaults to None.
        raise_exception (bool, optional): raise exception if something goes wrong. Defaults to True.
        raise_error (bool, optional): raise error if something goes wrong. Defaults to True.
        capture_output (bool, optional): capture output to return value. Defaults to False.
    """

    container = get_flavour_container()

    cmd = "run"
    args = ["--rm", "--user", CURRENT_UID, container, "artisan"] + args

    return docker_compose(
        cmd=cmd,
        args=args,
        env=env,
        docker_env=docker_env,
        raise_exception=raise_exception,
        raise_error=raise_error,
        capture_output=capture_output,
    )


def ui_artisan(
    args: list,
    env: Union[dict, None] = None,
    docker_env: dict = {},
    raise_exception: bool = True,
    raise_error: bool = True,
):
    """UI wrapper for artisan"""

    def run():
        if (
            artisan(
                args, env, docker_env, raise_exception, raise_error, capture_output=True
            )["returncode"]
            != 0
        ):
            return {"success": False, "text": "Failed to run artisan"}

        return {"success": True}

    artisan_args = " ".join(args)
    run_func(
        text=f"Running {C_CMD}artisan{C_END} {C_CODE}{artisan_args}{C_END}", func=run
    )
