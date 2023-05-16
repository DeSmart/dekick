"""
Local run for ReactJS (frontend) application
"""
from rich.console import Console
from rich.traceback import install

from flavours.react.shared import wait_for_container
from flavours.shared import pull_and_build_images, start_services, yarn_install

install()
console = Console()


def main():
    """Main"""
    pull_and_build_images()
    yarn_install()
    start_services()
    wait_for_container()
