import httpx
import os
import subprocess
import time


def print_heading(text: str) -> None:
    """Print a heading with a separator line above it."""
    print(f"\n--- {text} ---")


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

def start_long_running_subprocess(cmd: list[str] | str) -> subprocess.Popen:
    if not cmd:
        raise ValueError("cmd was empty")

    current_env = os.environ.copy()
    current_env["EXTRA_VAR_CMD_0"] = cmd[0]
    current_env["EXTRA_VAR_GREETING"] = "Hello, world!"

    # Without shell=True, environment variables would not be expanded on the command line. The default is shell=False.
    # Additionally, according to the Python docs for the subprocess.Popen constructor:
    # If shell is True, it is recommended to pass args as a string rather than as a sequence.
    process = subprocess.Popen(cmd, env=current_env, start_new_session=True, shell=False, cwd=None)
    return process

def stop_subprocess(process: subprocess.Popen, name: str) -> None:
    if process.poll() is not None:
        print(f"Process {name} (pid={process.pid}, args={process.args}) is already terminated")
        return
    
    print(f"Process {name} (pid={process.pid}, args={process.args}) is still running, terminating it")
    try:
        process.terminate()
        process.wait(timeout=5)
        print(f"Process {name} (pid={process.pid}, args={process.args}) terminated successfully")
    except subprocess.TimeoutExpired:
        # Force kill if graceful shutdown fails.
        process.kill()
        print(f"Process {name} (pid={process.pid}, args={process.args}) force killed")