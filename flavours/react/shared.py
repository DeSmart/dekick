from flavours.shared import setup_permissions as shared_setup_permissions
from flavours.shared import wait_for_container as shared_wait_for_container
from lib.dekickrc import get_dekickrc_value
from lib.dotenv import get_dotenv_var
from lib.misc import run_func


def app_is_ready():
    def run():
        try:
            react_app_home_url = get_dotenv_var("REACT_APP_HOME_URL")
            return {
                "success": True,
                "text": f"App should be available at {react_app_home_url}",
            }
        except KeyError as error:
            return {
                "success": False,
                "type": "warn",
                "text": f"Warning! App may not work properly. Reason: {error.args[0]}",
            }

    run_func(text="Checking if app is ready", func=run)


def wait_for_container():
    is_vite_enabled = get_dekickrc_value("dekick.settings.vite.enabled")

    search_string = "ready in" if is_vite_enabled else "Compiled successfully!"
    timeout = 10 if is_vite_enabled else 90

    shared_wait_for_container(search_string, timeout)


def setup_permissions():
    shared_setup_permissions("/.cache/ /.yarn/ build/")


def get_container() -> str:
    return "web"
