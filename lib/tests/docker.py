from os import environ, getcwd, getenv, getgid, getuid

from lib.tests.boilerplates import get_flavour_path
from lib.tests.dind import rbash_dind


def docker_no_running_container() -> bool:
    """Checks if there are no running containers except dekick"""
    env = get_docker_env()
    proc = rbash_dind(
        "Checking if no containers are running",
        'docker ps -q --format "{{.ID}}|{{.Image}}" | grep -v "dekick"',
        env=env,
        expected_code=1,
    )
    return proc["stdout"] == "" and proc["code"] == 1


def docker_kill_all_containers() -> bool:
    """Kills all running containers except dekick"""
    env = get_docker_env()
    rbash_dind(
        "Kills all running containers",
        'docker kill $(docker ps -q --format "{{.ID}}|{{.Image}}" | '
        + "grep -v \"dekick\" | awk -F'|' '{print$1}')"
        + " >/dev/null 2>&1; exit 0",
        env=env,
    )
    return True


def get_docker_env() -> dict:
    """Gets environment variables needed for DeKick to run properly"""
    flavour_path = get_flavour_path()

    return {
        "HOME": environ["HOME"],
        "PATH": "/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin",
        "DEKICK_PATH": getcwd(),
        "PROJECT_ROOT": flavour_path,
        "CURRENT_UID": getenv("CURRENT_UID") or f"{getuid()}:{getgid()}",
        "HOST_ARCH": getenv("HOST_ARCH") or "",
        "HOST_PLATFORM": getenv("HOST_PLATFORM") or "",
        "DEKICK_DEBUGGER": getenv("DEKICK_DEBUGGER") or "",
        "DEKICK_DOCKER_IMAGE": getenv("DEKICK_DOCKER_IMAGE") or "",
    }
