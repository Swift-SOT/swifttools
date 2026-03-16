# Local fixtures for tests/swift_too/swift/resolve
from unittest.mock import patch

import pytest

from swifttools.swift_too.swift.resolve import SwiftResolve


@pytest.fixture
def mock_client():
    with patch("httpx.Client") as mock:
        yield mock


@pytest.fixture
def mock_cookie_jar():
    with patch("swifttools.swift_too.base.common.cookie_jar") as mock:
        yield mock


@pytest.fixture
def resolve_instance(mock_client, mock_cookie_jar):
    return SwiftResolve(name="Test Name", autosubmit=False)


@pytest.fixture
def configured_resolve_instance(resolve_instance):
    """SwiftResolve instance configured with test coordinates and resolver."""
    resolve_instance.ra = 10.0
    resolve_instance.dec = 20.0
    resolve_instance.resolver = "Simbad"
    return resolve_instance
