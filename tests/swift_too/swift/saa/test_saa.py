from swifttools.swift_too.swift.saa import SwiftSAAEntry, SwiftSAAGetSchema


class TestSwiftSAAGetSchema:
    def test_init(self):
        schema = SwiftSAAGetSchema()
        assert schema.bat is False


class TestSwiftSAAEntry:
    def test_init_begin(self, begin_datetime, end_datetime):
        entry = SwiftSAAEntry(begin=begin_datetime, end=end_datetime)
        assert entry.begin == begin_datetime

    def test_init_end(self, begin_datetime, end_datetime):
        entry = SwiftSAAEntry(begin=begin_datetime, end=end_datetime)
        assert entry.end == end_datetime

    def test_table_property_header(self, sample_saa_entry):
        header, _ = sample_saa_entry._table
        assert header == ["Begin Time", "End Time"]

    def test_table_property_data(self, sample_saa_entry, begin_datetime, end_datetime):
        _, data = sample_saa_entry._table
        assert data == [[begin_datetime, end_datetime]]


class TestSwiftSAA:
    def test_init(self, swift_saa):
        assert swift_saa.entries == []

    def test_getitem(self, swift_saa, sample_saa_entry):
        swift_saa.entries = [sample_saa_entry]
        assert swift_saa[0] == sample_saa_entry

    def test_len(self, swift_saa, sample_saa_entry):
        swift_saa.entries = [sample_saa_entry]
        assert len(swift_saa) == 1

    def test_table_property_empty_header(self, swift_saa):
        header, _ = swift_saa._table
        assert header == []

    def test_table_property_empty_data(self, swift_saa):
        _, data = swift_saa._table
        assert data == []

    def test_table_property_with_entries_header(self, swift_saa, sample_saa_entries):
        swift_saa.entries = sample_saa_entries
        header, _ = swift_saa._table
        assert header == ["#", "Begin Time", "End Time"]

    def test_table_property_with_entries_length(self, swift_saa, sample_saa_entries):
        swift_saa.entries = sample_saa_entries
        _, data = swift_saa._table
        assert len(data) == 2

    def test_table_property_with_entries_first_row(self, swift_saa, sample_saa_entries):
        swift_saa.entries = sample_saa_entries
        _, data = swift_saa._table
        assert data[0] == [0, sample_saa_entries[0].begin, sample_saa_entries[0].end]

    def test_table_property_with_entries_second_row(self, swift_saa, sample_saa_entries):
        swift_saa.entries = sample_saa_entries
        _, data = swift_saa._table
        assert data[1] == [1, sample_saa_entries[1].begin, sample_saa_entries[1].end]
