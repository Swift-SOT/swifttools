from datetime import timedelta

import pytest

from swifttools.swift_too.swift.planquery import SwiftPPSTEntry, SwiftPPSTGetSchema


class TestSwiftPPSTEntry:
    def test_init(self, full_entry, begin_datetime, end_datetime):
        entry = full_entry
        assert entry.target_name == "Test Target"
        assert entry.ra == 10.0
        assert entry.dec == 20.0
        assert entry.roll == 30.0
        assert entry.begin == begin_datetime
        assert entry.end == end_datetime
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

    def test_exposure_property(self, simple_entry):
        entry = simple_entry
        assert entry.exposure == timedelta(hours=1)

    def test_table_property(self, entry_with_name_and_obs, begin_datetime, end_datetime):
        entry = entry_with_name_and_obs
        header, data = entry._table
        assert header == ["Begin Time", "End Time", "Target Name", "Observation Number", "Exposure (s)"]
        assert data == [[begin_datetime, end_datetime, "Test", "00012345678", 3600]]


class TestSwiftPPSTGetSchema:
    def test_valid_schema(self, test_datetime):
        schema = SwiftPPSTGetSchema(begin=test_datetime)
        assert schema.begin == test_datetime

    def test_invalid_schema_no_fields(self):
        with pytest.raises(ValueError, match="At least one of"):
            SwiftPPSTGetSchema()


class TestSwiftPPST:
    def test_init(self, ppst):
        assert ppst.entries == []

    def test_table_property_empty(self, ppst):
        header, data = ppst._table
        assert header == []
        assert data == []

    def test_table_property_with_entries(self, ppst, entry_with_name_and_obs):
        ppst.entries = [entry_with_name_and_obs]
        header, data = ppst._table
        assert header == ["Begin Time", "End Time", "Target Name", "Observation Number", "Exposure (s)"]
        assert len(data) == 1

    def test_observations_property(self, ppst, entry_with_obs_id):
        ppst.entries = [entry_with_obs_id]
        obs = ppst.observations
        assert "00012345678" in obs

    def test_getitem(self, ppst, basic_entry):
        ppst.entries = [basic_entry]
        assert ppst[0] == basic_entry

    def test_len(self, ppst):
        ppst.entries = [SwiftPPSTEntry(), SwiftPPSTEntry()]
        assert len(ppst) == 2
