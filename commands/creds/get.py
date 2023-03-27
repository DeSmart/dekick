
import sys
from argparse import ArgumentParser, Namespace

from halo import logging

from lib.environments import get_environments
from lib.logger import log_exception
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.providers.credentials import get_vars


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    parser.add_argument(
        "--env",
        required=False,
        default="",
        help="choose environment to get credentials for",
        choices=get_environments(), # type: ignore
        )
    parser.set_defaults(func=main)
    parser_default_args(parser)

def main(parser: Namespace, args: list): # pylint: disable=unused-argument
    """Main entry point for this command."""
    parser_default_funcs(parser)
    func_param = parser.env
    try:
        get_envs(func_param)
        sys.exit(0)
    except Exception as error:  # pylint: disable=broad-except
        logging.error("Message or exit code: %s", error)
        log_exception(error)
        sys.exit(1)


def get_envs(func_param):
    """Show credentials."""
    get_vars(func_param)
