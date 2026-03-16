from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from swifttools.swift_too.base.common import API_URL
from swifttools.swift_too.swift.toorequest import SwiftTOOFormSchema, SwiftTOOPostSchema, SwiftTOORequest


class TestSwiftTOORequestInit:
    def test_ra(self, too_request_base):
        assert abs(too_request_base.ra - 10.0) < 1e-5

    def test_dec(self, too_request_base):
        assert abs(too_request_base.dec - 20.0) < 1e-5

    def test_science_just(self, too_request_base):
        assert too_request_base.science_just == "Test justification"


class TestSwiftTOORequestSubmit:
    def test_submit_result_initial_status(self, too_request_base):
        too = too_request_base
        assert too.status.status == "Pending"

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_submit_result_status_after_submit(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Mock the response
        mock_response = mock_client.return_value.__enter__.return_value.post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "Accepted", "too_id": 123}

        # Mock login
        login_response = mock_client.return_value.__enter__.return_value.post.return_value
        login_response.status_code = 200

        with patch.object(too, "validate_post", return_value=True):
            with patch.object(type(too), "_post_schema") as mock_post_schema:
                mock_post_schema.model_validate.return_value.model_dump.return_value = {"param": "value"}

                def mock_handle_response(response):
                    # Directly update the object like _handle_response would
                    too.status.status = "Accepted"
                    too.too_id = 123
                    return True

                with patch.object(too, "_handle_response", side_effect=mock_handle_response):
                    _ = too.submit()
                    assert too.status.status == "Accepted"

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_submit_result_too_id_after_submit(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Mock the response
        mock_response = mock_client.return_value.__enter__.return_value.post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "Accepted", "too_id": 123}

        # Mock login
        login_response = mock_client.return_value.__enter__.return_value.post.return_value
        login_response.status_code = 200

        with patch.object(too, "validate_post", return_value=True):
            with patch.object(type(too), "_post_schema") as mock_post_schema:
                mock_post_schema.model_validate.return_value.model_dump.return_value = {"param": "value"}

                def mock_handle_response(response):
                    # Directly update the object like _handle_response would
                    too.status.status = "Accepted"
                    too.too_id = 123
                    return True

                with patch.object(too, "_handle_response", side_effect=mock_handle_response):
                    _ = too.submit()
                    assert too.too_id == 123

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_submit_status(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Mock the response
        mock_response = mock_client.return_value.__enter__.return_value.post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "Accepted", "too_id": 123}

        # Mock login
        login_response = mock_client.return_value.__enter__.return_value.post.return_value
        login_response.status_code = 200

        with patch.object(too, "validate_post", return_value=True):
            with patch.object(type(too), "_post_schema") as mock_post_schema:
                mock_post_schema.model_validate.return_value.model_dump.return_value = {"param": "value"}

                def mock_handle_response(response):
                    # Directly update the object like _handle_response would
                    too.status.status = "Accepted"
                    too.too_id = 123
                    return True

                with patch.object(too, "_handle_response", side_effect=mock_handle_response):
                    too.submit()
                    assert too.status.status == "Accepted"

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_submit_too_id(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Mock the response
        mock_response = mock_client.return_value.__enter__.return_value.post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "Accepted", "too_id": 123}

        # Mock login
        login_response = mock_client.return_value.__enter__.return_value.post.return_value
        login_response.status_code = 200

        with patch.object(too, "validate_post", return_value=True):
            with patch.object(type(too), "_post_schema") as mock_post_schema:
                mock_post_schema.model_validate.return_value.model_dump.return_value = {"param": "value"}

                def mock_handle_response(response):
                    # Directly update the object like _handle_response would
                    too.status.status = "Accepted"
                    too.too_id = 123
                    return True

                with patch.object(too, "_handle_response", side_effect=mock_handle_response):
                    too.submit()
                    assert too.too_id == 123


class TestSwiftTOORequestTableProperty:
    def test_table_header(self, too_request_base):
        too = too_request_base
        header, table = too._table
        assert header == ["Parameter", "Value"]

    def test_table_length(self, too_request_base):
        too = too_request_base
        header, table = too._table
        assert len(table) > 0

    def test_table_science_justification(self, too_request_base):
        too = too_request_base
        header, table = too._table
        param_names = [row[0] for row in table]
        assert "Science Justification" in param_names

    def test_table_exposure_time(self, too_request_base):
        too = too_request_base
        header, table = too._table
        param_names = [row[0] for row in table]
        assert "Exposure Time per Visit (seconds)" in param_names


class TestSwiftTOORequestTablePropertyWithDecision:
    def test_table_header_with_decision(self, too_request_with_decision):
        too = too_request_with_decision
        header, table = too._table
        assert header == ["Parameter", "Value"]

    def test_table_length_with_decision(self, too_request_with_decision):
        too = too_request_with_decision
        header, table = too._table
        assert len(table) > 0

    def test_table_object_name(self, too_request_with_decision):
        too = too_request_with_decision
        header, table = too._table
        param_values = [row[1] for row in table]
        assert "Test Target" in param_values


class TestSwiftTOORequestServerValidateSuccess:
    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_server_validate_result(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Set required fields for validate_post
        object.__setattr__(too, "target_name", "Test Target")
        object.__setattr__(too, "immediate_objective", "Test immediate objective")
        object.__setattr__(too, "uvot_just", "Test UVOT justification")
        # Clear errors before calling server_validate
        too.status.errors.clear()
        too.status.warnings = ["Some warning"]
        with patch.object(SwiftTOORequest, "validate_post", return_value=True):
            with patch.object(SwiftTOORequest, "submit", return_value=True):
                result = too.server_validate()
                assert result is True

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_server_validate_validate_only(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Set required fields
        object.__setattr__(too, "target_name", "Test Target")
        object.__setattr__(too, "immediate_objective", "Test objective")
        object.__setattr__(too, "uvot_just", "Test UVOT justification")
        with patch.object(SwiftTOORequest, "validate_post", return_value=True):
            with patch.object(SwiftTOORequest, "submit") as mock_submit:
                mock_submit.return_value = True
                too.status.errors = []
                too.status.warnings = ["Some warning"]
                too.server_validate()
                assert too.validate_only is False

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_server_validate_warnings(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Set required fields
        object.__setattr__(too, "target_name", "Test Target")
        object.__setattr__(too, "immediate_objective", "Test objective")
        object.__setattr__(too, "uvot_just", "Test UVOT justification")
        with patch.object(SwiftTOORequest, "validate_post", return_value=True):
            with patch.object(SwiftTOORequest, "submit") as mock_submit:
                mock_submit.return_value = True
                too.status.errors = []
                too.status.warnings = ["Some warning"]
                too.server_validate()
                assert len(too.status.warnings) == 1

    def test_server_validate_status_only_response_preserves_request_fields(self, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Set required fields
        object.__setattr__(too, "target_name", "Test Target")
        object.__setattr__(too, "immediate_objective", "Test objective")
        object.__setattr__(too, "uvot_just", "Test UVOT justification")

        original_target_name = too.target_name
        original_science_just = too.science_just

        # Return a status-only payload through the normal response handler.
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"status": "Validated"}

        with patch.object(SwiftTOORequest, "validate_post", return_value=True):
            with patch.object(
                SwiftTOORequest,
                "submit_post",
                autospec=True,
                side_effect=lambda this: this._handle_response(response),
            ):
                assert too.server_validate() is True

        assert too.target_name == original_target_name
        assert too.science_just == original_science_just

    def test_server_validate_status_only_response_preserves_validate_only(self, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        # Set required fields
        object.__setattr__(too, "target_name", "Test Target")
        object.__setattr__(too, "immediate_objective", "Test objective")
        object.__setattr__(too, "uvot_just", "Test UVOT justification")

        # Return a status-only payload through the normal response handler.
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"status": "Validated"}

        with patch.object(SwiftTOORequest, "validate_post", return_value=True):
            with patch.object(
                SwiftTOORequest,
                "submit_post",
                autospec=True,
                side_effect=lambda this: this._handle_response(response),
            ):
                assert too.server_validate() is True

        assert too.validate_only is False


class TestSwiftTOORequestServerValidateFailure:
    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_server_validate_result_failure(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        with patch.object(too, "validate_post", return_value=True):
            with patch.object(too, "submit") as mock_submit:
                mock_submit.return_value = True
                too.status.errors = ["Validation failed"]
                result = too.server_validate()
                assert result is False

    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_server_validate_validate_only_failure(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        too._api_base = API_URL
        with patch.object(too, "validate_post", return_value=True):
            with patch.object(too, "submit") as mock_submit:
                mock_submit.return_value = True
                too.status.errors = ["Validation failed"]
                too.server_validate()
                assert too.validate_only is False


class TestSwiftTOORequestServerValidateInvalidPost:
    def test_server_validate_invalid_post(self, too_request_base):
        too = too_request_base
        with patch.object(too, "validate_post", return_value=False):
            result = too.server_validate()
            assert result is False


class TestSwiftTOORequestAdditional:
    def test_init_validate_only(self, basic_too_request):
        assert basic_too_request.validate_only is False

    def test_init_debug(self, basic_too_request):
        assert basic_too_request.debug is False

    def test_table_property_decision_none_header(self, too_request_for_table):
        header, table = too_request_for_table._table
        assert header == ["Parameter", "Value"]

    def test_table_property_decision_none_table_length(self, too_request_for_table):
        header, table = too_request_for_table._table
        assert len(table) > 0

    def test_table_property_decision_not_none_header(self, too_request_with_decision_for_table):
        header, table = too_request_with_decision_for_table._table
        assert header == ["Parameter", "Value"]

    def test_table_property_decision_not_none_table_length(self, too_request_with_decision_for_table):
        header, table = too_request_with_decision_for_table._table
        assert len(table) > 0

    def test_server_validate_success(self, basic_too_request):
        request = basic_too_request
        # Set required fields
        object.__setattr__(request, "target_name", "Test Target")
        object.__setattr__(request, "immediate_objective", "Test objective")
        object.__setattr__(request, "uvot_just", "Test UVOT justification")
        # Clear errors from the start
        request.status.errors = []
        request.status.warnings = []

        with patch.object(SwiftTOORequest, "validate_post", return_value=True):
            with patch.object(SwiftTOORequest, "submit", return_value=True):
                result = request.server_validate()
                assert result is True

    def test_server_validate_with_errors(self, basic_too_request):
        request = basic_too_request
        request.validate_post = lambda: True

        original_submit = request.submit

        def mock_submit_with_errors():
            request.status.errors = ["Test error"]
            request.status.warnings = []

        request.submit = mock_submit_with_errors

        result = request.server_validate()
        assert result is False

        request.submit = original_submit

    def test_server_validate_validate_post_failure(self, basic_too_request):
        request = basic_too_request
        request.validate_post = lambda: False

        result = request.server_validate()
        assert result is False

    def test_server_validate_with_actual_validation_raises_exception(self, mock_resolve_default):
        request = SwiftTOORequest()

        schema = SwiftTOOFormSchema(
            target_name="Test Target",
            ra=10.0,
            dec=20.0,
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
            uvot_just="Test UVOT justification",
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
                ra=10.0,
                dec=20.0,
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
                ra=10.0,
                dec=20.0,
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
                ra=10.0,
                dec=20.0,
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
                ra=10.0,
                dec=20.0,
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
                ra=10.0,
                dec=20.0,
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
                ra=10.0,
                dec=20.0,
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
                ra=10.0,
                dec=20.0,
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
                ra=10.0,
                dec=20.0,
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
                uvot_mode="0x9999",
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
