import pytest
import time


@pytest.mark.parametrize("duration", [1, 3])
def test_sleep_01(duration: int):
    time.sleep(duration)
    assert duration > 0


@pytest.mark.parametrize("duration", [2, 4])
def test_sleep_02(duration: int):
    time.sleep(duration)
    assert duration > 0
