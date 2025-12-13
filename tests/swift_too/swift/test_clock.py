from datetime import datetime

import pytest

from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.swift.clock import SwiftClock, SwiftClockGetSchema, SwiftDateTimeSchema, TOOAPIClockCorrect


class MockClockCorrect(BaseSchema, TOOAPIClockCorrect):
    """Mock class to test TOOAPIClockCorrect mixin"""

    test_datetime: datetime


def test_swift_clock_init_with_met():
    """Test SwiftClock initialization with MET"""
    clock = SwiftClock(met=123456789.0, autosubmit=False)
    assert clock.met == 123456789.0  # Single value before post-processing


def test_swift_clock_init_with_utctime():
    """Test SwiftClock initialization with UTC time"""
    dt = datetime(2023, 1, 1, 12, 0, 0)
    clock = SwiftClock(utctime=dt, autosubmit=False)
    assert clock.utctime == dt


def test_swift_clock_init_with_swifttime():
    """Test SwiftClock initialization with Swift time"""
    dt = datetime(2023, 1, 1, 12, 0, 0)
    clock = SwiftClock(swifttime=dt, autosubmit=False)
    assert clock.swifttime == dt


def test_swift_clock_to_utctime():
    """Test converting clock entries to UTC time"""
    dt = datetime(2023, 1, 1, 12, 0, 0)
    clock = SwiftClock(swifttime=dt, autosubmit=False)
    # Mock some entries
    from swifttools.swift_too.swift.datetime import swiftdatetime

    clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)]
    clock.to_utctime()
    assert len(clock.entries) == 1
    # Check that the entry was converted
    assert clock.entries[0].isutc is True


def test_swift_clock_to_swifttime():
    """Test converting clock entries to Swift time"""
    dt = datetime(2023, 1, 1, 12, 0, 0)
    clock = SwiftClock(utctime=dt, autosubmit=False)
    # Mock some entries
    from swifttools.swift_too.swift.datetime import swiftdatetime

    clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)]
    clock.to_swifttime()
    assert len(clock.entries) == 1
    # Check that the entry was converted
    assert clock.entries[0].isutc is False


def test_swift_clock_len():
    """Test len() method"""
    clock = SwiftClock(autosubmit=False)
    assert len(clock) == 0
    # Mock entries
    clock.entries = [1, 2, 3]
    assert len(clock) == 3


def test_swift_clock_getitem():
    """Test indexing"""
    clock = SwiftClock(autosubmit=False)
    clock.entries = ["entry1", "entry2"]
    assert clock[0] == "entry1"
    assert clock[1] == "entry2"


def test_swift_clock_table_property():
    """Test _table property"""
    clock = SwiftClock(autosubmit=False)
    clock.entries = []
    header, data = clock._table
    assert header == []
    assert data == []


def test_swift_clock_table_property_with_entries():
    """Test _table property with entries"""
    clock = SwiftClock(autosubmit=False)
    # Mock entries with _table property
    from unittest.mock import MagicMock

    mock_entry = MagicMock()
    mock_entry._table = [["MET", "Swift Time", "UTC Time"], [123456789.0, datetime(2023, 1, 1), datetime(2023, 1, 1)]]
    clock.entries = [mock_entry]

    header, data = clock._table
    assert header == ["MET", "Swift Time", "UTC Time"]
    assert len(data) == 1


def test_tooapi_clock_correct_to_utctime():
    """Test TOOAPIClockCorrect to_utctime method"""
    from unittest.mock import Mock, patch

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    mock._clock = Mock()
    mock._datetime_refs = [([("model", "test_datetime")], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2023, 1, 2)]
    with patch.object(mock, "clock_correct") as mock_clock_correct:
        mock.to_utctime()
        mock._clock.to_utctime.assert_called_once()
        mock_clock_correct.assert_called_once()


def test_tooapi_clock_correct_to_swifttime():
    """Test TOOAPIClockCorrect to_swifttime method"""
    from unittest.mock import Mock, patch

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    mock._clock = Mock()
    mock._datetime_refs = [([("model", "test_datetime")], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2023, 1, 2)]
    with patch.object(mock, "clock_correct") as mock_clock_correct:
        mock.to_swifttime()
        mock._clock.to_swifttime.assert_called_once()
        mock_clock_correct.assert_called_once()


def test_swift_datetime_schema():
    """Test SwiftDateTimeSchema computed fields"""
    schema = SwiftDateTimeSchema(met=123456789.0, utcf=10.0, isutc=False)
    # Access computed fields
    swifttime = schema.swifttime
    utctime = schema.utctime
    assert isinstance(swifttime, datetime)
    assert isinstance(utctime, datetime)


def test_swift_clock_get_schema_validator():
    """Test SwiftClockGetSchema validator"""
    # Test valid case: exactly one field
    schema = SwiftClockGetSchema(met=123456789.0)
    assert schema.met == 123456789.0

    # Test invalid case: no fields
    with pytest.raises(ValueError, match="Exactly one of 'met', 'utctime', or 'swifttime' must be provided"):
        SwiftClockGetSchema()

    # Test invalid case: multiple fields
    with pytest.raises(ValueError, match="Exactly one of 'met', 'utctime', or 'swifttime' must be provided"):
        SwiftClockGetSchema(met=123456789.0, utctime=datetime(2023, 1, 1))

    # Test validator with non-dict (to cover the isinstance check)
    class MockValues:
        def __init__(self):
            self.met = 123456789.0
            self.utctime = None
            self.swifttime = None

    result = SwiftClockGetSchema.validate_exactly_one_field(MockValues())
    assert result["met"] == 123456789.0


def test_swift_clock_post_process():
    """Test _post_process method"""
    clock = SwiftClock(autosubmit=False)
    # Mock entries as SwiftDateTimeSchema
    from swifttools.swift_too.swift.datetime import swiftdatetime

    mock_entry = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
    clock.entries = [mock_entry]
    clock._post_process()
    assert isinstance(clock.met, list)
    assert isinstance(clock.swifttime, list)
    assert isinstance(clock.utctime, list)
    assert len(clock.met) == 1
    assert len(clock.swifttime) == 1
    assert len(clock.utctime) == 1


def test_index_datetimes():
    """Test index_datetimes function"""
    from unittest.mock import Mock

    from swifttools.swift_too.swift.clock import index_datetimes

    # Create a mock object with datetime attribute
    test_obj = Mock()
    test_obj.date = datetime(2023, 1, 1)
    test_obj.model_dump.return_value = {"date": datetime(2023, 1, 1)}

    i, values = index_datetimes(test_obj)
    assert i == 1
    assert len(values) == 1
    assert values[0] == datetime(2023, 1, 1)

    # Test with dict
    test_dict = {"date": datetime(2023, 1, 1)}
    i, values = index_datetimes(test_dict)
    assert i == 1
    assert len(values) == 1
    assert values[0] == datetime(2023, 1, 1)

    # Test setvals with dict
    new_dates = [datetime(2024, 1, 1)]
    i, values = index_datetimes(test_dict, setvals=new_dates)
    assert test_dict["date"] == datetime(2024, 1, 1)


def test_tooapi_clock_correct_header_title():
    """Test TOOAPIClockCorrect _header_title method"""
    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    mock._varnames = {"test_datetime": "Test DateTime"}
    # Mock swiftdatetime
    from swifttools.swift_too.swift.datetime import swiftdatetime

    mock.test_datetime = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)
    title = mock._header_title("test_datetime")
    assert "UTC" in title

    # Test Swift time
    mock.test_datetime = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
    title = mock._header_title("test_datetime")
    assert "Swift" in title


def test_tooapi_clock_correct_clock_correct():
    """Test TOOAPIClockCorrect clock_correct method with actual execution"""
    from unittest.mock import patch

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    # Add complex nested structures to cover all branches
    mock.nested_dict = {"inner_date": datetime(2023, 1, 1)}
    mock.nested_list = [datetime(2023, 1, 1)]
    mock.nested_schema = BaseSchema(nested_date=datetime(2023, 1, 1))
    mock.clock_instance = SwiftClock(autosubmit=False)  # To cover SwiftClock skip
    # This should create a clock and apply corrections
    with patch("swifttools.swift_too.swift.clock.Clock") as mock_clock_class:
        mock_clock_instance = mock_clock_class.return_value
        mock_clock_instance.entries = [
            datetime(2023, 1, 2),
            datetime(2023, 1, 3),
            datetime(2023, 1, 4),
            datetime(2023, 1, 5),
        ]
        mock.clock_correct()
        # Should have created a clock
        mock_clock_class.assert_called_once()
        assert mock._clock is not None
        assert mock._datetime_refs is not None
        # Call again to cover the else branch
        mock.clock_correct()
