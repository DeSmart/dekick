"""
Build for Node ExpressJS (backend) application
"""

from rich.console import Console
from rich.traceback import install

from flavours.golang.shared import ui_go
from flavours.shared import (
    copy_artifacts_from_dind,
    pull_and_build_images,
    start_services,
)
from lib.misc import check_file

install()
console = Console()


def main():
    """Main"""
    check_file(".env")
    pull_and_build_images()
    ui_go(["get", "./..."], "Installing dependencies")
    copy_artifacts_from_dind()
    ui_go(["run", "github.com/swaggo/swag/cmd/swag", "init", "-d", "cmd/api", "--parseDependency", "--parseInternal"], "Generating swagger docs")
    ui_go(["build", "cmd/api/main.go", "cmd/api/routes.go"], "Building application")
    start_services()
