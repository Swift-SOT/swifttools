class TestSwiftUVOTMode:
    def test_init(self, uvot_mode):
        assert uvot_mode.uvot_mode == 0x30ED

    def test_getitem_first(self, uvot_mode_with_two_entries, sample_uvot_entries):
        assert uvot_mode_with_two_entries[0] == sample_uvot_entries[0]

    def test_getitem_second(self, uvot_mode_with_two_entries, sample_uvot_entries):
        assert uvot_mode_with_two_entries[1] == sample_uvot_entries[1]

    def test_len_empty(self, uvot_mode_empty):
        assert len(uvot_mode_empty) == 0

    def test_len_three(self, uvot_mode_with_three_entries):
        assert len(uvot_mode_with_three_entries) == 3

    def test_str_empty(self, uvot_mode_empty):
        str_repr = str(uvot_mode_empty)
        assert "UVOT Mode:" in str_repr

    def test_str_with_entries_v(self, uvot_mode_with_entries):
        str_repr = str(uvot_mode_with_entries)
        assert "V" in str_repr

    def test_str_with_entries_comment(self, uvot_mode_with_entries):
        str_repr = str(uvot_mode_with_entries)
        assert "Test filter" in str_repr

    def test_repr_html_empty(self, uvot_mode_empty):
        html_repr = uvot_mode_empty._repr_html_()
        assert "UVOT Mode:" in html_repr

    def test_repr_html_with_entries_table(self, uvot_mode_with_entries):
        html_repr = uvot_mode_with_entries._repr_html_()
        assert "<table" in html_repr

    def test_repr_html_with_entries_v(self, uvot_mode_with_entries):
        html_repr = uvot_mode_with_entries._repr_html_()
        assert "V" in html_repr


class TestSwiftUVOTModeEntry:
    def test_init_uvot_mode(self, uvot_entry):
        assert uvot_entry.uvot_mode == 0x30ED

    def test_init_filter_name(self, uvot_entry):
        assert uvot_entry.filter_name is None

    def test_init_eventmode(self, uvot_entry):
        assert uvot_entry.eventmode is None

    def test_repr_html_table(self, uvot_entry):
        html_repr = uvot_entry._repr_html_()
        assert "<table" in html_repr
        assert "Parameter" in html_repr
        assert "Value" in html_repr
