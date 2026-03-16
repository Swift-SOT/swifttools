from datetime import timedelta

import pytest

from swifttools.swift_too.swift.planquery import SwiftPPSTEntry, SwiftPPSTGetSchema


class TestSwiftPPSTEntry:
    def test_init_target_name(self, full_entry):
        entry = full_entry
        assert entry.target_name == "Test Target"

    def test_init_ra(self, full_entry):
        entry = full_entry
        assert entry.ra == 10.0

    def test_init_dec(self, full_entry):
        entry = full_entry
        assert entry.dec == 20.0

    def test_init_roll(self, full_entry):
        entry = full_entry
        assert entry.roll == 30.0

    def test_init_begin(self, full_entry, begin_datetime):
        entry = full_entry
        assert entry.begin == begin_datetime

    def test_init_end(self, full_entry, end_datetime):
        entry = full_entry
        assert entry.end == end_datetime

    def test_init_target_id(self, full_entry):
        entry = full_entry
        assert entry.target_id == 123

    def test_init_segment(self, full_entry):
        entry = full_entry
        assert entry.segment == 1

    def test_init_obs_id(self, full_entry):
        entry = full_entry
        assert entry.obs_id == "00012345678"

    def test_init_bat_mode(self, full_entry):
        entry = full_entry
        assert entry.bat_mode == 1

    def test_init_xrt_mode(self, full_entry):
        entry = full_entry
        assert entry.xrt_mode == 7

    def test_init_uvot_mode(self, full_entry):
        entry = full_entry
        assert entry.uvot_mode == 0x9999

    def test_init_fom(self, full_entry):
        entry = full_entry
        assert entry.fom == 0.5

    def test_init_comment(self, full_entry):
        entry = full_entry
        assert entry.comment == "Test comment"

    def test_init_timetarg(self, full_entry):
        entry = full_entry
        assert entry.timetarg == 100

    def test_init_takodb(self, full_entry):
        entry = full_entry
        assert entry.takodb == "test"

    def test_exposure_property(self, simple_entry):
        entry = simple_entry
        assert entry.exposure == timedelta(hours=1)

    def test_table_property_header(self, entry_with_name_and_obs):
        entry = entry_with_name_and_obs
        header, data = entry._table
        assert header == ["Begin Time", "End Time", "Target Name", "Observation Number", "Exposure (s)"]

    def test_table_property_data(self, entry_with_name_and_obs, begin_datetime, end_datetime):
        entry = entry_with_name_and_obs
        header, data = entry._table
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

    def test_table_property_empty_header(self, ppst):
        header, data = ppst._table
        assert header == []

    def test_table_property_empty_data(self, ppst):
        header, data = ppst._table
        assert data == []

    def test_table_property_with_entries_header(self, ppst, entry_with_name_and_obs):
        ppst.entries = [entry_with_name_and_obs]
        header, data = ppst._table
        assert header == ["Begin Time", "End Time", "Target Name", "Observation Number", "Exposure (s)"]

    def test_table_property_with_entries_data_length(self, ppst, entry_with_name_and_obs):
        ppst.entries = [entry_with_name_and_obs]
        header, data = ppst._table
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
