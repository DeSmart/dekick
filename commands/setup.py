"""
Install required dependency packages defined in requirements.txt if they're not already installed.

Don't install anything if DeKick is running inside a Docker container (is dockerized)
"""

import os
import re
import subprocess

DEKICK_PATH = os.getenv("DEKICK_PATH") or f"{os.getcwd()}/dekick"


def is_dekick_dockerized() -> bool:
    """
    Check if DeKick is running inside a Docker container
    """
    return bool(os.getenv("DEKICK_DOCKER_IMAGE")) or False


def get_installed_packages() -> list:
    """
    Reads all installed packages and returns them as a list.
    """

    return (
        subprocess.check_output(["pip3", "freeze", "--disable-pip-version-check"])
        .decode("utf-8")
        .splitlines()
    )


def install_package(package):
    """
    Install a package using pip3
    """

    # Remove comments from package
    package_parsed = re.sub(r"^#.*$", "", package)

    if package_parsed == "":
        return

    package_name = package_parsed.split("==")[0]
    package_version = package_parsed.split("==")[1]

    print(f"Installing package {package_name}, version {package_version}")
    subprocess.check_call(
        [
            "pip3",
            "install",
            "-q",
            "-q",
            package,
            "--disable-pip-version-check",
        ],
        stdout=subprocess.PIPE,
    )


def get_required_packages() -> list:
    """
    Get required packages from the requirements.txt file
    """
    with open(f"{DEKICK_PATH}/requirements.txt", encoding="utf-8") as file:
        return file.read().splitlines()


def install_required_packages() -> None:
    """
    Install required packages
    """
    if is_dekick_dockerized():
        return

    installed_packages = get_installed_packages()
    required_packages = get_required_packages()

    diff = list(set(required_packages) - (set(installed_packages)))

    for package in diff:
        install_package(package)
