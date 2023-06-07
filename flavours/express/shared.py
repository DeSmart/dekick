from flavours.shared import ui_ask_for_log
from flavours.shared import wait_for_container as shared_wait_for_container
from lib.dotenv import get_dotenv_var
from lib.run_func import run_func


def get_container() -> str:
    return "web"


def wait_for_container(search_string: str, timeout: int = 30):
    if shared_wait_for_container(search_string, timeout=timeout, terminate=False):
        app_is_ready()
        return

    ui_ask_for_log()
    return


def app_is_ready():
    def run():
        try:
            api_url = get_dotenv_var("API_URL") or get_dotenv_var("APP_URL")
            return {
                "success": True,
                "text": f"App should be available at {api_url}",
            }
        except KeyError as error:
            return {
                "success": False,
                "type": "warn",
                "text": f"Warning! App may not work properly. Reason: {error.args[0]}",
            }

    run_func(text="Checking if app is ready", func=run)
