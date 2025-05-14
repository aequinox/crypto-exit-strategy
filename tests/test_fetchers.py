import pytest
import requests
from unittest.mock import MagicMock, patch

from main import (
    get_coingecko_global,
    get_fear_greed,
    get_m2_series,
    is_m2_flat,
    google_trends_hype,
    coinbase_app_top,
    load_history,
    save_history,
    check_alt_pullback,
)


class TestDataFetchers:
    """Tests for data fetching functions."""

    def test_coingecko_fetcher(self):
        """Test CoinGecko API fetcher with successful response."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {
                    "market_cap_percentage": {"btc": 40.0, "eth": 20.0},
                    "total_market_cap": {"usd": 2000000000000},
                }
            }
            mock_get.return_value = mock_response

            btc, eth, total = get_coingecko_global()
            assert btc == 40.0
            assert eth == 20.0
            assert total == 2000000000000.0
            assert isinstance(btc, float)
            assert isinstance(eth, float)
            assert isinstance(total, float)

    def test_coingecko_fetcher_error(self):
        """Test CoinGecko API fetcher with error response."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("API error")
            with pytest.raises(requests.exceptions.RequestException):
                get_coingecko_global()

    def test_fear_greed_fetcher(self):
        """Test Fear & Greed index fetcher with successful response."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": [{"value": "95"}]}
            mock_get.return_value = mock_response

            fg = get_fear_greed()
            assert fg == 95
            assert isinstance(fg, int)

    def test_fear_greed_fetcher_error(self):
        """Test Fear & Greed index fetcher with error response."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("API error")
            with pytest.raises(requests.exceptions.RequestException):
                get_fear_greed()

    def test_m2_series_fetcher(self):
        """Test M2 money supply fetcher with successful response."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "observations": [
                    {"value": "100"},
                    {"value": "101"},
                    {"value": "101.1"},
                ]
            }
            mock_get.return_value = mock_response

            m2 = get_m2_series()
            assert m2 == [100.0, 101.0, 101.1]
            assert isinstance(m2, list)
            assert all(isinstance(x, float) for x in m2)

    def test_m2_series_fetcher_error(self):
        """Test M2 money supply fetcher with error response."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("API error")
            with pytest.raises(requests.exceptions.RequestException):
                get_m2_series()

    @pytest.mark.parametrize(
        "m2_values,expected",
        [
            ([100.0, 100.001, 100.002], True),  # Should be flat (< 0.001 change)
            ([100.0, 110.0, 120.0], False),  # Should not be flat
            ([100.0, 100.0], False),  # Too short
            ([], False),  # Empty list
        ],
    )
    def test_m2_flat_detection(self, m2_values, expected):
        """Test M2 flattening detection with various inputs."""
        assert is_m2_flat(m2_values) == expected

    @pytest.mark.parametrize(
        "social_terms,hits_required,expected",
        [
            (["bitcoin"], 1, True),  # Should detect with 1 hit
            (["nonexistent"], 1, False),  # Should not detect
            (["bitcoin", "crypto"], 1, True),  # Should detect with multiple terms
            (["bitcoin"], 2, False),  # Should not detect with higher threshold
        ],
    )
    def test_google_trends_hype(self, social_terms, hits_required, expected):
        """Test Google Trends hype detection with various configurations."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = ')]}\'{"default":{"trendingSearchesDays":[{"trendingSearches":[{"title":{"query":"bitcoin moon"}}]}]}}'
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with patch("main.C.SOCIAL_TERMS", social_terms):
                with patch("main.C.TRENDS_HITS_REQ", hits_required):
                    assert google_trends_hype() == expected

    def test_google_trends_hype_error(self):
        """Test Google Trends hype detection with error response."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("API error")
            assert google_trends_hype() == False  # Should return False on error

    def test_google_trends_hype_empty(self):
        """Test Google Trends hype detection with empty response."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = ")]}'"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            assert google_trends_hype() == False

    @pytest.mark.parametrize(
        "app_name,expected",
        [
            ("Coinbase - Buy Bitcoin & Ether", True),  # Should detect Coinbase
            ("Other App", False),  # Should not detect other apps
        ],
    )
    def test_coinbase_trending(self, app_name, expected):
        """Test Coinbase app store trending detection with various app names."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "feed": {"results": [{"name": app_name}]}
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            assert coinbase_app_top() == expected

    def test_coinbase_trending_error(self):
        """Test Coinbase app store trending detection with error response."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("API error")
            assert coinbase_app_top() == False  # Should return False on error

    def test_coinbase_trending_empty(self):
        """Test Coinbase app store trending detection with empty response."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feed": {"results": []}}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            assert coinbase_app_top() == False


class TestHistoryFunctions:
    """Tests for history file handling functions."""

    def test_load_history_existing_file(self, tmp_path):
        """Test loading history from an existing file."""
        # Create a test history file
        history_file = tmp_path / "test_history.json"
        test_data = [{"date": "2025-01-01", "ratio": 0.5}]
        with open(history_file, "w") as f:
            import json

            json.dump(test_data, f)

        # Test loading
        with patch("main.C.HISTORY_FILE", str(history_file)):
            history = load_history()
            assert history == test_data

    def test_load_history_nonexistent_file(self):
        """Test loading history from a nonexistent file."""
        with patch("main.C.HISTORY_FILE", "nonexistent_file.json"):
            history = load_history()
            assert history == []

    def test_save_history(self, tmp_path):
        """Test saving history to a file."""
        history_file = tmp_path / "test_history.json"
        test_data = [{"date": f"2025-01-{i}", "ratio": 0.1 * i} for i in range(1, 100)]

        with patch("main.C.HISTORY_FILE", str(history_file)):
            save_history(test_data)

            # Verify file was created
            assert history_file.exists()

            # Verify content
            with open(history_file) as f:
                import json

                saved_data = json.load(f)
                assert len(saved_data) == 90  # Should keep only last 90 entries
                assert (
                    saved_data[0]["date"] == "2025-01-10"
                )  # First entry should be 10th
                assert (
                    saved_data[-1]["date"] == "2025-01-99"
                )  # Last entry should be 99th
