"""
Build for Node ExpressJS (backend) application
"""
from rich.console import Console
from rich.traceback import install

from flavours.shared import (
    copy_artifacts_from_dind,
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
    yarn_install()
    yarn_build()
    copy_artifacts_from_dind()
    start_services()
