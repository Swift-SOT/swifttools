from datetime import datetime, timedelta

import pytest

from swifttools.swift_too.swift_planquery import SwiftPPSTEntry


class TestSwiftPPSTEntry:
    def test_init_with_all_fields(self):
        """Test SwiftPPSTEntry initialization with all fields."""
        entry = SwiftPPSTEntry(
            target_name="Test Target",
            ra=123.456,
            dec=78.901,
            roll=45.0,
            begin=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 13, 0, 0),
            targetid=12345,
            seg=1,
            obs_id=98765,
            bat=1,
            xrt=2,
            uvot=3,
            fom=0.95,
            comment="Test observation",
            timetarg=100,
            takodb="test_db",
        )

        assert entry.targname == "Test Target"
        assert entry.ra == 123.456
        assert entry.dec == 78.901
        assert entry.roll == 45.0
        assert entry.begin == datetime(2023, 1, 1, 12, 0, 0)
        assert entry.end == datetime(2023, 1, 1, 13, 0, 0)
        assert entry.targetid == 12345
        assert entry.seg == 1
        assert entry.obs_id == "00098765000"
        assert entry.bat == 1
        assert entry.xrt == 2
        assert entry.uvot == 3
        assert entry.fom == 0.95
        assert entry.comment == "Test observation"
        assert entry.timetarg == 100
        assert entry.takodb == "test_db"

    def test_init_with_minimal_fields(self):
        """Test SwiftPPSTEntry initialization with minimal fields."""
        entry = SwiftPPSTEntry()

        assert entry.targname is None
        assert entry.ra is None
        assert entry.dec is None
        assert entry.roll is None
        assert entry.begin is None
        assert entry.end is None
        assert entry.targetid is None
        assert entry.seg is None
        assert entry.obs_id is None
        assert entry.bat is None
        assert entry.xrt is None
        assert entry.uvot is None
        assert entry.fom is None
        assert entry.comment is None
        assert entry.timetarg is None
        assert entry.takodb is None

    def test_exposure_property(self):
        """Test that exposure property calculates correctly."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 30, 0)
        entry = SwiftPPSTEntry(begin=begin_time, end=end_time)

        expected_exposure = end_time - begin_time
        assert entry.exposure == expected_exposure
        assert entry.exposure == timedelta(hours=1, minutes=30)

    def test_exposure_property_with_none_times(self):
        """Test that exposure property handles None times."""
        entry = SwiftPPSTEntry(begin=None, end=None)

        with pytest.raises(TypeError):
            _ = entry.exposure

    def test_target_name_alias(self):
        """Test that target_name alias works for targname field."""
        data = {"target_name": "Aliased Target"}
        entry = SwiftPPSTEntry(**data)

        assert entry.targname == "Aliased Target"

    def test_table_property(self):
        """Test that _table property returns correct format."""
        begin_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)
        entry = SwiftPPSTEntry(begin=begin_time, end=end_time, target_name="Test Target", obs_id="00012345001")

        header, rows = entry._table

        expected_header = ["Begin Time", "End Time", "Target Name", "Observation Number", "Exposure (s)"]
        assert header == expected_header
        assert len(rows) == 1
        assert rows[0][0] == begin_time
        assert rows[0][1] == end_time
        assert rows[0][2] == "Test Target"
        assert rows[0][3] == "00012345001"
        assert rows[0][4] == 3600  # 1 hour in seconds

    def test_varnames_mapping(self):
        """Test that _varnames mapping contains expected keys."""
        entry = SwiftPPSTEntry()

        expected_keys = [
            "begin",
            "end",
            "targname",
            "ra",
            "dec",
            "roll",
            "targetid",
            "seg",
            "xrt",
            "uvot",
            "bat",
            "fom",
            "obs_id",
            "exposure",
            "slewtime",
        ]

        for key in expected_keys:
            assert key in entry._varnames

        # Test some specific mappings
        assert entry._varnames["begin"] == "Begin Time"
        assert entry._varnames["targname"] == "Target Name"
        assert entry._varnames["ra"] == "RA(J2000)"
        assert entry._varnames["obs_id"] == "Observation Number"

    def test_header_title_method(self):
        """Test that _header_title method works correctly."""
        entry = SwiftPPSTEntry()

        # Test with existing key
        assert entry._header_title("begin") == "Begin Time"
        assert entry._header_title("targname") == "Target Name"

        # Test with non-existing key (should return the key itself)
        assert entry._header_title("unknown_key") == "unknown_key"

    def test_inheritance_from_base_classes(self):
        """Test that SwiftPPSTEntry inherits from expected base classes."""
        entry = SwiftPPSTEntry()

        # Should inherit from BaseSchema and TOOAPIClockCorrect
        assert hasattr(entry, "model_dump")  # From BaseSchema (Pydantic)
        # TOOAPIClockCorrect methods would be tested in their respective test files
