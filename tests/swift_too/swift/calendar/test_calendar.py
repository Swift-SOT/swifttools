from datetime import datetime


class TestSwiftCalendar:
    def test_init_entries(self, calendar):
        assert calendar.entries == []

    def test_getitem_first(self, calendar_with_two_entries, entry1):
        assert calendar_with_two_entries[0] == entry1

    def test_getitem_second(self, calendar_with_two_entries, entry2):
        assert calendar_with_two_entries[1] == entry2

    def test_len_empty(self, calendar):
        assert len(calendar) == 0

    def test_len_with_entries(self, calendar_with_three_entries):
        assert len(calendar_with_three_entries) == 3

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
    def test_init_type(self, basic_entry):
        assert basic_entry.type == "TOO"

    def test_init_pi_name(self, basic_entry):
        assert basic_entry.pi_name == ""

    def test_init_sip_target_ID(self, basic_entry):
        assert basic_entry.sip_target_ID == 0

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
