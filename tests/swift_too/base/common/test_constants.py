import importlib


def test_default_swift_too_api_url(monkeypatch):
    monkeypatch.delenv("SWIFT_TOO_API_URL", raising=False)

    import swifttools.swift_too.base.constants as constants

    reloaded = importlib.reload(constants)
    expected = f"https://www.swift.psu.edu/api/v{reloaded.API_VERSION}"

    assert reloaded.API_URL == expected
