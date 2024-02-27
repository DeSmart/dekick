import os
import sys
from argparse import ArgumentParser, Namespace

from lib.logger import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.providers.credentials import parser_driver_arguments
from lib.providers.credentials import ui_pull as provider_ui_pull


def parser_help() -> str:
    """Set description for this command, used in arguments parser"""
    return (
        "Pulls all environment variables and saves to envs/ dir for further processing"
    )


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
    exit_code = ui_pull(**vars(parser))
    sys.exit(exit_code)


def ui_pull(*args, **kwargs) -> int:
    """UI wrapper pulling all environment variables and saving to envs/ dir"""
    provider_ui_pull()
    return 0
