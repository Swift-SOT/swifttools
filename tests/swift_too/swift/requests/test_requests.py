from datetime import datetime

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
    def test_init(self, swift_requests):
        assert swift_requests.entries == []

    def test_getitem(self, swift_requests, sample_too_request):
        swift_requests.entries = [sample_too_request]
        assert swift_requests[0] == sample_too_request

    def test_len(self, swift_requests):
        swift_requests.entries = [SwiftTOORequest(too_id=1), SwiftTOORequest(too_id=2)]
        assert len(swift_requests) == 2

    def test_by_id(self, swift_requests):
        entry1 = SwiftTOORequest(too_id=123, target_name="Target1", autosubmit=False)
        entry2 = SwiftTOORequest(too_id=456, target_name="Target2", autosubmit=False)
        swift_requests.entries = [entry1, entry2]
        result = swift_requests.by_id(456)
        assert result == entry2

    def test_table_property_empty_header(self):
        requests = SwiftTOORequests(autosubmit=False)
        header, data = requests._table
        assert header == []

    def test_table_property_empty_data(self):
        requests = SwiftTOORequests(autosubmit=False)
        header, data = requests._table
        assert data == []

    def test_table_property_with_entries_header(self, swift_requests, sample_too_request):
        swift_requests.entries = [sample_too_request]
        header, data = swift_requests._table
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

    def test_table_property_with_entries_data_length(self, swift_requests, sample_too_request):
        swift_requests.entries = [sample_too_request]
        header, data = swift_requests._table
        assert len(data) == 1
