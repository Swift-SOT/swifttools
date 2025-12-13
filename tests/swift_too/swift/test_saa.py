from datetime import datetime

from swifttools.swift_too.swift.saa import SwiftSAA, SwiftSAAEntry, SwiftSAAGetSchema


class TestSwiftSAAGetSchema:
    def test_init(self):
        schema = SwiftSAAGetSchema()
        assert schema.bat is False


class TestSwiftSAAEntry:
    def test_init(self):
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftSAAEntry(begin=begin, end=end)
        assert entry.begin == begin
        assert entry.end == end

    def test_table_property(self):
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftSAAEntry(begin=begin, end=end)
        header, data = entry._table
        assert header == ["Begin Time", "End Time"]
        assert data == [[begin, end]]


class TestSwiftSAA:
    def test_init(self):
        saa = SwiftSAA(autosubmit=False)
        assert saa.entries == []

    def test_getitem(self):
        saa = SwiftSAA(autosubmit=False)
        entry = SwiftSAAEntry(begin=datetime(2023, 1, 1, 12, 0, 0), end=datetime(2023, 1, 1, 13, 0, 0))
        saa.entries = [entry]
        assert saa[0] == entry

    def test_len(self):
        saa = SwiftSAA(autosubmit=False)
        saa.entries = [SwiftSAAEntry(begin=datetime(2023, 1, 1, 12, 0, 0), end=datetime(2023, 1, 1, 13, 0, 0))]
        assert len(saa) == 1

    def test_table_property_empty(self):
        saa = SwiftSAA(autosubmit=False)
        header, data = saa._table
        assert header == []
        assert data == []

    def test_table_property_with_entries(self):
        saa = SwiftSAA(autosubmit=False)
        entry1 = SwiftSAAEntry(begin=datetime(2023, 1, 1, 12, 0, 0), end=datetime(2023, 1, 1, 13, 0, 0))
        entry2 = SwiftSAAEntry(begin=datetime(2023, 1, 2, 12, 0, 0), end=datetime(2023, 1, 2, 13, 0, 0))
        saa.entries = [entry1, entry2]
        header, data = saa._table
        assert header == ["#", "Begin Time", "End Time"]
        assert len(data) == 2
        assert data[0] == [0, entry1.begin, entry1.end]
        assert data[1] == [1, entry2.begin, entry2.end]
