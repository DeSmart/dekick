from argparse import ArgumentParser


def info() -> str:
    """Get info about this driver"""
    return "Dummy"


def init():
    """Initialize this driver"""


# pylint: disable=unused-argument
def get_envs(*args, env: str, **kwargs) -> str:
    """Get all variables from Gitlab"""
    return f"ENV={env}"


def arguments(parser: ArgumentParser):
    """Parse arguments for this driver"""
