from __future__ import annotations

import os
import threading
import time
import webbrowser

import uvicorn


HOST = os.environ.get("CATALOGOS_HOST", "127.0.0.1")
PORT = int(os.environ.get("CATALOGOS_PORT", "8000"))


def _open_browser() -> None:
    time.sleep(1.2)
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run("main:app", host=HOST, port=PORT)
