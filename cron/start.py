import json
import os
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

cron = Path(__file__).parent
lock_file = cron / "pid.lock"

overwrite_existing = sys.argv[-1] == "force"


def update_lockfile(overwrite_existing: bool = False) -> bool:
    if not overwrite_existing:
        with suppress(Exception), lock_file.open("r") as f:
            data = json.load(f)
            if data["pid"] != os.getpid() and time.time() - data["timestamp"] < 15:
                return True

    with lock_file.open("w") as f:
        json.dump({"pid": os.getpid(), "timestamp": time.time()}, f)

    return False


if update_lockfile(overwrite_existing):
    print(
        "Bot is already running in another process. Exiting gracefully.\n"
        "Use `python cron/start.py force` to force a new instance of the bot to run (will terminate the existing instance).",
    )
    sys.exit(0)

process = subprocess.Popen(
    [
        sys.executable,
        "main.py",
    ],
    stdout=(cron / "stdout.log").open("ab"),
    stderr=(cron / "stderr.log").open("ab"),
)


try:
    while process.poll() is None:
        if update_lockfile():
            print("Another process has overwritten our lockfile!")
            print("Terminating myself and allowing the other process to proceed.")
            process.kill()
            sys.exit(0)

        time.sleep(5)
finally:
    lock_file.unlink()
