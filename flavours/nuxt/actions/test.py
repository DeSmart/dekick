"""
Local run for Node ExpressJS (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.seed import ui_seed
from commands.yarn import ui_yarn
from flavours.shared import (
    copy_artifacts_from_dind,
    pull_and_build_images,
    start_services,
    yarn_build,
    yarn_install,
)

install()
console = Console()


def main(args: list):
    """Main"""
    pull_and_build_images()
    yarn_install()
    copy_artifacts_from_dind()
    yarn_build()
    start_services()
    ui_seed(force=True)
    ui_yarn(args=["test"])
