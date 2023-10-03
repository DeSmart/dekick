from os import getcwd, getenv

from lib.tests.boilerplates import get_project_root
from lib.tests.dind import rbash_dind


def any_container_running() -> bool:
    """Checks if there are any running container inside DinD"""
    env = get_docker_env()
    proc = rbash_dind(
        "Checking if there are any running containers",
        'docker ps --format "{{.ID}}|{{.Image}}"',
        env=env,
    )
    return proc["stdout"] != "" and proc["code"] == 0


def no_container_running() -> bool:
    """Checks if there are no running container inside DinD"""
    return not any_container_running()


def get_docker_env() -> dict:
    """Gets environment variables needed for DeKick to run properly"""

    return {
        "HOME": getenv("HOME"),
        "PATH": "/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin",
        "DEKICK_PATH": getcwd(),
        "PROJECT_ROOT": get_project_root(),
        "HOST_ARCH": getenv("HOST_ARCH") or "",
        "HOST_PLATFORM": getenv("HOST_PLATFORM") or "",
        "DEKICK_DEBUGGER": getenv("DEKICK_DEBUGGER") or "",
        "DEKICK_DOCKER_IMAGE": getenv("DEKICK_DOCKER_IMAGE") or "",
    }
