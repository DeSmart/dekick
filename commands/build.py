"""
Runs the specified command
"""
from argparse import ArgumentParser, Namespace
from sys import exit

from rich.traceback import install

from commands.local import flavour_action, install_logger
from commands.stop import stop
from flavours.shared import build_image, push_image
from lib.misc import check_argparse_arg, randomize_compose_project_name, randomize_ports
from lib.parser_defaults import parser_default_args, parser_default_funcs

install()


def arguments(parser: ArgumentParser):
    """Sets arguments for this command

    Args:
        parser (ArgumentParser): parser object that will be used to parse arguments
    """
    parser.set_defaults(func=main)
    parser_default_args(parser)
    parser.add_argument(
        "--target-image", required=True, help="target docker image name and tag"
    )

    docker_parser = parser.add_argument_group(
        title="Options needed to push docker image to external registry"
    )
    docker_parser.add_argument(
        "--push", action="store_true", help="should image be pushed to docker registry"
    )
    docker_parser.add_argument(
        "--docker-registry", required=False, help="docker registry URL"
    )
    docker_parser.add_argument(
        "--docker-login-user", required=False, help="user to login to docker registry"
    )
    docker_parser.add_argument(
        "--docker-login-password",
        required=False,
        help="password to login to docker registry",
    )


def main(parser: Namespace, args: list):  # pylint: disable=unused-argument
    """Main entry point for this command

    Args:
        parser (Namespace): parser object that was created by the argparse library
        args (list):
    """
    parser_default_funcs(parser)

    if build(
        target_image=parser.target_image,
        docker_login_user=parser.docker_login_user,
        docker_login_password=parser.docker_login_password,
        docker_registry=parser.docker_registry,
        push=parser.push,
        log_level=parser.log_level or "INFO",
        log_filename=parser.log_filename or "dekick-build.log",
    ):
        exit(0)

    exit(1)


# pylint: disable=too-many-arguments
def build(
    target_image: str,
    docker_login_user: str,
    docker_login_password: str,
    docker_registry: str,
    push: bool,
    log_level: str,
    log_filename: str,
) -> bool:
    """
    Build an image
    """
    install_logger(log_level, log_filename)

    if push is True:
        check_argparse_arg(docker_login_user, "--docker-login-user")
        check_argparse_arg(docker_login_password, "--docker-login-password")
        check_argparse_arg(docker_login_user, "--docker-login-user")

    randomize_ports()
    randomize_compose_project_name()

    try:
        flavour_action("build")
        build_image(target_image)

        if push is True:
            push_image(
                target_image, docker_login_user, docker_login_password, docker_registry
            )

    except Exception:  # pylint: disable=broad-except
        stop(remove=False)
        return False

    stop(
        remove=True,
    )
    return True
