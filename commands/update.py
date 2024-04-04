"""
Update DeKick

Get newest stable version of DeKick from the repository and replace current one
"""

import logging
import sys
from argparse import ArgumentParser, Namespace
from tempfile import mkdtemp

import requests
from rich.prompt import Confirm
from rich.traceback import install

from lib.dekickrc import version_int
from lib.logger import get_log_level, install_logger, log_exception
from lib.misc import check_command, run_shell
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import (
    C_CMD,
    C_CODE,
    C_END,
    C_WARN,
    CURRENT_UID,
    DEKICK_GIT_URL,
    DEKICK_PATH,
    DEKICK_STABLE_VERSION_URL,
    DEKICK_VERSION_PATH,
    PROJECT_ROOT,
)

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
    if parser.log_filename:
        install_logger(parser.log_level, parser.log_filename)
        exit_code = ui_update()
    else:
        exit_code = 0 if update() is True else 1

    sys.exit(exit_code)


def ui_update():
    """UI wrapper for update"""

    def wrapper():
        update()

    return run_func(text="Updating DeKick", func=wrapper)


def check_command_git():
    check_command(
        cmd_linux=["git", "--help"],
        cmd_osx=["git", "--help"],
        hint_linux="Please install git command",
        hint_osx="Please install git command",
        skip_if_dockerized=True,
    )


def update() -> bool:
    check_command_git()

    if not compare_versions():
        return False

    if not ask_for_update():
        return False
    tmpdir = make_tmpdir()
    ui_clone_dekick(tmpdir)
    ui_copy_files(tmpdir)
    ui_ask_commit()
    return True


def get_remote_version() -> str:
    """Get remote version of DeKick from the repository"""
    return requests.get(DEKICK_STABLE_VERSION_URL, timeout=10).text.strip()


DEKICK_LOCAL_VERSION = open(DEKICK_VERSION_PATH, "r", encoding="utf-8").read().strip()


def get_local_version() -> str:
    """Get local version of DeKick"""
    return DEKICK_LOCAL_VERSION


def compare_versions() -> bool:
    """Compare local and remote version of DeKick"""

    def run():
        local_version = get_local_version()
        remote_version = get_remote_version()

        if version_int(remote_version) > version_int(local_version):
            return {
                "success": True,
                "text": f"There's a new version of {C_CMD}Dekick{C_END} ({C_CODE}{remote_version}{C_END})",
                "func": lambda: True,
            }

        return {
            "success": True,
            "text": "DeKick is up to date",
            "func": lambda: False,
        }

    return run_func(
        f"Checking new version of {C_CMD}DeKick{C_END}",
        func=run,
        terminate=False,
    )


def ask_for_update() -> bool:
    question = "Update?"

    if Confirm.ask(question, default=False) is True:
        return True

    return False


def ui_clone_dekick(tmpdir: str):
    def run():
        try:
            run_shell(
                ["git", "clone", "--branch", "main", DEKICK_GIT_URL, tmpdir],
                capture_output=True,
                raise_exception=True,
            )
            return {
                "success": True,
                "text": "Updated successfully. Commit changes manually.",
            }
        except Exception as error:
            logging.error(error.args[0])
            if get_log_level() == "DEBUG":
                logging.exception(error)
            return {
                "success": False,
                "text": "Failed to update. Check log file for more information",
            }

    run_func(f"Cloning files to {tmpdir}", func=run)


def ui_copy_files(tmpdir: str):
    """Copies files from tmpdir to DEKICK_PATH"""

    def run():
        try:
            run_shell(
                f'rm -rf "{DEKICK_PATH}/"*; rm -rf "{DEKICK_PATH}/.git"; mv -f "{tmpdir}"/* "{DEKICK_PATH}"; mv -f "{tmpdir}"/.* "{DEKICK_PATH}"; rm -rf "{tmpdir}"; chown -R "{CURRENT_UID}" "{DEKICK_PATH}"',
                {},
                shell=True,
                capture_output=True,
                raise_exception=False,
                raise_error=False,
            )

            return {
                "success": True,
                "text": "Files copied successfully.",
            }
        except Exception as error:
            logging.error("Message or exit code: %s", error.args[0])
            log_exception(error)
            return {
                "success": False,
                "text": "Failed to copy files. Check log file for more information",
            }

    run_func(f"Copying files from {tmpdir} to {DEKICK_PATH}", func=run)


def ui_ask_commit():
    """Asks user to commit changes"""

    # Check if user uses git in the project
    output = run_shell(["git", "status"], {}, capture_output=True)
    if output["returncode"] > 0:
        return

    if Confirm.ask(
        "Do you want to stage the DeKick update to the Git repository?", default=False
    ):
        run_shell(["git", "add", f"{PROJECT_ROOT}/dekick"], {}, capture_output=True)

        print(
            f"Changes staged successfully. {C_WARN}Please commit them manually.{C_END}"
        )


def make_tmpdir() -> str:
    """Makes temporary directory"""
    return mkdtemp()
