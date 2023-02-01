from os import get_terminal_size, getcwd, getenv, getgid, getuid
from sys import stdout
from time import time

from lib.terminal_colors import TerminalColors

colors = TerminalColors()

DEKICK_MASTER_VERSION_URL = (
    "https://git.desmart.com/desmart/dekick/-/raw/master/.version"
)
DEKICK_GIT_URL = "https://git.desmart.com/desmart/dekick.git"
DEKICK_BOILERPLATES = [
    "api/node/js",
    "api/node/ts",
    "api/php/7.4",
    "api/php/8.0",
    "api/php/8.1",
    "front/react/generic",
    "mono/vue/8.0",
    "front/vue/deauth",
]
DEKICK_FLAVOURS = ["express", "react", "laravel"]

# Available commands to use with dekick
# Warning! If you add a new command, you must add it to ./docker/docker-entrypoint.sh also!
DEKICK_COMMANDS = [
    "artisan",
    "build",
    "composer",
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

C_CMD = colors.fg("purple")
C_CODE = colors.fg("orange")
C_END = colors.reset()
C_FILE = colors.fg("lightcyan")
C_BOLD = colors.bold()
C_ERROR = colors.fg("red")
C_WARN = colors.fg("yellow")

PROJECT_ROOT = getenv("PROJECT_ROOT") or f"{getcwd()}"
DEKICK_PATH = getenv("DEKICK_PATH") or f"{getcwd()}/dekick"
DEKICK_DOCKER_IMAGE = getenv("DEKICK_DOCKER_IMAGE") or None
CURRENT_UID = getenv("CURRENT_UID") or f"{getuid()}:{getgid()}"
GITLAB_URL = "https://git.desmart.com"
TERMINAL_COLUMN_WIDTH = (get_terminal_size().columns - 3) if stdout.isatty() else 120

DEKICKRC_TMPL_FILE = ".dekickrc.tmpl.yml"
DEKICKRC_FILE = ".dekickrc.yml"

DEKICKRC_TMPL_PATH = f"{DEKICK_PATH}/{DEKICKRC_TMPL_FILE}"
DEKICKRC_PATH = f"{PROJECT_ROOT}/{DEKICKRC_FILE}"

DEKICK_VERSION_FILE = ".version"
DEKICK_VERSION_PATH = f"{DEKICK_PATH}/{DEKICK_VERSION_FILE}"

DEKICK_MIGRATIONS_DIR = f"{DEKICK_PATH}/migrations"

DEKICK_DOTENV_FILE = ".env"
DEKICK_DOTENV_PATH = f"{PROJECT_ROOT}/{DEKICK_DOTENV_FILE}"

DEKICK_TIME_START = 0

DEKICK_PYTEST_MODE = False

BOILERPLATES_DEFAULT_GIT_URL = "https://github.com/desmart/dekick-boilerplates.git"  # pylint: disable=line-too-long
BOILERPLATES_PATH = getcwd() + "/boilerplates/"


def set_dekick_time_start():
    """Update DEKICK_TIME_START"""
    global DEKICK_TIME_START  # pylint: disable=global-statement
    DEKICK_TIME_START = time()


def get_dekick_time_start() -> float:
    """Get DEKICK_TIME_START"""
    return DEKICK_TIME_START


def get_seconds_since_dekick_start() -> int:
    """Get seconds since dekick start"""
    return int(round(time() - get_dekick_time_start()))


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
