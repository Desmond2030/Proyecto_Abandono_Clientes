# ESTADO_ARCHIVO: EN_MODIFICACION
"""Inicia API y dashboard: python app/run.py. Ctrl+C detiene sus procesos."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.client import ApiClient, ErrorAPI


def libre(port):
    with socket.socket() as connection:
        return connection.connect_ex(("127.0.0.1", port)) != 0


def main():
    children = []
    api = ApiClient("http://127.0.0.1:8000")
    try:
        if not libre(8501):
            raise RuntimeError("El puerto 8501 ya está ocupado. Cierra la instancia anterior antes de iniciar otra.")
        if libre(8000):
            children.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app",
                "--host", "127.0.0.1", "--port", "8000"], cwd=ROOT))
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if children[0].poll() is not None:
                    raise RuntimeError("La API no pudo iniciarse. Revisa el error anterior.")
                try:
                    api.salud()
                    break
                except ErrorAPI:
                    time.sleep(.3)
            else:
                raise RuntimeError("La API no quedó lista dentro del tiempo disponible.")
        else:
            api.salud()
        env = {**os.environ, "TELCO_API_URL": api.url}
        children.append(subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app/Home.py",
            "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "true",
            "--browser.gatherUsageStats", "false"], cwd=ROOT, env=env))
        print("App: http://127.0.0.1:8501 · API: http://127.0.0.1:8000/docs", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.5)
        raise RuntimeError("Uno de los servicios se cerró; se detienen los procesos iniciados por este comando.")
    except KeyboardInterrupt:
        print("Cerrando los servicios…", flush=True)
    except (RuntimeError, ErrorAPI) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        for child in reversed(children):
            if child.poll() is None:
                if os.name == "nt":
                    # El lanzador del venv puede tener otro python.exe como hijo.
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                else:
                    child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
