from datetime import datetime
from unittest.mock import Mock, patch

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


class TestSwiftClock:
    def test_init_with_met(self):
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

    def test_to_utctime_conversion(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(swifttime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)]
        clock.to_utctime()
        assert len(clock.entries) == 1

    def test_to_utctime_isutc_flag(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(swifttime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)]
        clock.to_utctime()
        assert clock.entries[0].isutc is True

    def test_to_swifttime_conversion(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(utctime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)]
        clock.to_swifttime()
        assert len(clock.entries) == 1

    def test_to_swifttime_isutc_flag(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        clock = SwiftClock(utctime=dt, autosubmit=False)
        clock.entries = [swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)]
        clock.to_swifttime()
        assert clock.entries[0].isutc is False

    def test_len_empty(self, swift_clock):
        assert len(swift_clock) == 0

    def test_len_with_entries(self, swift_clock):
        swift_clock.entries = [
            SwiftDateTimeSchema(met=1.0, utcf=0.0, isutc=False),
            SwiftDateTimeSchema(met=2.0, utcf=0.0, isutc=False),
            SwiftDateTimeSchema(met=3.0, utcf=0.0, isutc=False),
        ]
        assert len(swift_clock) == 3

    def test_len_with_none_entries(self):
        clock = SwiftClock(autosubmit=False)
        clock.entries = []
        assert len(clock) == 0

    def test_getitem_first(self, swift_clock):
        entry1 = SwiftDateTimeSchema(met=1.0, utcf=0.0, isutc=False)
        entry2 = SwiftDateTimeSchema(met=2.0, utcf=0.0, isutc=False)
        swift_clock.entries = [entry1, entry2]
        assert swift_clock[0] == entry1

    def test_getitem_second(self, swift_clock):
        entry1 = SwiftDateTimeSchema(met=1.0, utcf=0.0, isutc=False)
        entry2 = SwiftDateTimeSchema(met=2.0, utcf=0.0, isutc=False)
        swift_clock.entries = [entry1, entry2]
        assert swift_clock[1] == entry2

    def test_table_property_empty(self, swift_clock):
        swift_clock.entries = []
        header, data = swift_clock._table
        assert header == []

    def test_table_data_empty(self, swift_clock):
        swift_clock.entries = []
        header, data = swift_clock._table
        assert data == []

    def test_table_property_with_entries_header(self, swift_clock_with_entry):
        header, data = swift_clock_with_entry._table
        assert header == ["MET", "Swift Time", "UTC Time"]

    def test_table_property_with_entries_data_length(self, swift_clock_with_entry):
        header, data = swift_clock_with_entry._table
        assert len(data) == 1

    def test_post_process_met_type(self, swift_clock):
        mock_entry = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert isinstance(swift_clock.met, float)

    def test_post_process_swifttime_type(self, swift_clock):
        mock_entry = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert isinstance(swift_clock.swifttime, datetime)

    def test_post_process_utctime_type(self, swift_clock):
        mock_entry = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        swift_clock.entries = [mock_entry]
        swift_clock._post_process()
        assert isinstance(swift_clock.utctime, datetime)

    def test_post_process_met_length(self, swift_clock):
        entry1 = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        entry2 = swiftdatetime.frommet(123456790.0, utcf=11.0, isutc=False)
        swift_clock.entries = [entry1, entry2]
        swift_clock._post_process()
        assert isinstance(swift_clock.met, list)
        assert len(swift_clock.met) == 2

    def test_post_process_swifttime_length(self, swift_clock):
        entry1 = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        entry2 = swiftdatetime.frommet(123456790.0, utcf=11.0, isutc=False)
        swift_clock.entries = [entry1, entry2]
        swift_clock._post_process()
        assert isinstance(swift_clock.swifttime, list)
        assert len(swift_clock.swifttime) == 2

    def test_post_process_utctime_length(self, swift_clock):
        entry1 = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        entry2 = swiftdatetime.frommet(123456790.0, utcf=11.0, isutc=False)
        swift_clock.entries = [entry1, entry2]
        swift_clock._post_process()
        assert isinstance(swift_clock.utctime, list)
        assert len(swift_clock.utctime) == 2

    def test_legacy_aliases(self, swift_clock):
        entry = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        swift_clock.entries = [entry]
        swift_clock._post_process()
        assert swift_clock.utc == swift_clock.utctime
        assert swift_clock.swift == swift_clock.swifttime
        assert swift_clock.mettime == swift_clock.met


class TestTOOAPIClockCorrect:
    def test_to_utctime_calls_clock_method(self, mock_clock_correct):
        clock_mock = Mock()
        clock_mock.entries = [datetime(2023, 1, 2)]
        mock_clock_correct._clock = clock_mock
        mock_clock_correct._datetime_refs = [([("model", "test_datetime")], datetime(2023, 1, 1))]
        mock_clock_correct.to_utctime()
        clock_mock.to_utctime.assert_called_once()

    def test_to_swifttime_calls_clock_method(self, mock_clock_correct):
        clock_mock = Mock()
        clock_mock.entries = [datetime(2023, 1, 2)]
        mock_clock_correct._clock = clock_mock
        mock_clock_correct._datetime_refs = [([("model", "test_datetime")], datetime(2023, 1, 1))]
        mock_clock_correct.to_swifttime()
        clock_mock.to_swifttime.assert_called_once()

    def test_header_title_utc(self, mock_clock_correct):
        mock_clock_correct._varnames = {"test_datetime": "Test DateTime"}
        mock_clock_correct.test_datetime = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)
        title = mock_clock_correct._header_title("test_datetime")
        assert "UTC" in title

    def test_header_title_swift(self, mock_clock_correct):
        mock_clock_correct._varnames = {"test_datetime": "Test DateTime"}
        mock_clock_correct.test_datetime = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=False)
        title = mock_clock_correct._header_title("test_datetime")
        assert "Swift" in title

    def test_clock_correct_creates_clock(self, mock_clock_correct):
        mock_clock_correct.nested_dict = {"inner_date": datetime(2023, 1, 1)}
        mock_clock_correct.nested_list = [datetime(2023, 1, 1)]
        mock_clock_correct.nested_schema = BaseSchema(nested_date=datetime(2023, 1, 1))
        mock_clock_correct.clock_instance = SwiftClock(autosubmit=False)
        with patch("swifttools.swift_too.swift.clock.Clock") as mock_clock_class:
            mock_clock_instance = mock_clock_class.return_value
            mock_clock_instance.entries = [
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
                datetime(2023, 1, 5),
            ]
            mock_clock_correct.clock_correct()
            mock_clock_class.assert_called_once()

    def test_clock_correct_nested_traversal_success(self):
        mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
        mock.nested_list = [datetime(2023, 1, 1)]
        mock._clock = Mock()
        mock._datetime_refs = [([("model", "nested_list"), ("list", 0)], datetime(2023, 1, 1))]
        mock._clock.entries = [datetime(2023, 2, 2)]
        mock.clock_correct()
        assert mock.nested_list[0] == datetime(2023, 2, 2)

    def test_clock_correct_nested_dict_traversal_success(self):
        mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
        mock.nested_dict = {"inner": datetime(2023, 1, 1)}
        mock._clock = Mock()
        mock._datetime_refs = [([("model", "nested_dict"), ("dict", "inner")], datetime(2023, 1, 1))]
        mock._clock.entries = [datetime(2023, 3, 3)]
        mock.clock_correct()
        assert mock.nested_dict["inner"] == datetime(2023, 3, 3)


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

    def test_valid_mettime_alias(self):
        schema = SwiftClockGetSchema(mettime=123456789.0)
        assert schema.met == 123456789.0

    def test_valid_utc_alias(self):
        dt = datetime(2023, 1, 1)
        schema = SwiftClockGetSchema(utc=dt)
        assert schema.utctime == dt

    def test_valid_swift_alias(self):
        dt = datetime(2023, 1, 1)
        schema = SwiftClockGetSchema(swift=dt)
        assert schema.swifttime == dt


class TestIndexDatetimes:
    def test_with_mock_object_count(self):
        test_obj = Mock()
        test_obj.date = datetime(2023, 1, 1)
        test_obj.model_dump.return_value = {"date": datetime(2023, 1, 1)}
        i, values = index_datetimes(test_obj)
        assert i == 1

    def test_with_mock_object_values(self):
        test_obj = Mock()
        test_obj.date = datetime(2023, 1, 1)
        test_obj.model_dump.return_value = {"date": datetime(2023, 1, 1)}
        i, values = index_datetimes(test_obj)
        assert len(values) == 1

    def test_with_mock_object_value_content(self):
        test_obj = Mock()
        test_obj.date = datetime(2023, 1, 1)
        test_obj.model_dump.return_value = {"date": datetime(2023, 1, 1)}
        i, values = index_datetimes(test_obj)
        assert values[0] == datetime(2023, 1, 1)

    def test_with_dict_count(self):
        test_dict = {"date": datetime(2023, 1, 1)}
        i, values = index_datetimes(test_dict)
        assert i == 1

    def test_with_dict_values(self):
        test_dict = {"date": datetime(2023, 1, 1)}
        i, values = index_datetimes(test_dict)
        assert len(values) == 1

    def test_with_dict_value_content(self):
        test_dict = {"date": datetime(2023, 1, 1)}
        i, values = index_datetimes(test_dict)
        assert values[0] == datetime(2023, 1, 1)

    def test_setvals_with_dict(self):
        test_dict = {"date": datetime(2023, 1, 1)}
        new_dates = [datetime(2024, 1, 1)]
        index_datetimes(test_dict, setvals=new_dates)
        assert test_dict["date"] == datetime(2024, 1, 1)

    def test_with_simple_object_count(self):
        class SimpleObj:
            def __init__(self):
                self.date = datetime(2026, 1, 1)

        obj = SimpleObj()
        i, values = index_datetimes(obj)
        assert i == 1

    def test_with_simple_object_value(self):
        class SimpleObj:
            def __init__(self):
                self.date = datetime(2026, 1, 1)

        obj = SimpleObj()
        i, values = index_datetimes(obj)
        assert values[0] == datetime(2026, 1, 1)

    def test_with_container_count(self):
        class SimpleObj:
            def __init__(self):
                self.date = datetime(2026, 1, 1)

        class Container:
            def __init__(self):
                self.nested = SimpleObj()

        c = Container()
        i, values = index_datetimes(c)
        assert i == 1

    def test_with_container_value(self):
        class SimpleObj:
            def __init__(self):
                self.date = datetime(2026, 1, 1)

        class Container:
            def __init__(self):
                self.nested = SimpleObj()

        c = Container()
        i, values = index_datetimes(c)
        assert values[0] == datetime(2026, 1, 1)

    def test_skips_swiftclock_count(self):
        container = {"clock": SwiftClock(autosubmit=False)}
        i, values = index_datetimes(container)
        assert i == 0

    def test_skips_swiftclock_values(self):
        container = {"clock": SwiftClock(autosubmit=False)}
        i, values = index_datetimes(container)
        assert values == []

    def test_list_recursion_and_setattr_list_index(self):
        # List recursion
        d = {"dates": [datetime(2020, 1, 1), datetime(2021, 1, 1)]}
        i, values = index_datetimes(d)
        assert i == 2

    def test_list_recursion_and_setattr_list_length(self):
        # List recursion
        d = {"dates": [datetime(2020, 1, 1), datetime(2021, 1, 1)]}
        i, values = index_datetimes(d)
        assert len(values) == 2

    def test_list_recursion_and_setattr_setattr(self):
        # setattr path when dictionary is an object
        class Obj:
            def __init__(self):
                self.date = datetime(2022, 1, 1)

        o = Obj()
        new = [datetime(2030, 1, 1)]
        i, values = index_datetimes(o, setvals=new)
        assert o.date == datetime(2030, 1, 1)

    def test_dict_recursion_index(self):
        nested = {"outer": {"inner": datetime(2010, 1, 1)}}
        i, values = index_datetimes(nested)
        assert i == 1

    def test_dict_recursion_values(self):
        nested = {"outer": {"inner": datetime(2010, 1, 1)}}
        i, values = index_datetimes(nested)
        assert values[0] == datetime(2010, 1, 1)


class TestClockCorrectAssertion:
    def test_assertion_on_list_path(self, mock_clock_correct):
        mock_clock_correct._clock = Mock()
        mock_clock_correct._datetime_refs = [([("list", 0)], datetime(2023, 1, 1))]
        mock_clock_correct._clock.entries = [datetime(2023, 1, 2)]
        with pytest.raises(AssertionError, match="Expected list but got"):
            mock_clock_correct.clock_correct()

    def test_assertion_on_dict_path(self, mock_clock_correct):
        mock_clock_correct._clock = Mock()
        mock_clock_correct._datetime_refs = [([("dict", "k")], datetime(2023, 1, 1))]
        mock_clock_correct._clock.entries = [datetime(2023, 1, 2)]
        with pytest.raises(AssertionError, match="Expected dict but got"):
            mock_clock_correct.clock_correct()
