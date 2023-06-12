"""
Local run for Node ExpressJS (backend) application
"""
from rich.console import Console
from rich.traceback import install

from commands.yarn import ui_yarn
from flavours.shared import (
    copy_artifacts_from_dind,
    pull_and_build_images,
    yarn_install,
)

install()
console = Console()


def main(args: list):
    """Main"""
    pull_and_build_images()
    yarn_install()
    copy_artifacts_from_dind()
    ui_yarn(args=["test", "--ci", "--watchAll=false", "--forceExit"] + args)
