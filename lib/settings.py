"""Settings for DeKick"""

import time
from getpass import getuser
from glob import glob
from importlib import import_module
from os import get_terminal_size, getcwd, getenv, getuid, listdir, path
from sys import stdout

from lib.terminal_colors import TerminalColors

colors = TerminalColors()


C_CMD = colors.fg("purple")
C_CODE = colors.fg("orange")
C_END = colors.reset()
C_FILE = colors.fg("lightcyan")
C_BOLD = colors.bold()
C_ERROR = colors.fg("red")
C_WARN = colors.fg("yellow")
C_TIME = colors.fg("green")

PROJECT_ROOT = getenv("PROJECT_ROOT") or f"{getcwd()}"
DEKICK_PATH = getenv("DEKICK_PATH") or f"{getcwd()}/dekick"
DEKICK_DOCKER_IMAGE = getenv("DEKICK_DOCKER_IMAGE") or None
CURRENT_UID = str(getenv("CURRENT_UID") or getuid())
CURRENT_USERNAME = getenv("CURRENT_USERNAME") or getuser()
TERMINAL_COLUMN_WIDTH = (get_terminal_size().columns - 3) if stdout.isatty() else 120
HOST_HOME = str(getenv("HOST_HOME")) or f"/home/{CURRENT_USERNAME}"

DEKICK_STABLE_VERSION_URL = (
    "https://raw.githubusercontent.com/DeSmart/dekick/main/.version"
)
DEKICK_GIT_URL = "https://github.com/DeSmart/dekick.git"
DEKICK_BOILERPLATES = [
    "express/default",
    "express/socket-server",
    "laravel/php7_4",
    "laravel/php8_1",
    "laravel/php8_2",
    "react/default",
    "nuxt/default",
    "next/default",
    "nest/default",
]

DEKICKRC_TMPL_FILE = ".dekickrc.tmpl.yml"
DEKICKRC_FILE = ".dekickrc.yml"

DEKICKRC_PATH = f"{PROJECT_ROOT}/{DEKICKRC_FILE}"

DEKICK_VERSION_FILE = ".version"
DEKICK_VERSION_PATH = f"{DEKICK_PATH}/{DEKICK_VERSION_FILE}"

DEKICKRC_GLOBAL_FILE = "global.yml"
DEKICKRC_GLOBAL_HOST_PATH = f"{HOST_HOME}/.config/dekick/{DEKICKRC_GLOBAL_FILE}"
DEKICKRC_GLOBAL_PATH = f"/tmp/homedir/.config/dekick/{DEKICKRC_GLOBAL_FILE}"
DEKICKRC_GLOBAL_TMPL_PATH = f"{DEKICK_PATH}/global_tmpl.yml"

DEKICK_MIGRATIONS_DIR = f"{DEKICK_PATH}/migrations"

DEKICK_BOILERPLATES_INSTALL_PATH = getenv("DEKICK_BOILERPLATES_INSTALL_PATH") or ""

DEKICK_DOTENV_FILE = ".env"
DEKICK_DOTENV_PATH = f"{PROJECT_ROOT}/{DEKICK_DOTENV_FILE}"

DEKICK_TIME_START = 0

DEKICK_PYTEST_MODE = False

DEKICK_CI_MODE = False


def get_credentials_drivers():
    """Generate list of available credentials drivers"""
    drivers = [
        path.splitext(path.basename(file))[0]
        for file in glob(DEKICK_PATH + "/lib/drivers/credentials/*")
        if "__pycache__" not in file
    ]
    return drivers


DEKICK_CREDENTIALS_DRIVERS = get_credentials_drivers()


def get_credentials_drivers_info() -> dict:
    """Generate list of available credentials drivers"""
    drivers = DEKICK_CREDENTIALS_DRIVERS
    drivers_info = {}
    for driver in drivers:
        get_module = import_module(f"lib.drivers.credentials.{driver}._main")
        drivers_info[driver] = get_module.info()

    return drivers_info


def get_flavours() -> list:
    """Generate list of available flavours"""
    directory = DEKICK_PATH + "/flavours"
    return [
        subdir
        for subdir in listdir(directory)
        if path.isdir(path.join(directory, subdir)) and subdir != "__pycache__"
    ]


DEKICK_FLAVOURS = get_flavours()


def save_commands(commands: list):
    """Save commands to file for use in ./docker/dekick/docker-entrypoint.sh"""
    with open(DEKICK_PATH + "/commands.sh", "w", encoding="utf-8") as commands_file:
        commands_file.write("#!/bin/bash\n")
        commands_file.write('export DEKICK_COMMANDS=("' + '" "'.join(commands) + '")')


def get_dekick_commands():
    """Generate available commands to use with dekick"""
    commands: list = []
    for file in sorted(glob(f"{DEKICK_PATH}/commands/*.py")):
        file = path.splitext(path.basename(file))[0].replace("_", "-")
        if file != "__init__":
            commands.append(file)

    sub_commands: dict = {}
    for command in commands:
        for file in sorted(glob(f"{DEKICK_PATH}/commands/sub_{command}/*.py")):
            file = path.splitext(path.basename(file))[0].replace("_", "-")
            if file == "__init__":
                continue
            if command not in sub_commands:
                sub_commands[command] = []
            sub_commands[command].append(file)

    save_commands(commands)
    return {"commands": commands, "sub_commands": sub_commands}


DEKICK_COMMANDS = get_dekick_commands()


def set_dekick_time_start():
    """Update DEKICK_TIME_START"""
    global DEKICK_TIME_START  # pylint: disable=global-statement
    DEKICK_TIME_START = time.time()


def get_dekick_time_start() -> float:
    """Get DEKICK_TIME_START"""
    return DEKICK_TIME_START


def get_seconds_since_dekick_start(ndigits: int = 0) -> float:
    """Get seconds since dekick start"""
    return round(time.time() - get_dekick_time_start(), ndigits)


def is_dekick_dockerized() -> bool:
    """Check if DeKick is running inside a Docker container"""
    return bool(getenv("DEKICK_DOCKER_IMAGE")) or False


def set_pytest_mode(mode: bool):
    """Sets DEKICK_PYTEST_MODE to True"""
    global DEKICK_PYTEST_MODE  # pylint: disable=global-statement
    DEKICK_PYTEST_MODE = mode


def is_pytest() -> bool:
    """Check if DeKick is running inside a Docker container"""
    return DEKICK_PYTEST_MODE


def set_ci_mode(mode: bool):
    """Sets DEKICK_CI_MODE to True"""
    global DEKICK_CI_MODE  # pylint: disable=global-statement
    DEKICK_CI_MODE = mode


def is_ci() -> bool:
    """Check if DeKick is running in CI/CD environment"""
    return DEKICK_CI_MODE
