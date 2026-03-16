# Local fixtures for tests/swift_too/swift/calendar
from datetime import datetime

import pytest

from swifttools.swift_too.swift.calendar import SwiftCalendar, SwiftCalendarEntry


@pytest.fixture
def calendar():
    return SwiftCalendar(autosubmit=False)


@pytest.fixture
def sample_entry():
    entry = SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Test Target", ra=123.456, dec=-45.678, sip=1
    )
    entry.begin = datetime(2023, 1, 1, 12, 0, 0)
    entry.end = datetime(2023, 1, 1, 13, 0, 0)
    entry.xrt_mode = 7
    entry.uvot_mode = 39321
    entry.duration = 3600.0
    entry.asflown = 3500.0
    return entry


@pytest.fixture
def basic_entry():
    """Basic SwiftCalendarEntry with default parameters"""
    return SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Test Target", ra=123.456, dec=-45.678, sip=1
    )


@pytest.fixture
def entry1():
    """First test entry"""
    return SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Target1", ra=123.456, dec=-45.678, sip=1
    )


@pytest.fixture
def entry2():
    """Second test entry"""
    return SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12346, target_name="Target2", ra=123.456, dec=-45.678, sip=1
    )


@pytest.fixture
def calendar_with_two_entries(calendar, entry1, entry2):
    """Calendar with two entries for testing indexing"""
    calendar.entries = [entry1, entry2]
    return calendar


@pytest.fixture
def three_entries():
    """List of three SwiftCalendarEntry objects"""
    return [
        SwiftCalendarEntry(
            typeID=1,
            duration=3600.0,
            roll=0.0,
            target_ID=12345 + i,
            target_name=f"Target{i}",
            ra=123.456,
            dec=-45.678,
            sip=1,
        )
        for i in range(3)
    ]


@pytest.fixture
def calendar_with_three_entries(calendar, three_entries):
    """Calendar with three entries for testing length"""
    calendar.entries = three_entries
    return calendar
