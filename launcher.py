import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
BACKEND = ROOT / 'backend'
if BACKEND.is_dir():
    sys.path.insert(0, str(BACKEND))

from main import app  # noqa: E402
from uvicorn import Config, Server  # noqa: E402


def find_port() -> int:
    for port in range(8000, 8091):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                continue
            return port
    raise RuntimeError('Não foi encontrada uma porta livre entre 8000 e 8090.')


def wait_until_ready(url: str, timeout: float = 30) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    return False


def create_server(port: int) -> Server:
    # A --noconsole PyInstaller process has no stdout/stderr. Uvicorn's
    # default formatter probes those streams with isatty() while configuring
    # logging, so skip its console logging configuration in that environment.
    return Server(Config(app=app, host='127.0.0.1', port=port, log_level='info', log_config=None))


def main() -> None:
    port = find_port()
    server = create_server(port)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{port}'
    if not wait_until_ready(f'{url}/health'):
        server.should_exit = True
        raise RuntimeError('A API não ficou pronta dentro do limite de inicialização.')
    webbrowser.open(url)
    try:
        while thread.is_alive():
            thread.join(timeout=0.5)
    except KeyboardInterrupt:
        server.should_exit = True
        thread.join(timeout=5)


if __name__ == '__main__':
    main()
