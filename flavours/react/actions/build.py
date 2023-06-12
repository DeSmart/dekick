"""
Build for ReactJS (backend) application
"""
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


def main():
    """Main"""
    check_file(".env")
    pull_and_build_images()
    yarn_install()
    yarn_build()
    copy_artifacts_from_dind()
    start_services()
