# Local fixtures for tests/swift_too/swift/guano
from datetime import datetime

import pytest

from swifttools.swift_too.swift.guano import (
    SwiftGUANO,
    SwiftGUANOData,
    SwiftGUANOEntry,
    SwiftGUANOGTI,
)


@pytest.fixture
def guano():
    return SwiftGUANO(autosubmit=False)


@pytest.fixture
def entry():
    return SwiftGUANOEntry()


@pytest.fixture
def data():
    return SwiftGUANOData(all_gtis=[])


@pytest.fixture
def gti():
    return SwiftGUANOGTI()


@pytest.fixture
def mock_data():
    return type("MockData", (), {"exposure": 5.0, "gti": None, "all_gtis": []})()


@pytest.fixture
def mock_data_none():
    return type("MockData", (), {"exposure": None, "gti": None, "all_gtis": []})()


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"_calc_begin_end": lambda self: None})()


@pytest.fixture
def sample_guano_entries():
    """List of sample SwiftGUANOEntry objects for testing."""
    return [
        SwiftGUANOEntry(
            triggertype="GRB", triggertime=datetime(2023, 1, 1), offset=10.0, duration=5.0, obs_id="00012345001"
        ),
        SwiftGUANOEntry(
            triggertype="GRB", triggertime=datetime(2023, 1, 2), offset=20.0, duration=6.0, obs_id="00012345002"
        ),
    ]


@pytest.fixture
def guano_with_entries(guano, sample_guano_entries):
    """SwiftGUANO instance with sample entries."""
    guano.entries = sample_guano_entries
    return guano


@pytest.fixture
def guano_with_three_entries(guano):
    """SwiftGUANO instance with three entries."""
    entries = [
        SwiftGUANOEntry(
            triggertype="GRB",
            triggertime=datetime(2023, 1, i + 1),
            offset=10.0 * i,
            duration=5.0,
            obs_id=f"0001234500{i}",
        )
        for i in range(3)
    ]
    guano.entries = entries
    return guano


@pytest.fixture
def guano_entry_with_data():
    """SwiftGUANOEntry with associated data for table testing."""
    entry = SwiftGUANOEntry(
        triggertype="GRB",
        triggertime=datetime(2023, 1, 1, 12, 0, 0),
        offset=10.0,
        duration=5.0,
        obs_id="00012345001",
        quadsaway=0,
    )
    entry.data = SwiftGUANOData(exposure=5.0, all_gtis=[])
    return entry


@pytest.fixture
def guano_with_table_entry(guano, guano_entry_with_data):
    """SwiftGUANO instance with one entry for table testing."""
    guano.entries = [guano_entry_with_data]
    return guano
