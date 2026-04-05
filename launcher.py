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


def _configure_windows_gtk() -> None:
    if os.name != "nt":
        return

    candidates = []

    env_gtk_bin = os.environ.get("GTK_BIN")
    if env_gtk_bin:
        candidates.append(Path(env_gtk_bin))

    candidates.extend([
        RUNTIME_DIR / "gtk-runtime" / "bin",
        RUNTIME_DIR / "gtk" / "bin",
        Path(r"C:\msys64\ucrt64\bin"),
        Path(r"C:\msys64\mingw64\bin"),
        Path(r"C:\Program Files\GTK3-Runtime Win64\bin"),
        Path(r"C:\Program Files (x86)\GTK3-Runtime Win64\bin"),
    ])

    for candidate in candidates:
        if not candidate.exists():
            continue
        probe = candidate / "libgobject-2.0-0.dll"
        if not probe.exists():
            continue
        os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(candidate))
        _log(f"[INFO] GTK detectado en {candidate}")
        return

    _log("[WARN] No se encontro runtime GTK compatible en rutas conocidas.")


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
    _log("[INFO] launcher iniciado")
    try:
        _configure_windows_gtk()
        import uvicorn
        from main import app

        threading.Thread(target=_open_browser, daemon=True).start()
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_config=None,
            access_log=False,
        )
    except Exception:
        _log("[ERROR] El ejecutable fallo al iniciar.")
        _log(traceback.format_exc())
        raise
