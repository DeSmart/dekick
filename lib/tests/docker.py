from os import environ, getcwd, getenv, getgid, getuid

from lib.settings import BOILERPLATES_PATH
from lib.tests.rbash import rbash


def docker_no_running_container() -> bool:
    """Checks if there are no running containers except dekick"""
    proc = rbash(
        "Checking if no containers are running",
        'docker ps -q --format "{{.ID}}|{{.Image}}" | grep -v "dekick"',
        expected_code=1,
    )
    return proc["stdout"] == "" and proc["code"] == 1


def docker_kill_all_containers() -> bool:
    """Kills all running containers except dekick"""
    rbash(
        "Kills all running containers",
        'docker kill $(docker ps -q --format "{{.ID}}|{{.Image}}" | '
        + "grep -v \"dekick\" | awk -F'|' '{print$1}')"
        + " >/dev/null 2>&1; exit 0",
    )
    return True


def get_docker_env(flavour: str, version: str) -> dict:
    """Gets environment variables needed for DeKick to run properly"""
    project_root = f"{BOILERPLATES_PATH}{flavour}/{version}/"

    return {
        "HOME": environ["HOME"],
        "PATH": environ["PATH"],
        "DEKICK_PATH": getcwd(),
        "PROJECT_ROOT": project_root,
        "CURRENT_UID": getenv("CURRENT_UID") or f"{getuid()}:{getgid()}",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOST_ARCH": getenv("HOST_ARCH"),
        "HOST_PLATFORM": getenv("HOST_PLATFORM"),
        "DEKICK_DEBUGGER": getenv("DEKICK_DEBUGGER") or "",
        "DEKICK_DOCKER_IMAGE": getenv("DEKICK_DOCKER_IMAGE") or "",
    }
