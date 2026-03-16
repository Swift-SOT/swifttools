# Local fixtures for tests/swift_too/swift/clock


from datetime import datetime

import pytest

from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.swift.clock import SwiftClock, SwiftDateTimeSchema, TOOAPIClockCorrect


class MockClockCorrect(BaseSchema, TOOAPIClockCorrect):
    """Mock class to test TOOAPIClockCorrect mixin"""

    test_datetime: datetime


@pytest.fixture
def mock_clock_correct():
    """Fixture for MockClockCorrect instance."""
    return MockClockCorrect(test_datetime=datetime(2023, 1, 1))


@pytest.fixture
def swift_clock():
    """Fixture for SwiftClock instance with autosubmit=False."""
    return SwiftClock(autosubmit=False)


@pytest.fixture
def swift_datetime_schema():
    """Fixture for SwiftDateTimeSchema instance."""
    return SwiftDateTimeSchema(met=123456789.0, utcf=10.0, isutc=False)


@pytest.fixture
def swift_clock_with_entry(swift_clock):
    """Fixture for SwiftClock with a mock entry."""
    entry = SwiftDateTimeSchema(met=123456789.0, utcf=0.0, isutc=False)
    object.__setattr__(
        entry,
        "_table",
        [["MET", "Swift Time", "UTC Time"], [123456789.0, datetime(2023, 1, 1), datetime(2023, 1, 1)]],
    )
    swift_clock.entries = [entry]
    return swift_clock
