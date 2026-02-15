import runpy
import sys
import types
from pathlib import Path


class FakeApp:
    def __init__(self, config):
        self.config = config
        self.root_path = str(Path("/tmp/fake-app-root/app"))
        self.run_calls = []
        self.ssl_context = None

    def run(self, **kwargs):
        self.run_calls.append(kwargs)


class FakeSSLContext:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.loaded = None

    def load_cert_chain(self, cert_path, key_path):
        if self.should_fail:
            raise RuntimeError("bad cert")
        self.loaded = (cert_path, key_path)


def run_main_with_mocks(monkeypatch, app_config, cert_exists=True, load_cert_fails=False):
    fake_app = FakeApp(app_config)

    fake_app_module = types.ModuleType("app")
    fake_app_module.create_app = lambda: fake_app
    monkeypatch.setitem(sys.modules, "app", fake_app_module)

    fake_context = FakeSSLContext(should_fail=load_cert_fails)
    monkeypatch.setattr("ssl.SSLContext", lambda protocol: fake_context)

    monkeypatch.setattr("os.path.exists", lambda _: cert_exists)
    monkeypatch.setattr("platform.system", lambda: "Linux")

    sys.modules.pop("main", None)
    runpy.run_module("main", run_name="__main__")

    return fake_app, fake_context


def test_main_runs_http_when_https_disabled(monkeypatch):
    app, _ = run_main_with_mocks(
        monkeypatch,
        app_config={"USE_HTTPS": False, "DEBUG": True, "SERVER_HOST": "127.0.0.1", "SERVER_PORT": 8080},
    )

    assert len(app.run_calls) == 1
    assert app.run_calls[0]["host"] == "127.0.0.1"
    assert app.run_calls[0]["port"] == 8080
    assert "ssl_context" not in app.run_calls[0]


def test_main_falls_back_to_http_when_cert_missing(monkeypatch):
    app, _ = run_main_with_mocks(
        monkeypatch,
        app_config={"USE_HTTPS": True, "DEBUG": False, "SERVER_HOST": "0.0.0.0", "SERVER_PORT": 5000},
        cert_exists=False,
    )

    assert len(app.run_calls) == 1
    assert "ssl_context" not in app.run_calls[0]


def test_main_runs_https_when_cert_loads(monkeypatch):
    app, fake_context = run_main_with_mocks(
        monkeypatch,
        app_config={
            "USE_HTTPS": True,
            "DEBUG": False,
            "SERVER_HOST": "0.0.0.0",
            "SERVER_PORT": 5000,
            "SSL_CERT": "/etc/ssl/certs/home-cloud.crt",
            "SSL_KEY": "/etc/ssl/private/home-cloud.key",
        },
        cert_exists=True,
    )

    assert len(app.run_calls) == 1
    assert app.run_calls[0]["ssl_context"] is fake_context


def test_main_falls_back_once_when_cert_load_fails(monkeypatch):
    app, _ = run_main_with_mocks(
        monkeypatch,
        app_config={
            "USE_HTTPS": True,
            "DEBUG": False,
            "SERVER_HOST": "0.0.0.0",
            "SERVER_PORT": 5000,
            "SSL_CERT": "/etc/ssl/certs/home-cloud.crt",
            "SSL_KEY": "/etc/ssl/private/home-cloud.key",
        },
        cert_exists=True,
        load_cert_fails=True,
    )

    assert len(app.run_calls) == 1
    assert "ssl_context" not in app.run_calls[0]
