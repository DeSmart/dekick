import sys
from argparse import ArgumentParser, Namespace

from lib.parser_defaults import (
    parser_add_subparser_for_subcommands,
    parser_default_args,
    parser_default_funcs,
)


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    module_name = __name__.rsplit(".", maxsplit=1)[-1]
    parser_add_subparser_for_subcommands(parser, module_name)
    parser.set_defaults(func=main)
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command."""

    parser_default_funcs(parser)
    sys.exit(0)
