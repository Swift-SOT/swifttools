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


class TestSwiftResolveInit:
    def test_name(self, resolve_instance):
        assert resolve_instance.name == "Test Name"

    def test_status(self, resolve_instance):
        assert resolve_instance.status.status == "Pending"


class TestSwiftResolveValidate:
    def test_validate(self, resolve_instance):
        with patch.object(resolve_instance, "validate_get", return_value=True):
            assert resolve_instance.validate() is True


class TestSwiftResolveTable:
    def test_header(self, resolve_instance):
        resolve_instance.ra = 10.0
        resolve_instance.dec = 20.0
        resolve_instance.resolver = "Simbad"
        header, _ = resolve_instance._table
        assert header == ["Name", "RA (J2000)", "Dec (J2000)", "Resolver"]

    def test_table(self, resolve_instance):
        resolve_instance.ra = 10.0
        resolve_instance.dec = 20.0
        resolve_instance.resolver = "Simbad"
        _, table = resolve_instance._table
        # Floating point precision: expecting 10.00001 due to rounding
        assert table[0][0] == "Test Name"
        assert table[0][1] == "10.00001"
        assert table[0][2] == "20.00000"
        assert table[0][3] == "Simbad"


class TestSwiftResolveTableNoRa:
    def test_header_no_ra(self, resolve_instance):
        header, _ = resolve_instance._table
        assert header == []

    def test_table_no_ra(self, resolve_instance):
        _, table = resolve_instance._table
        assert table == []
