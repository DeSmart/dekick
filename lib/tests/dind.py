from logging import debug
from os import getgid, getuid

from lib.tests.rbash import rbash

DIND_CONTAINER_ID = None


def start_dind_container():
    """Start a Docker-in-Docker container"""
    global DIND_CONTAINER_ID  # pylint: disable=global-statement

    def create_dind_container():
        return rbash(
            "Starting DinD container",
            "docker run --privileged -d --rm --add-host host.docker.internal:host-gateway -e DOCKER_REGISTRY_MIRROR=http://host.docker.internal:5000/ -v $(pwd):$(pwd) -w $(pwd) desmart/dekick-dind:2.0.3",
        )["stdout"].strip()

    def chmod_socket_wait_for_dind():
        dind_container_id = get_dind_container_id()
        rbash(
            "Waiting for DinD to start then change permissions of docker socket",
            f'docker exec "{dind_container_id}" bash -c "while ! '
            + 'docker ps >/dev/null 2>&1; do sleep 1; done; chmod 666 /var/run/docker.sock"',
        )

    DIND_CONTAINER_ID = create_dind_container()
    chmod_socket_wait_for_dind()

    return True


def stop_dind_container():
    """Stop the Docker-in-Docker container"""
    global DIND_CONTAINER_ID  # pylint: disable=global-statement

    if DIND_CONTAINER_ID is None:
        debug("DinD container is not running")
        return True

    dind_container_id = get_dind_container_id()
    rbash(
        "Stopping DinD container",
        f'docker kill "{dind_container_id}" >/dev/null 2>&1; exit 0',
    )
    DIND_CONTAINER_ID = None
    return True


def get_dind_container_id():
    """Get the ID of the DinD container"""
    return DIND_CONTAINER_ID


def rbash_dind(info_desc, cmd, env=None, expected_code=0, **kwargs):
    """Runs command in DinD and returns its output"""
    env = env or {}
    dind_container_id = get_dind_container_id()
    current_uid = f"{getuid()}:{getgid()}"

    tmp_docker_env = ""

    for key, value in env.items():
        tmp_docker_env += f'-e {key}="{value}" '

    cmd = cmd.replace('"', '\\"')
    dind_cmd = (
        f"docker exec {tmp_docker_env} --user={current_uid} "
        + f'"{dind_container_id}" bash -c "{cmd}"'
    )

    debug(dind_cmd)

    return rbash(
        info_desc=info_desc,
        cmd=dind_cmd,
        env=env,
        expected_code=expected_code,
        **kwargs,
    )
