# Local fixtures for tests/swift_too/base/schemas
from datetime import datetime, timezone

import astropy.units as u  # type: ignore[import-untyped]
import pytest
from astropy.coordinates import SkyCoord  # type: ignore[import-untyped]
from astropy.time import Time  # type: ignore[import-untyped]


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
