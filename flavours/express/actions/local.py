"""
Local run for Node ExpressJS (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.seed import ui_seed
from flavours.express.shared import wait_for_container
from flavours.shared import (
    pull_and_build_images,
    start_services,
    yarn_build,
    yarn_install,
)

install()
console = Console()


def main():
    """Main"""
    pull_and_build_images()
    yarn_install()
    yarn_build()
    start_services()
    ui_seed()
    wait_for_container(search_string="API @ port", timeout=60)
