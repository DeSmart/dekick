import urllib.request
from logging import error, info
from os import getenv
from time import sleep

from lib.rbash import rbash
from lib.settings import DEKICK_PATH

REGISTRY_DOCKER_COMPOSE = DEKICK_PATH + "/docker/registry/docker-compose.yml"


def start_docker_registry():
    """Starts Docker registry"""
    rbash(
        "Starting Docker registry proxy",
        f"docker compose -f {REGISTRY_DOCKER_COMPOSE} up -d --no-recreate --quiet-pull",
        env=get_env(),
    )
    wait_for_docker_registry()


def wait_for_docker_registry():
    """Wait for Docker registry to start"""
    timer = 0
    timeout = 30
    search_string = "The docker caching proxy is working"
    url = "http://proxy:3128/"

    while timer < timeout:
        try:
            info("Waiting for Docker registry to start... %s", timer)
            contents = str(urllib.request.urlopen(url).read())
            if search_string in contents:
                info("Docker registry is up and running")
                return
        except Exception:  # pylint: disable=broad-except
            pass

        sleep(1)
        timer = timer + 1

    error("Docker registry didn't start properly")
    raise Exception("Docker registry didn't start properly")


def get_env():
    """Returns environment variables"""
    return {"COMPOSE_PROJECT_NAME": "dekick-registry", "PATH": getenv("PATH")}
