from logging import debug, error, info

from rich.traceback import install

from lib.dotenv import get_dotenv_var
from lib.settings import BOILERPLATES_DEFAULT_GIT_URL, BOILERPLATES_PATH, CURRENT_UID
from lib.tests.rbash import rbash

install()


def get_boilerplates_git_url() -> str:
    """Returns boilerplates git url"""
    return get_dotenv_var("BOILERPLATES_GIT_URL", BOILERPLATES_DEFAULT_GIT_URL)


def delete_boilerplates() -> bool:
    """Removes boilerplates from .BOILERPLATES_PATH directory"""
    return rbash("Removing boilerplates", f"rm -rf {BOILERPLATES_PATH}")["code"] == 0


def get_boilerplate(flavour: str, version: str) -> bool:
    """Downloads boilerplates to BOILERPLATES_PATH directory"""
    boileplates_git_url = get_boilerplates_git_url()
    rbash(
        f"Downloading boilerplate {flavour} {version}",
        'git clone --filter=blob:none --no-checkout --depth 1 --sparse "'
        + f'{boileplates_git_url}" {BOILERPLATES_PATH}',
    )
    rbash(
        "Setting up git sparse-checkout",
        f"cd {BOILERPLATES_PATH} && git sparse-checkout add {flavour}/{version}",
    )
    rbash("Running git checkout", f"cd {BOILERPLATES_PATH} && git checkout")
    rbash(
        f"Changing ownership to {CURRENT_UID}",
        f"chown -R {CURRENT_UID} {BOILERPLATES_PATH}{flavour}/{version}",
    )
    return (
        rbash(
            "Checking directory exists", f"ls {BOILERPLATES_PATH}{flavour}/{version}"
        )["stdout"]
        != ""
    )
