"""
Local run for NuxtJS flavour
"""
from rich.console import Console
from rich.traceback import install

from commands.seed import ui_seed
from flavours.nuxt.shared import app_is_ready
from flavours.shared import (
    pull_and_build_images,
    start_services,
    wait_for_container,
    yarn_install,
)
from lib.dekickrc import get_dekickrc_value

install()
console = Console()


def main():
    """Main"""
    pull_and_build_images()
    yarn_install()
    start_services()
    if get_dekickrc_value("dekick.settings.seed.local") is True:
        ui_seed(force=False, check_with_global_config=True)
    wait_for_container(search_string="Local:    http://")
    app_is_ready()
