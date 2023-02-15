from lib.tests.docker import get_docker_env
from lib.tests.rbash import rbash


def start_docker_registry():
    """Starts Docker registry"""
    rbash(
        "Starting Docker registry",
        "docker compose -f docker/registry/docker-compose.yml up -d",
        env=get_docker_env(),
    )


def stop_docker_registry():
    """Stops Docker registry"""
    rbash(
        "Stopping Docker registry",
        "docker compose -f docker/registry/docker-compose.yml down",
        env=get_docker_env(),
    )
