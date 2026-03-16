# Local fixtures for tests/swift_too/swift/datetime
from datetime import datetime, timedelta

import pytest

from swifttools.swift_too.swift.datetime import swiftdatetime


@pytest.fixture
def basic_dt():
    return swiftdatetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def utc_dt():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True)


@pytest.fixture
def utc_dt_with_utcf():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True, utcf=10.5)


@pytest.fixture
def dt_for_met():
    dt = swiftdatetime(2023, 1, 1)
    dt._swifttime = datetime(2001, 1, 1, 12, 0, 0)
    return dt


@pytest.fixture
def dt_for_setters():
    return swiftdatetime(2023, 1, 1)


@pytest.fixture
def utc_dt_for_property():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True)


@pytest.fixture
def non_utc_dt_for_property():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=False)


@pytest.fixture
def dt_for_table():
    return swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True, utcf=10.0)


@pytest.fixture
def dt1_for_sub():
    return swiftdatetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def dt2_for_sub():
    return swiftdatetime(2023, 1, 1, 11, 0, 0)


@pytest.fixture
def dt_for_add():
    return swiftdatetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def td_for_add():
    return timedelta(hours=1)
