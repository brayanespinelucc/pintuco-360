"""Run FastAPI privately and Streamlit publicly in one Render web service.

No backend/API contract changes. Render connects only to the Streamlit port.
Requires SUPABASE_URL, SUPABASE_ANON_KEY and optionally GEMINI_API_KEY
configured as Render environment variables, never embedded in source code.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

PRIVATE_API_PORT = 8000
DEFAULT_PUBLIC_PORT = 10000


def public_port_from_env() -> int:
    value = os.environ.get("PORT", str(DEFAULT_PUBLIC_PORT))
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("PORT debe ser un número entero válido.") from exc
    if not 1 <= port <= 65535 or port == PRIVATE_API_PORT:
        raise ValueError("PORT debe estar entre 1 y 65535 y no ser el puerto 8000.")
    return port


def commands(port: int) -> tuple[list[str], list[str]]:
    api = [
        sys.executable, "-m", "uvicorn", "backend.app.main:app",
        "--host", "127.0.0.1", "--port", str(PRIVATE_API_PORT),
    ]
    streamlit = [
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.address=0.0.0.0",
        f"--server.port={port}",
        "--server.headless=true",
        "--server.enableCORS=true",
        "--server.enableXsrfProtection=true",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    return api, streamlit


def main() -> int:
    port = public_port_from_env()
    # The Streamlit server calls FastAPI over a private loopback connection.
    # Never expose the API by binding Uvicorn to 0.0.0.0 in this deployment.
    os.environ["API_BASE_URL"] = f"http://127.0.0.1:{PRIVATE_API_PORT}"
    api_cmd, ui_cmd = commands(port)
    processes: list[subprocess.Popen] = []
    shutting_down = False

    def request_shutdown(signum: int, _frame: object) -> None:
        nonlocal shutting_down
        print(f"Recibida señal {signum}; cerrando COLORLINK.", flush=True)
        shutting_down = True

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)

    try:
        print("Iniciando API privada de COLORLINK...", flush=True)
        processes.append(subprocess.Popen(api_cmd, close_fds=True))
        print(f"Iniciando interfaz pública en el puerto {port}...", flush=True)
        processes.append(subprocess.Popen(ui_cmd, close_fds=True))
        while not shutting_down:
            for process in processes:
                result = process.poll()
                if result is not None:
                    print(f"El proceso {process.pid} terminó con código {result}.", flush=True)
                    return result or 1
            time.sleep(0.5)
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    sys.exit(main())
