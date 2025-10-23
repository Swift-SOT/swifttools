from unittest.mock import MagicMock

from swifttools.swift_too.swift.uvot import (
    Swift_UVOTModeEntry,
    SwiftUVOTMode,
    SwiftUVOTModeEntry,
    UVOT_mode_entry,
    UVOTModeEntry,
)


class TestSwiftUVOTModeEntry:
    def test_init_default_values(self):
        """Test initialization with default values."""
        entry = SwiftUVOTModeEntry()

        assert entry.uvotmode == 0
        assert entry.filter_num is None
        assert entry.min_exposure is None
        assert entry.filter_pos is None
        assert entry.filter_seqid is None
        assert entry.eventmode is None
        assert entry.field_of_view is None
        assert entry.binning is None
        assert entry.max_exposure is None
        assert entry.weight is None
        assert entry.special is None
        assert entry.comment is None
        assert hasattr(entry, "filter_name")

    def test_init_with_parameters(self):
        """Test initialization with specific parameters."""
        entry = SwiftUVOTModeEntry()
        entry.uvotmode = 12345
        entry.filter_num = 1
        entry.min_exposure = 100
        entry.filter_pos = 2
        entry.filter_seqid = 3
        entry.eventmode = 1
        entry.field_of_view = 17
        entry.binning = 2
        entry.max_exposure = 1000
        entry.weight = 1
        entry.special = 0
        entry.comment = "Test comment"
        entry.filter_name = "V"

        assert entry.uvotmode == 12345
        assert entry.filter_num == 1
        assert entry.min_exposure == 100
        assert entry.filter_pos == 2
        assert entry.filter_seqid == 3
        assert entry.eventmode == 1
        assert entry.field_of_view == 17
        assert entry.binning == 2
        assert entry.max_exposure == 1000
        assert entry.weight == 1
        assert entry.special == 0
        assert entry.comment == "Test comment"
        assert entry.filter_name == "V"

    def test_str_representation(self):
        """Test string representation returns filter name."""
        entry = SwiftUVOTModeEntry()
        entry.filter_name = "UVW1"

        assert str(entry) == "UVW1"

    def test_str_representation_empty_filter_name(self):
        """Test string representation with empty filter name."""
        entry = SwiftUVOTModeEntry()
        entry.filter_name = ""

        assert str(entry) == ""

    def test_optional_parameters_none(self):
        """Test that optional parameters can be None."""
        entry = SwiftUVOTModeEntry()

        # All optional parameters should be None by default
        optional_params = [
            "filter_num",
            "min_exposure",
            "filter_pos",
            "filter_seqid",
            "eventmode",
            "field_of_view",
            "binning",
            "max_exposure",
            "weight",
            "special",
            "comment",
        ]

        for param in optional_params:
            assert getattr(entry, param) is None

    def test_parameter_assignment(self):
        """Test that parameters can be assigned after initialization."""
        entry = SwiftUVOTModeEntry()

        # Test assigning various types
        entry.uvotmode = 999
        entry.filter_name = "B"
        entry.eventmode = 0
        entry.comment = "Special filter mode"

        assert entry.uvotmode == 999
        assert entry.filter_name == "B"
        assert entry.eventmode == 0
        assert entry.comment == "Special filter mode"

    def test_boolean_like_parameters(self):
        """Test parameters that might be used as booleans."""
        entry = SwiftUVOTModeEntry()

        # Test eventmode and weight as boolean-like
        entry.eventmode = 1
        entry.weight = 0

        assert entry.eventmode == 1
        assert entry.weight == 0

    def test_has_required_attributes(self):
        """Test that entry has all expected attributes."""
        entry = SwiftUVOTModeEntry()

        required_attrs = [
            "uvotmode",
            "filter_num",
            "min_exposure",
            "filter_pos",
            "filter_seqid",
            "eventmode",
            "field_of_view",
            "binning",
            "max_exposure",
            "weight",
            "special",
            "comment",
            "filter_name",
        ]

        for attr in required_attrs:
            assert hasattr(entry, attr)

    def test_inheritance_from_base_schema(self):
        """Test that SwiftUVOTModeEntry properly inherits from BaseSchema."""
        entry = SwiftUVOTModeEntry()

        # Should have BaseSchema attributes/methods
        assert hasattr(entry, "__dict__")

    def test_aliases(self):
        """Test that class aliases work correctly."""
        entry1 = UVOTModeEntry()
        entry2 = UVOT_mode_entry()
        entry3 = Swift_UVOTModeEntry()

        assert isinstance(entry1, SwiftUVOTModeEntry)
        assert isinstance(entry2, SwiftUVOTModeEntry)
        assert isinstance(entry3, SwiftUVOTModeEntry)

    def test_numeric_parameters_types(self):
        """Test that numeric parameters accept appropriate types."""
        entry = SwiftUVOTModeEntry()

        # Test integer parameters
        entry.uvotmode = 12345
        entry.filter_num = 5
        entry.min_exposure = 50
        entry.max_exposure = 5000

        assert isinstance(entry.uvotmode, int)
        assert isinstance(entry.filter_num, int)
        assert isinstance(entry.min_exposure, int)
        assert isinstance(entry.max_exposure, int)

    def test_filter_name_string_type(self):
        """Test that filter_name accepts string values."""
        entry = SwiftUVOTModeEntry()

        filter_names = ["V", "B", "U", "UVW1", "UVM2", "UVW2", "WHITE"]

        for name in filter_names:
            entry.filter_name = name
            assert entry.filter_name == name
            assert isinstance(entry.filter_name, str)

    class TestSwiftUVOTMode:
        def test_str_with_rejected_status(self):
            """Test string representation with rejected status."""
            mode = SwiftUVOTMode()

            # Mock a rejected status
            mock_status = MagicMock()
            mock_status.__class__.__name__ = "TOOStatus"
            mock_status.__eq__ = lambda self, other: other == "Rejected"
            mock_status.errors = ["Invalid mode", "Missing parameter"]
            mode.status = mock_status

            result = str(mode)
            assert result == "Rejected with the following error(s): Invalid mode Missing parameter"

        def test_str_with_entries(self):
            """Test string representation with valid entries."""
            mode = SwiftUVOTMode()
            mode.uvotmode = 12345

            # Create mock entries
            entry1 = SwiftUVOTModeEntry()
            entry1.filter_name = "V"
            entry1.eventmode = 1
            entry1.field_of_view = 17
            entry1.binning = 1
            entry1.max_exposure = 1000
            entry1.weight = 1
            entry1.comment = "Test comment"

            entry2 = SwiftUVOTModeEntry()
            entry2.filter_name = "UVW1"
            entry2.eventmode = 0
            entry2.field_of_view = 17
            entry2.binning = 2
            entry2.max_exposure = 500
            entry2.weight = 0
            entry2.comment = "Another comment"

            mode.entries = [entry1, entry2]

            result = str(mode)

            assert "UVOT Mode: 12345" in result
            assert "The following table summarizes this mode" in result
            assert "Filter" in result
            assert "Event FOV" in result
            assert "Max. Exp. Time" in result
            assert "V" in result
            assert "UVW1" in result
            assert "Filter: The particular filter in the sequence." in result

        def test_str_with_no_data(self):
            """Test string representation with no entries."""
            mode = SwiftUVOTMode()
            mode.entries = None

            result = str(mode)
            assert result == "No data"

        def test_str_with_empty_entries(self):
            """Test string representation with empty entries list."""
            mode = SwiftUVOTMode()
            mode.uvotmode = 0
            mode.entries = []

            result = str(mode)

            assert "UVOT Mode: 0" in result
            assert "The following table summarizes this mode" in result

        def test_str_with_none_values_in_entries(self):
            """Test string representation with entries containing None values."""
            mode = SwiftUVOTMode()
            mode.uvotmode = 999

            entry = SwiftUVOTModeEntry()
            entry.uvotmode = 999
            entry.filter_name = None
            entry.eventmode = None
            entry.field_of_view = None
            entry.binning = None
            entry.max_exposure = None
            entry.weight = None
            entry.comment = None

            mode.entries = [entry]

            result = str(mode)

            assert "UVOT Mode: 999" in result

        def test_str_formatting_structure(self):
            """Test the overall structure of the string output."""
            mode = SwiftUVOTMode()
            mode.uvotmode = 54321

            entry = SwiftUVOTModeEntry()
            entry.filter_name = "B"
            entry.eventmode = 1
            entry.field_of_view = 17
            entry.binning = 1
            entry.max_exposure = 800
            entry.weight = 1
            entry.comment = "Blue filter"

            mode.entries = [entry]

            result = str(mode)

            # Check that all expected sections are present
            assert result.startswith("UVOT Mode: 54321")
            assert "Filter:" in result and "The particular filter in the sequence." in result
            assert "Event FOV:" in result and "UVOT event data." in result
            assert "Image FOV:" in result and "UVOT image data." in result
            assert "Max. Exp. Time:" in result and "maximum amount of time" in result
            assert "Weighting:" in result and "Ratio of time spent" in result
            assert "Comments:" in result and "Additional notes" in result


class TestSwiftUVOTModeReprHTML:
    def test_repr_html_with_rejected_status(self):
        """Test HTML representation with rejected status."""
        mode = SwiftUVOTMode()

        # Mock a rejected status
        mock_status = MagicMock()
        mock_status.__class__.__name__ = "TOOStatus"
        mock_status.__eq__ = lambda self, other: other == "Rejected"
        mock_status.errors = ["Invalid mode", "Missing parameter"]
        mode.status = mock_status

        result = mode._repr_html_()
        assert result == "<b>Rejected with the following error(s): </b>Invalid mode Missing parameter"

    def test_repr_html_with_entries(self):
        """Test HTML representation with valid entries."""
        mode = SwiftUVOTMode()
        mode.uvotmode = 12345

        # Create mock entries
        entry1 = SwiftUVOTModeEntry()
        entry1.filter_name = "V"
        entry1.eventmode = 1
        entry1.field_of_view = 17
        entry1.binning = 1
        entry1.max_exposure = 1000
        entry1.weight = 1
        entry1.comment = "Test comment"

        entry2 = SwiftUVOTModeEntry()
        entry2.filter_name = "UVW1"
        entry2.eventmode = 0
        entry2.field_of_view = 17
        entry2.binning = 2
        entry2.max_exposure = 500
        entry2.weight = 0
        entry2.comment = "Another comment"

        mode.entries = [entry1, entry2]

        result = mode._repr_html_()

        # Check HTML structure
        assert "<h2>UVOT Mode: 12345</h2>" in result
        assert "<p>The following table summarizes this mode" in result
        assert '<table id="modelist"' in result
        assert "<th>Filter</th>" in result
        assert "<th>Event FOV</th>" in result
        assert "<th>Max. Exp. Time</th>" in result
        assert "<td>V</td>" in result
        assert "<td>UVW1</td>" in result
        assert '<p id="terms">' in result
        assert "<b>Filter: </b>The particular filter in the sequence." in result

    def test_repr_html_with_no_data(self):
        """Test HTML representation with no entries."""
        mode = SwiftUVOTMode()
        mode.entries = None

        result = mode._repr_html_()
        assert result == "No data"

    def test_repr_html_with_empty_entries(self):
        """Test HTML representation with empty entries list."""
        mode = SwiftUVOTMode()
        mode.uvotmode = 0
        mode.entries = []

        result = mode._repr_html_()

        assert "<h2>UVOT Mode: 0</h2>" in result
        assert "<p>The following table summarizes this mode" in result
        assert '<table id="modelist"' in result

    def test_repr_html_alternating_row_colors(self):
        """Test HTML representation with alternating row background colors."""
        mode = SwiftUVOTMode()
        mode.uvotmode = 999

        # Create multiple entries to test alternating colors
        entries = []
        for i in range(4):
            entry = SwiftUVOTModeEntry()
            entry.filter_name = f"Filter{i}"
            entry.eventmode = i % 2
            entry.field_of_view = 17
            entry.binning = 1
            entry.max_exposure = 1000
            entry.weight = 1
            entry.comment = f"Comment {i}"
            entries.append(entry)

        mode.entries = entries

        result = mode._repr_html_()

        # Check for alternating row styles
        assert '<tr style="background-color:#eee;">' in result
        assert "<tr>" in result

    def test_repr_html_with_none_values_in_entries(self):
        """Test HTML representation with entries containing None values."""
        mode = SwiftUVOTMode()
        mode.uvotmode = 999

        entry = SwiftUVOTModeEntry()
        entry.filter_name = None
        entry.eventmode = None
        entry.field_of_view = None
        entry.binning = None
        entry.max_exposure = None
        entry.weight = None
        entry.comment = None

        mode.entries = [entry]

        result = mode._repr_html_()

        assert "<h2>UVOT Mode: 999</h2>" in result
        assert "<td>None</td>" in result

    def test_repr_html_table_structure(self):
        """Test the HTML table structure and column headers."""
        mode = SwiftUVOTMode()
        mode.uvotmode = 54321

        entry = SwiftUVOTModeEntry()
        entry.filter_name = "B"
        entry.eventmode = 1
        entry.field_of_view = 17
        entry.binning = 1
        entry.max_exposure = 800
        entry.weight = 1
        entry.comment = "Blue filter"

        mode.entries = [entry]

        result = mode._repr_html_()

        # Check table headers
        expected_headers = [
            "<th>Filter</th>",
            "<th>Event FOV</th>",
            "<th>Image FOV</th>",
            "<th>Bin Size</th>",
            "<th>Max. Exp. Time</th>",
            "<th>Weighting</th>",
            "<th>Comments</th>",
        ]

        for header in expected_headers:
            assert header in result

        # Check table data
        assert "<td>B</td>" in result
        assert "<td>1</td>" in result
        assert "<td>17</td>" in result
        assert "<td>800</td>" in result
        assert "<td>Blue filter</td>" in result

    def test_repr_html_footer_explanations(self):
        """Test the HTML representation includes all footer explanations."""
        mode = SwiftUVOTMode()
        mode.uvotmode = 123
        mode.entries = [SwiftUVOTModeEntry()]

        result = mode._repr_html_()

        # Check all explanations are present
        explanations = [
            "<b>Filter: </b>The particular filter in the sequence.",
            "<b>Event FOV: </b>The size of the FOV (in arc-minutes) for UVOT event data.",
            "<b>Image FOV: </b>The size of the FOV (in arc-minutes) for UVOT image data.",
            "<b>Max. Exp. Time: </b>The maximum amount of time the snapshot will spend",
            "<b>Weighting: </b>Ratio of time spent on the particular filter",
            "<b>Comments: </b>Additional notes that may be useful to know.",
        ]

        for explanation in explanations:
            assert explanation in result

    def test_repr_html_complete_structure(self):
        """Test the complete HTML structure is properly formatted."""
        mode = SwiftUVOTMode()
        mode.uvotmode = 42
        mode.entries = [SwiftUVOTModeEntry()]

        result = mode._repr_html_()

        # Check overall structure
        assert result.startswith("<h2>UVOT Mode: 42</h2>")
        assert '<table id="modelist"' in result
        assert "</table>" in result
        assert '<p id="terms">' in result
        assert result.endswith("</p>")
