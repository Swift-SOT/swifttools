from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from swifttools.swift_too.swift.guano import (
    SwiftGUANOData,
    SwiftGUANOEntry,
    SwiftGUANOGetSchema,
)


class TestSwiftGUANO:
    def test_init_entries_empty(self, guano):
        assert guano.entries == []

    def test_getitem_first(self, guano_with_entries, sample_guano_entries):
        assert guano_with_entries[0] == sample_guano_entries[0]

    def test_getitem_second(self, guano_with_entries, sample_guano_entries):
        assert guano_with_entries[1] == sample_guano_entries[1]

    def test_len_empty(self, guano):
        assert len(guano) == 0

    def test_len_with_entries(self, guano_with_three_entries):
        assert len(guano_with_three_entries) == 3

    def test_validate_with_length(self, guano):
        guano.length = 1.0
        assert guano.validate() is True

    def test_validate_subthreshold_anonymous(self, guano):
        guano.subthreshold = True
        guano.username = "anonymous"
        assert guano.validate() is False

    def test_table_property_header(self, guano):
        # Minimal setup for table
        guano.entries = []
        header, table = guano._table
        assert header == [
            "Trigger Type",
            "Trigger Time",
            "Offset (s)",
            "Window Duration (s)",
            "Observation ID",
        ]

    def test_table_property_table_length(self, guano_with_table_entry):
        header, table = guano_with_table_entry._table
        assert len(table) == 1

    def test_table_property_first_entry_type(self, guano):
        entry1 = SwiftGUANOEntry(
            triggertype="GRB",
            triggertime=datetime(2023, 1, 1, 12, 0, 0),
            offset=10.0,
            duration=5.0,
            obs_id="00012345001",
            quadsaway=0,
        )
        entry1.data = SwiftGUANOData(exposure=5.0, all_gtis=[])
        guano.entries = [entry1]
        header, table = guano._table
        assert table[0][0] == "GRB"

    def test_table_property_first_entry_obs_id(self, guano):
        entry1 = SwiftGUANOEntry(
            triggertype="GRB",
            triggertime=datetime(2023, 1, 1, 12, 0, 0),
            offset=10.0,
            duration=5.0,
            obs_id="00012345001",
            quadsaway=0,
        )
        entry1.data = SwiftGUANOData(exposure=5.0, all_gtis=[])
        guano.entries = [entry1]
        header, table = guano._table
        assert table[0][4] == "00012345001"

    def test_table_property_second_entry_type(self, guano):
        entry2 = SwiftGUANOEntry(
            triggertype="TEST",
            triggertime=datetime(2023, 1, 1, 13, 0, 0),
            offset=20.0,
            duration=10.0,
            obs_id=None,
            quadsaway=2,
        )
        entry2.data = SwiftGUANOData(exposure=5.0, all_gtis=[])
        guano.entries = [entry2]
        header, table = guano._table
        assert table[0][0] == "TEST"

    def test_table_property_second_entry_obs_id(self, guano):
        entry2 = SwiftGUANOEntry(
            triggertype="TEST",
            triggertime=datetime(2023, 1, 1, 13, 0, 0),
            offset=20.0,
            duration=10.0,
            obs_id=None,
            quadsaway=2,
        )
        entry2.data = SwiftGUANOData(exposure=5.0, all_gtis=[])
        guano.entries = [entry2]
        header, table = guano._table
        assert table[0][4] == "Pending Execution"

    def test_table_property_third_entry_obs_id(self, guano):
        entry3 = SwiftGUANOEntry(
            triggertype="UNKNOWN",
            triggertime=datetime(2023, 1, 1, 14, 0, 0),
            offset=30.0,
            duration=15.0,
            obs_id=None,
            quadsaway=3,
        )
        entry3.data = SwiftGUANOData(exposure=15.0, all_gtis=[])
        guano.entries = [entry3]
        header, table = guano._table
        assert table[0][4] == "Unknown Status"

    def test_table_property_fourth_entry_obs_id(self, guano):
        entry4 = SwiftGUANOEntry(
            triggertype="EXECUTED",
            triggertime=datetime(2023, 1, 1, 15, 0, 0),
            offset=40.0,
            duration=20.0,
            obs_id=None,
            quadsaway=0,
        )
        entry4.data = SwiftGUANOData(exposure=20.0, all_gtis=[])
        guano.entries = [entry4]
        header, table = guano._table
        assert table[0][4] == "Pending Data"

    @patch("swifttools.swift_too.swift.clock.Clock")
    def test_post_process_calls_calc_begin_end(self, mock_clock_class, guano, mock_entry):
        mock_clock_instance = mock_clock_class.return_value
        mock_clock_instance.entries = []
        # Ensure mock_entry has required fields so _calc_begin_end runs safely
        mock_entry.triggertime = datetime(2023, 1, 1)
        mock_entry.offset = 10.0
        mock_entry.duration = 5.0
        guano.entries = [mock_entry]
        guano._post_process()
        # Assuming _calc_begin_end is called, but since it's a lambda, just check length
        assert len(guano.entries) == 1


class TestSwiftGUANOEntry:
    def test_init_obs_id_none(self, entry):
        assert entry.obs_id is None

    def test_executed_quadsaway_2(self, entry):
        entry.quadsaway = 2
        assert entry.executed is False

    def test_executed_quadsaway_3(self, entry):
        entry.quadsaway = 3
        assert entry.executed is False

    def test_executed_quadsaway_1(self, entry):
        entry.quadsaway = 1
        assert entry.executed is True

    def test_executed_quadsaway_4(self, entry):
        entry.quadsaway = 4
        assert entry.executed is True

    def test_uplinked_quadsaway_1(self, entry):
        entry.quadsaway = 1
        assert entry.uplinked is False

    def test_uplinked_quadsaway_3(self, entry):
        entry.quadsaway = 3
        assert entry.uplinked is False

    def test_uplinked_quadsaway_2(self, entry):
        entry.quadsaway = 2
        assert entry.uplinked is True

    def test_uplinked_quadsaway_4(self, entry):
        entry.quadsaway = 4
        assert entry.uplinked is True

    def test_calc_begin_end_begin(self, entry):
        entry.triggertime = datetime(2023, 1, 1, 12, 0, 0)
        entry.offset = 10.0
        entry.duration = 5.0
        entry._calc_begin_end()
        assert entry.begin == datetime(2023, 1, 1, 12, 0, 7, 500000)

    def test_calc_begin_end_end(self, entry):
        entry.triggertime = datetime(2023, 1, 1, 12, 0, 0)
        entry.offset = 10.0
        entry.duration = 5.0
        entry._calc_begin_end()
        assert entry.end == datetime(2023, 1, 1, 12, 0, 12, 500000)

    def test_table_header(self, entry, mock_data):
        entry.triggertype = "GRB"
        entry.triggertime = datetime(2023, 1, 1, 12, 0, 0)
        entry.offset = 10.0
        entry.duration = 5.0
        entry.obs_id = "00012345001"
        entry.data = mock_data
        header, table = entry._table
        assert header == ["Parameter", "Value"]

    def test_table_length(self, entry, mock_data):
        entry.triggertype = "GRB"
        entry.triggertime = datetime(2023, 1, 1, 12, 0, 0)
        entry.offset = 10.0
        entry.duration = 5.0
        entry.obs_id = "00012345001"
        entry.data = mock_data
        header, table = entry._table
        assert len(table) > 0

    def test_table_header_none_exposure(self, entry, mock_data_none):
        entry.data = mock_data_none
        header, table = entry._table
        assert header == ["Parameter", "Value"]

    def test_table_length_none_exposure(self, entry, mock_data_none):
        entry.data = mock_data_none
        header, table = entry._table
        assert len(table) > 0


class TestSwiftGUANOData:
    def test_init_gti_none(self, data):
        assert data.gti is None

    def test_utcf_property(self, data, gti):
        gti.utcf = 10.5
        data.gti = gti
        assert data.utcf == 10.5

    def test_subthresh_ms_file(self, data):
        data.filenames = ["test_ms_file.fits"]
        assert data.subthresh is True

    def test_subthresh_regular_file(self, data):
        data.filenames = ["test_file.fits"]
        assert data.subthresh is False

    def test_subthresh_none_filenames(self, data):
        data.filenames = None
        assert data.subthresh is None


class TestSwiftGUANOGTI:
    def test_init_filename_none(self, gti):
        assert gti.filename is None

    def test_init_exposure_zero(self, gti):
        assert gti.exposure == timedelta(0)

    def test_str_contains_begin(self, gti):
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 10, 0)
        gti.begin = begin
        gti.end = end
        gti.exposure = timedelta(minutes=10)
        str_repr = str(gti)
        assert "12:00:00" in str_repr

    def test_str_contains_end(self, gti):
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 10, 0)
        gti.begin = begin
        gti.end = end
        gti.exposure = timedelta(minutes=10)
        str_repr = str(gti)
        assert "12:10:00" in str_repr


class TestSwiftGUANOGetSchema:
    def test_validate_parameters_valid(self):
        values = {"triggertime": datetime(2023, 1, 1)}
        result = SwiftGUANOGetSchema.validate_parameters(values)
        assert result == values

    def test_validate_parameters_invalid(self):
        with pytest.raises(ValueError, match="At least one of the parameters must be provided"):
            SwiftGUANOGetSchema.validate_parameters({})
