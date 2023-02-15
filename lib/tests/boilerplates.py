from logging import fatal, warning
from os import getcwd, makedirs
from tempfile import mkdtemp

from rich.traceback import install

from lib.dotenv import get_dotenv_var
from lib.tests.rbash import rbash

install()
BOILERPLATES_PATH = None
BOILERPLATES_ROOT = getcwd() + "/tmp/boilerplates/base/"
FLAVOUR_PATH = None
FLAVOUR_ROOT = getcwd() + "/tmp/boilerplates/flavours/"


def generate_boilerplates_base_path() -> str:
    """Generates boilerplates path"""
    return BOILERPLATES_ROOT


def get_boilerplates_base_path() -> str:
    """Returns boilerplates path"""
    global BOILERPLATES_PATH  # pylint: disable=global-statement

    if BOILERPLATES_PATH is None:
        BOILERPLATES_PATH = generate_boilerplates_base_path()

    return BOILERPLATES_PATH


def get_boilerplates_git_url() -> str:
    """Returns boilerplates git url"""
    boilerplates_git_url = get_dotenv_var("BOILERPLATES_GIT_URL")

    if not boilerplates_git_url:
        fatal("BOILERPLATES_GIT_URL is not set in .env file")
        assert False

    return boilerplates_git_url


def download_boilerplates_base() -> bool:
    """Downloads boilerplates to BOILERPLATES_BASE_PATH directory"""
    boilerplates_git_url = get_boilerplates_git_url()
    boilerplates_path = get_boilerplates_base_path()

    ret = rbash(
        "Downloading boilerplates",
        f'git clone "{boilerplates_git_url}" "{boilerplates_path}"'
        #        + f'cd {boilerplates_path}; git config --global --add safe.directory "*"',
    )

    if ret["code"] == 128:
        warning("Boilerplates already exists")
        reset_boilerplates()

    return rbash("Checking directory exists", f"ls {boilerplates_path}")["stdout"] != ""


def delete_boilerplates() -> bool:
    """Removes boilerplates from .BOILERPLATES_PATH directory"""
    boilerplates_path = get_boilerplates_base_path()
    return (
        rbash("Removing boilerplates", f"sudo rm -rf {boilerplates_path}")["code"] == 0
    )


def generate_flavour_path() -> str:
    """Returns flavour and version generated path"""
    return _generate_path(FLAVOUR_ROOT)


def get_flavour_path(regenerate: bool = False) -> str:
    """Returns flavour path"""
    global FLAVOUR_PATH  # pylint: disable=global-statement

    if FLAVOUR_PATH is None or regenerate is True:
        FLAVOUR_PATH = generate_flavour_path()

    return FLAVOUR_PATH


def create_flavour(flavour: str, version: str) -> bool:
    """Copies boilerplate flavour to flavour generated directory"""
    boilerplates_path = get_boilerplates_base_path()
    flavour_path = get_flavour_path(regenerate=True)
    return (
        rbash(
            "Copying boilerplate flavour",
            f"rsync -a {boilerplates_path}{flavour}/{version}/ {flavour_path}",
        )["code"]
        == 0
    )


def delete_flavour() -> bool:
    """Removes flavour from .FLAVOUR_PATH directory"""
    flavour_path = get_flavour_path()
    return rbash("Removing flavour", f"sudo rm -rf {flavour_path}")["code"] == 0


def _generate_path(root: str) -> str:
    """Generates path"""
    makedirs(root, exist_ok=True)
    return mkdtemp(prefix="", dir=root) + "/"


def reset_boilerplates() -> bool:
    """Resets boilerplates repository to initial position"""
    boilerplates_path = get_boilerplates_base_path()
    rbash(
        "Resetting boilerplates",
        f"cd {boilerplates_path}; git pull; git reset --hard HEAD; git clean -fdx",
    )
    return True
