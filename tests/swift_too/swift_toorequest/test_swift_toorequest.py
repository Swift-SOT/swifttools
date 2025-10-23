from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from swifttools.swift_too.swift_toorequest import (
    TOO,
    Swift_TOO,
    Swift_TOO_Request,
    SwiftTOORequest,
    TOORequest,
    UrgencyEnum,
    XRTModeEnum,
)


@pytest.fixture
def mock_resolve_get():
    """Fixture to mock requests.get for testing."""
    mock_get = MagicMock()
    mock_get.return_value = MagicMock()
    mock_get.return_value.url = "https://my_big_fake_url.com"
    mock_get.return_value.status_code = 404
    mock_get.return_value.json = MagicMock(return_value='{"status": {"errors": ["Not Found"], "warnings": []}}')
    with patch("requests.get", mock_get) as mock_requests:
        yield mock_requests


class TestSwiftTOORequest:
    def test_init_with_basic_parameters(self, mock_resolve_get):
        """Test basic initialization of SwiftTOORequest."""

        too = SwiftTOORequest(source_name="Test Source", source_type="AGN", ra=123.456, dec=78.901)

        assert too.source_name == "Test Source"
        assert too.source_type == "AGN"
        assert np.isclose(too.ra, 123.456)
        assert np.isclose(too.dec, 78.901)

    def test_xrt_mode_enum(self):
        """Test XRTModeEnum values."""
        assert XRTModeEnum.AUTO == 0
        assert XRTModeEnum.PHOTON_COUNTING == 7
        assert XRTModeEnum.WINDOWED_TIMING == 6

    def test_urgency_enum(self):
        """Test UrgencyEnum values."""
        assert UrgencyEnum.URGENT == 0
        assert UrgencyEnum.HIGHEST == 1
        assert UrgencyEnum.HIGH == 2
        assert UrgencyEnum.MEDIUM == 3
        assert UrgencyEnum.LOW == 4

    def test_default_values(self):
        """Test default values are set correctly."""
        too = SwiftTOORequest()

        assert too.urgency == UrgencyEnum.MEDIUM
        assert too.xrt_mode == XRTModeEnum.PHOTON_COUNTING
        assert too.uvot_mode == "0x9999"
        assert too.proposal is False
        assert too.tiling is False

    def test_grb_parameters(self):
        """Test GRB-specific parameters."""
        trigger_time = datetime(2023, 1, 1, 12, 0, 0)
        too = SwiftTOORequest(source_type="GRB", grb_triggertime=trigger_time, grb_detector="Swift/BAT")

        assert too.source_type == "GRB"
        assert too.grb_triggertime == trigger_time
        assert too.grb_detector == "Swift/BAT"

    def test_proposal_parameters(self):
        """Test GI proposal parameters."""
        too = SwiftTOORequest(
            proposal=True, proposal_id="12345", proposal_pi="John Doe", proposal_trigger_just="Test justification"
        )

        assert too.proposal is True
        assert too.proposal_id == "12345"
        assert too.proposal_pi == "John Doe"
        assert too.proposal_trigger_just == "Test justification"

    def test_tiling_parameters(self):
        """Test tiling-related parameters."""
        too = SwiftTOORequest(
            tiling=True, number_of_tiles="7", exposure_time_per_tile=1000, tiling_justification="Large error region"
        )

        assert too.tiling is True
        assert too.number_of_tiles == "7"
        assert too.exposure_time_per_tile == 1000
        assert too.tiling_justification == "Large error region"

    def test_monitoring_parameters(self):
        """Test monitoring observation parameters."""
        too = SwiftTOORequest(num_of_visits=5, exp_time_per_visit=500, monitoring_freq="2 days")

        assert too.num_of_visits == 5
        assert too.exp_time_per_visit == 500
        assert too.monitoring_freq == "2 days"

    def test_brightness_parameters(self):
        """Test brightness-related parameters."""
        too = SwiftTOORequest(
            opt_mag=15.5, opt_filt="V", xrt_countrate="0.1", bat_countrate="0.05", other_brightness="Radio: 10 mJy"
        )

        assert too.opt_mag == 15.5
        assert too.opt_filt == "V"
        assert too.xrt_countrate == "0.1"
        assert too.bat_countrate == "0.05"
        assert too.other_brightness == "Radio: 10 mJy"

    def test_varnames_property(self):
        """Test that _varnames property contains expected keys."""
        too = SwiftTOORequest()

        assert "source_name" in too._varnames
        assert "ra" in too._varnames
        assert "dec" in too._varnames
        assert "urgency" in too._varnames
        assert too._varnames["source_name"] == "Object Name"
        assert too._varnames["ra"] == "Right Ascenscion (J2000)"

    @patch("swifttools.swift_too.swift_toorequest.SwiftTOORequest.validate_post")
    @patch("swifttools.swift_too.swift_toorequest.SwiftTOORequest.submit")
    def test_server_validate_success(self, mock_submit, mock_validate_post):
        """Test successful server validation."""
        too = SwiftTOORequest()
        too.status = Mock()
        too.status.warnings = []
        too.status.errors = []
        too.status.clear = Mock()

        mock_validate_post.return_value = True

        result = too.server_validate()

        assert result is True
        mock_validate_post.assert_called_once()
        mock_submit.assert_called_once()
        too.status.clear.assert_called_once()

    @patch("swifttools.swift_too.swift_toorequest.SwiftTOORequest.validate_post")
    def test_server_validate_validation_failure(self, mock_validate_post):
        """Test server validation with local validation failure."""
        too = SwiftTOORequest()
        mock_validate_post.return_value = False

        result = too.server_validate()

        assert result is False
        mock_validate_post.assert_called_once()

    @patch("swifttools.swift_too.swift_toorequest.SwiftTOORequest.validate_post")
    @patch("swifttools.swift_too.swift_toorequest.SwiftTOORequest.submit")
    def test_server_validate_server_errors(self, mock_submit, mock_validate_post):
        """Test server validation with server-side errors."""
        too = SwiftTOORequest()
        too.status = Mock()
        too.status.warnings = []
        too.status.errors = ["Server error"]

        mock_validate_post.return_value = True

        result = too.server_validate()

        assert result is False
        mock_validate_post.assert_called_once()
        mock_submit.assert_called_once()

    def test_aliases(self):
        """Test that class aliases work correctly."""

        too1 = Swift_TOO()
        too2 = TOO()
        too3 = TOORequest()
        too4 = Swift_TOO_Request()

        assert isinstance(too1, SwiftTOORequest)
        assert isinstance(too2, SwiftTOORequest)
        assert isinstance(too3, SwiftTOORequest)
        assert isinstance(too4, SwiftTOORequest)

    def test_endpoint_property(self):
        """Test that _endpoint is set correctly."""
        too = SwiftTOORequest()
        assert too._endpoint == "/swift/too"

    def test_optional_parameters(self):
        """Test setting various optional parameters."""
        too = SwiftTOORequest(
            poserr=5.0,
            instrument="UVOT",
            uvot_just="Filter selection justified",
        )

        assert too.poserr == 5.0
        assert too.instrument == "UVOT"
        assert too.uvot_just == "Filter selection justified"

    def test_schema_properties(self):
        """Test that schema properties are set correctly."""
        too = SwiftTOORequest()

        # These should be set by the class definition
        assert hasattr(too, "_schema")
        assert hasattr(too, "_post_schema")
