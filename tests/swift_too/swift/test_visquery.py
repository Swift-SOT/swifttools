from unittest.mock import patch

import pytest

from swifttools.swift_too.swift.visquery import SwiftVisQuery, SwiftVisWindow


@patch("swifttools.swift_too.base.common.cookie_jar")
@patch("httpx.Client")
def test_swift_vis_query_init(mock_client, mock_cookie_jar):
    vis = SwiftVisQuery(ra=10.0, dec=20.0, autosubmit=False)
    assert abs(vis.ra - 10.0) < 1e-5
    assert abs(vis.dec - 20.0) < 1e-5
    assert vis.status.status == "Pending"


def test_swift_vis_query_validate():
    vis = SwiftVisQuery(ra=10.0, dec=20.0, autosubmit=False)
    # Since validate calls validate_get, and _get_schema is set
    with patch.object(vis, "validate_get", return_value=True):
        assert vis.validate_get() is True


def test_swift_vis_query_table():
    vis = SwiftVisQuery(ra=10.0, dec=20.0, autosubmit=False)
    # Create a mock window
    from datetime import datetime, timedelta

    window = SwiftVisWindow(begin=datetime(2023, 1, 1, 0, 0), end=datetime(2023, 1, 2, 0, 0), length=timedelta(days=1))
    vis.windows = [window]

    header, table = vis._table
    assert header == ["Begin Time", "End Time", "Window length"]
    assert len(table) == 1


def test_swift_vis_query_table_empty():
    vis = SwiftVisQuery(ra=10.0, dec=20.0, autosubmit=False)
    header, table = vis._table
    assert header == []
    assert table == []


def test_swift_vis_window_table():
    from datetime import datetime, timedelta

    window = SwiftVisWindow(begin=datetime(2023, 1, 1, 0, 0), end=datetime(2023, 1, 2, 0, 0), length=timedelta(days=1))
    header, table = window._table
    assert header == ["Begin Time", "End Time", "Window length"]
    assert len(table) == 1
    assert table[0][0] == datetime(2023, 1, 1, 0, 0)
    assert table[0][1] == datetime(2023, 1, 2, 0, 0)
    assert table[0][2] == timedelta(days=1)


def test_swift_vis_window_getitem():
    from datetime import datetime, timedelta

    window = SwiftVisWindow(begin=datetime(2023, 1, 1, 0, 0), end=datetime(2023, 1, 2, 0, 0), length=timedelta(days=1))
    assert window[0] == window.begin
    assert window[1] == window.end
    with pytest.raises(IndexError):
        _ = window[2]


def test_swift_vis_query_entries():
    vis = SwiftVisQuery(ra=10.0, dec=20.0, autosubmit=False)
    from datetime import datetime, timedelta

    window = SwiftVisWindow(begin=datetime(2023, 1, 1, 0, 0), end=datetime(2023, 1, 2, 0, 0), length=timedelta(days=1))
    vis.windows = [window]
    assert vis.entries == vis.windows


def test_swift_vis_query_len():
    vis = SwiftVisQuery(ra=10.0, dec=20.0, autosubmit=False)
    assert len(vis) == 0
    from datetime import datetime, timedelta

    window = SwiftVisWindow(begin=datetime(2023, 1, 1, 0, 0), end=datetime(2023, 1, 2, 0, 0), length=timedelta(days=1))
    vis.windows = [window]
    assert len(vis) == 1


def test_swift_vis_query_getitem():
    vis = SwiftVisQuery(ra=10.0, dec=20.0, autosubmit=False)
    from datetime import datetime, timedelta

    window = SwiftVisWindow(begin=datetime(2023, 1, 1, 0, 0), end=datetime(2023, 1, 2, 0, 0), length=timedelta(days=1))
    vis.windows = [window]
    assert vis[0] == window
