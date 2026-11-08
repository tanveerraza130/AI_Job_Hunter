from pathlib import Path

import main


def test_keyword_mode_passes_request_to_engine(monkeypatch, tmp_path):
    calls = {}

    class FakeBrowser:
        def new_context(self):
            return object()

        def close(self):
            pass

    class FakeChromium:
        def launch(self, **kwargs):
            calls["launch"] = kwargs
            return FakeBrowser()

    class FakePlaywright:
        chromium = FakeChromium()

    class FakePlaywrightManager:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, *args):
            return False

    class FakeSummary:
        errors = []

    class FakeEngine:
        def __init__(self, **kwargs):
            calls["engine_kwargs"] = kwargs

        def run(self, requests, destination, profile_type=None):
            calls["requests"] = requests
            calls["destination"] = destination
            calls["profile_type"] = profile_type
            return FakeSummary()

        def close(self):
            calls["closed"] = True

    monkeypatch.setattr(
        main, "sync_playwright", lambda: FakePlaywrightManager()
    )
    monkeypatch.setattr(main, "_create_connector", lambda *args: "fake-connector")
    monkeypatch.setattr(main, "_create_exporter", lambda *args: "fake-exporter")
    monkeypatch.setattr(main, "Engine", FakeEngine)
    monkeypatch.setattr(main, "_print_summary", lambda *args: None)
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--keyword",
            "SFMC Platform Implementation Lead",
            "--location",
            "Gurgaon",
            "--connector",
            "naukri",
            "--max-jobs",
            "10",
            "--output",
            str(tmp_path),
        ],
    )

    result = main.main()

    assert result == 0
    assert len(calls["requests"]) == 1
    assert calls["requests"][0].keyword == "SFMC Platform Implementation Lead"
    assert calls["requests"][0].location == "Gurgaon"
    assert calls["requests"][0].max_jobs == 10
    assert calls["destination"] == tmp_path / "job_hunter.duckdb"
    assert calls["profile_type"] is None
    assert calls["closed"] is True
