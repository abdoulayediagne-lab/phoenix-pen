"""
Sovereign Updater Module for Phoenix Pen.
Checks GitHub commits on origin/main, applies 1-click git pull, and restarts seamlessly.
Atlas Standard: < 250 lines.
"""

import os
import subprocess
import sys
from typing import Any, Dict, Tuple
from version import __version__, GITHUB_REPO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_local_commit() -> str:
    """Returns the current short git hash of HEAD."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=4
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_remote_commit(timeout: int = 5) -> str | None:
    """Queries origin/main HEAD hash via git ls-remote without altering local git state."""
    try:
        res = subprocess.run(
            ["git", "ls-remote", "origin", "refs/heads/main"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=timeout
        )
        if res.returncode == 0 and res.stdout.strip():
            full_hash = res.stdout.split()[0].strip()
            return full_hash[:7]
    except Exception:
        pass
    return None


def check_for_updates(timeout: int = 5) -> Dict[str, Any]:
    """Checks whether a newer commit is published on origin/main."""
    local = get_local_commit()
    remote = get_remote_commit(timeout=timeout)
    if not remote:
        return {
            "has_update": False,
            "checked": False,
            "local": local,
            "remote": None,
            "version": __version__,
            "message": "Connexion GitHub indisponible"
        }
    has_update = (local != "unknown") and (local != remote)
    return {
        "has_update": has_update,
        "checked": True,
        "local": local,
        "remote": remote,
        "version": __version__,
        "message": f"Nouvelle version disponible ({remote})" if has_update else "À jour"
    }


def apply_update() -> Tuple[bool, str]:
    """Applies update using clean git reset and git pull origin main."""
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=BASE_DIR, capture_output=True, timeout=5)
        pull_res = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=30
        )
        if pull_res.returncode != 0:
            err = pull_res.stderr.strip() or pull_res.stdout.strip()
            return False, f"Erreur git pull: {err}"

        # Recompile AppIcon if needed
        inst_script = os.path.join(BASE_DIR, "installer_app_macos.sh")
        if os.path.exists(inst_script):
            subprocess.run(["/bin/bash", inst_script], cwd=BASE_DIR, capture_output=True, timeout=15)

        new_local = get_local_commit()
        return True, f"Mise à jour réussie ({new_local})"
    except Exception as e:
        return False, f"Exception mise à jour: {e}"


def restart_app() -> None:
    """Seamlessly restarts Phoenix Pen main process on macOS."""
    try:
        main_py = os.path.join(BASE_DIR, "python", "main.py")
        venv_py = os.path.join(BASE_DIR, ".venv", "bin", "python3")
        py_exec = venv_py if os.path.exists(venv_py) else sys.executable

        # Stop old instances cleanly
        subprocess.run(["pkill", "-f", "phoenix-pen.*main\\.py"], capture_output=True)

        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(BASE_DIR, "python")
        subprocess.Popen(["/usr/bin/arch", "-arm64", py_exec, main_py], cwd=BASE_DIR, env=env, close_fds=True)
        os._exit(0)
    except Exception as e:
        print(f"[Updater] Erreur redémarrage: {e}")
