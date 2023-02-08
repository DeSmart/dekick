from rich.traceback import install

from lib.dotenv import get_dotenv_var
from lib.settings import BOILERPLATES_PATH
from lib.tests.rbash import rbash

install()


def get_boilerplates_git_url() -> str:
    """Returns boilerplates git url"""
    return get_dotenv_var("BOILERPLATES_GIT_URL")


def delete_boilerplates() -> bool:
    """Removes boilerplates from .BOILERPLATES_PATH directory"""
    return rbash("Removing boilerplates", f"rm -rf {BOILERPLATES_PATH}")["code"] == 0


def get_boilerplates() -> bool:
    """Downloads boilerplates to BOILERPLATES_PATH directory"""
    boileplates_git_url = get_boilerplates_git_url()
    rbash(
        "Downloading boilerplates",
        f'git clone "{boileplates_git_url}" "{BOILERPLATES_PATH}"',
    )
    rbash(
        "Add git config",
        f"cd {BOILERPLATES_PATH}; git config --global --add safe.directory '*'",
    )
    return rbash("Checking directory exists", f"ls {BOILERPLATES_PATH}")["stdout"] != ""


def reset_boilerplates() -> bool:
    """Resets boilerplates repository to initial position"""
    rbash(
        "Resetting boilerplates",
        f"cd {BOILERPLATES_PATH}; git reset --hard HEAD; git clean -fdx",
    )
    return True
