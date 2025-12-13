from datetime import datetime

from swifttools.swift_too.swift.calendar import SwiftCalendar, SwiftCalendarEntry


def test_swift_calendar_init():
    """Test SwiftCalendar initialization"""
    calendar = SwiftCalendar(autosubmit=False)
    assert calendar.entries == []


def test_swift_calendar_getitem():
    """Test indexing"""
    calendar = SwiftCalendar(autosubmit=False)
    calendar.entries = ["entry1", "entry2"]
    assert calendar[0] == "entry1"
    assert calendar[1] == "entry2"


def test_swift_calendar_len():
    """Test len() method"""
    calendar = SwiftCalendar(autosubmit=False)
    assert len(calendar) == 0
    calendar.entries = [1, 2, 3]
    assert len(calendar) == 3


def test_swift_calendar_table_property():
    """Test _table property"""
    calendar = SwiftCalendar(autosubmit=False)
    calendar.entries = []
    header, table = calendar._table
    assert header == []
    assert table == []


def test_swift_calendar_table_property_with_entries():
    """Test _table property with entries"""
    calendar = SwiftCalendar(autosubmit=False)
    entry = SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Test Target", ra=123.456, dec=-45.678, sip=1
    )
    entry.start = datetime(2023, 1, 1, 12, 0, 0)
    entry.stop = datetime(2023, 1, 1, 13, 0, 0)
    entry.xrt_mode = 7
    entry.uvot_mode = 39321
    entry.duration = 3600.0
    entry.asflown = 3500.0
    calendar.entries = [entry]

    header, table = calendar._table
    assert len(header) == 7  # ["#"] + entry._table[0]
    assert header[0] == "#"
    assert len(table) == 1
    assert table[0][0] == 0  # index of first entry
    """Test SwiftCalendarEntry initialization"""
    entry = SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Test Target", ra=123.456, dec=-45.678, sip=1
    )
    assert entry.type == "TOO"
    assert entry.pi_name == ""
    assert entry.sip_target_ID == 0


def test_swift_calendar_entry_getitem():
    """Test SwiftCalendarEntry indexing"""
    entry = SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Test Target", ra=123.456, dec=-45.678, sip=1
    )
    entry.start = datetime(2023, 1, 1, 12, 0, 0)
    assert entry["start"] == datetime(2023, 1, 1, 12, 0, 0)


def test_swift_calendar_entry_table_property():
    """Test SwiftCalendarEntry _table property"""
    entry = SwiftCalendarEntry(
        typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Test Target", ra=123.456, dec=-45.678, sip=1
    )
    entry.start = datetime(2023, 1, 1, 12, 0, 0)
    entry.stop = datetime(2023, 1, 1, 13, 0, 0)
    entry.xrt_mode = 7
    entry.uvot_mode = 39321
    entry.duration = 3600.0
    entry.asflown = 3500.0

    header, table = entry._table
    assert len(header) == 6
    assert len(table) == 1
    assert table[0][0] == datetime(2023, 1, 1, 12, 0, 0)  # start
