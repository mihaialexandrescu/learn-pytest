import json
import multiprocessing
import pytest
import shutil
import time

from datetime import datetime
from filelock import FileLock
from pathlib import Path

from .helpers import print_heading


# --- pytest small fake/dummy fixtures ---

@pytest.fixture(scope="package", autouse=True)
def fake_fixture_02(test_dir: Path) -> None:
    print_heading(f"fake_fixture_02 (setup): {test_dir}")
    yield
    print_heading(f"fake_fixture_02 (teardown): {test_dir}")

@pytest.fixture(scope="package")
def test_dir() -> Path:
    return Path(*Path(__file__).resolve().parent.parts[-2:])


# --- once per global session initialization ---

@pytest.fixture(scope="session")
def session_data(tmp_path_factory, worker_id) -> str:
    # When xdist is NOT used: If you run pytest without the -n flag (or with -n0), the worker_id fixture returns the string "master".
    # When xdist IS used: If you run pytest -n 4, pytest-xdist spawns multiple worker processes (e.g., gw0, gw1, gw2, gw3).
    # From docs at https://pytest-xdist.readthedocs.io/en/latest/how-to.html#identifying-the-worker-process-during-a-test :
    # When xdist is disabled (running with -n0 for example), then worker_id will return "master".
    if worker_id == "master":
        print("\n--- session_data: Running on master node ---")
        return produce_expensive_data()
    
    # get the temp directory shared by all workers
    root_tmp_dir = tmp_path_factory.getbasetemp().parent

    print(f"Contents of {root_tmp_dir} pre-FileLock: {[item.name for item in root_tmp_dir.iterdir()]}")

    # When xdist IS used: If you run pytest -n 4, pytest-xdist spawns multiple worker processes (e.g., gw0, gw1, gw2, gw3).
    # Each worker is an independent Python process with its own memory.
    # Because they don't share memory, a session scoped fixture would normally run once per worker.
    # The following code uses a FileLock to ensure that even with multiple workers,
    # only the first one to reach the fixture actually executes the expensive logic,
    # while the others wait and then read the result from a shared file.
    fn = root_tmp_dir / "data.json"
    with FileLock(str(fn) + ".lock"):
        if fn.is_file():
            data = json.loads(fn.read_text())
        else:
            data = produce_expensive_data()
            fn.write_text(data) # not doing json.dumps(data) because that would lead to double serialization
    
    print(f"Contents of {root_tmp_dir} post-FileLock: {[item.name for item in root_tmp_dir.iterdir()]}")
    
    return data


def produce_expensive_data() -> str:
    time.sleep(5)
    return json.dumps({"timestamp": datetime.now().isoformat(), "temperature": 22, "humidity": 40})




# --- global session initialization with hooks ---

LOCAL_TMP_DIR_PATH = Path(__file__).resolve().parent / "tmp"
LOCAL_TMP_LOCKS_DIR_PATH = LOCAL_TMP_DIR_PATH / "locks"
LOCAL_TMP_DATA_DIR_PATH = LOCAL_TMP_DIR_PATH / "data"
LOCAL_TMP_DOCKER_LOCK_PATH = LOCAL_TMP_LOCKS_DIR_PATH / "docker.lock"

# It is not a good idea, in general, to use the Stash to share locks. Here it is done only for demonstration purposes.
_MP_LOCK_STASHKEY_01 = pytest.StashKey[multiprocessing.Lock]()


@pytest.hookimpl()
def pytest_sessionstart(session: pytest.Session) -> None:
    """ Prepare global session for tests prior to individual pytext-xdist workers creation """

    # Check if we are a worker process. Otherwise, we are the master process.
    if getattr(session.config, 'workerinput', None) is not None:
        # Choosing to NOT do anything in the worker process when using pytest-xdist workers.
        return

    LOCAL_TMP_LOCKS_DIR_PATH.mkdir(parents=True, exist_ok=False)

    LOCAL_TMP_DOCKER_LOCK_PATH.touch(exist_ok=False)

    # The Stash on the master node stays on the master node and is not synchronized with the pytest-xdist workers (if they exist).
    # It is not a good idea in general to use the Stash to share locks. Here it is done only for demonstration purposes.
    session.config.stash[_MP_LOCK_STASHKEY_01] = multiprocessing.Lock()



@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    """ Clean up global session after all tests have run """

    # Check if we are a worker process. Otherwise, we are the master process.
    if getattr(session.config, 'workerinput', None) is not None:
        # Choosing to NOT do anything in the worker process when using pytest-xdist workers.
        return

    # Remove the local temporary docker lock file.
    LOCAL_TMP_DOCKER_LOCK_PATH.unlink(missing_ok=True)

    # Remove the local temporary directory and its contents.
    # Using shutil.rmtree() instead of pathlib.Path.rmdir() because the latter requires the directory to be empty.
    shutil.rmtree(LOCAL_TMP_DIR_PATH)

    # Test the Lock object from the StashKey.
    print("\n--- sessionfinish -> Test the Lock object from the StashKey ---")
    lock = session.config.stash[_MP_LOCK_STASHKEY_01]
    print(f"MP_LOCK_STASHKEY_01 as received from stash: {lock}")
    with lock:
        print(f"MP_LOCK_STASHKEY_01 acquired: {lock}")
    print(f"MP_LOCK_STASHKEY_01 released: {lock}")



# This fixture DOES NOT WORK! The lock retrieved from the stash is None if we use the "-n" flag (other than "-n 0") .
# Explanation:
# When pytest-xdist workers are spawned, they start their own Python interpreter.
# While they receive a copy of the configuration, the stash is NOT automatically synchronized from the Master to the Workers after the workers have started.
# Even if you removed the if workerinput guard, a standard multiprocessing.Lock() created in the Master cannot be easily "sent" to workers via the stash.
# pytest-xdist communicates between Master and Workers using execnet, which serializes data.
# multiprocessing objects like Locks are generally not serializable in a way that allows them to function across unrelated process trees or via execnet pipes without a shared BaseManager.
#
# If your goal is to ensure only one worker accesses a resource at a time, a multiprocessing.Lock won't work easily with xdist. 
# The industry standard solution for this is the filelock library.
#
# @pytest.fixture(scope="session", autouse=True)
# def use_stashed_lock(request: pytest.FixtureRequest) -> None:
#     """ Use from a fixture the Lock set by the pytest_sessionstart hook for the StashKey """
#     # If you stash data on request.node (the test item), it is only available for that specific test.
#     # If you stash data on request.config, it persists for the entire test session.
#     lock = request.config.stash.get(_MP_LOCK_STASHKEY_01, None)
#     print("\n--- use_stashed_lock fixture setup ---")
#     print(f"MP_LOCK_STASHKEY_01 as received from stash: {lock}")
#     with lock:
#         print(f"MP_LOCK_STASHKEY_01 acquired: {lock}")
#     print(f"MP_LOCK_STASHKEY_01 released: {lock}")


# This fixture doesn't show anything when using pytest-xdist with the "-n" flag (except when "-n 0").
@pytest.fixture(scope="session", autouse=True)
def inspect_request(request: pytest.FixtureRequest) -> None:
    """ Inspect the request object """
    yield
    print("\n--- inspect_request fixture teardown ---")
    print(f"request.node: {request.node}")
    print(f"request.node.nodeid: {request.node.nodeid}")
    print(f"request.fixturename: {request.fixturename}")
    print(f"request.fixturenames: {request.fixturenames}")
    print(f"request.scope: {request.scope}")
    print(f"request.config: {request.config}")
    print(f"request.config.stash._storage: {request.config.stash._storage}")



# Fixtures don't even exist on the master node when using pytest-xdist with the "-n" flag (other than "-n 0").
# The following fixture creates EITHER a master.txt file OR a bunch of gw0.txt, gw1.txt, gw2.txt, etc files.
@pytest.fixture(scope="session", autouse=True)
def study_fixture_teardown_propagation(worker_id: str) -> None:
    """ Study the fixture teardown propagation """
    fn = Path(__file__).resolve().parent / "tmp2" / f"{worker_id}.txt"
    # Create parent directoy and file if they don't exist.
    fn.parent.mkdir(parents=True, exist_ok=True)
    fn.touch(exist_ok=True)
    # From docs for pathlib.Path.write_text():
    # Open the file pointed to in text mode, write data to it, and close the file.
    # An existing file of the same name is overwritten. The optional parameters have the same meaning as in open().
    fn.write_text(f"setup phase: {time_helper_ms_01()}\n")
    yield
    with open(fn, "a") as f:
        f.write(f"teardown phase: {time_helper_ms_01()}\n")
    
def time_helper_ms_01() -> str:
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"
