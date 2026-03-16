# Local fixtures for tests/swift_too/swift/swift_obsquery
from datetime import datetime

import pytest

from swifttools.swift_too.swift.obsquery import SwiftAFST, SwiftAFSTEntry, SwiftObservation


@pytest.fixture
def basic_afst_entry():
    """Basic SwiftAFSTEntry with minimal parameters."""
    return SwiftAFSTEntry(ra=266, dec=-29)


@pytest.fixture
def full_afst_entry():
    """SwiftAFSTEntry with all test parameters."""
    return SwiftAFSTEntry(
        begin=datetime(2023, 1, 1, 12, 0, 0),
        settle=datetime(2023, 1, 1, 12, 1, 0),
        end=datetime(2023, 1, 1, 12, 10, 0),
        target_name="Test Target",
        target_id=12345,
        segment=1,
        obs_id="00012345001",
        ra=123.456,
        dec=78.901,
    )


@pytest.fixture
def swift_afst():
    """SwiftAFST instance for testing."""
    return SwiftAFST(autosubmit=False)


@pytest.fixture
def swift_observation():
    """SwiftObservation instance for testing."""
    return SwiftObservation()


@pytest.fixture
def sample_afst_entries():
    """List of sample SwiftAFSTEntry objects for testing."""
    return [
        SwiftAFSTEntry(
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 5, 0),
            target_id=12345,
            segment=1,
            obs_id="00012345001",
            target_name="Test Target",
            ra_object=123.456,
            dec_object=78.901,
            xrt_mode=0,
            uvot_mode=261,
            bat_mode=1,
            ra=266,
            dec=-29,
        ),
        SwiftAFSTEntry(
            begin=datetime(2023, 1, 1, 12, 10, 0),
            settle=datetime(2023, 1, 1, 12, 11, 0),
            end=datetime(2023, 1, 1, 12, 15, 0),
            target_id=12345,
            segment=1,
            obs_id="00012345002",
            target_name="Test Target 2",
            ra_object=123.456,
            dec_object=78.901,
            xrt_mode=0,
            uvot_mode=261,
            bat_mode=1,
            ra=266,
            dec=-29,
        ),
    ]


@pytest.fixture
def swift_observation_with_entries(sample_afst_entries):
    """SwiftObservation instance with sample entries."""
    return SwiftObservation(entries=sample_afst_entries)
