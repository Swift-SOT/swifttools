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


class TestSwiftCalendar:
    def test_init_entries(self, calendar):
        assert calendar.entries == []

    def test_getitem_first(self, calendar):
        # Use valid `SwiftCalendarEntry` instances instead of raw strings
        entry1 = SwiftCalendarEntry(
            typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Target1", ra=123.456, dec=-45.678, sip=1
        )
        entry2 = SwiftCalendarEntry(
            typeID=1, duration=3600.0, roll=0.0, target_ID=12346, target_name="Target2", ra=123.456, dec=-45.678, sip=1
        )
        calendar.entries = [entry1, entry2]
        assert calendar[0] == calendar.entries[0]

    def test_getitem_second(self, calendar):
        entry1 = SwiftCalendarEntry(
            typeID=1, duration=3600.0, roll=0.0, target_ID=12345, target_name="Target1", ra=123.456, dec=-45.678, sip=1
        )
        entry2 = SwiftCalendarEntry(
            typeID=1, duration=3600.0, roll=0.0, target_ID=12346, target_name="Target2", ra=123.456, dec=-45.678, sip=1
        )
        calendar.entries = [entry1, entry2]
        assert calendar[1] == calendar.entries[1]

    def test_len_empty(self, calendar):
        assert len(calendar) == 0

    def test_len_with_entries(self, calendar):
        entries = [
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
        calendar.entries = entries
        assert len(calendar) == 3

    def test_table_property_header_empty(self, calendar):
        calendar.entries = []
        header, table = calendar._table
        assert header == []

    def test_table_property_table_empty(self, calendar):
        calendar.entries = []
        header, table = calendar._table
        assert table == []

    def test_table_property_with_entries_header_length(self, calendar, sample_entry):
        calendar.entries = [sample_entry]
        header, table = calendar._table
        assert len(header) == 7

    def test_table_property_with_entries_header_first(self, calendar, sample_entry):
        calendar.entries = [sample_entry]
        header, table = calendar._table
        assert header[0] == "#"

    def test_table_property_with_entries_table_length(self, calendar, sample_entry):
        calendar.entries = [sample_entry]
        header, table = calendar._table
        assert len(table) == 1

    def test_table_property_with_entries_table_first_index(self, calendar, sample_entry):
        calendar.entries = [sample_entry]
        header, table = calendar._table
        assert table[0][0] == 0


class TestSwiftCalendarEntry:
    def test_init_type(self):
        entry = SwiftCalendarEntry(
            typeID=1,
            duration=3600.0,
            roll=0.0,
            target_ID=12345,
            target_name="Test Target",
            ra=123.456,
            dec=-45.678,
            sip=1,
        )
        assert entry.type == "TOO"

    def test_init_pi_name(self):
        entry = SwiftCalendarEntry(
            typeID=1,
            duration=3600.0,
            roll=0.0,
            target_ID=12345,
            target_name="Test Target",
            ra=123.456,
            dec=-45.678,
            sip=1,
        )
        assert entry.pi_name == ""

    def test_init_sip_target_ID(self):
        entry = SwiftCalendarEntry(
            typeID=1,
            duration=3600.0,
            roll=0.0,
            target_ID=12345,
            target_name="Test Target",
            ra=123.456,
            dec=-45.678,
            sip=1,
        )
        assert entry.sip_target_ID == 0

    def test_getitem_start(self, sample_entry):
        assert sample_entry.begin == datetime(2023, 1, 1, 12, 0, 0)

    def test_table_property_header_length(self, sample_entry):
        header, table = sample_entry._table
        assert len(header) == 6

    def test_table_property_table_length(self, sample_entry):
        header, table = sample_entry._table
        assert len(table) == 1

    def test_table_property_table_first_start(self, sample_entry):
        header, table = sample_entry._table
        assert table[0][1] == datetime(2023, 1, 1, 13, 0, 0)
