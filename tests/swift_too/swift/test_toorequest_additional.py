from datetime import datetime
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from swifttools.swift_too.swift.toorequest import SwiftTOOFormSchema, SwiftTOOPostSchema, SwiftTOORequest


@pytest.fixture
def mock_resolve_default():
    """Pytest fixture to mock SwiftResolve with default values"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0
        yield mock_resolve_class


@pytest.fixture
def mock_resolve_test_target():
    """Pytest fixture to mock SwiftResolve with test target values"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 123.456
        mock_resolve_instance.dec = -45.678
        yield mock_resolve_class


class TestSwiftTOORequest:
    def test_init_validate_only(self):
        request = SwiftTOORequest(autosubmit=False)
        assert request.validate_only is False

    def test_init_debug(self):
        request = SwiftTOORequest(autosubmit=False)
        assert request.debug is False

    def test_table_property_decision_none_header(self, mock_resolve_test_target):
        request = SwiftTOORequest(autosubmit=False)
        request.decision = None
        request.too_id = 12345
        request.target_name = "Test Target"
        request.ra = 123.456
        request.dec = -45.678

        header, table = request._table
        assert header == ["Parameter", "Value"]

    def test_table_property_decision_none_table_length(self, mock_resolve_test_target):
        request = SwiftTOORequest(autosubmit=False)
        request.decision = None
        request.too_id = 12345
        request.target_name = "Test Target"
        request.ra = 123.456
        request.dec = -45.678

        header, table = request._table
        assert len(table) > 0

    def test_table_property_decision_not_none_header(self, mock_resolve_default):
        request = SwiftTOORequest(autosubmit=False)
        request.decision = "Approved"
        request.urgency = 2
        request.timestamp = datetime(2023, 1, 1, 12, 0, 0)

        header, table = request._table
        assert header == ["Parameter", "Value"]

    def test_table_property_decision_not_none_table_length(self, mock_resolve_default):
        request = SwiftTOORequest(autosubmit=False)
        request.decision = "Approved"
        request.urgency = 2
        request.timestamp = datetime(2023, 1, 1, 12, 0, 0)

        header, table = request._table
        assert len(table) > 0

    def test_server_validate_success(self):
        request = SwiftTOORequest(autosubmit=False)
        request.validate_post = lambda: True

        original_submit = request.submit

        def mock_submit():
            request.status.errors = []
            request.status.warnings = []

        request.submit = mock_submit

        result = request.server_validate()
        assert result is True

        request.submit = original_submit

    def test_server_validate_with_errors(self):
        request = SwiftTOORequest(autosubmit=False)
        request.validate_post = lambda: True

        original_submit = request.submit

        def mock_submit_with_errors():
            request.status.errors = ["Test error"]
            request.status.warnings = []

        request.submit = mock_submit_with_errors

        result = request.server_validate()
        assert result is False

        request.submit = original_submit

    def test_server_validate_validate_post_failure(self):
        request = SwiftTOORequest(autosubmit=False)
        request.validate_post = lambda: False

        result = request.server_validate()
        assert result is False

    def test_server_validate_with_actual_validation_raises_exception(self, mock_resolve_default):
        request = SwiftTOORequest()

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

        with pytest.raises(Exception):
            request.server_validate(schema)


class TestSwiftTOOFormSchema:
    def test_check_requirements_validator_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            SwiftTOOFormSchema(
                username="testuser",
                shared_secret="testsecret",
            )
        assert "Missing required field" in str(exc_info.value) or "Field required" in str(exc_info.value)

    def test_check_proposal_validator_missing_proposal_id(self, mock_resolve_default):
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

    def test_check_proposal_validator_missing_proposal_pi(self, mock_resolve_default):
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

    def test_check_proposal_validator_missing_trigger_justification(self, mock_resolve_default):
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

    def test_tiling_validator_missing_tiling_justification(self, mock_resolve_default):
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

    def test_brightness_validator_missing_brightness_values(self, mock_resolve_default):
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
            )
        assert "Must specify at least one brightness value" in str(exc_info.value)

    def test_grb_validator_missing_grb_details(self, mock_resolve_default):
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
            )
        assert "Must specify GRB trigger time and detector if source type is GRB" in str(exc_info.value)

    def test_uvot_validator_missing_uvot_justification(self, mock_resolve_default):
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

    def test_monitoring_validator_invalid_format(self, mock_resolve_default):
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

    def test_exposure_validator_missing_exp_time_per_visit(self, mock_resolve_default):
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
            )
        assert "Must specify exposure time per visit if number of visits is specified" in str(exc_info.value)


class TestSwiftTOOPostSchema:
    def test_check_requirements_validator_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            SwiftTOOPostSchema(
                username="testuser",
                shared_secret="testsecret",
            )
        assert "Missing required field" in str(exc_info.value) or "Field required" in str(exc_info.value)
