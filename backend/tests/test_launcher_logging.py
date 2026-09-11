import sys

from launcher import create_server


def test_pyinstaller_without_console_does_not_break_server_logging_setup(monkeypatch):
    monkeypatch.setattr(sys, 'stdout', None)
    monkeypatch.setattr(sys, 'stderr', None)

    server = create_server(0)

    assert server.config.log_config is None
