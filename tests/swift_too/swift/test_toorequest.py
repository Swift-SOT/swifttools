from unittest.mock import MagicMock, patch

from swifttools.swift_too.base.common import API_URL
from swifttools.swift_too.swift.toorequest import SwiftTOORequest


def test_swift_too_request_init():
    mock_resolve = MagicMock()
    mock_resolve.ra = 10.0
    mock_resolve.dec = 20.0
    mock_resolve.status.warnings = []
    mock_resolve.status.errors = []
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
        assert abs(too.ra - 10.0) < 1e-5
        assert abs(too.dec - 20.0) < 1e-5
        assert too.science_just == "Test justification"


@patch("swifttools.swift_too.base.common.cookie_jar")
@patch("httpx.Client")
def test_swift_too_request_submit(mock_client, mock_cookie_jar):
    mock_resolve = MagicMock()
    mock_resolve.ra = 10.0
    mock_resolve.dec = 20.0
    mock_resolve.status.warnings = []
    mock_resolve.status.errors = []
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

                def mock_model_validate(data):
                    too.status.status = "Accepted"
                    too.too_id = 123
                    return too

                with patch.object(too, "model_validate", side_effect=mock_model_validate):
                    result = too.submit()
                    assert result is True
                    assert too.status.status == "Accepted"
            assert too.too_id == 123


def test_swift_too_request_table_property():
    mock_resolve = MagicMock()
    mock_resolve.ra = 10.0
    mock_resolve.dec = 20.0
    mock_resolve.status.warnings = []
    mock_resolve.status.errors = []
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
            target_type="Normal",
            username="testuser",
            shared_secret="testsecret",
            autosubmit=False,
        )
        too.target_name = "Test Target"
        header, table = too._table
        assert header == ["Parameter", "Value"]
        assert len(table) > 0
        # Check that some expected parameters are in the table
        param_names = [row[0] for row in table]
        assert "Science Justification" in param_names
        assert "Exposure Time per Visit (seconds)" in param_names


def test_swift_too_request_table_property_with_decision():
    mock_resolve = MagicMock()
    mock_resolve.ra = 10.0
    mock_resolve.dec = 20.0
    mock_resolve.status.warnings = []
    mock_resolve.status.errors = []
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
        _ = SwiftTOORequest(
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
        # Create a new instance with decision set
        too_with_decision = SwiftTOORequest(
            ra=10.0,
            dec=20.0,
            science_just="Test justification",
            num_of_visits=1,
            exp_time_per_visit=1000,
            exp_time_just="Test exposure justification",
            obs_type="Spectroscopy",
            instrument="XRT",
            target_type="Normal",
            username="testuser",
            shared_secret="testsecret",
            autosubmit=False,
            decision="Approved",
        )
        too_with_decision.target_name = "Test Target"
        header, table = too_with_decision._table
        assert header == ["Parameter", "Value"]
        assert len(table) > 0
        # When decision is not None, different parameters are included
        param_names = [row[0] for row in table]
        assert "Object Name" in param_names  # target_name


@patch("swifttools.swift_too.base.common.cookie_jar")
@patch("httpx.Client")
def test_swift_too_request_server_validate_success(mock_client, mock_cookie_jar):
    mock_resolve = MagicMock()
    mock_resolve.ra = 10.0
    mock_resolve.dec = 20.0
    mock_resolve.status.warnings = []
    mock_resolve.status.errors = []
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
        too._api_base = API_URL
        # Mock the response for validate_post
        with patch.object(too, "validate_post", return_value=True):
            # Mock the submit method
            with patch.object(too, "submit") as mock_submit:
                mock_submit.return_value = True
                too.status.errors = []
                too.status.warnings = ["Some warning"]
                result = too.server_validate()
                assert result is True
                assert too.validate_only is False
                # Check that warnings were preserved
                assert len(too.status.warnings) == 1


@patch("swifttools.swift_too.base.common.cookie_jar")
@patch("httpx.Client")
def test_swift_too_request_server_validate_failure(mock_client, mock_cookie_jar):
    mock_resolve = MagicMock()
    mock_resolve.ra = 10.0
    mock_resolve.dec = 20.0
    mock_resolve.status.warnings = []
    mock_resolve.status.errors = []
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
        too._api_base = API_URL
        # Mock the response for validate_post
        with patch.object(too, "validate_post", return_value=True):
            # Mock the submit method
            with patch.object(too, "submit") as mock_submit:
                mock_submit.return_value = True
                too.status.errors = ["Validation failed"]
                result = too.server_validate()
                assert result is False
                assert too.validate_only is False


def test_swift_too_request_server_validate_invalid_post():
    mock_resolve = MagicMock()
    mock_resolve.ra = 10.0
    mock_resolve.dec = 20.0
    mock_resolve.status.warnings = []
    mock_resolve.status.errors = []
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
        with patch.object(too, "validate_post", return_value=False):
            result = too.server_validate()
            assert result is False
