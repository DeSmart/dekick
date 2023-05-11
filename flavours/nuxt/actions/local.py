"""
Local run for NuxtJS flavour
"""
from rich.console import Console
from rich.traceback import install

from commands.seed import ui_seed
from flavours.shared import (
    pull_and_build_images,
    start_services,
    wait_for_container,
    yarn_build,
    yarn_install,
)

install()
console = Console()


def main():
    """Main"""

    pull_and_build_images()
    yarn_install()
    # yarn_build()
    start_services()
    ui_seed()
    wait_for_container(search_string="Local:    http://")
