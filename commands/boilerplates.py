"""
Runs the specified command
"""
from argparse import ArgumentParser, Namespace

from rich.console import Console
from rich.traceback import install

from commands.local import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs

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
    local(parser)


def local(parser: Namespace) -> int:
    """Starts a local development environment"""

    parser_default_funcs(parser)
    install_logger(
        parser.log_level,
        parser.log_filename,
    )

    return True
