from datetime import datetime

import pytest

from swifttools.swift_too.swift.calendar import SwiftCalendar
from swifttools.swift_too.swift.requests import SwiftTOORequests, SwiftTOORequestsGetSchema
from swifttools.swift_too.swift.toorequest import SwiftTOORequest, SwiftTOORequestSchema


class TestSwiftTOORequestsGetSchema:
    def test_valid_schema(self):
        schema = SwiftTOORequestsGetSchema(begin=datetime(2023, 1, 1))
        assert schema.begin == datetime(2023, 1, 1)

    def test_invalid_schema_no_params(self):
        with pytest.raises(ValueError, match="At least one parameter must be set"):
            SwiftTOORequestsGetSchema()

    def test_validator_accepts_object_input(self):
        class InputObj:
            def __init__(self):
                self.begin = datetime(2023, 1, 1)

        data = SwiftTOORequestsGetSchema.validate_at_least_one_param(InputObj())
        assert isinstance(data, dict)
        assert data["begin"] == datetime(2023, 1, 1)


class TestSwiftTOORequests:
    def test_init(self, swift_requests):
        assert swift_requests.entries == []

    def test_getitem(self, swift_requests, sample_too_request):
        swift_requests.entries = [sample_too_request]
        assert swift_requests[0] == sample_too_request

    def test_getitem_empty_returns_schema(self, swift_requests):
        value = swift_requests[0]
        assert isinstance(value, SwiftTOORequestSchema)

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

    def test_format_uvot_mode_none(self):
        assert SwiftTOORequests._format_uvot_mode(None) is None

    def test_format_uvot_mode_int(self):
        assert SwiftTOORequests._format_uvot_mode(39321) == "0x9999"

    def test_format_uvot_mode_string_hex(self):
        assert SwiftTOORequests._format_uvot_mode("0x9999") == "0x9999"

    def test_format_uvot_mode_string_invalid(self):
        assert SwiftTOORequests._format_uvot_mode("not-a-mode") == "not-a-mode"

    def test_format_uvot_mode_passthrough(self):
        mode = {"mode": 1}
        assert SwiftTOORequests._format_uvot_mode(mode) == mode

    def test_format_xrt_mode_none(self):
        assert SwiftTOORequests._format_xrt_mode(None) == "Unset"

    def test_format_xrt_mode_string_invalid(self):
        assert SwiftTOORequests._format_xrt_mode("bad") == "bad"

    def test_format_xrt_mode_int_unknown(self):
        assert SwiftTOORequests._format_xrt_mode(99999) == "99999"

    def test_format_xrt_mode_passthrough(self):
        mode = {"mode": 1}
        assert SwiftTOORequests._format_xrt_mode(mode) == mode

    def test_too_request_calendar_is_swiftcalendar(self):
        req = SwiftTOORequest(
            too_id=24126,
            target_name="Test Target",
            calendar={
                "too_id": 24126,
                "entries": [
                    {
                        "begin": "2024-01-01T00:00:00",
                        "end": "2024-01-01T00:10:00",
                        "xrt_mode": 7,
                        "uvot_mode": 39321,
                        "duration": 600,
                    }
                ],
            },
            autosubmit=False,
        )

        assert isinstance(req.calendar, SwiftCalendar)
