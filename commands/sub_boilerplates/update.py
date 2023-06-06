"""Update local files with files from specific boilerplate defined in .dekickrc.yml"""
import logging
import sys
from argparse import ArgumentParser, Namespace
from glob import glob
from os import makedirs
from os.path import isdir
from shutil import copyfile
from tempfile import mkdtemp

from lib.dekickrc import get_dekick_version, get_dekickrc_value
from lib.global_config import get_global_config_value
from lib.logger import install_logger
from lib.misc import run_shell
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.run_func import run_func
from lib.settings import C_CODE, C_END, C_FILE, DEKICKRC_GLOBAL_HOST_PATH, PROJECT_ROOT
from lib.yaml.reader import read_yaml

BOILERPLATES_TMP_PATH = mkdtemp(prefix="boilerplates", dir="/tmp")


def parser_help() -> str:
    """Set description for this command, used in arguments parser"""
    return (
        "Updates local files with files from specific "
        + f"boilerplate defined in {C_FILE}.dekickrc.yml{C_END}"
    )


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    parser.set_defaults(func=main)
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command."""
    parser_default_funcs(parser)
    install_logger(parser.log_level, parser.log_filename or "/dev/null", False)
    exit_code = ui_update()
    sys.exit(exit_code)


def ui_update():
    """UI wrapper for docker_compose"""
    boilerplate = get_dekickrc_value("dekick.boilerplate")
    run_func(
        text=f"Downloading boilerplate {C_CODE}{boilerplate}{C_END} from Git repository",
        func=ui_download_boilerplate,
        func_args={"boilerplate": boilerplate},
    )
    return run_func(
        text=f"Updating local files with boilerplate {C_CODE}{boilerplate}{C_END}",
        func=ui_update_local_files,
        func_args={"boilerplate": boilerplate},
    )


def ui_download_boilerplate(boilerplate: str):
    """Download boilerplate files from repository"""
    try:
        boilerplates_git_url = get_global_config_value("boilerplates.git_url")
        dekick_version = get_dekick_version()

        run_shell(
            cmd=[
                "git",
                "clone",
                "-n",
                "--depth",
                "1",
                "--filter",
                "tree:0",
                boilerplates_git_url,
                BOILERPLATES_TMP_PATH,
            ],
            raise_exception=True,
            capture_output=True,
        )
        run_shell(
            cmd=[
                "git",
                "sparse-checkout",
                "set",
                "--no-cone",
                "--sparse-index",
                boilerplate,
            ],
            cwd=BOILERPLATES_TMP_PATH,
            raise_exception=True,
            capture_output=True,
        )

        if dekick_version != "develop":
            run_shell(
                cmd=["git", "tag", dekick_version],
                cwd=BOILERPLATES_TMP_PATH,
                raise_exception=True,
                capture_output=True,
            )

        run_shell(
            cmd=["git", "checkout", dekick_version],
            cwd=BOILERPLATES_TMP_PATH,
            raise_exception=True,
            capture_output=True,
        )
    except TypeError:
        return {
            "success": False,
            "text": "Please add URL to boilerplates Git repository "
            + f"using {C_CODE}boilerplates.git_url{C_END} "
            + f"key in your {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}",
        }


def ui_update_local_files(boilerplate: str):
    """Update local files with boilerplate files"""
    boilerplate_flat = read_yaml(
        f"{BOILERPLATES_TMP_PATH}/{boilerplate}/.boilerplate.yml"
    )

    patterns = boilerplate_flat.get("update-patterns")
    if not patterns or not isinstance(patterns, list):
        raise TypeError("Empty or non-existent patterns found in .boilerplate.yml file")

    for pattern in patterns:
        glob_pattern = f"{BOILERPLATES_TMP_PATH}/{boilerplate}/{pattern}"
        for file_from in glob(glob_pattern, recursive=True):
            file_to = file_from.replace(
                f"{BOILERPLATES_TMP_PATH}/{boilerplate}", PROJECT_ROOT
            )
            logging.debug("Copying file from %s to %s", file_from, file_to)

            if isdir(file_from):
                makedirs(file_to, exist_ok=True)
                continue

            copyfile(file_from, file_to)

    return {
        "success": True,
        "text": "Files copied successfully. Please review and commit changes into your project.",
    }
