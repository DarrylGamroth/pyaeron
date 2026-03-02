from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


def wait_for(
    predicate: Callable[[], bool],
    *,
    timeout: float,
    interval: float = 0.001,
    description: str = "condition",
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise TimeoutError(f"Timed out waiting for {description} after {timeout:.3f}s")


def find_aeronmd_binary() -> str | None:
    env_path = os.environ.get("AERON_MD_BINARY")
    if env_path and Path(env_path).is_file():
        return env_path

    common = Path("/opt/aeron/bin/aeronmd")
    if common.is_file():
        return str(common)

    from_path = shutil.which("aeronmd")
    return from_path


def free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@dataclass(slots=True)
class MediaDriverHarness:
    aeron_dir: str
    process: subprocess.Popen[str]
    log_file: str

    @classmethod
    def launch(cls, binary: str) -> MediaDriverHarness:
        temp_dir = tempfile.mkdtemp(prefix="pyaeron-md-")
        log_file = os.path.join(temp_dir, "aeronmd.log")
        env = os.environ.copy()
        env["AERON_DIR"] = temp_dir

        with open(log_file, "w") as log_handle:
            process = subprocess.Popen(
                [binary],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                start_new_session=True,
            )

        cnc_file = os.path.join(temp_dir, "cnc.dat")
        try:
            wait_for(
                lambda: os.path.exists(cnc_file),
                timeout=10.0,
                interval=0.01,
                description=f"media driver cnc file at {cnc_file}",
            )
        except Exception:
            process.terminate()
            process.wait(timeout=5)
            raise

        return cls(aeron_dir=temp_dir, process=process, log_file=log_file)

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
