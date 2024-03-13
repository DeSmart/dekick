import os
import sys
from argparse import ArgumentParser, Namespace
from logging import error

from lib.logger import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.providers.credentials import parser_driver_arguments
from lib.providers.credentials import ui_push as provider_ui_push
from lib.settings import C_END, C_ERROR


def parser_help() -> str:
    """Set description for this command, used in arguments parser"""
    return "Pushes all environment variables from envs/ dir for further processing"


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    parser.set_defaults(func=main)
    parser_default_args(parser)
    sub_command = os.path.splitext(os.path.basename(__file__))[0]
    parser_driver_arguments(sub_command, parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command."""
    parser_default_funcs(parser)
    install_logger(parser.log_level, parser.log_filename)
    exit_code = ui_push(**vars(parser))
    sys.exit(exit_code)


def ui_push(*args, **kwargs) -> int:
    """UI wrapper pulling all environment variables and saving to envs/ dir"""
    try:
        provider_ui_push()
    except Exception as e:
        error(e)
        print(f"{C_ERROR}Error{C_END}: {e}")
        return 1
    return 0
