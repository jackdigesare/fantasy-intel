import unittest
from unittest.mock import Mock, patch

import requests

from sleeper_api import SleeperError, _get


class SleeperApiSecurityTests(unittest.TestCase):
    @patch("sleeper_api.requests.get")
    def test_get_converts_invalid_json_to_safe_error(self, mock_get: Mock) -> None:
        response = Mock(status_code=200, content=b"not json")
        response.json.side_effect = ValueError("decoder internals")
        mock_get.return_value = response

        with self.assertRaisesRegex(
            SleeperError, r"^Sleeper returned an unexpected response\.$"
        ) as raised:
            _get("/state/nfl")

        self.assertIsInstance(raised.exception.__cause__, ValueError)

    @patch("sleeper_api.requests.get")
    def test_get_does_not_expose_network_error_details(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.ConnectionError(
            "proxy.internal.example refused the connection"
        )

        with self.assertRaisesRegex(
            SleeperError, r"^Could not reach Sleeper\. Try again shortly\.$"
        ) as raised:
            _get("/state/nfl")

        self.assertNotIn("proxy.internal.example", str(raised.exception))
        self.assertIsInstance(raised.exception.__cause__, requests.ConnectionError)


if __name__ == "__main__":
    unittest.main()
