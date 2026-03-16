# Local fixtures for tests/swift_too/swift/planquery

from datetime import datetime

import pytest

from swifttools.swift_too.swift.planquery import SwiftPPST, SwiftPPSTEntry


@pytest.fixture
def begin_datetime():
    return datetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def end_datetime():
    return datetime(2023, 1, 1, 13, 0, 0)


@pytest.fixture
def full_entry(begin_datetime, end_datetime):
    return SwiftPPSTEntry(
        target_name="Test Target",
        ra=10.0,
        dec=20.0,
        roll=30.0,
        begin=begin_datetime,
        end=end_datetime,
        target_id=123,
        segment=1,
        obs_id="00012345678",
        bat_mode=1,
        xrt_mode=7,
        uvot_mode=0x9999,
        fom=0.5,
        comment="Test comment",
        timetarg=100,
        takodb="test",
    )


@pytest.fixture
def simple_entry(begin_datetime, end_datetime):
    return SwiftPPSTEntry(begin=begin_datetime, end=end_datetime)


@pytest.fixture
def entry_with_name_and_obs(begin_datetime, end_datetime):
    return SwiftPPSTEntry(begin=begin_datetime, end=end_datetime, target_name="Test", obs_id="00012345678")


@pytest.fixture
def entry_with_obs_id():
    return SwiftPPSTEntry(obs_id="00012345678")


@pytest.fixture
def ppst():
    return SwiftPPST(autosubmit=False)


@pytest.fixture
def basic_entry():
    return SwiftPPSTEntry(target_name="Test")


@pytest.fixture
def test_datetime():
    return datetime(2023, 1, 1)
