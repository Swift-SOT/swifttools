from datetime import datetime, timedelta
from unittest.mock import patch

import numpy as np
import pytest
from pydantic import ValidationError

from swifttools.swift_too.swift.obsquery import (
    AFST,
    AFSTEntry,
    ObsEntry,
    ObsQuery,
    Swift_AFST,
    Swift_AFST_Entry,
    Swift_AFSTEntry,
    Swift_ObsEntry,
    Swift_Observation,
    Swift_Observations,
    Swift_ObsQuery,
    SwiftAFST,
    SwiftAFSTEntry,
    SwiftAFSTGetSchema,
    SwiftAFSTSchema,
    SwiftObservation,
    SwiftObservations,
)


class TestSwiftAFSTEntry:
    def test_init_begin(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.begin == datetime(2023, 1, 1, 12, 0, 0)

    def test_init_settle(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.settle == datetime(2023, 1, 1, 12, 1, 0)

    def test_init_end(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.end == datetime(2023, 1, 1, 12, 10, 0)

    def test_init_target_name(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.target_name == "Test Target"

    def test_init_targname_alias(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.targname == "Test Target"

    def test_init_target_id(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.target_id == 12345

    def test_init_segment(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.segment == 1

    def test_init_obs_id(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.obs_id == "00012345001"

    def test_init_ra(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.ra == 123.456

    def test_init_dec(self, full_afst_entry):
        """Test basic initialization of SwiftAFSTEntry."""
        assert full_afst_entry.dec == 78.901

    def test_exposure_property(self):
        """Test exposure property calculation."""
        entry = SwiftAFSTEntry(
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
            ra=266,
            dec=-29,
        )

        exposure = entry.exposure
        assert exposure == timedelta(minutes=9)

    def test_slewtime_property(self):
        """Test slewtime property calculation."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
        )

        slewtime = entry.slewtime
        assert slewtime == timedelta(minutes=1)

    def test_table_property_header_type(self):
        """Test _table property."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
            targname="Test Target",
            obs_id="00012345001",
        )

        header, data = entry._table
        assert isinstance(header, list)

    def test_table_property_data_type(self):
        """Test _table property."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
            targname="Test Target",
            obs_id="00012345001",
        )

        header, data = entry._table
        assert isinstance(data, list)

    def test_table_property_data_length(self):
        """Test _table property."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
            targname="Test Target",
            obs_id="00012345001",
        )

        header, data = entry._table
        assert len(data) == 1

    def test_table_property_row_length(self):
        """Test _table property."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
            targname="Test Target",
            obs_id="00012345001",
        )

        header, data = entry._table
        assert len(data[0]) == 6

    def test_varnames_contains_begin(self, basic_afst_entry):
        """Test _varnames contains expected keys."""
        assert "begin" in basic_afst_entry._varnames

    def test_varnames_contains_target_name(self, basic_afst_entry):
        """Test _varnames contains expected keys."""
        assert "target_name" in basic_afst_entry._varnames

    def test_varnames_contains_exposure(self, basic_afst_entry):
        """Test _varnames contains expected keys."""
        assert "exposure" in basic_afst_entry._varnames

    def test_varnames_begin_label(self, basic_afst_entry):
        """Test _varnames contains expected keys."""
        assert basic_afst_entry._varnames["begin"] == "Begin Time"

    def test_varnames_target_name_label(self, basic_afst_entry):
        """Test _varnames contains expected keys."""
        assert basic_afst_entry._varnames["target_name"] == "Target Name"

    def test_optional_obstype(self):
        """Test setting optional parameters."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            obstype="TOO",
            roll=45.0,
            bat_mode=1,
            xrt_mode=0,
            uvot_mode=261,
            fom=100,
            comment="Test observation",
        )

        assert entry.obstype == "TOO"

    def test_optional_roll(self):
        """Test setting optional parameters."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            obstype="TOO",
            roll=45.0,
            bat_mode=1,
            xrt_mode=0,
            uvot_mode=261,
            fom=100,
            comment="Test observation",
        )

        assert entry.roll == 45.0

    def test_optional_bat_mode(self):
        """Test setting optional parameters."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            obstype="TOO",
            roll=45.0,
            bat_mode=1,
            xrt_mode=0,
            uvot_mode=261,
            fom=100,
            comment="Test observation",
        )

        assert entry.bat_mode == 1

    def test_optional_xrt_mode(self):
        """Test setting optional parameters."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            obstype="TOO",
            roll=45.0,
            bat_mode=1,
            xrt_mode=0,
            uvot_mode=261,
            fom=100,
            comment="Test observation",
        )

        assert entry.xrt_mode == 0

    def test_optional_uvot_mode(self):
        """Test setting optional parameters."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            obstype="TOO",
            roll=45.0,
            bat_mode=1,
            xrt_mode=0,
            uvot_mode=261,
            fom=100,
            comment="Test observation",
        )

        assert entry.uvot_mode == 261

    def test_optional_fom(self):
        """Test setting optional parameters."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            obstype="TOO",
            roll=45.0,
            bat_mode=1,
            xrt_mode=0,
            uvot_mode=261,
            fom=100,
            comment="Test observation",
        )

        assert entry.fom == 100

    def test_optional_comment(self):
        """Test setting optional parameters."""
        entry = SwiftAFSTEntry(
            ra=266,
            dec=-29,
            obstype="TOO",
            roll=45.0,
            bat_mode=1,
            xrt_mode=0,
            uvot_mode=261,
            fom=100,
            comment="Test observation",
        )

        assert entry.comment == "Test observation"


class TestSwiftObservation:
    def create_sample_entries(self):
        """Create sample SwiftAFSTEntry objects for testing."""
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
        ]

    def test_init_empty(self):
        """Test initialization with no entries."""
        obs = SwiftObservation()
        assert len(obs) == 0
        assert obs.entries == []

    def test_init_with_entries_length(self):
        """Test initialization with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert len(obs) == 2

    def test_init_with_entries_assignment(self):
        """Test initialization with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert obs.entries == entries

    def test_list_methods_append_length(self, swift_observation, basic_afst_entry):
        """Test list-like methods."""
        swift_observation.append(basic_afst_entry)
        assert len(swift_observation) == 1

    def test_list_methods_append_access(self, swift_observation, basic_afst_entry):
        """Test list-like methods."""
        swift_observation.append(basic_afst_entry)
        assert swift_observation[0] == basic_afst_entry

    def test_list_methods_extend_length(self, swift_observation, basic_afst_entry, sample_afst_entries):
        """Test list-like methods."""
        swift_observation.append(basic_afst_entry)
        swift_observation.extend(sample_afst_entries)
        assert len(swift_observation) == 3

    def test_computed_properties_empty_target_id(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.target_id is None

    def test_computed_properties_empty_seg(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.seg is None

    def test_computed_properties_empty_obs_id(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.obs_id is None

    def test_computed_properties_empty_targname(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.targname is None

    def test_computed_properties_empty_ra_object(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.ra_object is None

    def test_computed_properties_empty_dec_object(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.dec_object is None

    def test_computed_properties_empty_exposure(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.exposure is None

    def test_computed_properties_empty_slewtime(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.slewtime is None

    def test_computed_properties_empty_begin(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.begin is None

    def test_computed_properties_empty_end(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.end is None

    def test_computed_properties_empty_xrt(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.xrt is None

    def test_computed_properties_empty_uvot(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.uvot is None

    def test_computed_properties_empty_bat(self, swift_observation):
        """Test computed properties with empty observation."""
        assert swift_observation.bat is None

    def test_computed_properties_with_entries_target_id(self, swift_observation_with_entries):
        """Test computed properties with entries."""
        assert swift_observation_with_entries.target_id == 12345

    def test_computed_properties_with_entries_segment(self, swift_observation_with_entries):
        """Test computed properties with entries."""
        assert swift_observation_with_entries.segment == 1

    def test_computed_properties_with_entries_obs_id(self, swift_observation_with_entries):
        """Test computed properties with entries."""
        assert swift_observation_with_entries.obs_id == "00012345001"

    def test_computed_properties_with_entries_target_name(self):
        """Test computed properties with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.target_name == "Test Target"

    def test_computed_properties_with_entries_ra_object(self):
        """Test computed properties with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.ra_object == 123.456

    def test_computed_properties_with_entries_dec_object(self):
        """Test computed properties with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.dec_object == 78.901

    def test_computed_properties_with_entries_xrt_mode(self):
        """Test computed properties with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.xrt_mode == 0

    def test_computed_properties_with_entries_uvot_mode(self):
        """Test computed properties with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.uvot_mode == 261

    def test_computed_properties_with_entries_bat_mode(self):
        """Test computed properties with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.bat_mode == 1

    def test_time_aggregation_begin(self):
        """Test time aggregation properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        # Begin should be earliest begin time
        assert obs.begin == datetime(2023, 1, 1, 12, 0, 0)

    def test_time_aggregation_end(self):
        """Test time aggregation properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        # End should be latest end time
        assert obs.end == datetime(2023, 1, 1, 12, 15, 0)

    def test_time_aggregation_exposure(self):
        """Test time aggregation properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        # Exposure should sum individual exposures (4 min + 4 min = 8 min)
        assert obs.exposure == timedelta(minutes=8)

    def test_time_aggregation_slewtime(self):
        """Test time aggregation properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        # Slewtime should sum individual slewtimes (1 min + 1 min = 2 min)
        assert obs.slewtime == timedelta(minutes=2)

    def test_snapshots_property(self):
        """Test snapshots property."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert obs.snapshots == entries

    def test_compatibility_properties_ra_point(self):
        """Test ra_point and dec_point compatibility properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.ra_point == obs.ra_object

    def test_compatibility_properties_dec_point(self):
        """Test ra_point and dec_point compatibility properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.dec_point == obs.dec_object

    def test_aliases_obsid(self):
        """Test property aliases."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.obsid == obs.obs_id

    def test_aliases_target_id(self):
        """Test property aliases."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.target_id == obs.target_id

    def test_aliases_segment(self):
        """Test property aliases."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        assert obs.segment == obs.seg

    def test_table_property_header_type(self):
        """Test _table property."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        header, data = obs._table
        assert isinstance(header, list)

    def test_table_property_data_type(self):
        """Test _table property."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        header, data = obs._table
        assert isinstance(data, list)

    def test_table_property_data_length(self):
        """Test _table property."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)
        header, data = obs._table
        assert len(data) == 1


class TestSwiftObservations:
    def test_init_empty(self):
        """Test initialization of empty SwiftObservations."""
        obs_dict = SwiftObservations()
        assert len(obs_dict) == 0

    def test_dict_functionality_length(self):
        """Test dictionary functionality."""
        obs_dict = SwiftObservations()
        obs = SwiftObservation()
        obs_dict["00012345001"] = obs
        assert len(obs_dict) == 1

    def test_dict_functionality_access(self):
        """Test dictionary functionality."""
        obs_dict = SwiftObservations()
        obs = SwiftObservation()
        obs_dict["00012345001"] = obs
        assert obs_dict["00012345001"] == obs

    def test_table_property_empty_header(self):
        """Test _table property with empty dictionary."""
        obs_dict = SwiftObservations()
        header, data = obs_dict._table
        assert header == []

    def test_table_property_empty_data(self):
        """Test _table property with empty dictionary."""
        obs_dict = SwiftObservations()
        header, data = obs_dict._table
        assert data == []


class TestSwiftAFST:
    def test_init_with_basic_parameters_ra(self):
        """Test basic initialization of SwiftAFST."""
        afst = SwiftAFST(
            ra=123.456, dec=78.901, radius=0.5, begin=datetime(2023, 1, 1), end=datetime(2023, 1, 2), autosubmit=False
        )
        assert np.isclose(afst.ra, 123.456)

    def test_init_with_basic_parameters_dec(self):
        """Test basic initialization of SwiftAFST."""
        afst = SwiftAFST(
            ra=123.456, dec=78.901, radius=0.5, begin=datetime(2023, 1, 1), end=datetime(2023, 1, 2), autosubmit=False
        )
        assert np.isclose(afst.dec, 78.901)

    def test_init_with_basic_parameters_radius(self):
        """Test basic initialization of SwiftAFST."""
        afst = SwiftAFST(
            ra=123.456, dec=78.901, radius=0.5, begin=datetime(2023, 1, 1), end=datetime(2023, 1, 2), autosubmit=False
        )
        assert np.isclose(afst.radius, 0.5)

    def test_init_with_basic_parameters_begin(self):
        """Test basic initialization of SwiftAFST."""
        afst = SwiftAFST(
            ra=123.456, dec=78.901, radius=0.5, begin=datetime(2023, 1, 1), end=datetime(2023, 1, 2), autosubmit=False
        )
        assert afst.begin == datetime(2023, 1, 1)

    def test_init_with_basic_parameters_end(self):
        """Test basic initialization of SwiftAFST."""
        afst = SwiftAFST(
            ra=123.456, dec=78.901, radius=0.5, begin=datetime(2023, 1, 1), end=datetime(2023, 1, 2), autosubmit=False
        )
        assert afst.end == datetime(2023, 1, 2)

    def test_default_values_radius(self, swift_afst):
        """Test default values."""
        assert swift_afst.radius is None  # Default radius is None when no ra/dec

    def test_default_values_target_id(self, swift_afst):
        """Test default values."""
        assert swift_afst.target_id is None

    def test_default_values_obs_id(self, swift_afst):
        """Test default values."""
        assert swift_afst.obs_id is None

    def test_default_values_entries(self, swift_afst):
        """Test default values."""
        assert swift_afst.entries == []

    def test_api_properties_api_name(self, swift_afst):
        """Test API-related properties."""
        assert swift_afst.api_name == "Swift_AFST"

    def test_api_properties_endpoint(self, swift_afst):
        """Test API-related properties."""
        assert swift_afst._endpoint == "/swift/obsquery"

    def test_api_properties_has_schema(self, swift_afst):
        """Test API-related properties."""
        assert hasattr(swift_afst, "_schema")

    def test_api_properties_has_get_schema(self, swift_afst):
        """Test API-related properties."""
        assert hasattr(swift_afst, "_get_schema")

    def test_list_methods_append_length(self, swift_afst, basic_afst_entry):
        """Test list-like methods."""
        swift_afst.append(basic_afst_entry)
        assert len(swift_afst) == 1

    def test_list_methods_append_access(self, swift_afst, basic_afst_entry):
        """Test list-like methods."""
        swift_afst.append(basic_afst_entry)
        assert swift_afst[0] == basic_afst_entry

    def test_table_property_empty(self, swift_afst):
        """Test _table property with empty AFST."""
        header, data = swift_afst._table

        assert header == []
        assert data == []

    def test_table_property_with_entries_header_type(self, swift_afst, full_afst_entry):
        """Test _table property with entries."""
        swift_afst.append(full_afst_entry)
        header, data = swift_afst._table
        assert isinstance(header, list)

    def test_table_property_with_entries_data_type(self, swift_afst, full_afst_entry):
        """Test _table property with entries."""
        swift_afst.append(full_afst_entry)
        header, data = swift_afst._table
        assert isinstance(data, list)

    def test_table_property_with_entries_data_length(self, swift_afst, full_afst_entry):
        """Test _table property with entries."""
        swift_afst.append(full_afst_entry)
        header, data = swift_afst._table
        assert len(data) == 1

    def test_observations_property_empty(self, swift_afst):
        """Test observations property with no entries."""
        obs = swift_afst.observations

        assert isinstance(obs, SwiftObservations)
        assert len(obs) == 0

    def test_observations_property_with_entries_length(self, swift_afst, sample_afst_entries):
        """Test observations property with entries."""
        for entry in sample_afst_entries:
            swift_afst.append(entry)

        obs = swift_afst.observations
        assert len(obs) == 2  # Two unique obs_ids

    def test_observations_property_with_entries_contains_first_obs_id(self, swift_afst, sample_afst_entries):
        """Test observations property with entries."""
        for entry in sample_afst_entries:
            swift_afst.append(entry)

        obs = swift_afst.observations
        assert "00012345001" in obs

    def test_observations_property_with_entries_contains_second_obs_id(self, swift_afst, sample_afst_entries):
        """Test observations property with entries."""
        for entry in sample_afst_entries:
            swift_afst.append(entry)

        obs = swift_afst.observations
        assert "00012345002" in obs

    def test_observations_property_with_entries_first_obs_length(self):
        """Test observations property with entries."""
        afst = SwiftAFST(autosubmit=False)
        entry1 = SwiftAFSTEntry(obs_id="00012345001", targname="Target1", ra=266, dec=-29)
        entry2 = SwiftAFSTEntry(obs_id="00012345002", targname="Target2", ra=266, dec=-29)
        entry3 = SwiftAFSTEntry(obs_id="00012345001", targname="Target1", ra=266, dec=-29)  # Same obs_id as entry1

        afst.append(entry1)
        afst.append(entry2)
        afst.append(entry3)

        obs = afst.observations
        assert len(obs["00012345001"]) == 2  # Two entries for this obs_id

    def test_observations_property_with_entries_second_obs_length(self):
        """Test observations property with entries."""
        afst = SwiftAFST(autosubmit=False)
        entry1 = SwiftAFSTEntry(obs_id="00012345001", targname="Target1", ra=266, dec=-29)
        entry2 = SwiftAFSTEntry(obs_id="00012345002", targname="Target2", ra=266, dec=-29)
        entry3 = SwiftAFSTEntry(obs_id="00012345001", targname="Target1", ra=266, dec=-29)  # Same obs_id as entry1

        afst.append(entry1)
        afst.append(entry2)
        afst.append(entry3)

        obs = afst.observations
        assert len(obs["00012345002"]) == 1  # One entry for this obs_id

    def test_local_variables(self):
        """Test _local variables are defined."""
        afst = SwiftAFST(autosubmit=False)
        expected_local = ["obsid", "name", "skycoord", "length", "target_id", "shared_secret"]
        assert afst._local == expected_local

    def test_time_format(self):
        """Test time format setting."""
        afst = SwiftAFST(autosubmit=False)
        assert afst._isutc is False  # Default is spacecraft time, not UTC

    def test_optional_parameters_target_id(self):
        """Test setting optional parameters."""
        with patch("swifttools.swift_too.swift.obsquery.SwiftAFST.validate_get", return_value=True):
            afst = SwiftAFST(
                target_id=12345,
                obs_id=67890,
                afstmax=datetime(2023, 12, 31),
                autosubmit=False,
            )
        assert afst.target_id == 12345

    def test_optional_parameters_obs_id(self):
        """Test setting optional parameters."""
        with patch("swifttools.swift_too.swift.obsquery.SwiftAFST.validate_get", return_value=True):
            afst = SwiftAFST(
                target_id=12345,
                obs_id=67890,
                afstmax=datetime(2023, 12, 31),
                autosubmit=False,
            )
        assert afst.obs_id == "00067890000"

    def test_optional_parameters_afstmax(self):
        """Test setting optional parameters."""
        with patch("swifttools.swift_too.swift.obsquery.SwiftAFST.validate_get", return_value=True):
            afst = SwiftAFST(
                target_id=12345,
                obs_id=67890,
                afstmax=datetime(2023, 12, 31),
                autosubmit=False,
            )
        assert afst.afstmax == datetime(2023, 12, 31)

    def test_target_id_list(self):
        """Test target_id as list."""
        afst = SwiftAFST(target_id=[12345, 67890], autosubmit=False)
        assert afst.target_id == [12345, 67890]


class TestAliases:
    def test_swift_afst_entry_aliases(self):
        """Test SwiftAFSTEntry aliases."""
        aliases = [
            Swift_AFST_Entry,
            ObsEntry,
            Swift_ObsEntry,
            AFSTEntry,
            Swift_AFSTEntry,
        ]

        for alias in aliases:
            entry = alias(targname="Test", ra=266, dec=-29)
            assert isinstance(entry, SwiftAFSTEntry)

    def test_swift_afst_aliases(self):
        """Test SwiftAFST aliases."""
        aliases = [
            Swift_ObsQuery,
            ObsQuery,
            AFST,
            Swift_AFST,
        ]

        for alias in aliases:
            afst = alias(autosubmit=False)
            assert isinstance(afst, SwiftAFST)

    def test_swift_observation_aliases(self):
        """Test SwiftObservation aliases."""
        obs = Swift_Observation()
        assert isinstance(obs, SwiftObservation)

    def test_swift_observations_aliases(self):
        """Test SwiftObservations aliases."""
        obs_dict = Swift_Observations()
        assert isinstance(obs_dict, SwiftObservations)


class TestSchemas:
    def test_swift_afst_get_schema_defaults(self):
        """Test SwiftAFSTGetSchema requires at least one field."""
        with pytest.raises(ValidationError):
            SwiftAFSTGetSchema()

    def test_swift_afst_schema_defaults_radius(self):
        """Test SwiftAFSTSchema default values."""
        schema = SwiftAFSTSchema()
        assert schema.radius is None

    def test_swift_afst_schema_defaults_target_id(self):
        """Test SwiftAFSTSchema default values."""
        schema = SwiftAFSTSchema()
        assert schema.target_id is None

    def test_swift_afst_schema_defaults_obs_id(self):
        """Test SwiftAFSTSchema default values."""
        schema = SwiftAFSTSchema()
        assert schema.obs_id is None

    def test_swift_afst_schema_defaults_afstmax(self):
        """Test SwiftAFSTSchema default values."""
        schema = SwiftAFSTSchema()
        assert schema.afstmax is None

    def test_swift_afst_schema_defaults_entries(self):
        """Test SwiftAFSTSchema default values."""
        schema = SwiftAFSTSchema()
        assert schema.entries == []
