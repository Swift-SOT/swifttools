from datetime import datetime
from unittest.mock import Mock, patch

from swifttools.swift_too.swift_clock import (
    SwiftClock,
    SwiftDateTimeSchema,
    TOOAPIClockCorrect,
    index_datetimes,
)
from swifttools.swift_too.swift_datetime import swiftdatetime


class TestSwiftDateTimeSchema:
    def test_swifttime_computed_field(self):
        """Test that swifttime computed field returns correct swiftdatetime."""
        with patch("swifttools.swift_too.swift_clock.swiftdatetime.frommet") as mock_frommet:
            mock_dt = Mock()
            mock_dt.swifttime = datetime(2023, 1, 1, 12, 0, 0)
            mock_frommet.return_value = mock_dt

            schema = SwiftDateTimeSchema(met=123456.0, utcf=1.0, isutc=False)
            result = schema.swifttime

            mock_frommet.assert_called_once_with(123456.0, utcf=1.0, isutc=False)
            assert result == datetime(2023, 1, 1, 12, 0, 0)

    def test_utctime_computed_field(self):
        """Test that utctime computed field returns correct swiftdatetime."""
        with patch("swifttools.swift_too.swift_clock.swiftdatetime.frommet") as mock_frommet:
            mock_dt = Mock()
            mock_dt.utctime = datetime(2023, 1, 1, 12, 0, 0)
            mock_frommet.return_value = mock_dt

            schema = SwiftDateTimeSchema(met=123456.0, utcf=1.0, isutc=True)
            result = schema.utctime

            mock_frommet.assert_called_once_with(123456.0, utcf=1.0, isutc=True)
            assert result == datetime(2023, 1, 1, 12, 0, 0)


class TestSwiftClock:
    def test_init_with_defaults(self):
        """Test SwiftClock initialization with default values."""
        clock = SwiftClock()
        assert clock.met is None
        assert clock.utctime is None
        assert clock.swifttime is None
        assert clock.entries == []

    def test_post_process(self):
        """Test _post_process method converts entries correctly."""
        with patch("swifttools.swift_too.swift_clock.swiftdatetime.frommet") as mock_frommet:
            mock_entry1 = Mock()
            mock_entry1.met = 123456.0
            mock_entry1.swifttime = datetime(2023, 1, 1, 12, 0, 0)
            mock_entry1.utctime = datetime(2023, 1, 1, 12, 0, 1)

            mock_entry2 = Mock()
            mock_entry2.met = 123457.0
            mock_entry2.swifttime = datetime(2023, 1, 1, 12, 0, 1)
            mock_entry2.utctime = datetime(2023, 1, 1, 12, 0, 2)

            mock_frommet.side_effect = [mock_entry1, mock_entry2]

            clock = SwiftClock()
            clock.entries = [
                SwiftDateTimeSchema(met=123456.0, utcf=1.0, isutc=False),
                SwiftDateTimeSchema(met=123457.0, utcf=1.0, isutc=False),
            ]

            clock._post_process()

            assert clock.met == [123456.0, 123457.0]
            assert clock.swifttime == [datetime(2023, 1, 1, 12, 0, 0), datetime(2023, 1, 1, 12, 0, 1)]
            assert clock.utctime == [datetime(2023, 1, 1, 12, 0, 1), datetime(2023, 1, 1, 12, 0, 2)]

    def test_getitem(self):
        """Test __getitem__ method."""
        clock = SwiftClock()
        mock_entry = Mock()
        clock.entries = [mock_entry]

        assert clock[0] == mock_entry

    def test_len_with_entries(self):
        """Test __len__ method with entries."""
        clock = SwiftClock()
        clock.entries = [Mock(), Mock(), Mock()]

        assert len(clock) == 3

    def test_len_without_entries(self):
        """Test __len__ method without entries."""
        clock = SwiftClock()
        clock.entries = None

        assert len(clock) == 0

    def test_table_property_with_entries(self):
        """Test _table property with entries."""
        clock = SwiftClock()
        mock_entry1 = Mock()
        mock_entry1._table = [["header1", "header2"], [["value1", "value2"]]]
        mock_entry2 = Mock()
        mock_entry2._table = [["header1", "header2"], [["value3", "value4"]]]

        clock.entries = [mock_entry1, mock_entry2]

        header, values = clock._table
        assert header == ["header1", "header2"]
        assert values == [["value1", "value2"], ["value3", "value4"]]

    def test_table_property_without_entries(self):
        """Test _table property without entries."""
        clock = SwiftClock()
        clock.entries = []

        header, values = clock._table
        assert header == []
        assert values == []

    def test_to_utctime(self):
        """Test to_utctime method."""
        with patch("swifttools.swift_too.swift_clock.swiftdatetime.frommet") as mock_frommet:
            mock_entry1 = Mock()
            mock_entry1.met = 123456.0
            mock_entry1.utcf = 1.0

            mock_entry2 = Mock()
            mock_entry2.met = 123457.0
            mock_entry2.utcf = 2.0

            mock_converted1 = Mock()
            mock_converted2 = Mock()
            mock_frommet.side_effect = [mock_converted1, mock_converted2]

            clock = SwiftClock()
            clock.entries = [mock_entry1, mock_entry2]

            clock.to_utctime()

            assert mock_frommet.call_count == 2
            mock_frommet.assert_any_call(123456.0, utcf=1.0, isutc=True)
            mock_frommet.assert_any_call(123457.0, utcf=2.0, isutc=True)
            assert clock.entries == [mock_converted1, mock_converted2]

    def test_to_swifttime(self):
        """Test to_swifttime method."""
        with patch("swifttools.swift_too.swift_clock.swiftdatetime.frommet") as mock_frommet:
            mock_entry1 = Mock()
            mock_entry1.met = 123456.0
            mock_entry1.utcf = 1.0

            mock_entry2 = Mock()
            mock_entry2.met = 123457.0
            mock_entry2.utcf = 2.0

            mock_converted1 = Mock()
            mock_converted2 = Mock()
            mock_frommet.side_effect = [mock_converted1, mock_converted2]

            clock = SwiftClock()
            clock.entries = [mock_entry1, mock_entry2]

            clock.to_swifttime()

            assert mock_frommet.call_count == 2
            mock_frommet.assert_any_call(123456.0, utcf=1.0, isutc=False)
            mock_frommet.assert_any_call(123457.0, utcf=2.0, isutc=False)
            assert clock.entries == [mock_converted1, mock_converted2]


class TestIndexDatetimes:
    def test_index_datetimes_with_datetime_values(self):
        """Test index_datetimes function with datetime values."""
        dt1 = datetime(2023, 1, 1, 12, 0, 0)
        dt2 = datetime(2023, 1, 2, 12, 0, 0)

        dictionary = {"date1": dt1, "date2": dt2, "other": "value"}

        i, values = index_datetimes(dictionary)

        assert i == 2
        assert values == [dt1, dt2]

    def test_index_datetimes_with_setvals(self):
        """Test index_datetimes function with setvals parameter."""
        dt1 = datetime(2023, 1, 1, 12, 0, 0)
        new_dt1 = datetime(2023, 1, 1, 12, 0, 1)

        dictionary = {"date1": dt1}
        setvals = [new_dt1]

        i, values = index_datetimes(dictionary, setvals=setvals)

        assert dictionary["date1"] == new_dt1

    def test_header_title_with_swiftdatetime_utc(self):
        """Test _header_title method with UTC swiftdatetime."""

        class TestClass(TOOAPIClockCorrect):
            def __init__(self):
                self._varnames = {"test_param": "Test Parameter"}
                self.test_param = swiftdatetime.frommet(123456.0, utcf=1.0, isutc=True)
                self.test_param.isutc = True

        test_obj = TestClass()
        result = test_obj._header_title("test_param")

        assert result == "Test Parameter (UTC)"

    def test_header_title_with_swiftdatetime_swift(self):
        """Test _header_title method with Swift swiftdatetime."""

        class TestClass(TOOAPIClockCorrect):
            def __init__(self):
                self._varnames = {"test_param": "Test Parameter"}
                self.test_param = swiftdatetime.frommet(123456.0, utcf=1.0, isutc=False)

        test_obj = TestClass()
        result = test_obj._header_title("test_param")

        assert result == "Test Parameter (Swift)"

    def test_header_title_with_non_swiftdatetime(self):
        """Test _header_title method with non-swiftdatetime value."""

        class TestClass(TOOAPIClockCorrect):
            def __init__(self):
                self._varnames = {"test_param": "Test Parameter"}
                self.test_param = "some_value"

        test_obj = TestClass()
        result = test_obj._header_title("test_param")

        assert result == "Test Parameter"
