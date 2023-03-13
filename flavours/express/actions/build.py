"""
Build for Node ExpressJS (backend) application
"""
from rich.console import Console
from rich.traceback import install

from flavours.express.shared import setup_permissions
from flavours.shared import (
    copy_artifacts_from_dind,
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
    copy_artifacts_from_dind()
    yarn_build()
    start_services()
