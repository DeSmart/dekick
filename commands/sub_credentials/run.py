import os
import sys
from argparse import ArgumentParser, Namespace
from logging import error

from commands.local import check_dekickrc
from lib.logger import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.providers.credentials import parser_driver_arguments
from lib.providers.credentials import ui_run_action as provider_ui_run_action
from lib.settings import C_CODE, C_END, C_ERROR, C_FILE


def parser_help() -> str:
    """Set description for this command, used in arguments parser"""
    return (
        "Run action specific to credentials provider "
        + f"defined in {C_FILE}.dekickrc.yml{C_END} "
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
    exit_code = ui_run(**vars(parser))
    sys.exit(exit_code)


def ui_run(**kwargs):
    """UI wrapper"""
    check_dekickrc()
    try:
        provider_ui_run_action()
    except Exception as e:
        error(e)
        print(f"{C_ERROR}Error{C_END}: {e}")
        return 1
