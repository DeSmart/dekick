import pytest

from lib.tests.dekick_commands import (
    dekick_build,
    dekick_local,
    dekick_status,
    dekick_stop,
)
from lib.tests.misc import parse_flavour_version

FLAVOUR, VERSION = parse_flavour_version(__file__)


@pytest.mark.command_local
def test_local():
    """Tests `dekick local` command"""
    assert dekick_local(FLAVOUR, VERSION)


@pytest.mark.command_status
def test_local_status_success():
    """Tests `dekick status` command"""
    assert dekick_local(FLAVOUR, VERSION)
    assert dekick_status(FLAVOUR, VERSION)


@pytest.mark.command_status
def test_local_status_failed():
    """Tests `dekick status` command"""
    assert not dekick_status(FLAVOUR, VERSION)


@pytest.mark.command_local_stop
def test_local_stop():
    """Tests `dekick status` command"""
    assert dekick_stop(FLAVOUR, VERSION)


@pytest.mark.command_build
def test_build():
    """Tests `dekick build` command"""
    assert dekick_build(FLAVOUR, VERSION)
