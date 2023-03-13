from logging import fatal, warning
from os import getcwd

from rich.traceback import install

from lib.dekickrc import get_dekick_version
from lib.dotenv import get_dotenv_var
from lib.rbash import rbash

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


def get_boilerplates_branch() -> str:
    """Gets boilerplates branch"""
    dekick_version = get_dekick_version()
    return f"release/{dekick_version}"


def download_boilerplates() -> bool:
    """Downloads boilerplates to BOILERPLATES_BASE_PATH directory"""
    boilerplates_git_url = get_boilerplates_git_url()
    boilerplates_path = get_boilerplates_path()
    boilerplates_branch = get_boilerplates_branch()

    ret = rbash(
        "Downloading boilerplates",
        f'git clone -b "{boilerplates_branch}" "{boilerplates_git_url}" "{boilerplates_path}"',
    )

    if ret["code"] == 128:
        warning("Boilerplates already exists")
        reset_boilerplates()

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


def get_project_root() -> str:
    """Gets project root path for DinD container"""
    return DIND_PROJECT_ROOT


def reset_boilerplates() -> bool:
    """Resets boilerplates repository to initial position"""
    boilerplates_path = get_boilerplates_path()
    boilerplates_branch = get_boilerplates_branch()

    rbash(
        "Resetting boilerplates",
        f'cd {boilerplates_path}; git checkout "{boilerplates_branch}"; git pull; git reset --hard HEAD; git clean -fdx',
    )
    return True
