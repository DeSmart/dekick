from logging import debug, warning
from os import getgid, getuid

from lib.rbash import rbash
from lib.settings import DEKICK_VERSION_PATH

DIND_CONTAINER_ID = ""


def start_dind_container(count: int = 0) -> str:
    """Start a Docker-in-Docker container"""

    def create_dind_container():

        global DIND_CONTAINER_ID  # pylint: disable=global-statement
        dekick_version = get_dekick_version()
        container_id = rbash(
            "Starting DinD container",
            f"docker run --privileged -d --rm --add-host proxy:host-gateway -v $(pwd):$(pwd) -w $(pwd) desmart/dekick-dind:{dekick_version}",
        )["stdout"].strip()
        DIND_CONTAINER_ID = container_id

    def chmod_socket_wait_for_dind():
        dind_container_id = get_dind_container_id()
        ret = rbash(
            "Waiting for DinD to start then change permissions of docker socket",
            f'docker exec "{dind_container_id}" bash -c "while ! '
            + 'docker ps >/dev/null 2>&1; do sleep 1; done; chmod 666 /var/run/docker.sock"',
        )

        if ret["code"] == 137:
            return False
        return True

    create_dind_container()

    dind_started = chmod_socket_wait_for_dind()
    max_retries = 5
    if not dind_started and count < max_retries:
        count = count + 1
        warning("DinD didn't start properly, retrying... %s", count)
        return start_dind_container(count)

    if not dind_started and count >= max_retries:
        raise Exception("DinD didn't start properly")

    return DIND_CONTAINER_ID


def stop_dind_container():
    """Stop the Docker-in-Docker container"""
    global DIND_CONTAINER_ID  # pylint: disable=global-statement

    if DIND_CONTAINER_ID == "":
        debug("DinD container is not running")
        return True

    dind_container_id = get_dind_container_id()
    rbash(
        "Stopping DinD container",
        f'docker kill "{dind_container_id}"; exit 0',
    )
    DIND_CONTAINER_ID = ""
    return True


def get_dind_container_id() -> str:
    """Get the ID of the DinD container"""
    return DIND_CONTAINER_ID


def rbash_dind(info_desc, cmd, env=None, expected_code=0, user=None, **kwargs):
    """Runs command in DinD and returns its output"""
    env = env or {}
    dind_container_id = get_dind_container_id()

    if user is None:
        user = f"{getuid()}:{getgid()}"

    tmp_docker_env = ""

    for key, value in env.items():
        tmp_docker_env += f'-e {key}="{value}" '

    cmd = cmd.replace('"', '\\"')
    dind_cmd = (
        f"docker exec {tmp_docker_env} --user={user} "
        + f'"{dind_container_id}" bash -c "{cmd}"'
    )

    return rbash(
        info_desc=info_desc,
        cmd=dind_cmd,
        env=env,
        expected_code=expected_code,
        **kwargs,
    )


def get_dekick_version() -> str:
    """Gets current version of DeKick"""
    return open(DEKICK_VERSION_PATH, encoding="utf-8").read().strip()
