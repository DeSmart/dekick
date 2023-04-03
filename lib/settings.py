import time
from getpass import getuser
from glob import glob
from os import get_terminal_size, getcwd, getenv, getuid, path
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

DEKICK_MASTER_VERSION_URL = (
    "https://raw.githubusercontent.com/DeSmart/dekick/main/.version"
)
DEKICK_GIT_URL = "https://github.com/DeSmart/dekick.git"
DEKICK_BOILERPLATES = [
    "express/default",
    "laravel/php7_4",
    "laravel/php8_1",
    "laravel/php8_2",
    "react/default",
]
DEKICK_FLAVOURS = ["express", "react", "laravel"]
DEKICK_CREDENTIALS_DRIVERS = [
    path.splitext(path.basename(file))[0]
    for file in glob(DEKICK_PATH + "/lib/drivers/credentials/*.py")
]

# Available commands to use with dekick
DEKICK_COMMANDS = [
    "artisan",
    "build",
    "composer",
    "credentials",
    "docker-compose",
    "knex",
    "local",
    "logs",
    "node",
    "npm",
    "npx",
    "phpunit",
    "pint",
    "seed",
    "status",
    "stop",
    "test",
    "update",
    "yarn",
]

DEKICKRC_TMPL_FILE = ".dekickrc.tmpl.yml"
DEKICKRC_FILE = ".dekickrc.yml"

DEKICKRC_PATH = f"{PROJECT_ROOT}/{DEKICKRC_FILE}"

DEKICK_VERSION_FILE = ".version"
DEKICK_VERSION_PATH = f"{DEKICK_PATH}/{DEKICK_VERSION_FILE}"

DEKICK_MIGRATIONS_DIR = f"{DEKICK_PATH}/migrations"

DEKICK_DOTENV_FILE = ".env"
DEKICK_DOTENV_PATH = f"{PROJECT_ROOT}/{DEKICK_DOTENV_FILE}"

DEKICK_TIME_START = 0

DEKICK_PYTEST_MODE = False

DEKICK_CI_MODE = False


def save_commands():
    """Save commands to file for use with ./docker/dekick/docker-entrypoint.sh"""
    with open(DEKICK_PATH + "/commands.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write('export DEKICK_COMMANDS=("' + '" "'.join(DEKICK_COMMANDS) + '")')


save_commands()


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
