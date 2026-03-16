from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from swifttools.swift_too.swift.requests import SwiftTOORequests, SwiftTOORequestsGetSchema
from swifttools.swift_too.swift.toorequest import SwiftTOORequest


class TestSwiftTOORequestsGetSchema:
    def test_valid_schema(self):
        schema = SwiftTOORequestsGetSchema(begin=datetime(2023, 1, 1))
        assert schema.begin == datetime(2023, 1, 1)

    def test_invalid_schema_no_params(self):
        with pytest.raises(ValueError, match="At least one parameter must be set"):
            SwiftTOORequestsGetSchema()


class TestSwiftTOORequests:
    @patch("swifttools.swift_too.swift.resolve.SwiftResolve")
    def test_init(self, mock_resolve):
        mock_resolve.return_value = MagicMock(ra=10.0, dec=20.0, status=MagicMock(warnings=[], errors=[]))
        requests = SwiftTOORequests(autosubmit=False)
        assert requests.entries == []

    @patch("swifttools.swift_too.swift.resolve.SwiftResolve")
    def test_getitem(self, mock_resolve):
        mock_resolve.return_value = MagicMock(ra=10.0, dec=20.0, status=MagicMock(warnings=[], errors=[]))
        requests = SwiftTOORequests(autosubmit=False)
        entry = SwiftTOORequest(too_id=123)
        requests.entries = [entry]
        assert requests[0] == entry

    @patch("swifttools.swift_too.swift.resolve.SwiftResolve")
    def test_len(self, mock_resolve):
        mock_resolve.return_value = MagicMock(ra=10.0, dec=20.0, status=MagicMock(warnings=[], errors=[]))
        requests = SwiftTOORequests(autosubmit=False)
        requests.entries = [SwiftTOORequest(too_id=1), SwiftTOORequest(too_id=2)]
        assert len(requests) == 2

    @patch("swifttools.swift_too.swift.resolve.SwiftResolve")
    def test_by_id(self, mock_resolve):
        mock_resolve.return_value = MagicMock(ra=10.0, dec=20.0, status=MagicMock(warnings=[], errors=[]))
        requests = SwiftTOORequests(autosubmit=False)
        entry1 = SwiftTOORequest(too_id=123, target_name="Target1", autosubmit=False)
        entry2 = SwiftTOORequest(too_id=456, target_name="Target2", autosubmit=False)
        requests.entries = [entry1, entry2]
        result = requests.by_id(456)
        assert result == entry2

    def test_table_property_empty(self):
        requests = SwiftTOORequests(autosubmit=False)
        header, data = requests._table
        assert header == []
        assert data == []

    @patch("swifttools.swift_too.swift.resolve.SwiftResolve")
    def test_table_property_with_entries(self, mock_resolve):
        mock_resolve.return_value = MagicMock(ra=10.0, dec=20.0, status=MagicMock(warnings=[], errors=[]))
        requests = SwiftTOORequests(autosubmit=False)
        entry = SwiftTOORequest(
            too_id=123,
            target_name="Test Target",
            instrument="XRT",
            ra=10.0,
            dec=20.0,
            uvot_mode_approved=0x9999,
            xrt_mode_approved=7,
            timestamp=datetime(2023, 1, 1),
            l_name="Test L",
            urgency=2,  # HIGH
            date_begin=datetime(2023, 1, 1),
            date_end=datetime(2023, 1, 2),
            target_id=456,
            autosubmit=False,
        )
        requests.entries = [entry]
        header, data = requests._table
        expected_header = [
            "ToO ID",
            "Object Name",
            "Instrument",
            "Right Ascenscion (J2000)",
            "Declination (J2000)",
            "UVOT Mode (Approved)",
            "XRT Mode (Approved)",
            "Time Submitted",
            "Requester",
            "Urgency",
            "Begin date",
            "End date",
            "Primary Target ID",
        ]
        assert header == expected_header
        assert len(data) == 1
