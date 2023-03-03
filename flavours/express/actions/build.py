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
from lib.misc import check_file

install()
console = Console()


def main():
    """Main"""
    check_file(".env")
    pull_and_build_images()
    setup_permissions()
    yarn_install()
    yarn_build()
    start_services()
