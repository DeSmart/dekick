"""Various filesystem utilities"""
from os import chown as oschown
from os import stat, utime

from lib.settings import CURRENT_UID


def chown(path: str):
    """Changes the owner of a file"""
    s = stat(path)
    gid = int(s.st_gid)
    try:
        oschown(path, int(CURRENT_UID), gid)
    except Exception:  # pylint: disable=broad-except
        pass


def touch(path: str):
    """Creates an empty file"""
    with open(path, "a", encoding="utf-8"):
        utime(path, None)
