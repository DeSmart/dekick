from logging import fatal, warning
from os import getcwd
from re import match

from rich.traceback import install

from lib.dekickrc import get_dekick_version
from lib.dotenv import get_dotenv_var
from lib.rbash import rbash
from lib.settings import DEKICKRC_GLOBAL_PATH

install()
BOILERPLATES_ROOT = getcwd() + "/tmp/boilerplates/"
DIND_PROJECT_ROOT = "/project_root/"


def get_boilerplates_path() -> str:
    """Gets boilerplates base path"""
    return BOILERPLATES_ROOT


def get_boilerplates_git_url() -> str:
    """Returns boilerplates git url"""
    boilerplates_git_url = get_dotenv_var("BOILERPLATES_GIT_URL")

    if not boilerplates_git_url:
        fatal("BOILERPLATES_GIT_URL is not set in .env file")
        assert False

    return boilerplates_git_url


def get_boilerplates_tag() -> str:
    """Gets boilerplates branch"""
    dekick_version = get_dekick_version()

    if dekick_version == "develop" or match(r"^\d+\.\d+\.\d+$", dekick_version):
        return dekick_version

    return f"feature/{dekick_version}"


def download_boilerplates() -> bool:
    """Downloads boilerplates to BOILERPLATES_BASE_PATH directory"""
    boilerplates_git_url = get_boilerplates_git_url()
    boilerplates_path = get_boilerplates_path()
    boilerplates_tag = get_boilerplates_tag()

    ret = rbash(
        "Add safe.directory to git config",
        "git config --global --add safe.directory '*'",
    )

    ret = rbash(
        "Downloading boilerplates",
        f'git clone -b master "{boilerplates_git_url}" "{boilerplates_path}"',
    )

    if ret["code"] == 128:
        warning("Boilerplates already exists")
        reset_boilerplates()

    rbash(
        f"Switching to tag/branch {boilerplates_tag}",
        f"cd {boilerplates_path};" + f"git checkout {boilerplates_tag}",
    )
    return rbash("Checking directory exists", f"ls {boilerplates_path}")["stdout"] != ""


def delete_boilerplates() -> bool:
    """Removes boilerplates from .BOILERPLATES_PATH directory"""
    boilerplates_path = get_boilerplates_path()
    return (
        rbash("Removing boilerplates", f"sudo rm -rf {boilerplates_path}")["code"] == 0
    )


def copy_flavour_to_container(flavour: str, version: str, container_id: str):
    """Copies boilerplate flavour to flavour generated directory"""
    boilerplates_path = get_boilerplates_path()
    project_root = get_project_root()
    rbash(
        "Create project path",
        f'docker exec {container_id} mkdir -p "{project_root}"',
    )
    rbash(
        f"Copying flavour/version to DinD container {container_id}",
        f"docker cp -aq {boilerplates_path}{flavour}/{version}/. {container_id}:{project_root}",
    )
    rbash(
        "Changing permissions",
        f'docker exec {container_id} bash -c "chmod -R oug+rw {project_root}; chown -R 1000 {project_root}"',
    )


def copy_global_config_to_container(container_id: str):
    rbash(
        f"Create {DEKICKRC_GLOBAL_PATH}",
        f'docker exec {container_id} mkdir -p $(dirname "{DEKICKRC_GLOBAL_PATH}")',
    )
    rbash(
        f"Copying {DEKICKRC_GLOBAL_PATH} to DinD container {container_id}",
        f"docker cp -aq {DEKICKRC_GLOBAL_PATH} {container_id}:{DEKICKRC_GLOBAL_PATH}",
    )


def get_project_root() -> str:
    """Gets project root path for DinD container"""
    return DIND_PROJECT_ROOT


def reset_boilerplates() -> bool:
    """Resets boilerplates repository to initial position"""
    boilerplates_path = get_boilerplates_path()

    rbash(
        "Resetting boilerplates",
        f"cd {boilerplates_path}; git pull; git reset --hard HEAD; git clean -fdx",
    )
    return True
