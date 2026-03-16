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
    object.__setattr__(clock, "entries", [1, 2, 3])
    assert len(clock) == 3


def test_swift_clock_getitem():
    """Test indexing"""
    clock = SwiftClock(autosubmit=False)
    # Use real SwiftDateTimeSchema entries to satisfy validation
    from swifttools.swift_too.swift.clock import SwiftDateTimeSchema

    clock.entries = [
        SwiftDateTimeSchema(met=1.0, utcf=0.0, isutc=False),
        SwiftDateTimeSchema(met=2.0, utcf=0.0, isutc=False),
    ]
    assert clock[0].met == 1.0
    assert clock[1].met == 2.0


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

    # Create a minimal SwiftDateTimeSchema instance with a compatible _table
    from swifttools.swift_too.swift.clock import SwiftDateTimeSchema

    mock_entry = SwiftDateTimeSchema(met=123456789.0, utcf=0.0, isutc=False)
    # attach a _table attribute expected by the code
    object.__setattr__(
        mock_entry,
        "_table",
        [["MET", "Swift Time", "UTC Time"], [123456789.0, datetime(2023, 1, 1), datetime(2023, 1, 1)]],
    )
    clock.entries = [mock_entry]

    header, data = clock._table
    assert header == ["MET", "Swift Time", "UTC Time"]
    assert len(data) == 1


def test_tooapi_clock_correct_to_utctime():
    """Test TOOAPIClockCorrect to_utctime method"""
    from unittest.mock import Mock

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    # Set private attributes using object.__setattr__ to avoid pydantic hooks
    clock_mock = Mock()
    clock_mock.entries = [datetime(2023, 1, 2)]
    object.__setattr__(mock, "_clock", clock_mock)
    object.__setattr__(mock, "_datetime_refs", [([("model", "test_datetime")], datetime(2023, 1, 1))])
    # Don't patch clock_correct - it overwrites _clock
    mock.to_utctime()
    clock_mock.to_utctime.assert_called_once()


def test_tooapi_clock_correct_to_swifttime():
    """Test TOOAPIClockCorrect to_swifttime method"""
    from unittest.mock import Mock

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    clock_mock = Mock()
    clock_mock.entries = [datetime(2023, 1, 2)]
    object.__setattr__(mock, "_clock", clock_mock)
    object.__setattr__(mock, "_datetime_refs", [([("model", "test_datetime")], datetime(2023, 1, 1))])
    # Don't patch clock_correct - it overwrites _clock
    mock.to_swifttime()
    clock_mock.to_swifttime.assert_called_once()


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
        # Check that to_utctime was called on the clock instance
        mock_clock_instance.to_utctime.assert_called_once()
        # Check _datetime_refs was set
        assert mock._datetime_refs is not None
        # Call again to cover the else branch
        mock.clock_correct()


def test_index_datetimes_object_attributes_and_dictrecursion():
    """Test index_datetimes iterates object attributes and __dict__ recursion"""
    from swifttools.swift_too.swift.clock import index_datetimes

    class SimpleObj:
        def __init__(self):
            self.date = datetime(2026, 1, 1)

    obj = SimpleObj()
    i, values = index_datetimes(obj)
    assert i == 1
    assert values[0] == datetime(2026, 1, 1)

    # Test recursion via __dict__ for nested object
    class Container:
        def __init__(self):
            self.nested = SimpleObj()

    c = Container()
    i, values = index_datetimes(c)
    assert i == 1
    assert values[0] == datetime(2026, 1, 1)


def test_index_datetimes_skips_swiftclock_instances():
    """Ensure SwiftClock instances are skipped when indexing"""
    from swifttools.swift_too.swift.clock import SwiftClock, index_datetimes

    container = {"clock": SwiftClock(autosubmit=False)}
    i, values = index_datetimes(container)
    assert i == 0
    assert values == []


def test_clock_correct_assertion_on_incorrect_path_types():
    """Trigger assertion branches when path expects list or dict but finds others"""
    from unittest.mock import Mock

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    # Prevent creation of a new Clock
    mock._clock = Mock()

    # List assertion: path indicates list but current is not a list
    mock._datetime_refs = [([("list", 0)], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2023, 1, 2)]
    with pytest.raises(AssertionError, match="Expected list but got"):
        mock.clock_correct()

    # Dict assertion: path indicates dict but current is not a dict
    mock._datetime_refs = [([("dict", "k")], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2023, 1, 2)]
    with pytest.raises(AssertionError, match="Expected dict but got"):
        mock.clock_correct()


def test_swift_clock_len_with_none_entries():
    """len() should return 0 when entries is empty list"""
    clock = SwiftClock(autosubmit=False)
    # In Pydantic v2, entries cannot be None - use empty list instead
    clock.entries = []
    assert len(clock) == 0


def test_index_datetimes_list_recursion_and_setattr():
    from swifttools.swift_too.swift.clock import index_datetimes

    # List recursion
    d = {"dates": [datetime(2020, 1, 1), datetime(2021, 1, 1)]}
    i, values = index_datetimes(d)
    assert i == 2
    assert len(values) == 2

    # setattr path when dictionary is an object
    class Obj:
        def __init__(self):
            self.date = datetime(2022, 1, 1)

    o = Obj()
    new = [datetime(2030, 1, 1)]
    i, values = index_datetimes(o, setvals=new)
    assert o.date == datetime(2030, 1, 1)


def test_clock_correct_nested_traversal_success():
    from unittest.mock import Mock

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    mock.nested_list = [datetime(2023, 1, 1)]
    # Prevent creation of a new Clock
    mock._clock = Mock()
    mock._datetime_refs = [([("model", "nested_list"), ("list", 0)], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2023, 2, 2)]
    mock.clock_correct()
    assert mock.nested_list[0] == datetime(2023, 2, 2)


def test_clock_correct_nested_dict_traversal_success():
    from unittest.mock import Mock

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    mock.nested_dict = {"inner": datetime(2023, 1, 1)}
    # Prevent creation of a new Clock
    mock._clock = Mock()
    mock._datetime_refs = [([("model", "nested_dict"), ("dict", "inner")], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2023, 3, 3)]
    mock.clock_correct()
    assert mock.nested_dict["inner"] == datetime(2023, 3, 3)


def test_index_datetimes_dict_recursion():
    from swifttools.swift_too.swift.clock import index_datetimes

    nested = {"outer": {"inner": datetime(2010, 1, 1)}}
    i, values = index_datetimes(nested)
    assert i == 1
    assert values[0] == datetime(2010, 1, 1)


def test_clock_correct_collects_dict_in_model_field():
    from unittest.mock import patch

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))
    # create a child BaseSchema that contains a dict
    # Attach a plain dict directly into __dict__ so BaseSchema __dict__ exposes it
    object.__setattr__(mock, "some_dict", {"d": datetime(2022, 2, 2)})
    # Patch Clock so we don't call real implementation
    with patch("swifttools.swift_too.swift.clock.Clock"):
        mock.clock_correct()
        # ensure datetime_refs were collected and include the dict key
        assert hasattr(mock, "_datetime_refs")
        # check at least one path element contains a dict entry
        assert any(any(k == "dict" for k, _ in path) for path, _ in mock._datetime_refs)


def test_clock_correct_inner_list_and_dict_traversal_branches():
    from unittest.mock import Mock

    mock = MockClockCorrect(test_datetime=datetime(2023, 1, 1))

    # Create structure: self.outer -> list -> element with attribute 'attr'
    Elem = type("Elem", (), {"attr": datetime(2023, 1, 1)})
    mock.outer = [Elem()]
    mock._clock = Mock()
    mock._datetime_refs = [([("model", "outer"), ("list", 0), ("model", "attr")], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2029, 9, 9)]
    mock.clock_correct()
    assert mock.outer[0].attr == datetime(2029, 9, 9)

    # Create structure: self.outerdict -> dict -> element with attribute 'attr'
    mock.outerdict = {"k": Elem()}
    mock._clock = Mock()
    mock._datetime_refs = [([("model", "outerdict"), ("dict", "k"), ("model", "attr")], datetime(2023, 1, 1))]
    mock._clock.entries = [datetime(2030, 10, 10)]
    mock.clock_correct()
    assert mock.outerdict["k"].attr == datetime(2030, 10, 10)
