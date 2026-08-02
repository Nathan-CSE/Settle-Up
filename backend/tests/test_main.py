from flask import Flask

from app.main import create_app, main


def test_create_app_registers_settlement_route():
    app = create_app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/api/settlement" in rules


def test_main_smoke_starts_dev_server(monkeypatch):
    calls = {}

    def fake_run(self, debug=False):
        calls["debug"] = debug

    monkeypatch.setattr(Flask, "run", fake_run)

    main()

    assert calls == {"debug": True}
