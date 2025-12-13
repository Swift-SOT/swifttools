from swifttools.swift_too.swift.uvot import SwiftUVOTMode, SwiftUVOTModeEntry


def test_swift_uvot_mode_init():
    """Test SwiftUVOTMode initialization"""
    uvot = SwiftUVOTMode(uvot_mode=0x30ED, autosubmit=False)
    assert uvot.uvot_mode == 0x30ED


def test_swift_uvot_mode_getitem():
    """Test indexing"""
    uvot = SwiftUVOTMode(autosubmit=False)
    uvot.entries = ["entry1", "entry2"]
    assert uvot[0] == "entry1"
    assert uvot[1] == "entry2"


def test_swift_uvot_mode_len():
    """Test len() method"""
    uvot = SwiftUVOTMode(autosubmit=False)
    assert len(uvot) == 0
    uvot.entries = [1, 2, 3]
    assert len(uvot) == 3


def test_swift_uvot_mode_str():
    """Test __str__ method"""
    uvot = SwiftUVOTMode(uvot_mode=0x30ED, autosubmit=False)
    uvot.entries = []
    str_repr = str(uvot)
    assert "UVOT Mode:" in str_repr

    # Test with entries
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
    uvot.entries = [entry]
    str_repr = str(uvot)
    assert "V" in str_repr
    assert "Test filter" in str_repr


def test_swift_uvot_mode_repr_html():
    """Test _repr_html_ method"""
    uvot = SwiftUVOTMode(uvot_mode=0x30ED, autosubmit=False)
    uvot.entries = []
    html_repr = uvot._repr_html_()
    assert "UVOT Mode:" in html_repr

    # Test with entries
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
    uvot.entries = [entry]
    html_repr = uvot._repr_html_()
    assert "<table" in html_repr
    assert "V" in html_repr


def test_swift_uvot_mode_entry_init():
    """Test SwiftUVOTModeEntry initialization"""
    entry = SwiftUVOTModeEntry(uvot_mode=0x30ED)
    assert entry.uvot_mode == 0x30ED
    assert entry.filter_name is None  # Default is None
    assert entry.eventmode is None  # Default is None
