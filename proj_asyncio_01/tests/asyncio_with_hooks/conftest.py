import asyncio
import pytest

from pathlib import Path

from .helpers import print_heading


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
    return


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
    return
