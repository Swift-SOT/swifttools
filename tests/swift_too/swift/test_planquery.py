from datetime import datetime, timedelta

import pytest

from swifttools.swift_too.swift.planquery import SwiftPPST, SwiftPPSTEntry, SwiftPPSTGetSchema


class TestSwiftPPSTEntry:
    def test_init(self):
        entry = SwiftPPSTEntry(
            target_name="Test Target",
            ra=10.0,
            dec=20.0,
            roll=30.0,
            begin=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 13, 0, 0),
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
        assert entry.target_name == "Test Target"
        assert entry.ra == 10.0
        assert entry.dec == 20.0
        assert entry.roll == 30.0
        assert entry.begin == datetime(2023, 1, 1, 12, 0, 0)
        assert entry.end == datetime(2023, 1, 1, 13, 0, 0)
        assert entry.target_id == 123
        assert entry.segment == 1
        assert entry.obs_id == "00012345678"
        assert entry.bat_mode == 1
        assert entry.xrt_mode == 7
        assert entry.uvot_mode == 0x9999
        assert entry.fom == 0.5
        assert entry.comment == "Test comment"
        assert entry.timetarg == 100
        assert entry.takodb == "test"

    def test_exposure_property(self):
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftPPSTEntry(begin=begin, end=end)
        assert entry.exposure == timedelta(hours=1)

    def test_table_property(self):
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftPPSTEntry(begin=begin, end=end, target_name="Test", obs_id="00012345678")
        header, data = entry._table
        assert header == ["Begin Time", "End Time", "Target Name", "Observation Number", "Exposure (s)"]
        assert data == [[begin, end, "Test", "00012345678", 3600]]


class TestSwiftPPSTGetSchema:
    def test_valid_schema(self):
        schema = SwiftPPSTGetSchema(begin=datetime(2023, 1, 1))
        assert schema.begin == datetime(2023, 1, 1)

    def test_invalid_schema_no_fields(self):
        with pytest.raises(ValueError, match="At least one of"):
            SwiftPPSTGetSchema()


class TestSwiftPPST:
    def test_init(self):
        ppst = SwiftPPST(autosubmit=False)
        assert ppst.entries == []

    def test_table_property_empty(self):
        ppst = SwiftPPST(autosubmit=False)
        header, data = ppst._table
        assert header == []
        assert data == []

    def test_table_property_with_entries(self):
        ppst = SwiftPPST(autosubmit=False)
        entry = SwiftPPSTEntry(
            begin=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 13, 0, 0),
            target_name="Test",
            obs_id="00012345678",
        )
        ppst.entries = [entry]
        header, data = ppst._table
        assert header == ["Begin Time", "End Time", "Target Name", "Observation Number", "Exposure (s)"]
        assert len(data) == 1

    def test_observations_property(self):
        ppst = SwiftPPST(autosubmit=False)
        entry = SwiftPPSTEntry(obs_id="00012345678")
        ppst.entries = [entry]
        obs = ppst.observations
        assert "00012345678" in obs

    def test_getitem(self):
        ppst = SwiftPPST(autosubmit=False)
        entry = SwiftPPSTEntry(target_name="Test")
        ppst.entries = [entry]
        assert ppst[0] == entry

    def test_len(self):
        ppst = SwiftPPST(autosubmit=False)
        ppst.entries = [SwiftPPSTEntry(), SwiftPPSTEntry()]
        assert len(ppst) == 2
