from logging import debug, info, warning

from bash import bash


def rbash(info_desc: str, cmd: str, expected_code: int = 0, **kwargs) -> dict:
    """Runs command in bash and returns its output"""
    info(info_desc)
    debug(cmd)
    if kwargs:
        debug(kwargs)
    ret = bash(cmd, **kwargs)

    stdout = ret.stdout.decode("utf-8").replace("\r", "")
    stderr = ret.stderr.decode("utf-8").replace("\r", "")
    code = ret.code

    if ret.code != expected_code:
        warning("stdout:\n%s", stdout)
        warning("stderr:\n%s", stderr)
        warning("code: %s", ret.code)
    else:
        debug("stdout:\n%s", stdout)
        debug("stderr:\n%s", stderr)
        debug("code: %s", ret.code)

    return {"stdout": stdout, "stderr": stderr, "code": code}
