"""
Comments
"""

import argparse
import atexit
import logging
import sys
from importlib import import_module
from time import time

from humanfriendly import format_timespan
from rich.console import Console
from rich.traceback import install

from lib.dekickrc import get_dekick_version
from lib.settings import (
    C_CMD,
    C_CODE,
    C_END,
    C_FILE,
    DEKICK_COMMANDS,
    DEKICK_DOCKER_IMAGE,
    TERMINAL_COLUMN_WIDTH,
    get_dekick_time_start,
    is_dekick_dockerized,
    set_dekick_time_start,
)

install()
console = Console()

set_dekick_time_start()

parser = argparse.ArgumentParser(
    prog="dekick",
    description="""
DeKick is a provisioning and building application used to run and build applications with
different flavours (languages, frameworks) in local, test, beta and production environments.
""",
)
sub_parser = parser.add_subparsers(required=True, dest="command", help="command to run")

ARG_COMMAND = sys.argv[1] if len(sys.argv) > 1 else None
ARG_SUBCOMMAND = sys.argv[2] if len(sys.argv) > 2 else None

# Help support - if no command is given, show help, thus load all commands
if ARG_COMMAND is None or ARG_COMMAND not in DEKICK_COMMANDS["commands"]:
    for command in DEKICK_COMMANDS["commands"]:
        command_parser = sub_parser.add_parser(command, help=f"{command} help")
        module_name = command.replace("-", "_")  # pylint: disable=invalid-name
        module = import_module(f"commands.{module_name}")
        module.arguments(command_parser)
# Load only one command
else:
    command_parser = sub_parser.add_parser(ARG_COMMAND, help=f"{ARG_COMMAND} help")
    module_name = ARG_COMMAND.replace("-", "_")  # pylint: disable=invalid-name
    module = import_module(f"commands.{module_name}")
    module.arguments(command_parser)

namespace, args = parser.parse_known_args()


def show_banner():
    """Shows a banner with the current version of DeKick."""
    version = (
        f"docker:{DEKICK_DOCKER_IMAGE}"
        if is_dekick_dockerized()
        else get_dekick_version()
    )

    full_command = namespace.command
    dekick_str_len = len(f"DeKick {full_command}")
    version_str_len = len(f"version: {version}")

    print(
        f"\n{C_CMD}DeKick{C_END} {C_FILE}{full_command}"
        + (((TERMINAL_COLUMN_WIDTH - 2) - version_str_len - dekick_str_len) * " ")
        + f"{C_END} version: {C_CODE}{version}{C_END}"
        + ""
    )
    print(TERMINAL_COLUMN_WIDTH * "─")


def show_run_time():
    """Shows total the run time of the application."""
    total_run_time = format_timespan(round(time() - get_dekick_time_start()))
    print(TERMINAL_COLUMN_WIDTH * "─")
    running_time = f"{C_CMD}DeKick{C_END} was running {C_CODE}{total_run_time}{C_END}"
    print(running_time)
    logging.info(running_time)


if ARG_COMMAND != "boilerplates" and ARG_SUBCOMMAND != "install":
    show_banner()
    atexit.register(show_run_time)

try:
    namespace.func(namespace, args)
except KeyboardInterrupt:
    sys.stdout.write("\033[2K")
    print("\r  Keyboard interrupted (CTRL+c)")
    sys.exit()
