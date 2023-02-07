from os import path

import pytest

from lib.boilerplates import delete_boilerplates, get_boilerplates, reset_boilerplates
from lib.tests.docker import docker_kill_all_containers, docker_no_running_container


@pytest.fixture(scope="session", autouse=True)
def setup_boilerplates(request):
    """Setup boilerplates before running tests"""
    assert delete_boilerplates()
    assert get_boilerplates()
    assert docker_kill_all_containers()
    assert docker_no_running_container()
    request.addfinalizer(teardown_boilerplates)


def teardown_boilerplates():
    """Teardown boilerplates after running tests"""
    assert delete_boilerplates()


@pytest.fixture(scope="function", autouse=True)
def setup(request):
    """Cleans up boilerplates and stops containers before running test"""
    assert reset_boilerplates()
    request.addfinalizer(teardown)


def teardown():
    """Cleans up boilerplates and stops containers after running test"""
    assert docker_kill_all_containers()
    assert docker_no_running_container()
