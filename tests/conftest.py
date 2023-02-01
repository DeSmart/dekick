from os import path

import pytest

from lib.boilerplates import delete_boilerplates, get_boilerplate
from lib.tests.docker import docker_kill_all_containers, docker_no_running_container
from lib.tests.misc import parse_flavour_version


@pytest.fixture(scope="function", autouse=True)
def setup(request):
    """Cleans up boilerplates and stops containers before running test"""
    assert docker_kill_all_containers()
    assert docker_no_running_container()
    assert delete_boilerplates()
    assert get_boilerplate(*parse_flavour_version(path.basename(request.node.fspath)))
    request.addfinalizer(teardown)


def teardown():
    """Cleans up boilerplates and stops containers after running test"""
    assert docker_kill_all_containers()
    assert docker_no_running_container()
    assert delete_boilerplates()
