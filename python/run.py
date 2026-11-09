"""
Single-Instance Application Runner for Phoenix Pen.
Ensures single active process via PID lock and handles OS termination signals.
Atlas Standard: < 250 lines.
"""

import os
import signal
import sys

PID_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phoenix_pen.pid")


def is_already_running() -> bool:
    """Checks if another instance is currently running using PID file."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            # Check if process with old_pid is active
            os.kill(old_pid, 0)
            return True
        except (OSError, ValueError):
            # Process does not exist or stale PID file
            cleanup_pid()
    return False


def write_pid() -> None:
    """Writes current PID to lock file."""
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def cleanup_pid() -> None:
    """Removes PID lock file upon exit."""
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass


def main() -> None:
    if is_already_running():
        print("⚠️ Phoenix Pen is already running in background.")
        sys.exit(0)

    write_pid()

    # Register cleanup handlers
    def _sig_handler(signum, frame):
        cleanup_pid()
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    try:
        from main import main as app_main
        sys.exit(app_main())
    finally:
        cleanup_pid()


if __name__ == "__main__":
    main()
