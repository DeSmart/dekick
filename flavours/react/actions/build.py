"""
Build for ReactJS (backend) application
"""
from rich.traceback import install

from flavours.react.shared import setup_permissions
from flavours.shared import (
    pull_and_build_images,
    start_services,
    yarn_build,
    yarn_install,
)

install()


def main():
    """Main"""
    pull_and_build_images()
    setup_permissions()
    yarn_install()
    yarn_build()
    start_services()
