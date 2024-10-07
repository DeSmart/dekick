"""
Local run for Node ExpressJS (backend) application
"""

from rich.console import Console
from rich.traceback import install

from flavours.express.shared import wait_for_container
from flavours.golang.shared import ui_go
from flavours.shared import pull_and_build_images, start_services

install()
console = Console()


def main():
    """Main"""
    pull_and_build_images()
    ui_go(["get", "./..."], "Installing dependencies")
    start_services()
    wait_for_container(search_string="http server started", timeout=60)
