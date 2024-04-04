"""
Runs the specified command
"""

import sys
from argparse import ArgumentParser, Namespace
from os.path import isfile

import flatdict
from beaupy import prompt, select
from rich.traceback import install

from commands.local import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.settings import (
    C_END,
    C_FILE,
    DEKICK_FLAVOURS,
    DEKICKRC_FILE,
    get_credentials_drivers,
    get_credentials_drivers_info,
)
from lib.yaml.saver import save_flat

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
        ui_creator(
            log_level=parser.log_level or "INFO",
            log_filename=parser.log_filename or "dekick-e2e.log",
            args=args,
        )
    )


# pylint: disable=too-many-arguments
def ui_creator(log_level: str, log_filename: str, args: list) -> int:
    """
    Run unit test for specific flavour
    """
    install_logger(log_level, log_filename)

    ui_create_dekickrc()

    return 0


def ui_create_dekickrc():
    """
    Create dekickrc file
    """

    if isfile(DEKICKRC_FILE):
        return

    print(f"Creating {C_FILE}{DEKICKRC_FILE}{C_END}")

    print("Flavour:")
    drc_flat = {
        "dekick": {"flavour": ui_select_flavour()},
        "project": {"name": prompt("Project name"), "group": prompt("Project group")},
    }

    print("Credentials (.env) provider:")
    credentials_driver = ui_select_credentials_driver()

    if credentials_driver != "none":
        drc_flat["project"]["providers"] = {
            "credentials": {
                "driver": credentials_driver,
            }
        }

    save_flat(DEKICKRC_FILE, flatdict.FlatDict(drc_flat))


def ui_select_flavour() -> str:
    ret = DEKICK_FLAVOURS[
        int(
            str(
                select(
                    options=DEKICK_FLAVOURS,
                    cursor="🢧",
                    cursor_style="cyan",
                    return_index=True,
                )
            )
        )
    ]
    print(ret + "\n")
    return ret


def ui_select_credentials_driver() -> str:
    credentials_drivers = ["none"] + get_credentials_drivers()
    credentials_drivers_info = get_credentials_drivers_info()
    credentials_drivers_info["none"] = "- none -"

    ret = credentials_drivers[
        int(
            str(
                select(
                    preprocessor=lambda x: credentials_drivers_info[x],
                    options=credentials_drivers,
                    cursor="🢧",
                    cursor_style="cyan",
                    return_index=True,
                )
            )
        )
    ]
    print(credentials_drivers_info[ret] + "\n")
    return ret
