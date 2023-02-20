"""
Misc functions
"""
import difflib
import logging
import os
import platform
import sys
import tempfile
import time
from importlib import import_module
from os.path import basename, exists
from random import randint
from subprocess import PIPE, CalledProcessError, Popen
from typing import Union

from rich.traceback import install

from lib.dekickrc import get_dekickrc_value
from lib.logger import get_log_filename, log_exception
from lib.settings import (
    C_BOLD,
    C_CMD,
    C_END,
    C_ERROR,
    C_FILE,
    CURRENT_UID,
    DEKICK_DOCKER_IMAGE,
    PROJECT_ROOT,
    is_dekick_dockerized,
)
from lib.spinner import DEFAULT_SPINNER_MODE, create_spinner

install()

# pylint: disable=too-many-branches
def run_func(
    text: str,
    func=None,
    func_args: Union[None, dict] = None,
    terminate: bool = True,
) -> bool:
    """Run function with spinner

    Args:
        text (str): _description_
        func (_type_, optional): _description_. Defaults to None.
        func_args (Union[None, dict], optional): _description_. Defaults to None.
        terminate (bool, optional): _description_. Defaults to True.

    Returns:
        bool: _description_
    """

    logging.debug(locals())

    logging.info(text)
    spinner = create_spinner(text=text)

    spinner.start()

    if func is None:
        time.sleep(0.25)
        spinner.succeed()
        return True

    out = None

    try:
        if func_args is not None:
            out = func(**func_args)
        else:
            out = func()
    except Exception as error:  # pylint: disable=broad-except

        log_file = get_log_filename()
        fail_text = (
            f"{C_ERROR}Failed{C_END}. Please see {C_FILE}{log_file}{C_END}"
            + " for more information"
        )

        if DEFAULT_SPINNER_MODE == "halo":
            fail_text = (
                f"{text} {C_ERROR}failed{C_END}. Please see {C_FILE}{log_file}{C_END}"
                + " for more information"
            )

        spinner.fail(text=fail_text)

        logging.error("Error message: %s", error.args[0])
        log_exception(error)

        if terminate is True:
            sys.exit(1)

    if out is not None and out["success"] is not True:
        logging.debug(out)

        if "type" in out and out["type"] == "warn":
            logging.warning(out["text"])
            spinner.warn(text=out["text"])
        else:
            logging.error(out["text"])
            spinner.fail(text=out["text"])

        if terminate is True:
            logging.debug("Terminating DeKick with exit code 1")
            sys.exit(1)
        else:
            return False

    if out is not None and "text" in out and out["text"] != "":
        logging.info(out["text"])
        spinner.succeed(text=out["text"])
    else:
        spinner.succeed()

    if out is not None and "func" in out:
        logging.debug("Calling another function from run_func() with args: %s", out)

        if "func_args" in out:
            return out["func"](**out["func_args"])

        return out["func"]()

    return True


# pylint: disable=too-many-arguments
def check_command(
    cmd_linux: list,
    cmd_osx: list,
    hint_linux: str,
    hint_osx: str,
    arguments: int = 1,
    skip_if_dockerized: bool = False,
) -> bool:
    """Check if shell command is available
    Ends the script with the exit error code

    Args:
        cmd_linux (list):
        cmd_osx (list):
        hint_linux (str):
        hint_osx (str):
        arguments (int, optional): Defaults to 1.
        ommit_dockerized (bool, optional): Defaults to False. ommit checking if running in dockerized environment

    Returns:
        bool:
    """

    if skip_if_dockerized is True and is_dekick_dockerized():
        return True

    logging.debug(locals())

    cmd = cmd_osx if get_platform() == "osx" else cmd_linux
    hint = hint_osx if get_platform() == "osx" else hint_linux

    is_available = True

    try:
        run_shell(cmd, raise_exception=True, capture_output=True)
    except CalledProcessError:
        is_available = False

    spinner = create_spinner(
        f"Checking command {C_CMD}{' '.join(cmd[0:arguments])}{C_END}"
    )
    spinner.start()

    if is_available is True:
        time.sleep(0.2)
    else:
        spinner.fail()
        print(f"  {hint}")
        sys.exit(1)

    spinner.succeed()

    return is_available


def check_file(file) -> None:
    """Check file"""

    spinner = create_spinner(f"Checking file {C_FILE}{basename(file)}{C_END} exists")
    spinner.start()

    if exists(file):
        spinner.succeed()
    else:
        spinner.fail()
        sys.exit(1)


def default_env(override_env: Union[dict, None] = None) -> dict:
    """
    Generate default environment for use with subshell commands

    You can override default environment vars by passing the exact name of the variable
    """
    compose_project_name = get_compose_project_name()

    if override_env is None:
        override_env = {}

    env = override_env
    env["DOCKER_DEFAULT_PLATFORM"] = get_cpu_arch()
    env["COMPOSE_PROJECT_NAME"] = (
        os.getenv("COMPOSE_PROJECT_NAME") or compose_project_name
    )
    env["PROJECT_ROOT"] = PROJECT_ROOT
    env["CURRENT_UID"] = CURRENT_UID
    env["PATH"] = os.getenv("PATH")

    # Override environment variables
    for var in list(env):
        if var in override_env:
            env[var] = override_env[var]

    # Create environment variables DOCKER_PORT_{service}
    # if it's set in file .dekickrc in dekick.ports
    ports = get_dekickrc_value("dekick.ports")

    for port_def in ports:
        service = port_def["service"].upper().replace("-", "_")
        env[f"DOCKER_PORT_{service}"] = os.getenv(f"DOCKER_PORT_{service}") or str(
            port_def["port"]
        )

    return env


def get_cpu_arch() -> str:
    """Detects the platform for M1 (linux/arm64) or Intel (linux/amd64) CPU"""
    host_arch = os.getenv("HOST_ARCH")

    if host_arch is not None:
        return "linux/arm64" if host_arch.casefold() == "arm64" else "linux/amd64"

    return "linux/arm64" if platform.processor() == "arm" else "linux/amd64"


def get_platform() -> str:
    """Detects system (OS X or Linux)"""
    host_platform = os.getenv("HOST_PLATFORM")

    if host_platform is not None:
        return "osx" if host_platform.casefold() == "darwin" else "linux"

    return "osx" if sys.platform == "darwin" else "linux"


def is_port_free(port: int) -> bool:
    """Check if port is free"""

    try:
        run_shell(
            [
                "docker",
                "run",
                "--rm",
                "-p",
                f"{port}:{port}",
                DEKICK_DOCKER_IMAGE,
                "ls",
            ],
            raise_exception=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False


def run_shell(
    cmd: list,
    env: Union[dict, None] = None,
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = False,
) -> dict:
    """
    Run a shell command

    Args:
        cmd (list): command and its arguments to execute
        env (Union[dict, None], optional): Environment variables passed to executed command.
            They are added to default ones (see @misc.default_env). Defaults to None.
        raise_exception (bool, optional): True - raises exception when the command returncode > 0.
            Defaults to True.
        raise_error (bool, optional): True - raises logger error.
            Defaults to True.
        capture_output (bool, optional): True - output is returned,
            False - output (stdout and stderr) is printed immediately to terminal.
            Defaults to False.

    Raises:
        CalledProcessError: _description_

    Returns:
        dict: ["returncode": int, "stdout": str, "stderr": str]
    """
    env = default_env(env)

    stdout = ""
    stderr = ""
    returncode = 0
    logfile = get_log_filename()
    logging.debug(locals())

    with Popen(
        args=cmd,
        env=env,
        stdout=PIPE if capture_output is True else sys.stdout,
        stderr=PIPE if capture_output is True else sys.stderr,
        universal_newlines=True,
    ) as proc:

        stderr, stdout = proc.communicate()
        returncode = proc.returncode

        if capture_output is True:
            stdout = stdout + stderr
            stderr = ""

        returncode = proc.returncode

    if int(returncode) > 0:
        logging.info("Command %s output: %s", cmd, str(stdout).strip())

        if logfile != "" and raise_error is True:
            error = str(stderr).strip()
            logging.error("Error from running %s: %s", cmd, error)

        if raise_exception is True:
            raise CalledProcessError(returncode, cmd, "", f"Failed to execute {cmd}")

    if stderr:
        logging.debug("Command %s stderr:\n%s", cmd, stderr)
    if stdout:
        logging.debug("Command %s stdout:\n%s", cmd, stdout)

    return {"stdout": stdout, "stderr": stderr, "returncode": returncode}


def get_colored_diff(old: str, new: str) -> Union[str, bool]:
    """Generates colored diff between two strings"""

    if old == new:
        return False

    def red(text: str):
        return f"[red]{text}[/red]"

    def green(text: str):
        return f"[green]{text}[/green]"

    def normal(text: str):
        return f"{text}"

    result = ""
    codes = difflib.SequenceMatcher(a=old, b=new).get_opcodes()
    for code in codes:
        if code[0] == "equal":
            result += normal(old[code[1] : code[2]])
        if code[0] == "delete":
            result += red(old[code[1] : code[2]])
        elif code[0] == "insert":
            result += green(new[code[3] : code[4]])
        elif code[0] == "replace":
            result += red(old[code[1] : code[2]]) + green(new[code[3] : code[4]])

    return result

    # lines_only = ""
    # for line in result.split("\n"):
    #     if line.find("[red]") != -1 or line.find("[green]") != -1:
    #         lines_only += f"{line}\n"

    # return lines_only.strip()


def create_temporary_dir() -> str:
    """Creates temporary directory"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        return tmp_dir


def check_argparse_arg(arg, name):
    """Checks if required argument is passed"""
    if arg is None:
        print(f"Error: Missing required argument {name}")
        sys.exit(1)


def get_flavour() -> str:
    """Gets specific flavour name"""
    return get_dekickrc_value("dekick.flavour")


def get_flavour_container() -> str:
    """Gets specific flavour container name"""
    flavour = get_flavour()
    return import_module(f"flavours.{flavour}.shared").get_container()


def first_run_banner():
    """Shows some info if project is run for the first time"""
    if not os.path.exists(f"{PROJECT_ROOT}/.env"):
        print(
            f"{C_BOLD}{C_CMD}  This seems to be a first run on this machine, "
            + "please be patient while we prepare"
            + f" your environment{C_END}"
        )
        time.sleep(2)


def randomize_ports():
    """Create environment variables with randomized port numbers"""
    for port_def in get_dekickrc_value("dekick.ports"):
        service = port_def["service"].upper().replace("-", "_")
        port = randint(10000, 50000)
        os.environ[f"DOCKER_PORT_{service}"] = str(port)
        logging.debug("Randomizing port DOCKER_PORT_%s=%s", service, port)


def randomize_compose_project_name():
    """Create environment variable with randomized compose project name"""
    project = f"{get_compose_project_name()}{randint(10000, 50000)}"
    os.environ["COMPOSE_PROJECT_NAME"] = project
    logging.debug("Randomizing compose project COMPOSE_PROJECT_NAME=%s", project)


def get_compose_project_name() -> str:
    """Get compose project name"""
    project_name = get_dekickrc_value("project.name")
    project_group = get_dekickrc_value("project.group")

    return str(f"{project_group}_{project_name}" if project_group else project_name)
