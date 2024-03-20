from beaupy import prompt
from rich.console import Console
from rich.prompt import Confirm

from lib.dotenv import env2dict
from lib.drivers.credentials.hashicorp_vault._main import (
    DEKICK_ENVS_DIR,
    _is_maintainer,
    create_envs_dir,
    get_envs,
    info,
    ui_push,
)
from lib.environments import get_environments
from lib.glcli import get_project_var
from lib.global_config import get_global_config_value
from lib.run_func import run_func
from lib.settings import C_BOLD, C_CMD, C_CODE, C_END, C_FILE, DEKICKRC_GLOBAL_HOST_PATH

console = Console()
ask = Confirm.ask


def ui_action(root_token: str = "") -> bool:
    """Migrate environment variables from GitLab to Hashicorp Vault"""
    if not _is_maintainer():
        raise ValueError(
            f"You don't have proper rights to migrate from GitLab to {info()}. You need to have {C_CMD}admin{C_END} or {C_CMD}maintainer{C_END} rights."
        )

    if not ask(
        f"Are you sure you want to migrate from GitLab to {info()}?", default=False
    ):
        return False

    token = str(get_global_config_value("gitlab.token"))

    if not token:
        if ask(
            f"GitLab token not found in {C_FILE}{DEKICKRC_GLOBAL_HOST_PATH}{C_END}. Would you like to enter it now?",
            default=False,
        ):
            token = prompt(
                "Enter your GitLab token: ", secure=True, validator=lambda x: len(x) > 0
            )
        else:
            return False

    environments = get_environments()
    create_envs_dir()

    for env in environments:
        print(f"Getting environment {C_CODE}{env}{C_END} from GitLab")
        env_data = get_project_var(scope=env, token=token)
        env_file = f"{DEKICK_ENVS_DIR}/{env}.env"
        with open(env_file, "w", encoding="utf-8") as file:
            file.write(env_data)
            print(
                f"  Storing environment {C_CODE}{env}{C_END} variables into {C_FILE}{env_file}{C_END}"
            )

    if ask(f"Would you like to push these environments to {info()}?", default=False):
        ui_push(no_confirm=True)

    print(f"\n{C_BOLD}Checking consistency of the environments{C_END}")

    def check_env_key_value(
        env: str, source_env: dict, dest_env: dict, source_name: str, dest_name: str
    ):
        for env_key, env_value in source_env.items():
            if env_key not in dest_env:
                return {
                    "success": False,
                    "text": f"Variable {C_CODE}{env_key}{C_END} not found in {dest_name} for environment {C_CODE}{env}{C_END}",
                }
            if env_value != dest_env[env_key]:
                return {
                    "success": False,
                    "text": f"Variable {C_CODE}{env_key}{C_END} in {dest_name} for environment {C_CODE}{env}{C_END} does not match {source_name} value ({C_CODE}{env_value}{C_END} {C_BOLD}vs{C_END} {C_CODE}{dest_env[env_key]}{C_END})",
                }

    for env in environments:
        env_gitlab = env2dict(get_project_var(scope=env, token=token))
        env_hvac = env2dict(get_envs(env=env, token=root_token))

        run_func(
            f"Checking consitency {info()} -> GitLab for environment {C_CODE}{env}{C_END}",
            func=lambda: check_env_key_value(
                env, env_gitlab, env_hvac, info(), "GitLab"
            ),
        )
        run_func(
            f"Checking consistency GitLab -> {info()} for environment {C_CODE}{env}{C_END}",
            func=lambda: check_env_key_value(
                env, env_hvac, env_gitlab, "GitLab", info()
            ),
        )

    print(f"\nAll environments have been successfully migrated to {info()}")

    return True
