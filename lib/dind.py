from contextlib import contextmanager
from logging import debug, warning
from os import getcwd
from os.path import exists, isdir

from lib.dekickrc import get_dekick_version
from lib.rbash import rbash
from lib.registry import start_docker_registry
from lib.run_func import run_func
from lib.settings import CURRENT_UID, CURRENT_USERNAME, is_pytest

DIND_CONTAINER_ID = ""


@contextmanager
def dind_container():
    """Start a Docker-in-Docker container"""

    if is_pytest():
        debug("Not using DinD container in pytest mode")
        yield ""
        return

    def create_dind_container():
        global DIND_CONTAINER_ID  # pylint: disable=global-statement
        dekick_version = get_dekick_version()
        container_id = rbash(
            "Starting DinD container",
            f"docker run --privileged -d --rm --add-host proxy:host-gateway desmart/dekick-dind:{dekick_version}",
        )["stdout"].strip()
        DIND_CONTAINER_ID = container_id
        wait_for_dind()

    def check_dind_docker_running() -> bool:
        dind_container_id = get_dind_container_id()
        ret = rbash(
            "Waiting for DinD to start then change permissions of docker socket",
            f'docker exec "{dind_container_id}" bash -c "while ! '
            + "docker ps >/dev/null 2>&1; do sleep 1; done; chmod 666 /var/run/docker.sock; "
            + f"adduser -D -h /tmp/homedir -u {CURRENT_UID} {CURRENT_USERNAME}"
            + '"',
        )

        if ret["code"] == 137:
            return False
        return True

    def wait_for_dind():
        max_retries = 5
        count = 1
        while count < max_retries and not check_dind_docker_running():
            count = count + 1
            warning("DinD didn't start properly, retrying... %s", count)
            create_dind_container()

        if count > max_retries:
            raise Exception("DinD didn't start properly")

    try:
        run_func(text="Starting Docker registry proxy", func=start_docker_registry)
        run_func(text="Creating DinD container", func=create_dind_container)
        run_func(text="Copying project to DinD container", func=copy_to_dind)
        yield DIND_CONTAINER_ID
    finally:
        stop_dind_container()


def copy_to_dind(filename: str = ""):
    """Copy the project to the DinD container"""
    if not is_dind_running():
        return

    dind_container_id = get_dind_container_id()
    current_path = getcwd()
    rbash(
        "Create project path",
        f'docker exec {dind_container_id} mkdir -p "{current_path}"',
    )
    filename = filename or "."
    rbash(
        "Copying project to DinD container",
        f'docker cp -aq "{current_path}/{filename}" "{dind_container_id}:{current_path}"',
    )
    rbash(
        "Changing permissions",
        f'docker exec {dind_container_id} chmod -R oug+rw "{current_path}"',
    )


def copy_from_dind(resource: str):
    """Copy the project files (artifacts) from the DinD container back to host"""

    if not is_dind_running():
        return

    dind_container_id = get_dind_container_id()
    current_path = getcwd()
    full_path = f"{current_path}/{resource}"

    if exists(full_path) and isdir(full_path):
        full_path = full_path + "/."

    rbash(
        f"Copying {full_path} from dind container {dind_container_id} to host",
        f'docker cp -aq "{dind_container_id}:{full_path}" "{full_path}"',
    )


def stop_dind_container():
    """Stop the Docker-in-Docker container"""
    if not is_dind_running():
        return

    global DIND_CONTAINER_ID  # pylint: disable=global-statement

    if DIND_CONTAINER_ID == "":
        debug("DinD container is not running")
        return

    dind_container_id = get_dind_container_id()
    rbash(
        "Stopping DinD container",
        f'docker kill "{dind_container_id}"; exit 0',
    )
    DIND_CONTAINER_ID = ""


def get_dind_container_id() -> str:
    """Get the ID of the DinD container"""
    return DIND_CONTAINER_ID


def is_dind_running() -> bool:
    """Check if DinD is running"""
    return get_dind_container_id() != ""
