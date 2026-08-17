# Local fixtures for tests/swift_too/base/schemas
import os
import time
from datetime import datetime, timezone

import astropy.units as u  # type: ignore[import-untyped]
import pytest
from astropy.coordinates import SkyCoord  # type: ignore[import-untyped]
from astropy.time import Time  # type: ignore[import-untyped]


@pytest.fixture
def non_utc_timezone():
    """Run the process in a non-UTC timezone for the duration of a test.

    Datetime handling should not depend on the timezone of the machine running
    the code, so tests that check this need a timezone that is not UTC.
    Skipped where `time.tzset` is unavailable, i.e. anywhere but Unix.
    """
    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset is not available on this platform")

    original = os.environ.get("TZ")
    os.environ["TZ"] = "America/New_York"  # UTC-5 in January
    time.tzset()
    try:
        yield
    finally:
        if original is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = original
        time.tzset()


@pytest.fixture
def test_datetime():
    """Common test datetime: 2020-01-01 12:00:00 UTC"""
    return datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def test_datetime_str():
    """Common test datetime string"""
    return "2020-01-01T12:00:00Z"


@pytest.fixture
def test_time():
    """Common test Time object"""
    return Time("2020-01-01T12:00:00Z")


@pytest.fixture
def test_skycoord():
    """Common test SkyCoord: ra=30°, dec=10°"""
    return SkyCoord(ra=30 * u.deg, dec=10 * u.deg)


@pytest.fixture
def test_skycoord_2():
    """Common test SkyCoord: ra=45°, dec=15°"""
    return SkyCoord(ra=45 * u.deg, dec=15 * u.deg)
