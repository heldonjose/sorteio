from unittest.mock import patch, MagicMock
import pytest
from apps.instagram.client import InstagramClient, InstagramAPIError


class TestInstagramClient:
    def _make_client(self):
        return InstagramClient(access_token="test-token")

    def _mock_response(self, data: dict, status_code: int = 200):
        mock = MagicMock()
        mock.json.return_value = data
        mock.status_code = status_code
        return mock

    @patch("apps.instagram.client.requests.get")
    def test_get_me_success(self, mock_get):
        mock_get.return_value = self._mock_response({
            "user_id": "123",
            "username": "testuser",
            "name": "Test User",
            "account_type": "BUSINESS",
        })
        client = self._make_client()
        result = client.get_me()
        assert result["username"] == "testuser"

    @patch("apps.instagram.client.requests.get")
    def test_get_me_api_error(self, mock_get):
        mock_get.return_value = self._mock_response({
            "error": {"message": "Invalid OAuth access token", "code": 190}
        })
        client = self._make_client()
        with pytest.raises(InstagramAPIError) as exc_info:
            client.get_me()
        assert exc_info.value.code == 190

    @patch("apps.instagram.client.requests.get")
    def test_get_media_passes_after_cursor(self, mock_get):
        mock_get.return_value = self._mock_response({"data": [], "paging": {}})
        client = self._make_client()
        client.get_media(after="cursor123")
        call_params = mock_get.call_args[1]["params"]
        assert call_params["after"] == "cursor123"

    @patch("apps.instagram.client.requests.get")
    def test_get_comments_empty_data_no_error(self, mock_get):
        # Em modo dev, a API retorna data vazio sem erro — deve ser tratado normalmente
        mock_get.return_value = self._mock_response({
            "data": [],
            "paging": {"cursors": {"after": "next_cursor"}, "next": "https://..."}
        })
        client = self._make_client()
        result = client.get_comments("media_001")
        assert result["data"] == []

    def test_rate_limit_error_detection(self):
        for code in (4, 17, 32, 613):
            err = InstagramAPIError("Rate limit", code=code)
            assert err.is_rate_limit is True

    def test_non_rate_limit_error(self):
        err = InstagramAPIError("Invalid token", code=190)
        assert err.is_rate_limit is False
