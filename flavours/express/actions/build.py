"""
Build for Node ExpressJS (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.stop import stop
from flavours.express.shared import setup_permissions
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
    setup_permissions()
    yarn_install()
    yarn_build()
    start_services()
