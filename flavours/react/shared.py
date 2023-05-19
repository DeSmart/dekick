from flavours.shared import ui_ask_for_log
from flavours.shared import wait_for_container as shared_wait_for_container
from lib.dekickrc import get_dekickrc_value
from lib.dotenv import get_dotenv_var
from lib.run_func import run_func


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
    failed_string = "[vite]" if is_vite_enabled else "Failed to compile."
    timeout = 10 if is_vite_enabled else 90

    if shared_wait_for_container(
        search_string, failed_string, timeout, terminate=False
    ):
        app_is_ready()
        return

    ui_ask_for_log()
    return


def get_container() -> str:
    return "web"
