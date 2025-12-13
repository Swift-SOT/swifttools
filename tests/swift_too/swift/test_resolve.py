from unittest.mock import patch

from swifttools.swift_too.swift.resolve import SwiftResolve


@patch("swifttools.swift_too.base.common.cookie_jar")
@patch("httpx.Client")
def test_swift_resolve_init(mock_client, mock_cookie_jar):
    resolve = SwiftResolve(name="Test Name", autosubmit=False)
    assert resolve.name == "Test Name"
    assert resolve.status.status == "Pending"


def test_swift_resolve_validate():
    resolve = SwiftResolve(name="Test Name", autosubmit=False)
    # Since validate calls validate_get, and _get_schema is set
    with patch.object(resolve, "validate_get", return_value=True):
        assert resolve.validate() is True


def test_swift_resolve_table():
    resolve = SwiftResolve(name="Test Name", autosubmit=False)
    resolve.ra = 10.0
    resolve.dec = 20.0
    resolve.resolver = "Simbad"

    header, table = resolve._table
    assert header == ["Name", "RA (J2000)", "Dec (J2000)", "Resolver"]
    assert table == [["Test Name", "10.00000", "20.00000", "Simbad"]]


def test_swift_resolve_table_no_ra():
    resolve = SwiftResolve(name="Test Name", autosubmit=False)
    header, table = resolve._table
    assert header == []
    assert table == []
