from datetime import datetime
from unittest.mock import patch

from swifttools.swift_too.swift.saa import SwiftSAA, SwiftSAAEntry


class TestSwiftSAAEntry:
    def test_swiftsaaentry_creation(self):
        """Test that SwiftSAAEntry can be created with begin and end times."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)

        entry = SwiftSAAEntry(begin=begin_time, end=end_time)

        assert entry.begin == begin_time
        assert entry.end == end_time

    def test_swiftsaaentry_varnames(self):
        """Test that _varnames contains the expected mappings."""
        entry = SwiftSAAEntry(begin=datetime.now(), end=datetime.now())

        assert entry._varnames["begin"] == "Begin Time"
        assert entry._varnames["end"] == "End Time"

    def test_swiftsaaentry_table_property(self):
        """Test the table property returns correct format."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)

        entry = SwiftSAAEntry(begin=begin_time, end=end_time)

        header, data = entry._table

        assert header == ["Begin Time", "End Time"]
        assert data == [[begin_time, end_time]]

    def test_swiftsaaentry_private_table_property(self):
        """Test the _table property returns correct format with header titles."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)

        entry = SwiftSAAEntry(begin=begin_time, end=end_time)

        with patch.object(entry, "_header_title") as mock_header_title:
            mock_header_title.side_effect = lambda x: f"Header {x}"

            header, data = entry._table

            assert header == ["Header begin", "Header end"]
            assert data == [[begin_time, end_time]]
            mock_header_title.assert_any_call("begin")
            mock_header_title.assert_any_call("end")

    def test_swiftsaaentry_inheritance(self):
        """Test that SwiftSAAEntry inherits from expected classes."""
        entry = SwiftSAAEntry(begin=datetime.now(), end=datetime.now())

        # Check if it has methods/attributes from parent classes
        assert hasattr(entry, "_varnames")  # from BaseSchema
        assert hasattr(entry, "begin")
        assert hasattr(entry, "end")

    def test_swiftsaaentry_with_same_begin_end_time(self):
        """Test SwiftSAAEntry with identical begin and end times."""
        same_time = datetime(2023, 1, 1, 12, 0, 0)

        entry = SwiftSAAEntry(begin=same_time, end=same_time)

        assert entry.begin == same_time
        assert entry.end == same_time

        header, data = entry._table
        assert data == [[same_time, same_time]]


def test_swiftsaa_empty_table_property():
    """Test the _table property returns empty lists when no entries."""
    saa = SwiftSAA()

    header, data = saa._table

    assert header == []
    assert data == []


def test_swiftsaa_single_entry_table_property():
    """Test the _table property with a single entry."""
    begin_time = datetime(2023, 1, 1, 12, 0, 0)
    end_time = datetime(2023, 1, 1, 13, 0, 0)
    entry = SwiftSAAEntry(begin=begin_time, end=end_time)

    saa = SwiftSAA()
    saa.entries = [entry]

    header, data = saa._table

    assert header == ["#", "Begin Time", "End Time"]
    assert data == [[0, begin_time, end_time]]


def test_swiftsaa_multiple_entries_table_property():
    """Test the _table property with multiple entries."""
    begin_time1 = datetime(2023, 1, 1, 12, 0, 0)
    end_time1 = datetime(2023, 1, 1, 13, 0, 0)
    begin_time2 = datetime(2023, 1, 1, 14, 0, 0)
    end_time2 = datetime(2023, 1, 1, 15, 0, 0)

    entry1 = SwiftSAAEntry(begin=begin_time1, end=end_time1)
    entry2 = SwiftSAAEntry(begin=begin_time2, end=end_time2)

    saa = SwiftSAA()
    saa.entries = [entry1, entry2]

    header, data = saa._table

    assert header == ["#", "Begin Time", "End Time"]
    assert data == [[0, begin_time1, end_time1], [1, begin_time2, end_time2]]


def test_swiftsaa_getitem():
    """Test the __getitem__ method for accessing entries by index."""
    begin_time1 = datetime(2023, 1, 1, 12, 0, 0)
    end_time1 = datetime(2023, 1, 1, 13, 0, 0)
    begin_time2 = datetime(2023, 1, 1, 14, 0, 0)
    end_time2 = datetime(2023, 1, 1, 15, 0, 0)

    entry1 = SwiftSAAEntry(begin=begin_time1, end=end_time1)
    entry2 = SwiftSAAEntry(begin=begin_time2, end=end_time2)

    saa = SwiftSAA()
    saa.entries = [entry1, entry2]

    assert saa[0] == entry1
    assert saa[1] == entry2


def test_swiftsaa_len():
    """Test the __len__ method returns correct number of entries."""
    saa = SwiftSAA()
    assert len(saa) == 0

    begin_time = datetime(2023, 1, 1, 12, 0, 0)
    end_time = datetime(2023, 1, 1, 13, 0, 0)
    entry = SwiftSAAEntry(begin=begin_time, end=end_time)

    saa.entries = [entry]
    assert len(saa) == 1

    entry2 = SwiftSAAEntry(begin=begin_time, end=end_time)
    saa.entries.append(entry2)
    assert len(saa) == 2
