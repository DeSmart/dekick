import logging
from typing import Union

from commands.docker_compose import docker_compose, ui_docker_compose
from flavours.shared import ui_ask_for_log
from flavours.shared import wait_for_container as shared_wait_for_container
from lib.dotenv import get_dotenv_var
from lib.misc import get_flavour_container
from lib.run_func import run_func
from lib.settings import CURRENT_UID


def get_container() -> str:
    return "web"


def wait_for_container(search_string: Union[str, list], timeout: int = 30):
    if shared_wait_for_container(search_string, timeout=timeout, terminate=False):
        app_is_ready()
        return

    ui_ask_for_log()
    return


def app_is_ready():
    def run():
        try:
            api_url = get_dotenv_var(
                "API_URL", raise_exception=False
            ) or get_dotenv_var("APP_URL")
            return {
                "success": True,
                "text": f"App should be available at {api_url}",
            }
        except KeyError as error:
            return {
                "success": False,
                "type": "warn",
                "text": f"Warning! App may not work properly. Reason: {error.args[0]}",
            }

    run_func(text="Checking if app is ready", func=run)


def ui_go(args: list, description: str = "Running go"):
    """It runs go in a container

    Args:
        args (list): _description_
    """

    if not args:
        args = []

    def run():
        go(args)

    run_func(
        text=description,
        func=run,
    )


def go(
    args: list,
    env: Union[dict, None] = None,
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = True,
):
    """It runs go in a container

    Args:
        args (list): _description_
        env (Union[dict, None], optional): additional env added on top of default one. Defaults to None.
        raise_exception (bool, optional): raise exception if something goes wrong. Defaults to True.
        raise_error (bool, optional): raise error if something goes wrong. Defaults to True.
        capture_output (bool, optional): capture output to return value. Defaults to False.
    """
    logging.info("Running go (%s)", args)

    container = get_flavour_container()

    cmd = "run"
    args = [
        "--rm",
        "-e",
        "HOME=/tmp",
        "--user",
        CURRENT_UID,
        container,
        "go",
    ] + args

    return docker_compose(
        cmd=cmd,
        args=args,
        env=env,
        raise_exception=raise_exception,
        raise_error=raise_error,
        capture_output=capture_output,
    )
