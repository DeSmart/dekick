import pytest

from lib.misc import get_platform
from lib.tests.dekick_commands import (
    dekick_build,
    dekick_dotenv_replace,
    dekick_local,
    dekick_status,
    dekick_stop,
    dekick_test,
)
from lib.tests.docker import any_container_running, no_container_running
from lib.tests.misc import parse_flavour_version

FLAVOUR, VERSION = parse_flavour_version(__file__)


@pytest.mark.command_local
@pytest.mark.basic
def test_local():
    """Tests `dekick local` command"""
    assert dekick_local(FLAVOUR, VERSION)
    assert any_container_running()


@pytest.mark.command_status
@pytest.mark.basic
def test_local_status_success():
    """Tests `dekick status` command"""
    assert dekick_local(FLAVOUR, VERSION)
    assert dekick_status(FLAVOUR, VERSION)
    assert any_container_running()


@pytest.mark.command_status
@pytest.mark.extended
def test_local_status_failed():
    """Tests `dekick status` command"""
    assert not dekick_status(FLAVOUR, VERSION)


@pytest.mark.command_local_stop
@pytest.mark.basic
def test_local_stop():
    """Tests `dekick status` command"""
    assert dekick_local(FLAVOUR, VERSION)
    assert dekick_stop(FLAVOUR, VERSION)
    assert no_container_running()


@pytest.mark.command_local_stop
@pytest.mark.extended
def test_local_stop_remove():
    """Tests `dekick status` command"""
    assert dekick_local(FLAVOUR, VERSION)
    assert dekick_stop(FLAVOUR, VERSION, ["--remove"])
    assert no_container_running()


@pytest.mark.command_test
@pytest.mark.basic
def test_local_test():
    """Tests `dekick test` command"""
    assert dekick_test(FLAVOUR, VERSION)


@pytest.mark.command_build
@pytest.mark.basic
def test_build():
    """Tests `dekick build` command"""
    assert dekick_build(FLAVOUR, VERSION)


@pytest.mark.command_build
@pytest.mark.extended
def test_build_app_env_production():
    """
    Tests `dekick build` command with additional APP_ENV environment
    variable set to `production`
    """
    assert dekick_dotenv_replace(FLAVOUR, VERSION, {"APP_ENV": "production"})
    assert dekick_build(FLAVOUR, VERSION)
