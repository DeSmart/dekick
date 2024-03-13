"""
Shared functions for all flavours
"""

import logging
from subprocess import CalledProcessError
from sys import stdout
from typing import Union

from rich.prompt import Confirm

from commands.composer import composer
from commands.docker_compose import (
    docker_compose,
    get_container_log,
    ui_docker_compose,
    wait_for_log,
)
from commands.yarn import ui_yarn
from lib.dekickrc import get_dekickrc_value
from lib.dind import copy_from_dind
from lib.dotenv import get_dotenv_var
from lib.logger import log_exception
from lib.misc import create_temporary_dir, get_flavour_container, run_shell
from lib.run_func import run_func
from lib.settings import (
    C_CMD,
    C_CODE,
    C_END,
    C_FILE,
    CURRENT_UID,
    get_seconds_since_dekick_start,
    is_ci,
    is_pytest,
)


def composer_install():
    """Run composer install command"""

    args = []

    if args is None:
        args = []

    def check_app_env():
        try:
            app_env = get_dotenv_var("APP_ENV")
            if app_env in ("production", "beta"):
                logging.debug(
                    "APP_ENV is %s: running composer install in production mode",
                    app_env,
                )
                args.append("--no-dev")
                args.append("--optimize-autoloader")

        except KeyError:  # pylint: disable=broad-except
            return {
                "status": False,
                "text": "No key APP_ENV defined in .env file",
            }

    def run_composer_install():
        try:
            composer(["install", *args])
        except CalledProcessError as error:
            raise RuntimeError(f"{error.stderr}") from error

    run_func(text=f"Getting APP_ENV from {C_FILE}.env{C_END}", func=check_app_env)
    run_func(text=f"Running {C_CMD}composer install{C_END}", func=run_composer_install)


def yarn_install():
    """Run yarn install command"""
    ui_yarn(args=["install"])


def copy_artifacts_from_dind():
    """Copy artifacts from dind container to host"""
    artifacts_dir = get_dekickrc_value("project.artifacts")

    if not is_ci() or is_pytest() or artifacts_dir is None:
        return

    for artifact_dir in artifacts_dir:
        resource = artifact_dir["path"]
        run_func(
            text=f"Copying {C_FILE}{resource}{C_END} from container to host",
            func=copy_from_dind,
            func_args={"resource": resource},
        )


def yarn_build():
    """Run yarn build command"""
    ui_yarn(args=["build"])


def start_services():
    """Start all services defined in docker-compose.yml file"""
    ui_docker_compose(cmd="up", args=["-d"], text="Starting services")


def start_service(service: str):
    """Start service"""
    ui_docker_compose(
        cmd="up",
        args=["-d", service, service],
        text=f"Starting service {C_CMD}{service}{C_END}",
    )


def stop_service(
    service: str, kill: bool = False, remove: bool = False, volumes: bool = False
):
    """Stop service"""

    def run():
        cmd = "stop" if kill is False else "kill"
        docker_compose(
            cmd=cmd, args=[service], raise_exception=True, capture_output=True
        )

        if remove is True:
            args = [service, "--force"]

            if volumes is True:
                args.append("--volumes")

            docker_compose(
                cmd="rm",
                args=args,
                raise_exception=True,
                capture_output=True,
            )

    run_func(text=f"Stopping {C_CMD}{service}{C_END} service", func=run)


def kill_service(service: str):
    """Kill service"""

    def run():
        cmd = "kill"
        args = [service]
        docker_compose(cmd=cmd, args=args, raise_exception=True, capture_output=True)

    run_func(text=f"Killing {C_CMD}{service}{C_END} service", func=run)


def get_all_services() -> list:
    """Get all services defined in docker-compose.yml file"""
    ret = docker_compose(cmd="config", args=["--services"], capture_output=True)
    return str(ret["stdout"]).strip().split("\n")


def wait_for_container(
    search_string: Union[str, list],
    failed_string: str = "",
    timeout: int = 60,
    container=None,
    terminate: bool = True,
) -> bool:
    """Wait for container logs to contain a search_string

    Args:
        search_string (str): Search string
        timeout (int, optional): Timeout. Defaults to 60.
    """
    container = container or get_flavour_container()

    def run():
        try:
            wait_for_log(container, search_string, failed_string, timeout)
            return {
                "success": True,
                "text": f"Your {C_CMD}{container}{C_END} container is ready!",
            }
        except (TimeoutError, RuntimeError) as error:
            logging.error(str(error.args[0]))
            return {
                "success": False,
                "text": str(error.args[0]),
            }
        except Exception as error:  # pylint: disable=broad-except
            error_text = (
                f"Failed to start {C_CMD}{container}{C_END} container, check container "
                + f"logs for more information. {error}"
            )
            logging.error(error_text)
            return {
                "success": False,
                "text": error_text,
            }

    return run_func(
        text=f"Waiting for {C_CMD}{container}{C_END} container to start",
        func=run,
        terminate=terminate,
    )


def build_image(target_image: str):
    """Build image"""
    container = get_flavour_container()
    tmp_dir = retrieve_files_from_container(container)

    def run():
        run_shell(
            [
                "docker",
                "build",
                f"{tmp_dir}",
                "-f",
                "docker/Dockerfile",
                "-t",
                target_image,
            ],
            capture_output=True,
            raise_exception=True,
        )

    run_func(
        text=f"Building image {C_CODE}{target_image}{C_END} using files "
        + f"from {C_CODE}{tmp_dir}{C_END}",
        func=run,
    )


def retrieve_files_from_container(container: str) -> str:
    """Retrieve files from container"""
    tmp_dir = create_temporary_dir()

    def run():
        try:
            image_id = find_image_id_by_container(container)
        except Exception as err:  # pylint: disable=broad-except
            logging.error(err)
            return {
                "success": False,
                "text": f"Failed to find image id for container {container}",
            }

        run_shell(
            cmd=["docker", "cp", f"{image_id}:/usr/src/app", tmp_dir],
            raise_exception=True,
        )

    run_func(
        text=f"Copying files from container {C_CODE}{container}{C_END} to {C_CODE}{tmp_dir}{C_END}",
        func=run,
    )

    return tmp_dir


def find_image_id_by_container(container: str) -> str:
    """Find image id by container name"""
    ret = docker_compose(
        cmd="ps", args=["-q", container], capture_output=True, raise_exception=True
    )
    return str(ret["stdout"]).strip()


def push_image(
    image_name: str,
    docker_login_user: str,
    docker_login_password: str,
    docker_registry: str,
) -> None:
    """Push image to Docker registry"""

    def run():
        try:
            run_shell(
                [
                    "docker",
                    "login",
                    "-u",
                    docker_login_user,
                    "-p",
                    docker_login_password,
                    docker_registry,
                ],
                capture_output=True,
            )

            run_shell(["docker", "push", image_name], capture_output=True)
            return {"success": True}
        except Exception as error:  # pylint: disable=broad-except
            logging.error("Message or exit code: %s", error.args[0])
            log_exception(error)
            return {
                "success": False,
                "text": f"Failed to push image {image_name} to {docker_registry}, "
                + f"check {C_CMD}dekick.log{C_END} for more information",
            }

    run_func(
        text=f"Pushing image {image_name} to {docker_registry}",
        func=run,
    )


def pull_and_build_images():
    """Pull and build images"""

    def run():
        args = [get_flavour_container()]
        docker_compose(cmd="build", args=args, env={})

    run_func(
        text="Pulling and building images",
        func=run,
    )


def save_image_to_dind(image_name: str) -> str:
    """Save image to tar file"""

    image_file = f"{image_name}.tar"

    def run():
        run_shell(["docker", "save", "-o", image_file, image_name])

    run_func(
        text=f"Saving image {C_CODE}{image_name}{C_END} to {C_FILE}{image_file}{C_END}",
        func=run,
    )

    return image_file


def copy_image_to_host(image_path: str):
    """Copy image from dind container to host"""

    def run():
        copy_from_dind(resource=image_path)

    run_func(
        text=f"Copying image {C_FILE}{image_path}{C_END} from container to host",
        func=run,
    )


def load_image_to_host(image_path: str):
    """Load image from tar file"""

    def run():
        run_shell(
            ["docker", "load", "-i", image_path],
            capture_output=True,
            raise_exception=True,
        )

    run_func(
        text=f"Loading Docker image to host from {C_FILE}{image_path}{C_END}",
        func=run,
    )


def remove_image_file(image_path: str):
    """Remove image file"""

    def run():
        run_shell(["rm", "-f", image_path])

    run_func(
        text=f"Removing image file {C_FILE}{image_path}{C_END}",
        func=run,
    )


def setup_permissions(dirs: str):
    """Setup permissions for directories"""

    def run():
        cmd = "run"
        args = [
            "-T",
            "--rm",
            "--user=root",
            get_flavour_container(),
            "sh",
            "-c",
            f"mkdir -p {dirs}; chown {CURRENT_UID} {dirs}",
        ]

        docker_compose(cmd=cmd, args=args, env={})

        return {"success": True, "text": ""}

    run_func(
        text="Creating required directories and setting permissions",
        func=run,
    )


def is_service_running(service: str) -> bool:
    """Check if service is running"""
    ret = docker_compose(
        cmd="ps",
        args=["--services", "--filter", "status=running", service],
        capture_output=True,
        raise_exception=False,
    )
    return bool(ret["stdout"].strip() == service)


def ui_ask_for_log():
    """Ask if user wants to see logs"""
    if stdout.isatty() is False:
        return

    container = get_flavour_container()
    question = "Do you want to see logs?"
    if Confirm.ask(question, default=False) is True:
        get_container_log(
            container, get_seconds_since_dekick_start(), capture_output=False
        )
