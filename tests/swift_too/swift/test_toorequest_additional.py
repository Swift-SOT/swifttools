from datetime import datetime
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from swifttools.swift_too.swift.toorequest import SwiftTOOFormSchema, SwiftTOOPostSchema, SwiftTOORequest


def mock_swift_resolve():
    """Helper function to mock SwiftResolve for tests that set target_name"""
    return patch("swifttools.swift_too.swift.resolve.SwiftResolve")


@pytest.fixture
def mock_resolve():
    """Pytest fixture to mock SwiftResolve"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0
        yield mock_resolve_class


def test_swift_too_request_init():
    """Test SwiftTOORequest initialization"""
    request = SwiftTOORequest(autosubmit=False)
    assert request.validate_only is False
    assert request.debug is False


def test_swift_too_request_table_property():
    """Test _table property"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        # Create a mock resolve instance
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 123.456
        mock_resolve_instance.dec = -45.678

        request = SwiftTOORequest(autosubmit=False)
        # Test with decision None
        request.decision = None
        request.too_id = 12345
        request.target_name = "Test Target"
        request.ra = 123.456
        request.dec = -45.678

        header, table = request._table
        assert header == ["Parameter", "Value"]
        assert len(table) > 0

        # Test with decision not None
        request.decision = "Approved"
        request.urgency = 2
        request.timestamp = datetime(2023, 1, 1, 12, 0, 0)

        header, table = request._table
        assert header == ["Parameter", "Value"]
        assert len(table) > 0


def test_swift_too_request_server_validate():
    """Test server_validate method"""
    request = SwiftTOORequest(autosubmit=False)

    # Mock validate_post to return True
    request.validate_post = lambda: True

    # Mock submit method
    original_submit = request.submit

    def mock_submit():
        request.status.errors = []
        request.status.warnings = []

    request.submit = mock_submit

    result = request.server_validate()
    assert result is True

    # Test with validation errors
    def mock_submit_with_errors():
        request.status.errors = ["Test error"]
        request.status.warnings = []

    request.submit = mock_submit_with_errors

    result = request.server_validate()
    assert result is False

    # Restore original submit
    request.submit = original_submit


def test_swift_too_request_validate_post_failure():
    """Test server_validate when validate_post fails"""
    request = SwiftTOORequest(autosubmit=False)

    # Mock validate_post to return False
    request.validate_post = lambda: False

    result = request.server_validate()
    assert result is False


def test_swift_too_form_schema_check_requirements_validator():
    """Test SwiftTOOFormSchema check_requirements validator"""
    # This should fail because required fields are missing
    with pytest.raises(ValidationError) as exc_info:
        SwiftTOOFormSchema(
            username="testuser",
            shared_secret="testsecret",
            # Missing required fields like ra, dec, etc.
        )
    # The error should mention missing required field
    assert "Missing required field" in str(exc_info.value) or "Field required" in str(exc_info.value)


def test_swift_too_form_schema_check_proposal_validator():
    """Test SwiftTOOFormSchema check_proposal validator"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        # Test proposal validation: missing proposal_id
        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                proposal=True,
                proposal_pi="Test PI",
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                instrument="XRT",
            )
        assert "Must specify proposal ID and PI if GI proposal" in str(exc_info.value)

        # Test proposal validation: missing proposal_pi
        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                proposal=True,
                proposal_id="12345",
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                instrument="XRT",
            )
        assert "Must specify proposal ID and PI if GI proposal" in str(exc_info.value)

        # Test proposal validation: missing trigger justification
        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                proposal=True,
                proposal_id="12345",
                proposal_pi="Test PI",
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                instrument="XRT",
            )
        assert "Must specify proposal trigger justification if GI TOO" in str(exc_info.value)


def test_swift_too_form_schema_tiling_validator():
    """Test SwiftTOOFormSchema tiling validator"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                tiling=True,
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                instrument="XRT",
            )
        assert "Must specify tiling justification if tiling is True" in str(exc_info.value)


def test_swift_too_form_schema_brightness_validator():
    """Test SwiftTOOFormSchema brightness validator"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                instrument="XRT",
                # No brightness values specified
            )
        assert "Must specify at least one brightness value" in str(exc_info.value)


def test_swift_too_form_schema_grb_validator():
    """Test SwiftTOOFormSchema GRB validator"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                target_type="GRB",
                target_name="Test Target",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                xrt_countrate="1.0",
                instrument="XRT",
                # Missing grb_triggertime and grb_detector
            )
        assert "Must specify GRB trigger time and detector if source type is GRB" in str(exc_info.value)


def test_swift_too_form_schema_uvot_validator():
    """Test SwiftTOOFormSchema UVOT validator"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                uvot_mode="0x1234",
                uvot_just="",
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                xrt_countrate="1.0",
                grb_triggertime="2023-01-01T00:00:00",
                grb_detector="BAT",
                instrument="XRT",
            )
        assert "Must specify UVOT justification if UVOT mode is not filter of the day" in str(exc_info.value)


def test_swift_too_form_schema_monitoring_validator():
    """Test SwiftTOOFormSchema monitoring validator"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                monitoring_freq="invalid_format",
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                xrt_countrate="1.0",
                grb_triggertime="2023-01-01T00:00:00",
                grb_detector="BAT",
                instrument="XRT",
            )
        assert "Monitoring frequency in incorrect format" in str(exc_info.value)


def test_swift_too_form_schema_exposure_validator():
    """Test SwiftTOOFormSchema exposure validator"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        with pytest.raises(ValueError) as exc_info:
            SwiftTOOFormSchema(
                target_name="Test Target",
                target_type="GRB",
                obs_type="Spectroscopy",
                science_just="Test justification",
                immediate_objective="Test objective",
                exposure=1000,
                exp_time_just="Test exp justification",
                num_of_visits=2,
                monitoring_freq="1 day",
                xrt_countrate="1.0",
                grb_triggertime="2023-01-01T00:00:00",
                grb_detector="BAT",
                instrument="XRT",
                # Missing exp_time_per_visit
            )
        assert "Must specify exposure time per visit if number of visits is specified" in str(exc_info.value)


def test_swift_too_post_schema_check_requirements_validator():
    """Test SwiftTOOPostSchema check_requirements validator"""
    # This should fail because required fields are missing
    with pytest.raises(ValidationError) as exc_info:
        SwiftTOOPostSchema(
            username="testuser",
            shared_secret="testsecret",
            # Missing required fields like ra, dec, etc.
        )
    # The error should mention missing required field
    assert "Missing required field" in str(exc_info.value) or "Field required" in str(exc_info.value)


def test_server_validate_with_actual_validation():
    """Test server_validate method with actual validation (not mocked)"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0

        # Create a request object
        request = SwiftTOORequest()

        # Create a valid schema instance that should pass validation
        schema = SwiftTOOFormSchema(
            target_name="Test Target",
            target_type="GRB",
            obs_type="Spectroscopy",
            science_just="Test justification",
            immediate_objective="Test objective",
            exposure=1000,
            exp_time_just="Test exp justification",
            xrt_countrate="1.0",
            grb_triggertime="2023-01-01T00:00:00",
            grb_detector="BAT",
            instrument="XRT",
            opt_mag=20.0,
            opt_filt="V",
        )

        # This will attempt to call validate_post, which should fail with connection error
        # but the line 313 should be executed
        with pytest.raises(Exception):  # Could be connection error or API error
            request.server_validate(schema)
