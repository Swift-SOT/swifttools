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
    def test_init_with_basic_parameters(self):
        """Test basic initialization of SwiftAFSTEntry."""
        entry = SwiftAFSTEntry(
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

        assert entry.begin == datetime(2023, 1, 1, 12, 0, 0)
        assert entry.settle == datetime(2023, 1, 1, 12, 1, 0)
        assert entry.end == datetime(2023, 1, 1, 12, 10, 0)
        assert entry.target_name == "Test Target"
        assert entry.targname == "Test Target"
        assert entry.target_id == 12345
        assert entry.segment == 1
        assert entry.obs_id == "00012345001"
        assert entry.ra == 123.456
        assert entry.dec == 78.901

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

    def test_table_property(self):
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
        assert isinstance(data, list)
        assert len(data) == 1
        assert len(data[0]) == 6

    def test_varnames_property(self):
        """Test _varnames contains expected keys."""
        entry = SwiftAFSTEntry(ra=266, dec=-29)

        assert "begin" in entry._varnames
        assert "target_name" in entry._varnames
        assert "exposure" in entry._varnames
        assert entry._varnames["begin"] == "Begin Time"
        assert entry._varnames["target_name"] == "Target Name"

    def test_optional_parameters(self):
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
        assert entry.roll == 45.0
        assert entry.bat_mode == 1
        assert entry.xrt_mode == 0
        assert entry.uvot_mode == 261
        assert entry.fom == 100
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

    def test_init_with_entries(self):
        """Test initialization with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert len(obs) == 2
        assert obs.entries == entries

    def test_list_methods(self):
        """Test list-like methods."""
        obs = SwiftObservation()
        entry = SwiftAFSTEntry(targname="Test", ra=266, dec=-29)

        obs.append(entry)
        assert len(obs) == 1
        assert obs[0] == entry

        additional_entries = self.create_sample_entries()
        obs.extend(additional_entries)
        assert len(obs) == 3

    def test_computed_properties_empty(self):
        """Test computed properties with empty observation."""
        obs = SwiftObservation()

        assert obs.target_id is None
        assert obs.seg is None
        assert obs.obs_id is None
        assert obs.targname is None
        assert obs.ra_object is None
        assert obs.dec_object is None
        assert obs.exposure is None
        assert obs.slewtime is None
        assert obs.begin is None
        assert obs.end is None
        assert obs.xrt is None
        assert obs.uvot is None
        assert obs.bat is None

    def test_computed_properties_with_entries(self):
        """Test computed properties with entries."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert obs.target_id == 12345
        assert obs.segment == 1
        assert obs.obs_id == "00012345001"
        assert obs.target_name == "Test Target"
        assert obs.ra_object == 123.456
        assert obs.dec_object == 78.901
        assert obs.xrt_mode == 0
        assert obs.uvot_mode == 261
        assert obs.bat_mode == 1

    def test_time_aggregation(self):
        """Test time aggregation properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        # Begin should be earliest begin time
        assert obs.begin == datetime(2023, 1, 1, 12, 0, 0)
        # End should be latest end time
        assert obs.end == datetime(2023, 1, 1, 12, 15, 0)

        # Exposure should sum individual exposures (4 min + 4 min = 8 min)
        assert obs.exposure == timedelta(minutes=8)
        # Slewtime should sum individual slewtimes (1 min + 1 min = 2 min)
        assert obs.slewtime == timedelta(minutes=2)

    def test_snapshots_property(self):
        """Test snapshots property."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert obs.snapshots == entries

    def test_compatibility_properties(self):
        """Test ra_point and dec_point compatibility properties."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert obs.ra_point == obs.ra_object
        assert obs.dec_point == obs.dec_object

    def test_aliases(self):
        """Test property aliases."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        assert obs.obsid == obs.obs_id
        assert obs.target_id == obs.target_id
        assert obs.segment == obs.seg

    def test_table_property(self):
        """Test _table property."""
        entries = self.create_sample_entries()
        obs = SwiftObservation(entries=entries)

        header, data = obs._table
        assert isinstance(header, list)
        assert isinstance(data, list)
        assert len(data) == 1


class TestSwiftObservations:
    def test_init_empty(self):
        """Test initialization of empty SwiftObservations."""
        obs_dict = SwiftObservations()
        assert len(obs_dict) == 0

    def test_dict_functionality(self):
        """Test dictionary functionality."""
        obs_dict = SwiftObservations()
        obs = SwiftObservation()
        obs_dict["00012345001"] = obs

        assert len(obs_dict) == 1
        assert obs_dict["00012345001"] == obs

    def test_table_property_empty(self):
        """Test _table property with empty dictionary."""
        obs_dict = SwiftObservations()
        header, data = obs_dict._table

        assert header == []
        assert data == []


class TestSwiftAFST:
    def test_init_with_basic_parameters(self):
        """Test basic initialization of SwiftAFST."""
        afst = SwiftAFST(
            ra=123.456, dec=78.901, radius=0.5, begin=datetime(2023, 1, 1), end=datetime(2023, 1, 2), autosubmit=False
        )

        assert np.isclose(afst.ra, 123.456)
        assert np.isclose(afst.dec, 78.901)
        assert np.isclose(afst.radius, 0.5)
        assert afst.begin == datetime(2023, 1, 1)
        assert afst.end == datetime(2023, 1, 2)

    def test_default_values(self):
        """Test default values."""
        afst = SwiftAFST(autosubmit=False)

        assert afst.radius is None  # Default radius is None when no ra/dec
        assert afst.target_id is None
        assert afst.obs_id is None
        assert afst.entries == []

    def test_api_properties(self):
        """Test API-related properties."""
        afst = SwiftAFST(autosubmit=False)

        assert afst.api_name == "Swift_AFST"
        assert afst._endpoint == "/swift/obsquery"
        assert hasattr(afst, "_schema")
        assert hasattr(afst, "_get_schema")

    def test_list_methods(self):
        """Test list-like methods."""
        afst = SwiftAFST(autosubmit=False)
        entry = SwiftAFSTEntry(targname="Test", ra=266, dec=-29)

        afst.append(entry)
        assert len(afst) == 1
        assert afst[0] == entry

    def test_table_property_empty(self):
        """Test _table property with empty AFST."""
        afst = SwiftAFST(autosubmit=False)
        header, data = afst._table

        assert header == []
        assert data == []

    def test_table_property_with_entries(self):
        """Test _table property with entries."""
        afst = SwiftAFST(autosubmit=False)
        entry = SwiftAFSTEntry(
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
            targname="Test Target",
            obs_id="00012345001",
            ra=266,
            dec=-29,
        )
        afst.append(entry)

        header, data = afst._table
        assert isinstance(header, list)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_observations_property_empty(self):
        """Test observations property with no entries."""
        afst = SwiftAFST(autosubmit=False)
        obs = afst.observations

        assert isinstance(obs, SwiftObservations)
        assert len(obs) == 0

    def test_observations_property_with_entries(self):
        """Test observations property with entries."""
        afst = SwiftAFST(autosubmit=False)
        entry1 = SwiftAFSTEntry(obs_id="00012345001", targname="Target1", ra=266, dec=-29)
        entry2 = SwiftAFSTEntry(obs_id="00012345002", targname="Target2", ra=266, dec=-29)
        entry3 = SwiftAFSTEntry(obs_id="00012345001", targname="Target1", ra=266, dec=-29)  # Same obs_id as entry1

        afst.append(entry1)
        afst.append(entry2)
        afst.append(entry3)

        obs = afst.observations
        assert len(obs) == 2  # Two unique obs_ids
        assert "00012345001" in obs
        assert "00012345002" in obs
        assert len(obs["00012345001"]) == 2  # Two entries for this obs_id
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

    def test_optional_parameters(self):
        """Test setting optional parameters."""
        with patch("swifttools.swift_too.swift.obsquery.SwiftAFST.validate_get", return_value=True):
            afst = SwiftAFST(
                target_id=12345,
                obs_id=67890,
                afstmax=datetime(2023, 12, 31),
                autosubmit=False,
            )

        assert afst.target_id == 12345
        assert afst.obs_id == "00067890000"
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

    def test_swift_afst_schema_defaults(self):
        """Test SwiftAFSTSchema default values."""

        schema = SwiftAFSTSchema()
        assert schema.radius is None
        assert schema.target_id is None
        assert schema.obs_id is None
        assert schema.afstmax is None
        assert schema.entries == []
