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
from re import sub
from subprocess import PIPE, CalledProcessError, Popen
from typing import Union

from rich.traceback import install

from lib.dekickrc import get_dekickrc_value
from lib.dind import get_dind_container_id, is_dind_running
from lib.logger import get_log_filename
from lib.settings import (
    C_BOLD,
    C_CMD,
    C_END,
    C_FILE,
    CURRENT_UID,
    PROJECT_ROOT,
    is_dekick_dockerized,
)
from lib.spinner import create_spinner

install()


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
        ommit_dockerized (bool, optional): Defaults to False.
            ommit checking if running in dockerized environment

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
    # env["DOCKER_DEFAULT_PLATFORM"] = get_cpu_arch()
    env["COMPOSE_PROJECT_NAME"] = (
        os.getenv("COMPOSE_PROJECT_NAME") or compose_project_name
    )

    env["PROJECT_ROOT"] = PROJECT_ROOT
    env["CURRENT_UID"] = str(CURRENT_UID)
    env["PATH"] = os.getenv("PATH")
    env["HOME"] = os.getenv("HOME")

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

    logging.debug(env)

    return env


def get_cpu_arch() -> str:
    """Detects the platform for M1 (linux/arm64) or Intel (linux/amd64) CPU"""
    host_arch = os.getenv("HOST_ARCH")

    if host_arch is not None:
        return "linux/arm64" if host_arch.casefold() == "arm64" else "linux/amd64"

    return "linux/arm64" if platform.processor() == "arm" else "linux/amd64"


def get_platform() -> str:
    """Detects system (OS X or Linux)
    Returns: osx or linux
    """
    host_platform = os.getenv("HOST_PLATFORM")

    if host_platform is not None:
        return "osx" if host_platform.casefold() == "darwin" else "linux"

    return "osx" if sys.platform == "darwin" else "linux"


def get_subsystem() -> str:
    """Detects subsystem (ie. WSL2 on Windows)
    Returns: wsl or default
    """
    return str(os.getenv("HOST_SUBSYSTEM"))


def get_wsl_distro() -> str:
    """If on WSL then return distro name"""
    if get_subsystem() != "wsl":
        return ""

    return str(os.getenv("WSL_DISTRO_NAME"))


def are_all_ports_free(ports: list) -> bool:
    """Check if any of the given ports are occupied"""
    port_args = []
    for port in ports:
        port_args.append("-p")
        port_args.append(f"{port}:{port}")

    try:
        run_shell(
            [
                "docker",
                "run",
                "--rm",
            ]
            + port_args
            + ["hello-world"],
            raise_exception=True,
            capture_output=True,
        )
        return True
    except Exception:  # pylint: disable=broad-except
        return False


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
                "hello-world",
            ],
            raise_exception=True,
            capture_output=True,
        )
        return True
    except Exception:  # pylint: disable=broad-except
        return False


def run_shell(
    cmd: Union[list, str],
    env: Union[dict, None] = None,
    raise_exception: bool = True,
    raise_error: bool = True,
    capture_output: bool = False,
    cwd=None,
    shell=False,
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

    if is_dind_running():
        tmp_docker_env = []

        for key, value in env.items():
            tmp_docker_env = tmp_docker_env + ["-e", f"{key}={value}"]

        dind_container_id = get_dind_container_id()
        cmd = [
            "docker",
            "exec",
            "--user",
            CURRENT_UID,
            "-w",
            os.getcwd(),
            *tmp_docker_env,
            dind_container_id,
        ] + list(cmd)

    with Popen(
        args=cmd,
        env=env,
        stdout=PIPE if capture_output is True else sys.stdout,
        stderr=PIPE if capture_output is True else sys.stderr,
        universal_newlines=True,
        cwd=cwd,
        shell=shell,
    ) as proc:
        stderr, stdout = proc.communicate()
        returncode = proc.returncode

        if capture_output is True:
            stdout = stdout + stderr
            stderr = ""

        returncode = proc.returncode

    stdout_debug = str(stdout).strip()
    stderr_debug = str(stderr).strip()

    if capture_output is True:
        stderr_debug = stdout_debug

    if int(returncode) > 0:
        logging.info("Command %s output: %s", cmd, stdout_debug)

        if logfile != "" and raise_error is True:
            error = stderr_debug
            logging.error("Failed to execute %s: %s", cmd, error)

        if raise_exception is True:
            raise CalledProcessError(returncode, cmd, stdout, stderr)

    if stderr:
        logging.debug("Command %s stderr:\n%s", cmd, stderr_debug)
    if stdout:
        logging.debug("Command %s stdout:\n%s", cmd, stdout_debug)

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
    return str(get_dekickrc_value("dekick.flavour"))


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
        time.sleep(1)


def get_compose_project_name() -> str:
    """Get compose project name"""
    regex = r"[^a-zA-Z0-9_-]"
    project_name = get_dekickrc_value("project.name")
    project_name = sub(regex, "-", str(project_name))
    project_group = get_dekickrc_value("project.group")
    project_group = sub(regex, "-", str(project_group))

    return str(f"{project_group}_{project_name}" if project_group else project_name)
