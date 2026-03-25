import asyncio
import pytest


# --- pytest-asyncio ---
# Test execution and concurrency
# pytest-asyncio runs async tests sequentially, just like how pytest runs synchronous tests. Each asynchronous test runs within its assigned event loop.
# This sequential execution is intentional and important for maintaining test isolation.
# Running tests concurrently could introduce race conditions and side effects where one test could interfere with another, making test results unreliable and difficult to debug.

# Auto mode
# In auto mode pytest-asyncio automatically adds the asyncio marker to all asynchronous test functions. 
# It will also take ownership of all async fixtures, regardless of whether they are decorated with @pytest.fixture or @pytest_asyncio.fixture.

# All tests in a module can be run inside the same event loop by marking them with pytest.mark.asyncio(loop_scope="module"). 
# This is easily achieved by adding a pytestmark statement to your module.
pytestmark = pytest.mark.asyncio(loop_scope="module")


@pytest.mark.parametrize("duration", [1, 3])
async def test_sleep_01(duration: int):
    await asyncio.sleep(duration)
    assert duration > 0


@pytest.mark.parametrize("duration", [2, 4])
async def test_sleep_02(duration: int):
    await asyncio.sleep(duration)
    assert duration > 0
