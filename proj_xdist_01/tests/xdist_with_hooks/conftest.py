import pytest
import subprocess

from pathlib import Path

from .helpers import print_heading, start_long_running_subprocess, stop_subprocess


# --- pytest small fake/dummy fixtures ---

@pytest.fixture(scope="session", autouse=True)
def fake_fixture_01() -> None:
    print_heading(f"fake_fixture_01 (setup)")
    yield
    print_heading(f"fake_fixture_01 (teardown)")


@pytest.fixture(scope="package", autouse=True)
def fake_fixture_02(test_dir: Path) -> None:
    print_heading(f"fake_fixture_02 (setup): {test_dir}")
    yield
    print_heading(f"fake_fixture_02 (teardown): {test_dir}")

@pytest.fixture(scope="package")
def test_dir() -> Path:
    return Path(*Path(__file__).resolve().parent.parts[-2:])


# --- pytest initialization hooks ---

# From https://docs.pytest.org/en/stable/reference/reference.html#pytest.Stash
# Stash is a type-safe heterogeneous mutable mapping that allows keys and value types to be defined separately from where it (the Stash) is created.
# Usually you will be given an object which has a Stash, for example Config or a Node.
# If a module or plugin wants to store data in this Stash, it creates StashKeys for its keys (at the module level).
# Value type must match the key type.
_COMM_STR_KEY_01 = pytest.StashKey[str]()
_COMM_INT_KEY_01 = pytest.StashKey[int]()
# Because pytest-xdist sends data to workers over a communication pipe (execnet),
# any data you pass through "workerinput" must be serializable (like strings, integers, lists, or dictionaries).
# Environment Variables: If you are passing strings (like a database URL or a file path), this works perfectly.
# Complex Objects: You cannot pass a multiprocessing.Lock or a database connection object directly through workerinput, as these cannot be serialized.
#
# I intend to use this subprocess.Popen object only on the master's Stash and for it to be picked up by the master's pytest_sessionfinish hook.
# Such an object could not be serialized and sent to the workers.
_COMM_PROC_KEY_01 = pytest.StashKey[subprocess.Popen]()

@pytest.hookimpl()
def pytest_sessionstart(session: pytest.Session) -> None:
    """ Prepare global session for tests prior to individual pytext-xdist workers creation """

    # Check if we are a worker process. Otherwise, we are the master process.
    if getattr(session.config, 'workerinput', None) is not None:
        print("\n--- SessionStart:Worker process detected. ---")
        print(f"workerinput: {getattr(session.config, 'workerinput', None)}")
        # Choosing to not do anything in the worker process to prepare for a global setup when using pytest-xdist.
        return

    print("\n--- SessionStart: Master process detected. ---\n")
    
    # Stash some data for the master process to find later in the sessionfinish hook.
    session.config.stash[_COMM_STR_KEY_01] = "Hello, pytest-xdist!"
    session.config.stash[_COMM_INT_KEY_01] = 42
    session.config.stash[_COMM_PROC_KEY_01] = start_long_running_subprocess(["sleep", "30s"])


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode) -> None:
    """ Clean up global session after all tests have run """

    # Check if we are a worker process. Otherwise, we are the master process.
    if getattr(session.config, 'workerinput', None) is not None:
        print("\n--- SessionFinish: Worker process detected. ---")
        print(f"workerinput: {getattr(session.config, 'workerinput', None)}")
        # Choosing to not do anything in the worker process to prepare for a global setup when using pytest-xdist.
        return

    print("\n--- SessionFinish: Master process detected. ---")

    # Use the data from the stash.
    print(f"_COMM_STR_KEY_01: {session.config.stash[_COMM_STR_KEY_01]}")
    print(f"_COMM_INT_KEY_01: {session.config.stash[_COMM_INT_KEY_01]}")
    stop_subprocess(session.config.stash[_COMM_PROC_KEY_01], "sessionstart_proc")
