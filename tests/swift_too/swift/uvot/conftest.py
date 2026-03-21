# Local fixtures for tests/swift_too/swift/uvot
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
    return SwiftUVOTModeEntry(uvot_mode=0x30ED, filter_name="")


@pytest.fixture
def sample_uvot_entries():
    """List of sample SwiftUVOTModeEntry objects for testing."""
    return [
        SwiftUVOTModeEntry(uvot_mode=0x30ED, filter_name=""),
        SwiftUVOTModeEntry(uvot_mode=0x30ED, filter_name=""),
    ]


@pytest.fixture
def uvot_mode_with_two_entries(uvot_mode_empty, sample_uvot_entries):
    """SwiftUVOTMode instance with two sample entries."""
    uvot_mode_empty.entries = sample_uvot_entries
    return uvot_mode_empty


@pytest.fixture
def uvot_mode_with_three_entries(uvot_mode_empty):
    """SwiftUVOTMode instance with three entries."""
    entries = [
        SwiftUVOTModeEntry(uvot_mode=0x30ED, filter_name=""),
        SwiftUVOTModeEntry(uvot_mode=0x30ED, filter_name=""),
        SwiftUVOTModeEntry(uvot_mode=0x30ED, filter_name=""),
    ]
    uvot_mode_empty.entries = entries
    return uvot_mode_empty
