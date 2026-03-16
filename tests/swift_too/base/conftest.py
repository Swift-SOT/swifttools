from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel

from swifttools.swift_too.base.common import TOOAPIBaseclass
from swifttools.swift_too.base.status import TOOStatus


@pytest.fixture
def mock_client():
    with patch("httpx.Client") as mock:
        yield mock


@pytest.fixture
def mock_cookie_jar():
    with patch("swifttools.swift_too.base.common.cookie_jar") as mock:
        yield mock


@pytest.fixture
def mock_validated_payload():
    validated = Mock()
    validated.model_dump.return_value = {"param": "value"}
    return validated


@pytest.fixture
def post_only_model_cls():
    class PostOnlyModel(BaseModel, TOOAPIBaseclass):
        _endpoint = "/test"
        _post_schema = Mock()
        status: TOOStatus = TOOStatus()

    return PostOnlyModel
