from commands.local import get_env_from_gitlab


def init():
    pass


def get_vars(env: str):
    get_env_from_gitlab(scope=env)


def update_vars(env: str, vars: dict) -> None:
    """Updates all project variables in Gitlab"""
    return
