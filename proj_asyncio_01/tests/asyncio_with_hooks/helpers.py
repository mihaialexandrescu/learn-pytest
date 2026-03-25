import httpx
import time


def print_heading(text: str) -> None:
    """Print a heading with a separator line above it."""
    print(f"\n----- {text} -----")


def wait_http_ready(
    url: str,
    *,
    timeout_s: float = 30.0,
    poll_s: float = 0.5,
    accept_status: tuple[int, ...] = (200,),
) -> None:
    """Poll GET url from the host until status is acceptable or timeout."""
    ok = set(accept_status)
    deadline = time.time() + timeout_s
    last_err: str | None = None

    while time.time() < deadline:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code in ok:
                return
            last_err = f"HTTP {resp.status_code}"
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_err = str(e)
        time.sleep(poll_s)
    raise RuntimeError(
        f"Ready check {url} did not return {accept_status} within {timeout_s}s "
        f"(last: {last_err})"
    )
