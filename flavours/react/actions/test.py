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
from lib.dekickrc import get_dekickrc_value

install()
console = Console()


def main(args: list):
    is_vite_enabled = get_dekickrc_value("dekick.settings.vite.enabled")
    """Main"""
    pull_and_build_images()
    yarn_install()
    copy_artifacts_from_dind()
    if is_vite_enabled:
        ui_yarn(args=["test"] + args)
    else:
        ui_yarn(args=["test", "--ci", "--watchAll=false", "--forceExit"] + args)

