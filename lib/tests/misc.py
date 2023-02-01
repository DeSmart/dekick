"""Miscellaneous functinos running tests"""
from os import getcwd, getenv

from rich.traceback import install

install()


def parse_flavour_version(file: str) -> tuple:
    """Parses flavour and version from test file name"""
    file = file.split("/")[-1]
    return (
        file.split("__")[0].replace("test_", ""),
        file.split("__")[1].replace(".py", ""),
    )


def get_dekick_runner() -> str:
    if getenv("DEKICK_DOCKER_IMAGE"):
        return "dekick"
    else:
        return getcwd() + "/dekick-docker.sh"
