# Local fixtures for tests/swift_too/swift/saa
from datetime import datetime

import pytest

from swifttools.swift_too.swift.saa import SwiftSAA, SwiftSAAEntry


@pytest.fixture
def begin_datetime():
    """Sample begin datetime for SAA entries."""
    return datetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def end_datetime():
    """Sample end datetime for SAA entries."""
    return datetime(2023, 1, 1, 13, 0, 0)


@pytest.fixture
def swift_saa():
    """SwiftSAA instance for testing."""
    return SwiftSAA(autosubmit=False)


@pytest.fixture
def sample_saa_entry(begin_datetime, end_datetime):
    """Sample SwiftSAAEntry for testing."""
    return SwiftSAAEntry(begin=begin_datetime, end=end_datetime)


@pytest.fixture
def sample_saa_entries(begin_datetime, end_datetime):
    """List of sample SwiftSAAEntry instances for testing."""
    entry1 = SwiftSAAEntry(begin=begin_datetime, end=end_datetime)
    entry2 = SwiftSAAEntry(begin=datetime(2023, 1, 2, 12, 0, 0), end=datetime(2023, 1, 2, 13, 0, 0))
    return [entry1, entry2]
