from lib.dekickrc import get_dekickrc_value
from lib.run_func import run_func


def get_container() -> str:
    return "web"


def app_is_ready():
    def run():
        container_name = get_container()
        ports = list(get_dekickrc_value("dekick.ports", check_with_template=False))
        app_url = None

        for port_def in ports:
            if port_def["service"] == container_name:
                port = port_def["port"]
                app_url = f"http://localhost:{port}"
                break

        if app_url is None:
            return {
                "success": False,
                "type": "warn",
                "text": "Warning! App may not work properly, "
                + f"no port mapping for service {container_name} detected",
            }
        return {
            "success": True,
            "text": f"App should be available at {app_url}",
        }

    run_func(text="Checking if app is ready", func=run)
