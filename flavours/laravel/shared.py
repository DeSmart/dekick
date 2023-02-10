"""
Shared functions for Laravel flavour
"""
import json
import shutil
from os.path import exists

from commands.artisan import artisan
from commands.docker_compose import docker_compose
from lib.dekickrc import get_dekickrc_value
from lib.dotenv import get_dotenv_var
from lib.fs import chown
from lib.misc import run_func
from lib.settings import C_CMD, C_END, CURRENT_UID


def api_is_ready():
    """Display a message when the API is ready."""

    def run():
        try:
            healtcheck_key = get_dotenv_var("HEALTHCHECK_KEY")
            app_url = get_dotenv_var("APP_URL")
            return {
                "success": True,
                "text": f"API should be available at {app_url}/api/healthcheck?HEALTHCHECK_KEY={healtcheck_key}",
            }
        except KeyError as error:
            return {
                "success": False,
                "text": f"Warning! App may not work properly. Reason: {error.args[0]}",
                "type": "warn",
            }

    run_func(text="Checking if app is ready", func=run)


def setup_dirs():
    """Setup permissions for the Laravel project."""

    def run():
        dirs_chown = "bootstrap/cache/ storage/ storage/app/ storage/app/public/ storage/app/scribe/ storage/framework/ storage/framework/cache/ storage/framework/testing/ storage/framework/sessions/ storage/framework/views/ storage/app/apidoc storage/logs/ vendor/ /.cache/"
        dirs_chmod = "bootstrap/cache/ storage/ vendor/ /.cache/"
        cmd = "run"
        args = [
            "-T",
            "--rm",
            "--user=root",
            get_container(),
            "sh",
            "-c",
            f"mkdir -p {dirs_chown}; chown {CURRENT_UID} {dirs_chown}; chmod o+rwX {dirs_chmod} -R",
        ]

        docker_compose(cmd=cmd, args=args, env={})

        return {"success": True, "text": ""}

    run_func(
        text="Creating required directories",
        func=run,
    )


def db_migrate(service: str = "db"):
    """Migration the database."""

    def run():
        artisan(
            args=["migrate:fresh"],
            capture_output=True,
            docker_env={"DB_HOST": service},
        )

    run_func(
        text=f"Running {C_CMD}artisan migrate:fresh{C_END} using {C_CMD}{service}{C_END}",
        func=run,
    )


def generate_apidoc():
    """Generate API documentation using Scribe."""

    if not get_dekickrc_value("dekick.settings.apidoc.generate"):
        return

    def run():

        generator_type = (
            "apidoc"
            if get_dekickrc_value("dekick.settings.apidoc.legacy")
            else "scribe"
        )

        try:
            shutil.rmtree(f".{generator_type}")
        except FileNotFoundError:
            pass

        artisan(args=[f"{generator_type}:generate"], capture_output=True)

    run_func(text="Generating API documentation", func=run)


def laravel_nova_support():
    """Saves the Laravel Nova credentials in the auth.json file."""
    try:
        nova_username = get_dotenv_var("NOVA_USERNAME")
        nova_password = get_dotenv_var("NOVA_PASSWORD")
    except KeyError:
        return

    auth_tmpl_file = "auth.json.tmpl"
    auth_file = "auth.json"

    if not exists(auth_tmpl_file):
        return

    if exists("auth.json"):
        return

    def run():
        with open(auth_tmpl_file, "r", encoding="utf-8") as file:
            auth_json = json.load(file)
            auth_json["http-basic"]["nova.laravel.com"] = {
                "username": nova_username,
                "password": nova_password,
            }

        with open(auth_file, "w", encoding="utf-8") as file:
            file.write(json.dumps(auth_json, indent=4))
            chown(auth_file)

    run_func("Setting up Laravel Nova", func=run)


def get_container() -> str:
    """Return the main container name."""
    return "web"
