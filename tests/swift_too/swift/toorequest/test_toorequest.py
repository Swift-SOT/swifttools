from unittest.mock import MagicMock, patch

import pytest

from swifttools.swift_too.base.common import API_URL
from swifttools.swift_too.swift.toorequest import SwiftTOORequest


@pytest.fixture
def mock_resolve():
    mock = MagicMock()
    mock.ra = 10.0
    mock.dec = 20.0
    mock.status.warnings = []
    mock.status.errors = []
    return mock


@pytest.fixture
def too_request_base(mock_resolve):
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
        too = SwiftTOORequest(
            ra=10.0,
            dec=20.0,
            science_just="Test justification",
            num_of_visits=1,
            exp_time_per_visit=1000,
            exp_time_just="Test exposure justification",
            obs_type="Spectroscopy",
            instrument="XRT",
            target_name="Test Target",
            target_type="Normal",
            username="testuser",
            shared_secret="testsecret",
            autosubmit=False,
        )
        return too


@pytest.fixture
def too_request_with_decision(mock_resolve):
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
        too = SwiftTOORequest(
            ra=10.0,
            dec=20.0,
            science_just="Test justification",
            num_of_visits=1,
            exp_time_per_visit=1000,
            exp_time_just="Test exposure justification",
            obs_type="Spectroscopy",
            instrument="XRT",
            target_name="Test Target",
            target_type="Normal",
            username="testuser",
            shared_secret="testsecret",
            autosubmit=False,
            decision="Approved",
        )
        return too


class TestSwiftTOORequestInit:
    def test_ra(self, too_request_base):
        assert abs(too_request_base.ra - 10.0) < 1e-5

    def test_dec(self, too_request_base):
        assert abs(too_request_base.dec - 20.0) < 1e-5

    def test_science_just(self, too_request_base):
        assert too_request_base.science_just == "Test justification"


class TestSwiftTOORequestSubmit:
    @patch("swifttools.swift_too.base.common.cookie_jar")
    @patch("httpx.Client")
    def test_submit_result(self, mock_client, mock_cookie_jar, too_request_base):
        too = too_request_base
        assert too.status.status == "Pending"
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
