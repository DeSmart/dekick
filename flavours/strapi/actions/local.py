"""
Local run for Node ExpressJS (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.seed import ui_seed
from flavours.express.shared import wait_for_container
from flavours.shared import pull_and_build_images, start_services, yarn_install
from lib.dekickrc import get_dekickrc_value

install()
console = Console()


def main():
    """Main"""
    pull_and_build_images()
    yarn_install()
    start_services()
    wait_for_container(
        search_string=["To access the server", "Create your first administrator"],
        timeout=60,
    )
