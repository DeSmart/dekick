"""
Check services defined in docker-compose.yml file are running
"""
import sys
from argparse import ArgumentParser, Namespace

from rich.console import Console
from rich.traceback import install

from flavours.shared import get_all_services, is_service_running
from lib.logger import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import C_CMD, C_END

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
    sys.exit(status())


def status() -> int:
    """It runs yarn in a container

    Args:
        args (list): _description_
        env (Union[dict, None], optional): additional env added on top of default one. Defaults to None.
        raise_exception (bool, optional): raise exception if something goes wrong. Defaults to True.
        raise_error (bool, optional): raise error if something goes wrong. Defaults to True.
        capture_output (bool, optional): capture output to return value. Defaults to False.
    """

    def run(service):
        if is_service_running(service):
            return {
                "success": True,
                "text": f"Service {C_CMD}{service}{C_END} is running",
            }
        return {
            "success": False,
            "text": f"Service {C_CMD}{service}{C_END} is not running",
        }

    services = get_all_services()

    for service in services:
        ret = run_func(
            text=f"Checking {C_CMD}{service}{C_END}",
            func=run,
            func_args={"service": service},
            terminate=False,
        )

        if ret is False:
            return 1

    return 0
