import re

from lib.settings import (
    DEKICK_BOILERPLATES,
    DEKICK_CREDENTIALS_DRIVERS,
    DEKICK_FLAVOURS,
)


def validator_url(value: str) -> bool:
    """Validates if the provided string is a valid URL."""
    pattern = re.compile(r"(http|https)://[a-zA-Z0-9./?#-_]+")
    return bool(pattern.match(value))


def validator_name(value: str) -> bool:
    """Validates if the provided string contains only English characters plus '_' and '-' signs."""
    return bool(re.match(r"^[\w\d_\-/]+$", value))


def validator_any(value: str) -> bool:
    """Validates if any character is present in the provided string."""
    return len(value) > 0


def validator_bool(value: str) -> bool:
    """Validates if the provided string is either 'True' or 'False'."""
    return value.lower() in ["true", "false"]


def validator_port(value: str) -> bool:
    """
    Validates if the provided string represents a valid network port number.
    Should be an integer between 0-65535 (inclusive).
    """
    try:
        port = int(value)
        return 0 <= port <= 65535
    except ValueError:
        return False


def validator_rel_path(value: str) -> bool:
    """
    Validates if the provided string is a valid Unix-style relative file path.
    E.g. "usr/local/bin/python"
    """
    pattern = re.compile(r"^\.?[a-zA-Z0-9\.=+_\-/]+$")
    return bool(pattern.match(value))


def validator_boilerplate(value: str) -> bool:
    """Checks if the provided string is a valid boilerplate name."""
    return value in DEKICK_BOILERPLATES


def validator_flavour(value: str) -> bool:
    """Checks if the provided string is a valid flavor name."""
    return value in DEKICK_FLAVOURS


def validator_credentials_driver(value: str) -> bool:
    """Checks if the provided string is a valid credentials driver name."""
    return value in DEKICK_CREDENTIALS_DRIVERS
