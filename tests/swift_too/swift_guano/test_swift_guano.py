from datetime import datetime, timedelta

from swifttools.swift_too.swift.guano import (
    SwiftGUANO,
    SwiftGUANOData,
    SwiftGUANOEntry,
    SwiftGUANOGTI,
)


class TestSwiftGUANOGTI:
    def test_str_representation(self):
        """Test string representation of SwiftGUANOGTI."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 30, 0)
        exposure = timedelta(minutes=30)

        gti = SwiftGUANOGTI(begin=begin, end=end, exposure=exposure)

        expected = f"{begin} - {end} ({exposure})"
        assert str(gti) == expected


class TestSwiftGUANOData:
    def test_utcf_property(self):
        """Test utcf property returns gti.utcf when gti exists."""
        gti = SwiftGUANOGTI(utcf=0.5)
        data = SwiftGUANOData(gti=gti, all_gtis=[])

        assert data.utcf == 0.5

    def test_utcf_property_no_gti(self):
        """Test utcf property returns None when gti is None."""
        data = SwiftGUANOData(gti=None, all_gtis=[])

        assert data.utcf is None

    def test_subthresh_property_true(self):
        """Test subthresh property returns True for single ms file."""
        data = SwiftGUANOData(filenames=["file_ms.fits"], all_gtis=[])

        assert data.subthresh is True

    def test_subthresh_property_false_multiple_files(self):
        """Test subthresh property returns False for multiple files."""
        data = SwiftGUANOData(filenames=["file1.fits", "file2.fits"], all_gtis=[])

        assert data.subthresh is False

    def test_subthresh_property_false_no_ms(self):
        """Test subthresh property returns False for single file without ms."""
        data = SwiftGUANOData(filenames=["file.fits"], all_gtis=[])

        assert data.subthresh is False

    def test_subthresh_property_none(self):
        """Test subthresh property returns None when filenames is None."""
        data = SwiftGUANOData(filenames=None, all_gtis=[])

        assert data.subthresh is None


class TestSwiftGUANOEntry:
    def test_executed_property_true(self):
        """Test executed property returns True when quadsaway is not 2 or 3."""
        entry = SwiftGUANOEntry(quadsaway=0)
        assert entry.executed is True

        entry = SwiftGUANOEntry(quadsaway=1)
        assert entry.executed is True

    def test_executed_property_false(self):
        """Test executed property returns False when quadsaway is 2 or 3."""
        entry = SwiftGUANOEntry(quadsaway=2)
        assert entry.executed is False

        entry = SwiftGUANOEntry(quadsaway=3)
        assert entry.executed is False

    def test_uplinked_property_true(self):
        """Test uplinked property returns True when quadsaway is not 1 or 3."""
        entry = SwiftGUANOEntry(quadsaway=0)
        assert entry.uplinked is True

        entry = SwiftGUANOEntry(quadsaway=2)
        assert entry.uplinked is True

    def test_uplinked_property_false(self):
        """Test uplinked property returns False when quadsaway is 1 or 3."""
        entry = SwiftGUANOEntry(quadsaway=1)
        assert entry.uplinked is False

        entry = SwiftGUANOEntry(quadsaway=3)
        assert entry.uplinked is False

    def test_calc_begin_end(self):
        """Test _calc_begin_end method calculates correct begin and end times."""
        triggertime = datetime(2023, 1, 1, 12, 0, 0)
        offset = 100
        duration = 50

        entry = SwiftGUANOEntry(triggertime=triggertime, offset=offset, duration=duration)
        entry._calc_begin_end()

        expected_begin = triggertime + timedelta(seconds=offset - duration / 2)
        expected_end = triggertime + timedelta(seconds=offset + duration / 2)

        assert entry.begin == expected_begin
        assert entry.end == expected_end

    def test_table_property_with_data_exposure(self):
        """Test _table property when data has exposure."""
        data = SwiftGUANOData(exposure=100.5, all_gtis=[])
        entry = SwiftGUANOEntry(data=data, triggertime=datetime.now())

        header, table = entry._table

        assert header == ["Parameter", "Value"]
        data_row = next((row for row in table if row[0] == "data"), None)
        assert data_row is not None
        assert "100.5s of BAT event data" in data_row[1]

    def test_table_property_without_data_exposure(self):
        """Test _table property when data has no exposure."""
        data = SwiftGUANOData(exposure=None, all_gtis=[])
        entry = SwiftGUANOEntry(data=data, triggertime=datetime.now())

        header, table = entry._table

        assert header == ["Parameter", "Value"]
        data_row = next((row for row in table if row[0] == "data"), None)
        assert data_row is not None
        assert "No BAT event data found" in data_row[1]


class TestSwiftGUANO:
    def test_getitem_and_len(self):
        """Test __getitem__ and __len__ methods."""
        entry1 = SwiftGUANOEntry()
        entry2 = SwiftGUANOEntry()
        #        with patch("swifttools.swift_too.swift.guano.SwiftGUANO.validate_get", return_value=False):
        guano = SwiftGUANO(entries=[entry1, entry2])

        assert len(guano) == 2
        assert guano[0] == entry1
        assert guano[1] == entry2

    def test_validate_success(self):
        """Test validate method returns True for valid parameters."""
        guano = SwiftGUANO(begin=datetime.now(), username="testuser")

        assert guano.validate() is True

    def test_table_property(self):
        """Test _table property formats entries correctly."""
        triggertime = datetime(2023, 1, 1, 12, 0, 0)
        data = SwiftGUANOData(exposure=100.0, all_gtis=[])

        entry = SwiftGUANOEntry(
            triggertype="GRB", triggertime=triggertime, offset=50, duration=100, obs_id="12345", data=data
        )

        guano = SwiftGUANO(entries=[entry])
        header, table = guano._table

        expected_header = ["Trigger Type", "Trigger Time", "Offset (s)", "Window Duration (s)", "Observation ID"]

        assert header == expected_header
        assert len(table) == 1
        assert table[0][0] == "GRB"
        assert table[0][1] == triggertime
        assert table[0][2] == 50
        assert table[0][3] == "100.0*"
        assert table[0][4] == "12345"
