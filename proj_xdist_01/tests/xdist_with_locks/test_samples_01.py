import pytest
import time


@pytest.mark.parametrize("duration", [1, 3])
def test_sleep_01(duration: int, session_data: str):
    time.sleep(duration)
    assert duration > 0

@pytest.mark.parametrize("duration", [2, 4])
def test_sleep_02(duration: int, session_data: str):
    time.sleep(duration)
    assert duration > 0


@pytest.mark.xfail(reason="This test is expected to fail")
def test_fail(session_data: str):
    print(f"\ntest_fail -> session_data: {session_data}")
    assert False
