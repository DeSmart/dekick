
import sys
from argparse import ArgumentParser, Namespace

from halo import logging

from lib.logger import log_exception
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    parser.set_defaults(func=main)
    parser_default_args(parser)

def main(parser: Namespace, args: list): # pylint: disable=unused-argument
    """Main entry point for this command."""

    parser_default_funcs(parser)
    sys.exit(
        update_envs()
    )

def update_envs():
    """Show credentials."""
    run_func("update", func=greetings)

def greetings(arg):
    """Show greetings."""
    return arg