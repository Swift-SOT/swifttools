# Local fixtures for tests/swift_too/swift/visquery
from datetime import datetime, timedelta

import pytest

from swifttools.swift_too.swift.visquery import SwiftVisQuery, SwiftVisWindow


@pytest.fixture
def vis_query():
    return SwiftVisQuery(
        ra=10.0, dec=20.0, begin=datetime(2023, 1, 1), end=datetime(2023, 1, 2), length=1, autosubmit=False
    )


@pytest.fixture
def vis_window():
    return SwiftVisWindow(begin=datetime(2023, 1, 1, 0, 0), end=datetime(2023, 1, 2, 0, 0), length=timedelta(days=1))


@pytest.fixture
def vis_query_with_window(vis_query, vis_window):
    vis_query.windows = [vis_window]
    return vis_query
