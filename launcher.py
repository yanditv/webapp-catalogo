from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from urllib.request import urlopen

import uvicorn


HOST = os.environ.get("CATALOGOS_HOST", "127.0.0.1")
PORT = int(os.environ.get("CATALOGOS_PORT", "8000"))
APP_URL = f"http://{HOST}:{PORT}"
RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
LOG_DIR = RUNTIME_DIR / "data"
LOG_FILE = LOG_DIR / "launcher.log"


def _log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(message.rstrip() + "\n")


def _wait_until_ready(timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(APP_URL, timeout=1.5) as response:
                if response.status < 500:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def _open_browser() -> None:
    if not _wait_until_ready():
        _log(f"[WARN] El servidor no respondio a tiempo en {APP_URL}")
        return

    try:
        if os.name == "nt":
            subprocess.Popen(["cmd", "/c", "start", "", APP_URL], shell=False)
        else:
            webbrowser.open(APP_URL)
    except Exception:
        _log("[ERROR] No se pudo abrir el navegador automaticamente.")
        _log(traceback.format_exc())


if __name__ == "__main__":
    try:
        threading.Thread(target=_open_browser, daemon=True).start()
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            log_config=None,
            access_log=False,
        )
    except Exception:
        _log("[ERROR] El ejecutable fallo al iniciar.")
        _log(traceback.format_exc())
        raise
