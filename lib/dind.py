from contextlib import contextmanager
from logging import debug, warning
from os import getcwd
from subprocess import Popen

from lib.dekickrc import get_dekick_version
from lib.tests.rbash import rbash

DIND_CONTAINER_ID = ""


@contextmanager
def dind_container():
    """Start a Docker-in-Docker container"""

    def create_dind_container():

        global DIND_CONTAINER_ID  # pylint: disable=global-statement
        dekick_version = get_dekick_version()
        container_id = rbash(
            "Starting DinD container",
            f"docker run --privileged -d --rm --add-host proxy:host-gateway -w {getcwd()} desmart/dekick-dind:{dekick_version}",
        )["stdout"].strip()
        DIND_CONTAINER_ID = container_id

    def chmod_socket_wait_for_dind() -> bool:
        dind_container_id = get_dind_container_id()
        ret = rbash(
            "Waiting for DinD to start then change permissions of docker socket",
            f'docker exec "{dind_container_id}" bash -c "while ! '
            + 'docker ps; do sleep 1; done; chmod 666 /var/run/docker.sock"',
        )

        if ret["code"] == 137:
            return False
        return True

    try:
        create_dind_container()
        max_retries = 5
        count = 1
        while count < max_retries and not chmod_socket_wait_for_dind():
            count = count + 1
            warning("DinD didn't start properly, retrying... %s", count)
            create_dind_container()

        if count > max_retries:
            raise Exception("DinD didn't start properly")

        copy_project_to_dind()
        yield DIND_CONTAINER_ID
    finally:
        stop_dind_container()


def copy_project_to_dind():
    """Copy the project to the DinD container"""
    dind_container_id = get_dind_container_id()
    current_path = getcwd()
    debug(
        "Copying %s to DinD container %s:%s",
        current_path,
        dind_container_id,
        current_path,
    )

    cmd = f'docker cp -aq "{current_path}/." "{dind_container_id}:{current_path}"'
    debug("Running command: %s", cmd)

    Popen(
        cmd,
        shell=True,
        universal_newlines=True,
    )


def stop_dind_container():
    """Stop the Docker-in-Docker container"""
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


def get_dind_project_root():
    return DIND_PROJECT_ROOT


def get_dind_container_id() -> str:
    """Get the ID of the DinD container"""
    return DIND_CONTAINER_ID


def is_dind_running() -> bool:
    """Check if DinD is running"""
    return get_dind_container_id() != ""
