"""Various filesystem utilities"""
import os

from lib.settings import CURRENT_UID


def chown(path: str):
    """Changes the owner of a file"""
    uid = int(CURRENT_UID.split(":")[0])
    gid = int(CURRENT_UID.split(":")[1])
    os.chown(
        path,
        uid,
        gid,
    )


def touch(path: str):
    """Creates an empty file"""
    with open(path, "a", encoding="utf-8"):
        os.utime(path, None)
