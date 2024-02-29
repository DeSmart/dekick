"""
Local run for Node ExpressJS (backend) application
"""

from rich.traceback import install

from flavours.express.shared import wait_for_container
from flavours.shared import pull_and_build_images, start_services, yarn_install

install()


def main():
    """Main"""
    pull_and_build_images()
    yarn_install()
    start_services()
    wait_for_container(search_string=["Ready in", "ready started server"], timeout=60)
