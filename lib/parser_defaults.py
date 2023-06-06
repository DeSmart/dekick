"""Default arguments and functions for commands"""
from argparse import ArgumentParser
from importlib import import_module

from lib.settings import DEKICK_COMMANDS, set_ci_mode, set_pytest_mode
from lib.spinner import set_spinner_mode


def parser_default_args(parser):
    """Adds default arguments to commands"""

    def log_level():
        """Adds the log level argument"""
        parser.add_argument(
            "--log-level",
            required=False,
            default="INFO",
            help="Log level used for logging, default is INFO, use DEBUG to get more information",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        )

    def log_filename():
        parser.add_argument(
            "--log-filename",
            required=False,
            default="",
            help="Log filename used for logging. Use special value `stdout` to log directly to stdout.",
        )

    def ci_cd():
        """Flag to indicate if we are running tests in CI/CD environment"""
        parser.add_argument(
            "--ci",
            required=False,
            action="store_true",
            help="Used for running command in CI/CD environment",
        )

    def pytest():
        """Flag to indicate if we are running tests with Pytest"""
        parser.add_argument(
            "--pytest",
            required=False,
            action="store_true",
            help="Used for running command with PyTest environment",
        )

    def spinner():
        """What spinner to use?"""
        parser.add_argument(
            "--spinner",
            required=False,
            type=str,
            choices=["simple", "null", "halo"],
            help="What spinner to use? Default is `halo` but when running in a "
            + "CI/CD pipeline, when there's no TTY, it's automatically used `simple`",
        )

    log_level()
    log_filename()
    ci_cd()
    pytest()
    spinner()


def parser_default_funcs(parser):
    """Adds default functions to commands"""

    def pytest():
        """Sets the pytest mode"""
        set_pytest_mode(parser.pytest)

    def ci_cd():
        """Sets the CI/CD mode"""
        set_ci_mode(parser.ci)

    def spinner():
        set_spinner_mode(parser.spinner)

    pytest()
    ci_cd()
    spinner()


def parser_add_subparser_for_subcommands(parser: ArgumentParser, module_name: str):
    """Adds subparsers for subcommands"""
    sub_parser = parser.add_subparsers(
        dest="subcommand", required=True, metavar="subcommand"
    )
    for sub_command in DEKICK_COMMANDS["sub_commands"][module_name]:
        sub_module_name = sub_command.replace("-", "_")  # pylint: disable=invalid-name
        module = import_module(f"commands.sub_{module_name}.{sub_module_name}")
        sub_command_parser = sub_parser.add_parser(
            sub_command, help=module.parser_help()
        )
        module.arguments(sub_command_parser)
