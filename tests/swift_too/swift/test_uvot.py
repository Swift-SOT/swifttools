import pytest

from swifttools.swift_too.swift.uvot import SwiftUVOTMode, SwiftUVOTModeEntry


@pytest.fixture
def uvot_mode():
    return SwiftUVOTMode(uvot_mode=0x30ED, autosubmit=False)


@pytest.fixture
def uvot_mode_empty():
    uvot = SwiftUVOTMode(autosubmit=False)
    uvot.entries = []
    return uvot


@pytest.fixture
def uvot_mode_with_entries(uvot_mode_empty):
    entry = SwiftUVOTModeEntry(
        uvot_mode=0x30ED,
        filter_name="V",
        eventmode=False,
        field_of_view=17,
        binning=1,
        max_exposure=1000,
        weight=True,
        comment="Test filter",
    )
    uvot_mode_empty.entries = [entry]
    return uvot_mode_empty


@pytest.fixture
def uvot_entry():
    return SwiftUVOTModeEntry(uvot_mode=0x30ED)


class TestSwiftUVOTMode:
    def test_init(self, uvot_mode):
        assert uvot_mode.uvot_mode == 0x30ED

    def test_getitem_first(self):
        uvot = SwiftUVOTMode(autosubmit=False)
        entry1 = SwiftUVOTModeEntry(uvot_mode=0x30ED)
        entry2 = SwiftUVOTModeEntry(uvot_mode=0x30ED)
        uvot.entries = [entry1, entry2]
        assert uvot[0] == entry1

    def test_getitem_second(self):
        uvot = SwiftUVOTMode(autosubmit=False)
        entry1 = SwiftUVOTModeEntry(uvot_mode=0x30ED)
        entry2 = SwiftUVOTModeEntry(uvot_mode=0x30ED)
        uvot.entries = [entry1, entry2]
        assert uvot[1] == entry2

    def test_len_empty(self):
        uvot = SwiftUVOTMode(autosubmit=False)
        assert len(uvot) == 0

    def test_len_three(self):
        uvot = SwiftUVOTMode(autosubmit=False)
        entry1 = SwiftUVOTModeEntry(uvot_mode=0x30ED)
        entry2 = SwiftUVOTModeEntry(uvot_mode=0x30ED)
        entry3 = SwiftUVOTModeEntry(uvot_mode=0x30ED)
        uvot.entries = [entry1, entry2, entry3]
        assert len(uvot) == 3

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
