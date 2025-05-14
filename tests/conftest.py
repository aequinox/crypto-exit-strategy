import pytest
import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any


@pytest.fixture
def mock_env(monkeypatch):
    """
    Mock environment variables for testing.

    This fixture sets up a controlled environment with predefined values
    for all configuration variables used by the application.
    """
    test_env = {
        "EMAIL_ADDRESS": "test@example.com",
        "EMAIL_PASSWORD": "test_password",
        "FRED_API_KEY": "test_fred_key",
        "BTC_DOM_THRESHOLD": "45.0",
        "M2_FLAT_THRESHOLD": "0.001",
        "ALT_PULLBACK": "0.90",
        "TRENDS_HITS_REQ": "2",
        "SOCIAL_TERMS": "bitcoin,crypto,eth",
        "HISTORY_FILE": "test_history.json",
        "APP_STORE_RSS": "https://test.example.com/apps.json",
        "FEAR_GREED_API": "https://test.example.com/fng",
    }
    for k, v in test_env.items():
        monkeypatch.setenv(k, v)
    return test_env


@pytest.fixture
def mock_responses():
    """
    Mock API responses for testing.

    This fixture provides standardized mock responses for all external APIs
    used by the application, including success and error scenarios.
    """

    class MockResponses:
        @staticmethod
        def coingecko_global(success=True):
            if not success:
                raise requests.exceptions.RequestException("API error")
            return {
                "data": {
                    "market_cap_percentage": {"btc": 40.0, "eth": 20.0},
                    "total_market_cap": {"usd": 2000000000000},
                }
            }

        @staticmethod
        def fear_greed(success=True):
            if not success:
                raise requests.exceptions.RequestException("API error")
            return {"data": [{"value": "95"}]}

        @staticmethod
        def m2_series(success=True, empty=False):
            if not success:
                raise requests.exceptions.RequestException("API error")
            if empty:
                return {"observations": []}
            return {
                "observations": [{"value": "100"}, {"value": "101"}, {"value": "101.1"}]
            }

        @staticmethod
        def google_trends(success=True, empty=False):
            if not success:
                raise requests.exceptions.RequestException("API error")
            if empty:
                return ")]}'"
            return ')]}\'{"default":{"trendingSearchesDays":[{"trendingSearches":[{"title":{"query":"bitcoin moon"}}]}]}}'

        @staticmethod
        def app_store(success=True, empty=False):
            if not success:
                raise requests.exceptions.RequestException("API error")
            if empty:
                return {"feed": {"results": []}}
            return {"feed": {"results": [{"name": "Coinbase - Buy Bitcoin & Ether"}]}}

    return MockResponses


@pytest.fixture
def mock_requests(mock_responses):
    """
    Mock requests.get for all HTTP requests.

    This fixture intercepts all HTTP requests made with requests.get and
    returns appropriate mock responses based on the URL.
    """
    with patch("requests.get") as mock_get:

        def get_response(url, **kwargs):
            mock = MagicMock()
            if "coingecko" in url:
                mock.json.return_value = mock_responses.coingecko_global()
            elif "fng" in url:
                mock.json.return_value = mock_responses.fear_greed()
            elif "fred" in url:
                mock.json.return_value = mock_responses.m2_series()
            elif "trends" in url:
                mock.text = mock_responses.google_trends()
            elif "apps" in url:
                mock.json.return_value = mock_responses.app_store()
            mock.raise_for_status = MagicMock()
            return mock

        mock_get.side_effect = get_response
        return mock_get


@pytest.fixture
def mock_requests_error():
    """
    Mock requests.get to simulate API errors.

    This fixture makes all HTTP requests fail with an exception,
    allowing tests to verify error handling.
    """
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("API error")
        return mock_get


@pytest.fixture
def mock_smtp():
    """
    Mock SMTP for email testing.

    This fixture intercepts all SMTP operations to prevent actual emails
    from being sent during tests.
    """
    with patch("smtplib.SMTP") as mock_smtp:
        yield mock_smtp


@pytest.fixture
def mock_smtp_error():
    """
    Mock SMTP to simulate email sending errors.

    This fixture makes SMTP operations fail with an exception,
    allowing tests to verify error handling in email sending.
    """
    with patch("smtplib.SMTP") as mock_smtp:
        mock_context = MagicMock()
        mock_context.__enter__.side_effect = smtplib.SMTPException("SMTP error")
        mock_smtp.return_value = mock_context
        return mock_smtp


@pytest.fixture
def mock_history_file(tmp_path):
    """
    Create a temporary history file for testing.

    This fixture creates a controlled history file with predefined data
    in a temporary directory to avoid affecting real data.
    """
    history_file = tmp_path / "test_history.json"
    # Create 30 days of history with max ratio 0.5
    history = [
        {"date": f"2025-04-{day:02d}", "ratio": 0.4 + 0.1 * (day / 30)}
        for day in range(1, 31)
    ]
    with open(history_file, "w") as f:
        json.dump(history, f)

    # Return both the file path and the history data
    return {"path": str(history_file), "data": history}


import requests
import smtplib
