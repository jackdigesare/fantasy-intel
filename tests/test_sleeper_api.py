import unittest
from unittest.mock import Mock, patch

from sleeper_api import SleeperError, get_league, get_user, get_user_leagues


class SleeperApiPathSecurityTests(unittest.TestCase):
    @patch("sleeper_api._get")
    def test_username_is_encoded_as_one_path_segment(self, mock_get: Mock) -> None:
        mock_get.return_value = {"user_id": "123"}

        get_user.__wrapped__("../players/nfl")

        mock_get.assert_called_once_with("/user/..%2Fplayers%2Fnfl")

    @patch("sleeper_api._get")
    def test_preencoded_username_cannot_escape_path(self, mock_get: Mock) -> None:
        mock_get.return_value = {"user_id": "123"}

        get_user.__wrapped__("%2e%2e%2fplayers%2fnfl")

        mock_get.assert_called_once_with(
            "/user/%252e%252e%252fplayers%252fnfl"
        )

    @patch("sleeper_api._get")
    def test_non_numeric_league_id_is_rejected_before_request(
        self, mock_get: Mock
    ) -> None:
        with self.assertRaisesRegex(
            SleeperError, r"^Enter a numeric Sleeper league ID\.$"
        ):
            get_league.__wrapped__("../players/nfl")

        mock_get.assert_not_called()

    @patch("sleeper_api._get")
    def test_upstream_path_values_are_encoded(self, mock_get: Mock) -> None:
        mock_get.return_value = []

        get_user_leagues.__wrapped__("123/../../players", "2026/../../nfl")

        mock_get.assert_called_once_with(
            "/user/123%2F..%2F..%2Fplayers/leagues/nfl/"
            "2026%2F..%2F..%2Fnfl"
        )


if __name__ == "__main__":
    unittest.main()
