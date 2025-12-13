from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from swifttools.swift_too.swift.guano import SwiftGUANO, SwiftGUANOData, SwiftGUANOEntry, SwiftGUANOGTI


def test_swift_guano_init():
    """Test SwiftGUANO initialization"""
    guano = SwiftGUANO(autosubmit=False)
    assert guano.entries == []


def test_swift_guano_getitem():
    """Test indexing"""
    guano = SwiftGUANO(autosubmit=False)
    guano.entries = ["entry1", "entry2"]
    assert guano[0] == "entry1"
    assert guano[1] == "entry2"


def test_swift_guano_len():
    """Test len() method"""
    guano = SwiftGUANO(autosubmit=False)
    assert len(guano) == 0
    guano.entries = [1, 2, 3]
    assert len(guano) == 3


def test_swift_guano_validate():
    """Test validate method"""
    guano = SwiftGUANO(autosubmit=False)
    # When no parameters are set, validate should return None but may raise AttributeError
    # due to model initialization. Let's test with parameters set.

    # Test with parameters - set length directly
    guano.length = 1.0
    assert guano.validate() is True

    # Test subthreshold with anonymous user
    guano.subthreshold = True
    guano.username = "anonymous"
    assert guano.validate() is False


def test_swift_guano_entry_init():
    """Test SwiftGUANOEntry initialization"""
    entry = SwiftGUANOEntry()
    assert entry.obs_id is None


def test_swift_guano_data_init():
    """Test SwiftGUANOData initialization"""
    data = SwiftGUANOData(all_gtis=[])
    assert data.gti is None


def test_swift_guano_data_properties():
    """Test SwiftGUANOData properties"""
    # Test utcf property
    gti = SwiftGUANOGTI(utcf=10.5)
    data = SwiftGUANOData(all_gtis=[], gti=gti)
    assert data.utcf == 10.5

    # Test subthresh property
    data = SwiftGUANOData(all_gtis=[], filenames=["test_ms_file.fits"])
    assert data.subthresh is True

    data = SwiftGUANOData(all_gtis=[], filenames=["test_file.fits"])
    assert data.subthresh is False

    data = SwiftGUANOData(all_gtis=[], filenames=None)
    assert data.subthresh is None


def test_swift_guano_gti_init():
    """Test SwiftGUANOGTI initialization"""
    gti = SwiftGUANOGTI()
    assert gti.filename is None
    assert gti.exposure == timedelta(0)


def test_swift_guano_gti_str():
    """Test SwiftGUANOGTI __str__ method"""
    begin = datetime(2023, 1, 1, 12, 0, 0)
    end = datetime(2023, 1, 1, 12, 10, 0)
    gti = SwiftGUANOGTI(begin=begin, end=end, exposure=timedelta(minutes=10))
    str_repr = str(gti)
    assert "12:00:00" in str_repr
    assert "12:10:00" in str_repr


def test_swift_guano_entry_properties():
    """Test SwiftGUANOEntry properties"""
    entry = SwiftGUANOEntry()

    # Test executed property
    entry.quadsaway = 2
    assert entry.executed is False
    entry.quadsaway = 3
    assert entry.executed is False
    entry.quadsaway = 1
    assert entry.executed is True
    entry.quadsaway = 4
    assert entry.executed is True

    # Test uplinked property
    entry.quadsaway = 1
    assert entry.uplinked is False
    entry.quadsaway = 3
    assert entry.uplinked is False
    entry.quadsaway = 2
    assert entry.uplinked is True
    entry.quadsaway = 4
    assert entry.uplinked is True


def test_swift_guano_entry_calc_begin_end():
    """Test SwiftGUANOEntry _calc_begin_end method"""
    entry = SwiftGUANOEntry(triggertime=datetime(2023, 1, 1, 12, 0, 0), offset=10.0, duration=5.0)
    entry._calc_begin_end()
    assert entry.begin == datetime(2023, 1, 1, 12, 0, 7, 500000)  # 12:00:00 + 10 - 2.5 = 12:00:07.5
    assert entry.end == datetime(2023, 1, 1, 12, 0, 12, 500000)  # 12:00:00 + 10 + 2.5 = 12:00:12.5


def test_swift_guano_entry_table():
    """Test SwiftGUANOEntry _table property"""
    entry = SwiftGUANOEntry(
        triggertype="GRB", triggertime=datetime(2023, 1, 1, 12, 0, 0), offset=10.0, duration=5.0, obs_id="00012345001"
    )
    # Mock data with exposure as float (seconds)
    mock_data = type("MockData", (), {"exposure": 5.0, "gti": None})()
    entry.data = mock_data

    header, table = entry._table
    assert header == ["Parameter", "Value"]
    # Should contain various parameters
    assert len(table) > 0

    # Test case where exposure is None
    mock_data_none = type("MockData", (), {"exposure": None, "gti": None})()
    entry.data = mock_data_none
    header2, table2 = entry._table
    assert header2 == ["Parameter", "Value"]
    assert len(table2) > 0


def test_swift_guano_get_schema_validate():
    """Test SwiftGUANOGetSchema validate_parameters"""
    from swifttools.swift_too.swift.guano import SwiftGUANOGetSchema

    # Valid case - has parameters
    values = {"triggertime": datetime(2023, 1, 1)}
    result = SwiftGUANOGetSchema.validate_parameters(values)
    assert result == values

    # Invalid case - no parameters
    with pytest.raises(ValueError, match="At least one of the parameters must be provided"):
        SwiftGUANOGetSchema.validate_parameters({})


def test_swift_guano_table_property():
    """Test SwiftGUANO _table property with entries"""
    guano = SwiftGUANO(autosubmit=False)

    # Create mock entries
    entry1 = SwiftGUANOEntry(
        triggertype="GRB",
        triggertime=datetime(2023, 1, 1, 12, 0, 0),
        offset=10.0,
        duration=5.0,
        obs_id="00012345001",
        quadsaway=0,
    )
    mock_data1 = type("MockData", (), {"exposure": 5.0, "gti": None})()
    entry1.data = mock_data1

    entry2 = SwiftGUANOEntry(
        triggertype="TEST",
        triggertime=datetime(2023, 1, 1, 13, 0, 0),
        offset=20.0,
        duration=10.0,
        obs_id=None,
        quadsaway=2,  # Not executed (quadsaway=2), but uplinked
    )
    mock_data2 = type(
        "MockData", (), {"exposure": 5.0, "gti": None}
    )()  # Different exposure to trigger the != condition
    entry2.data = mock_data2

    entry3 = SwiftGUANOEntry(
        triggertype="UNKNOWN",
        triggertime=datetime(2023, 1, 1, 14, 0, 0),
        offset=30.0,
        duration=15.0,
        obs_id=None,
        quadsaway=3,  # Neither executed nor uplinked
    )
    mock_data3 = type("MockData", (), {"exposure": 15.0, "gti": None})()
    entry3.data = mock_data3

    entry4 = SwiftGUANOEntry(
        triggertype="EXECUTED",
        triggertime=datetime(2023, 1, 1, 15, 0, 0),
        offset=40.0,
        duration=20.0,
        obs_id=None,
        quadsaway=0,  # Executed but no obs_id yet
    )
    mock_data4 = type("MockData", (), {"exposure": 20.0, "gti": None})()
    entry4.data = mock_data4

    guano.entries = [entry1, entry2, entry3, entry4]

    header, table = guano._table
    assert header == [
        "Trigger Type",
        "Trigger Time",
        "Offset (s)",
        "Window Duration (s)",
        "Observation ID",
    ]
    assert len(table) == 4
    assert table[0][0] == "GRB"
    assert table[0][4] == "00012345001"
    assert table[1][0] == "TEST"
    assert table[1][4] == "Pending Execution"  # quadsaway=2
    assert table[2][0] == "UNKNOWN"
    assert table[2][4] == "Unknown Status"  # quadsaway=3
    assert table[3][0] == "EXECUTED"
    assert table[3][4] == "Pending Data"  # quadsaway=0, executed=True


def test_swift_guano_post_process():
    """Test _post_process method"""
    with patch("swifttools.swift_too.swift.clock.Clock") as mock_clock_class:
        # Create a mock clock instance
        mock_clock_instance = mock_clock_class.return_value
        mock_clock_instance.entries = []

        guano = SwiftGUANO(autosubmit=False)
        # Mock entries with _calc_begin_end method
        mock_entry = type("MockEntry", (), {"_calc_begin_end": lambda self: None})()
        guano.entries = [mock_entry]
        guano._post_process()
        # Should call _calc_begin_end and clock_correct
        assert len(guano.entries) == 1
