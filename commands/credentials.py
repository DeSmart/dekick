import sys
from argparse import ArgumentParser, Namespace
from importlib import import_module

from lib.parser_defaults import parser_default_args, parser_default_funcs

DEKICK_CREDENTIALS_SUB_COMMANDS = ["get", "update", "savedotenv"]


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    sub_parser = parser.add_subparsers(
        dest="subcommand", required=True, metavar="subcommand"
    )
    for sub_command in DEKICK_CREDENTIALS_SUB_COMMANDS:
        sub_command_parser = sub_parser.add_parser(
            sub_command, help=f"{sub_command.capitalize()} credentials"
        )
        module_name = sub_command.replace("-", "_")  # pylint: disable=invalid-name
        module = import_module(f"commands.sub_credentials.{module_name}")
        module.arguments(sub_command_parser)

    parser.set_defaults(func=main)
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command."""

    parser_default_funcs(parser)
    sys.exit(0)
