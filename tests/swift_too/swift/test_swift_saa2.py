from datetime import datetime

import pytest

from swifttools.swift_too.swift.saa import (
    SAA,
    Swift_SAA,
    SwiftSAA,
    SwiftSAAEntry,
    SwiftSAAGetSchema,
    SwiftSAASchema,
)


class TestSwiftSAAGetSchema:
    def test_swiftsaagetschema_creation(self):
        """Test that SwiftSAAGetSchema can be created with default values."""
        schema = SwiftSAAGetSchema()
        assert schema.bat is False

    def test_swiftsaagetschema_with_bat_true(self):
        """Test SwiftSAAGetSchema with bat parameter set to True."""
        schema = SwiftSAAGetSchema(bat=True)
        assert schema.bat is True

    def test_swiftsaagetschema_extra_fields_ignored(self):
        """Test that extra fields are ignored due to ConfigDict."""
        schema = SwiftSAAGetSchema(bat=True, extra_field="ignored")
        assert schema.bat is True
        assert not hasattr(schema, "extra_field")


class TestSwiftSAASchema:
    def test_swiftsaaschema_default_values(self):
        """Test SwiftSAASchema default initialization."""
        schema = SwiftSAASchema()
        assert schema.bat is False
        assert schema.entries == []
        assert schema.status is not None

    def test_swiftsaaschema_with_entries(self):
        """Test SwiftSAASchema with entries."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftSAAEntry(begin=begin_time, end=end_time)

        schema = SwiftSAASchema(entries=[entry])
        assert len(schema.entries) == 1
        assert schema.entries[0] == entry


class TestSwiftSAA:
    def test_swiftsaa_initialization(self):
        """Test SwiftSAA can be created with default values."""
        saa = SwiftSAA()
        assert saa.bat is False
        assert len(saa.entries) == 0
        assert saa.status is not None

    def test_swiftsaa_class_attributes(self):
        """Test SwiftSAA has correct class attributes."""
        assert SwiftSAA._schema == SwiftSAASchema
        assert SwiftSAA._get_schema == SwiftSAAGetSchema
        assert SwiftSAA._endpoint == "/swift/saa"
        assert SwiftSAA._isutc is True

    def test_swiftsaa_getitem_with_entries(self):
        """Test __getitem__ method for accessing entries by index."""
        begin_time1 = datetime(2023, 1, 1, 12, 0, 0)
        end_time1 = datetime(2023, 1, 1, 13, 0, 0)
        begin_time2 = datetime(2023, 1, 1, 14, 0, 0)
        end_time2 = datetime(2023, 1, 1, 15, 0, 0)

        entry1 = SwiftSAAEntry(begin=begin_time1, end=end_time1)
        entry2 = SwiftSAAEntry(begin=begin_time2, end=end_time2)

        saa = SwiftSAA(entries=[entry1, entry2])

        assert saa[0] == entry1
        assert saa[1] == entry2

    def test_swiftsaa_getitem_index_error(self):
        """Test __getitem__ raises IndexError for out of range index."""
        saa = SwiftSAA()

        with pytest.raises(IndexError):
            _ = saa[0]

    def test_swiftsaa_len_empty(self):
        """Test __len__ returns 0 for empty SwiftSAA."""
        saa = SwiftSAA()
        assert len(saa) == 0

    def test_swiftsaa_len_with_entries(self):
        """Test __len__ returns correct count with entries."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)
        entry1 = SwiftSAAEntry(begin=begin_time, end=end_time)
        entry2 = SwiftSAAEntry(begin=begin_time, end=end_time)

        saa = SwiftSAA(entries=[entry1, entry2])
        assert len(saa) == 2

    def test_swiftsaa_table_property_empty(self):
        """Test _table property returns empty lists when no entries."""
        saa = SwiftSAA()
        header, data = saa._table

        assert header == []
        assert data == []

    def test_swiftsaa_table_property_single_entry(self):
        """Test _table property with a single entry."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftSAAEntry(begin=begin_time, end=end_time)

        saa = SwiftSAA(entries=[entry])
        header, data = saa._table

        assert header == ["#", "Begin Time", "End Time"]
        assert len(data) == 1
        assert data[0][0] == 0
        assert data[0][1] == begin_time
        assert data[0][2] == end_time

    def test_swiftsaa_table_property_multiple_entries(self):
        """Test _table property with multiple entries."""
        begin_time1 = datetime(2023, 1, 1, 12, 0, 0)
        end_time1 = datetime(2023, 1, 1, 13, 0, 0)
        begin_time2 = datetime(2023, 1, 1, 14, 0, 0)
        end_time2 = datetime(2023, 1, 1, 15, 0, 0)
        begin_time3 = datetime(2023, 1, 1, 16, 0, 0)
        end_time3 = datetime(2023, 1, 1, 17, 0, 0)

        entry1 = SwiftSAAEntry(begin=begin_time1, end=end_time1)
        entry2 = SwiftSAAEntry(begin=begin_time2, end=end_time2)
        entry3 = SwiftSAAEntry(begin=begin_time3, end=end_time3)

        saa = SwiftSAA(entries=[entry1, entry2, entry3])
        header, data = saa._table

        assert header == ["#", "Begin Time", "End Time"]
        assert len(data) == 3
        assert data[0] == [0, begin_time1, end_time1]
        assert data[1] == [1, begin_time2, end_time2]
        assert data[2] == [2, begin_time3, end_time3]

    def test_swiftsaa_with_bat_parameter(self):
        """Test SwiftSAA with bat parameter set."""
        saa = SwiftSAA(bat=True)
        assert saa.bat is True

    def test_swiftsaa_inheritance(self):
        """Test that SwiftSAA has expected parent class methods/attributes."""
        saa = SwiftSAA()

        # Check for TOOAPIBaseclass, TOOAPIClockCorrect, SwiftSAASchema
        assert hasattr(saa, "entries")
        assert hasattr(saa, "status")
        assert hasattr(saa, "bat")
        assert hasattr(saa, "_endpoint")
        assert hasattr(saa, "_schema")

    def test_swiftsaa_mutable_entries(self):
        """Test that entries can be modified after creation."""
        saa = SwiftSAA()
        assert len(saa) == 0

        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftSAAEntry(begin=begin_time, end=end_time)

        saa.entries.append(entry)
        assert len(saa) == 1
        assert saa[0] == entry

    def test_swiftsaa_aliases(self):
        """Test that SAA alias exists and works."""

        saa1 = SAA()
        saa2 = Swift_SAA()

        assert isinstance(saa1, SwiftSAA)
        assert isinstance(saa2, SwiftSAA)
