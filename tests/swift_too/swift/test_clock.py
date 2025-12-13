from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.swift.clock import (
    SwiftClock,
    SwiftClockGetSchema,
    SwiftDateTimeSchema,
    TOOAPIClockCorrect,
    index_datetimes,
)
from swifttools.swift_too.swift.datetime import swiftdatetime


class MockClockCorrect(BaseSchema, TOOAPIClockCorrect):
    """Mock class to test TOOAPIClockCorrect mixin"""

    test_datetime: datetime


@pytest.fixture
def swift_clock():
    return SwiftClock(autosubmit=False)


@pytest.fixture
def mock_clock_correct():
    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    mock._clock = Mock()
    mock._datetime_refs = [([("model", "test_datetime")], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2023, 1, 2)]
    return mock


@pytest.fixture
def swift_datetime_schema():
    return SwiftDateTimeSchema(met=123456789.0, utcf=10.0, isutc=False)


@pytest.fixture
def mock_entry():
    return swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)


@pytest.fixture
def test_obj():
    test_obj = Mock()
    test_obj.date = datetime(2023, 1, 1)
    test_obj.model_dump.return_value = {"date": datetime(2023, 1, 1)}
    return test_obj


@pytest.fixture
def test_dict():
    return {"date": datetime(2023, 1, 1)}


class TestSwiftClockInit:
    def test_init_with_met(self, swift_clock):
        clock = SwiftClock(met=123456789.0, autosubmit=False)
        assert clock.met == 123456789.0

    def test_init_with_utctime(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(utctime=dt, autosubmit=False)
        assert clock.utctime == dt

    def test_init_with_swifttime(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(swifttime=dt, autosubmit=False)
        assert clock.swifttime == dt


class TestSwiftClockMethods:
    def test_to_utctime(self, swift_clock):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(swifttime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)]
        clock.to_utctime()
        assert len(clock.entries) == 1

    def test_to_utctime_conversion(self, swift_clock):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(swifttime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)]
        clock.to_utctime()
        assert clock.entries[0].isutc is True

    def test_to_swifttime(self, swift_clock):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(utctime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)]
        clock.to_swifttime()
        assert len(clock.entries) == 1

    def test_to_swifttime_conversion(self, swift_clock):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(utctime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)]
        clock.to_swifttime()
        assert clock.entries[0].isutc is False

    def test_len_empty(self, swift_clock):
        assert len(swift_clock) == 0

    def test_len_with_entries(self, swift_clock):
        swift_clock.entries = [1, 2, 3]
        assert len(swift_clock) == 3

    def test_getitem_first(self, swift_clock):
        swift_clock.entries = ["entry1", "entry2"]
        assert swift_clock[0] == "entry1"

    def test_getitem_second(self, swift_clock):
        swift_clock.entries = ["entry1", "entry2"]
        assert swift_clock[1] == "entry2"

    def test_table_property_empty(self, swift_clock):
        swift_clock.entries = []
        header, data = swift_clock._table
        assert header == []

    def test_table_property_empty_data(self, swift_clock):
        swift_clock.entries = []
        header, data = swift_clock._table
        assert data == []

    def test_table_property_with_entries_header(self, swift_clock):
        mock_entry = MagicMock()
        mock_entry._table = [
            ["MET", "Swift Time", "UTC Time"],
            [123456789.0, datetime(2023, 1, 1), datetime(2023, 1, 1)],
        ]
        swift_clock.entries = [mock_entry]
        header, data = swift_clock._table
        assert header == ["MET", "Swift Time", "UTC Time"]

    def test_table_property_with_entries_data_length(self, swift_clock):
        mock_entry = MagicMock()
        mock_entry._table = [
            ["MET", "Swift Time", "UTC Time"],
            [123456789.0, datetime(2023, 1, 1), datetime(2023, 1, 1)],
        ]
        swift_clock.entries = [mock_entry]
        header, data = swift_clock._table
        assert len(data) == 1

    def test_post_process_met_type(self, swift_clock, mock_entry):
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert isinstance(swift_clock.met, list)

    def test_post_process_swifttime_type(self, swift_clock, mock_entry):
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert isinstance(swift_clock.swifttime, list)

    def test_post_process_utctime_type(self, swift_clock, mock_entry):
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert isinstance(swift_clock.utctime, list)

    def test_post_process_met_length(self, swift_clock, mock_entry):
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert len(swift_clock.met) == 1

    def test_post_process_swifttime_length(self, swift_clock, mock_entry):
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert len(swift_clock.swifttime) == 1

    def test_post_process_utctime_length(self, swift_clock, mock_entry):
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert len(swift_clock.utctime) == 1


class TestTOOAPIClockCorrect:
    def test_to_utctime_calls_clock_to_utctime(self, mock_clock_correct):
        with patch.object(mock_clock_correct, "clock_correct"):
            mock_clock_correct.to_utctime()
            mock_clock_correct._clock.to_utctime.assert_called_once()

    def test_to_utctime_calls_clock_correct(self, mock_clock_correct):
        with patch.object(mock_clock_correct, "clock_correct") as mock_clock_correct_method:
            mock_clock_correct.to_utctime()
            mock_clock_correct_method.assert_called_once()

    def test_to_swifttime_calls_clock_to_swifttime(self, mock_clock_correct):
        with patch.object(mock_clock_correct, "clock_correct"):
            mock_clock_correct.to_swifttime()
            mock_clock_correct._clock.to_swifttime.assert_called_once()

    def test_to_swifttime_calls_clock_correct(self, mock_clock_correct):
        with patch.object(mock_clock_correct, "clock_correct") as mock_clock_correct_method:
            mock_clock_correct.to_swifttime()
            mock_clock_correct_method.assert_called_once()

    def test_header_title_utc(self):
        mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
        mock._varnames = {"test_datetime": "Test DateTime"}
        mock.test_datetime = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)
        title = mock._header_title("test_datetime")
        assert "UTC" in title

    def test_header_title_swift(self):
        mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
        mock._varnames = {"test_datetime": "Test DateTime"}
        mock.test_datetime = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        title = mock._header_title("test_datetime")
        assert "Swift" in title

    def test_clock_correct_creates_clock(self):
        mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
        mock.nested_dict = {"inner_date": datetime(2023, 1, 1)}
        mock.nested_list = [datetime(2023, 1, 1)]
        mock.nested_schema = BaseSchema(nested_date=datetime(2023, 1, 1))
        mock.clock_instance = SwiftClock(autosubmit=False)
        with patch("swifttools.swift_too.swift.clock.Clock") as mock_clock_class:
            mock_clock_instance = mock_clock_class.return_value
            mock_clock_instance.entries = [
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
                datetime(2023, 1, 5),
            ]
            mock.clock_correct()
            mock_clock_class.assert_called_once()

    def test_clock_correct_sets_clock_attribute(self):
        mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
        mock.nested_dict = {"inner_date": datetime(2023, 1, 1)}
        mock.nested_list = [datetime(2023, 1, 1)]
        mock.nested_schema = BaseSchema(nested_date=datetime(2023, 1, 1))
        mock.clock_instance = SwiftClock(autosubmit=False)
        with patch("swifttools.swift_too.swift.clock.Clock") as mock_clock_class:
            mock_clock_instance = mock_clock_class.return_value
            mock_clock_instance.entries = [
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
                datetime(2023, 1, 5),
            ]
            mock.clock_correct()
            assert mock._clock is not None

    def test_clock_correct_sets_datetime_refs(self):
        mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
        mock.nested_dict = {"inner_date": datetime(2023, 1, 1)}
        mock.nested_list = [datetime(2023, 1, 1)]
        mock.nested_schema = BaseSchema(nested_date=datetime(2023, 1, 1))
        mock.clock_instance = SwiftClock(autosubmit=False)
        with patch("swifttools.swift_too.swift.clock.Clock") as mock_clock_class:
            mock_clock_instance = mock_clock_class.return_value
            mock_clock_instance.entries = [
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
                datetime(2023, 1, 5),
            ]
            mock.clock_correct()
            assert mock._datetime_refs is not None


class TestSwiftDateTimeSchema:
    def test_swifttime_type(self, swift_datetime_schema):
        swifttime = swift_datetime_schema.swifttime
        assert isinstance(swifttime, datetime)

    def test_utctime_type(self, swift_datetime_schema):
        utctime = swift_datetime_schema.utctime
        assert isinstance(utctime, datetime)


class TestSwiftClockGetSchema:
    def test_valid_met(self):
        schema = SwiftClockGetSchema(met=123456789.0)
        assert schema.met == 123456789.0

    def test_invalid_no_fields(self):
        with pytest.raises(ValueError, match="Exactly one of 'met', 'utctime', or 'swifttime' must be provided"):
            SwiftClockGetSchema()

    def test_invalid_multiple_fields(self):
        with pytest.raises(ValueError, match="Exactly one of 'met', 'utctime', or 'swifttime' must be provided"):
            SwiftClockGetSchema(met=123456789.0, utctime=datetime(2023, 1, 1))

    def test_validate_exactly_one_field(self):
        class MockValues:
            def __init__(self):
                self.met = 123456789.0
                self.utctime = None
                self.swifttime = None

        result = SwiftClockGetSchema.validate_exactly_one_field(MockValues())
        assert result["met"] == 123456789.0


class TestIndexDatetimes:
    def test_index_datetimes_obj_count(self, test_obj):
        i, values = index_datetimes(test_obj)
        assert i == 1

    def test_index_datetimes_obj_values_length(self, test_obj):
        i, values = index_datetimes(test_obj)
        assert len(values) == 1

    def test_index_datetimes_obj_values_content(self, test_obj):
        i, values = index_datetimes(test_obj)
        assert values[0] == datetime(2023, 1, 1)

    def test_index_datetimes_dict_count(self, test_dict):
        i, values = index_datetimes(test_dict)
        assert i == 1

    def test_index_datetimes_dict_values_length(self, test_dict):
        i, values = index_datetimes(test_dict)
        assert len(values) == 1

    def test_index_datetimes_dict_values_content(self, test_dict):
        i, values = index_datetimes(test_dict)
        assert values[0] == datetime(2023, 1, 1)

    def test_index_datetimes_setvals_dict(self, test_dict):
        new_dates = [datetime(2024, 1, 1)]
        index_datetimes(test_dict, setvals=new_dates)
        assert test_dict["date"] == datetime(2024, 1, 1)
