"""Update local files with files from specific boilerplate defined in .dekickrc.yml"""
import sys
from argparse import ArgumentParser, Namespace
from glob import glob
from os.path import dirname

from beaupy import confirm, prompt, select
from rich.console import Console

from lib.dekickrc import get_dekick_version
from lib.global_config import get_global_config_value
from lib.logger import install_logger
from lib.parser_defaults import parser_default_args, parser_default_funcs
from lib.rbash import rbash
from lib.run_func import run_func
from lib.settings import (
    C_CODE,
    C_END,
    C_FILE,
    DEKICK_BOILERPLATES,
    DEKICK_BOILERPLATES_INSTALL_PATH,
    DEKICK_GIT_URL,
    DEKICKRC_GLOBAL_HOST_PATH,
)
from lib.yaml.reader import read_yaml

console = Console()


def parser_help() -> str:
    """Set description for this command, used in arguments parser"""
    return "Install boilerplate into current directory"


def arguments(parser: ArgumentParser):
    """Set arguments for this command."""
    parser.set_defaults(func=main)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Do not ask for confirmation, assume always default answer",
    )
    parser_default_args(parser)


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command."""
    parser_default_funcs(parser)
    install_logger(parser.log_level, parser.log_filename or "/dev/null", False)
    ui_choose(parser.force)
    sys.exit(0)


def ui_choose(force: bool = False):
    """UI wrapper for docker_compose"""
    if force is False and not confirm(
        "Do you want to install boilerplate in the current directory"
        + f" ({DEKICK_BOILERPLATES_INSTALL_PATH})?",
        default_is_yes=True,
    ):
        return

    console.print("\nChoose a boilerplate to install:")
    boilerplate = select(list(DEKICK_BOILERPLATES), cursor="🢧", cursor_style="cyan")
    run_func(
        text=f"Installing {C_CODE}{boilerplate}{C_END} to "
        + f"{C_FILE}{DEKICK_BOILERPLATES_INSTALL_PATH}{C_END}",
        func=ui_install,
        func_args={"boilerplate": boilerplate},
    )


def ui_install(boilerplate: str):
    """UI wrapper for install"""
    check_current_dir()
    download_boilerplate(boilerplate)
    download_dekick()
    cleanup(boilerplate)

    return {
        "success": True,
        "text": f"Boilerplate installed successfully, DeKick "
        + f"installed into {C_FILE}dekick/{C_END} directory",
    }


def check_current_dir():
    """Check if current directory is empty"""
    if len(glob(f"{DEKICK_BOILERPLATES_INSTALL_PATH}/*")) > 0:
        raise RuntimeError(
            "Current directory should be empty but it's not. "
            + "Please choose a different directory.",
        )


def download_boilerplate(boilerplate: str):
    """Download boilerplate files from repository"""
    try:
        boilerplates_git_url = get_global_config_value("boilerplates.git_url")
        dekick_version = get_dekick_version()

        rbash(
            "Download boilerplate files",
            "git clone -n --depth 1 --filter tree:0 "
            + f'"{boilerplates_git_url}" "{DEKICK_BOILERPLATES_INSTALL_PATH}"',
        )
        rbash(
            "Apply sparse checkout",
            f'cd "{DEKICK_BOILERPLATES_INSTALL_PATH}";'
            + f"git sparse-checkout set --no-cone --sparse-index {boilerplate}",
        )

        if dekick_version != "develop":
            rbash(
                "Checkout specific boilerplate version (tag)",
                f'cd {DEKICK_BOILERPLATES_INSTALL_PATH}";'
                + f'git tag "{dekick_version}',
            )

        rbash(
            "Checkout specific boilerplate version (branch)",
            f'cd "{DEKICK_BOILERPLATES_INSTALL_PATH}"; git checkout {dekick_version}',
        )
    except TypeError as exc:
        raise TypeError(
            "Please add URL to boilerplates Git repository "
            + f"using {C_CODE}boilerplates.git_url{C_END} key "
            + f"in your {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}",
        ) from exc


def download_dekick():
    """Download newest version of DeKick to dekick/ directory"""
    rbash(
        "Download newest version of DeKick to dekick/ directory",
        f"git clone --branch main {DEKICK_GIT_URL} dekick",
    )


def cleanup(boilerplate: str):
    """Clean up boilerplate files"""
    boilerplate_flat = read_yaml(
        f"{DEKICK_BOILERPLATES_INSTALL_PATH}/{boilerplate}/.boilerplate.yml"
    )

    rbash("Remove .git directory", f"rm -rf {DEKICK_BOILERPLATES_INSTALL_PATH}/.git")

    ignores = boilerplate_flat.get("install-ignore")
    if not ignores or not isinstance(ignores, list):
        raise TypeError(
            "Empty or non-existent install-ignores found in .boilerplate.yml file"
        )

    for ignore in ignores:
        delete_pattern = f"{DEKICK_BOILERPLATES_INSTALL_PATH}/{boilerplate}/{ignore}"
        rbash(f"Remove {delete_pattern}", f"rm -rf {delete_pattern}")

    rbash(
        "Move boilerplate files to the root directory",
        f"mv {DEKICK_BOILERPLATES_INSTALL_PATH}/{boilerplate}/* {DEKICK_BOILERPLATES_INSTALL_PATH}/;"
        + f"mv {DEKICK_BOILERPLATES_INSTALL_PATH}/{boilerplate}/.* {DEKICK_BOILERPLATES_INSTALL_PATH}/",
    )

    boilerplate_basedir = dirname(boilerplate)

    rbash(
        "Remove boilerplate directory",
        f"rm -rf {DEKICK_BOILERPLATES_INSTALL_PATH}/{boilerplate_basedir}",
    )
