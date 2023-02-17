"""
Runs the specified command
"""
import logging
import sys
from argparse import ArgumentParser, Namespace

from rich.traceback import install

from commands.local import flavour_action, install_logger
from commands.stop import stop
from lib.misc import randomize_compose_project_name, randomize_ports
from lib.parser_defaults import parser_default_args, parser_default_funcs

install()


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

    sys.exit(
        test(
            log_level=parser.log_level or "INFO",
            log_filename=parser.log_filename or "dekick-test.log",
        )
    )


# pylint: disable=too-many-arguments
def test(
    log_level: str,
    log_filename: str,
) -> int:
    """
    Run unit test for specific flavour
    """
    install_logger(log_level, log_filename)

    randomize_ports()
    randomize_compose_project_name()

    try:
        flavour_action("test")
        return 0
    except Exception as err:  # pylint: disable=broad-except
        logging.error("Error running tests")
        logging.debug("Error: %s", err)
        stop(remove=True, volumes=False)
        return 1
