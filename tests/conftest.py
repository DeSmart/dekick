from logging import basicConfig, debug
from os import environ, makedirs, path, remove, rename
from os.path import dirname, exists
from time import sleep

import pytest
from filelock import SoftFileLock, Timeout

from lib.registry import start_docker_registry
from lib.tests.boilerplates import copy_flavour_to_container, download_boilerplates
from lib.tests.dind import start_dind_container, stop_dind_container
from lib.tests.misc import parse_flavour_version


def pytest_configure(config):
    """Setup different logs for each worker"""
    worker_id = environ.get("PYTEST_XDIST_WORKER")

    if worker_id is not None:

        log_filename = f"logs/pytest_{worker_id}.log"

        if exists(log_filename):
            previous_log_filename = log_filename + ".bak"
            if exists(previous_log_filename):
                remove(previous_log_filename)
            rename(log_filename, previous_log_filename)

        basicConfig(
            format=config.getini("log_file_format"),
            filename=log_filename,
            level=config.getini("log_file_level"),
        )


def init_session():
    """Do some things before workers start"""
    lock_path = "tmp/pytest.lock"
    makedirs(dirname(lock_path), exist_ok=True)

    worker_id = environ.get("PYTEST_XDIST_WORKER")
    debug("worker_id: %s", worker_id)

    timeout = int(
        0 if worker_id is None or worker_id == "master" else worker_id.replace("gw", "")
    )
    sleep(timeout)

    lock = SoftFileLock(lock_path, timeout=240)

    try:
        lock.acquire(poll_interval=1, timeout=5)
    except Timeout:
        lock.acquire(poll_interval=1)
        debug("Lock acquired, let's move!")
        return
    else:

        if exists(lock_path):
            remove(lock_path)

        with SoftFileLock(lock_path):
            start_docker_registry()
            download_boilerplates()
            return


@pytest.fixture(scope="session", autouse=True)
def start_session():
    """Setup boilerplates before running tests"""
    debug("start session")
    init_session()


@pytest.fixture(scope="function", autouse=True)
def start_function(request):
    """Cleans up boilerplates and stops containers before running test"""
    container_id = start_dind_container()
    copy_flavour_to_container(
        *parse_flavour_version(path.basename(request.node.fspath)),
        container_id=container_id,
    )
    request.addfinalizer(teardown_function)


def teardown_function():
    """Cleans up boilerplates and stops containers after running test"""
    stop_dind_container()
