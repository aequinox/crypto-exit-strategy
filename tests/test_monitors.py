import pytest
import json
import os
import smtplib
import requests
from unittest.mock import patch, call, MagicMock
from datetime import datetime, timezone
from main import check_alt_pullback, send_email, main, load_history, save_history


class TestAltcoinPullback:
    """Tests for altcoin pullback detection."""

    def test_alt_pullback_detection(self, tmp_path):
        """Test altcoin pullback detection with various ratios and thresholds."""
        # Create a history file with a known maximum ratio
        history_file = tmp_path / "test_history.json"
        # Create 30 days of history with max ratio 0.5
        history = [
            {"date": f"2025-04-{day:02d}", "ratio": 0.4 + 0.1 * (day / 30)}
            for day in range(1, 31)
        ]
        with open(history_file, "w") as f:
            json.dump(history, f)

        with patch("main.C.HISTORY_FILE", str(history_file)):
            with patch("main.C.ALT_PULLBACK", 0.9):
                # Test with ratio that should trigger pullback
                # (0.4 is less than 0.9 * max_ratio of 0.5)
                result = check_alt_pullback(0.4)
                assert (
                    result is True
                ), f"Expected True for pullback detection, got {result}"

                # Test with ratio that shouldn't trigger pullback
                # (0.6 is greater than 0.9 * max_ratio of 0.5)
                result = check_alt_pullback(0.6)
                assert result is False, f"Expected False for no pullback, got {result}"

    def test_alt_pullback_insufficient_history(self, tmp_path):
        """Test altcoin pullback detection with insufficient history."""
        # Create history with only 3 days (less than required 5)
        history_file = tmp_path / "short_history.json"
        history = [{"date": f"2025-04-{day:02d}", "ratio": 0.5} for day in range(1, 4)]
        with open(history_file, "w") as f:
            json.dump(history, f)

        with patch("main.C.HISTORY_FILE", str(history_file)):
            # Should return False due to insufficient history
            assert check_alt_pullback(0.4) is False

    def test_alt_pullback_updates_history(self, tmp_path):
        """Test that check_alt_pullback updates the history file with the current ratio."""
        history_file = tmp_path / "update_history.json"
        history = [{"date": f"2025-04-{day:02d}", "ratio": 0.5} for day in range(1, 31)]
        with open(history_file, "w") as f:
            json.dump(history, f)

        # Create a fixed date for testing
        fixed_date = "2025-05-01"

        with patch("main.C.HISTORY_FILE", str(history_file)):
            # Mock datetime.now to return a fixed date
            with patch("main.datetime") as mock_datetime:
                mock_dt = MagicMock()
                mock_dt.date.return_value.isoformat.return_value = fixed_date
                mock_datetime.now.return_value = mock_dt

                # Call the function with a new ratio
                check_alt_pullback(0.6)

                # Verify the history was updated
                updated_history = load_history()
                assert any(
                    entry["date"] == fixed_date and entry["ratio"] == 0.6
                    for entry in updated_history
                )


class TestEmailAlerts:
    """Tests for email alert functionality."""

    def test_email_sending_success(self, mock_smtp, monkeypatch):
        """Test successful email alert sending."""
        # Patch the email address to match the expected value
        monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "test_password")

        # Reload the module to pick up the mocked environment variables
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # Use the send_email function from the reloaded module
        main_module.send_email("Test Subject", "Test Body")
        mock_smtp.assert_called_once()
        mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()

        # Verify email content
        args, _ = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        email_msg = args[0]
        assert email_msg["Subject"] == "Test Subject"
        assert email_msg["From"] == "test@example.com"
        assert email_msg["To"] == "test@example.com"
        assert "Test Body" in email_msg.get_payload()

    def test_email_sending_failure(self, mock_smtp_error, monkeypatch):
        """Test email alert sending with SMTP error."""
        # Patch the email address to match the expected value
        monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "test_password")

        # Reload the module to pick up the mocked environment variables
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # The function should handle the error gracefully
        with pytest.raises(smtplib.SMTPException):
            main_module.send_email("Test Subject", "Test Body")


class TestMainMonitoring:
    """Tests for the main monitoring function."""

    def test_main_all_triggers(
        self, mock_requests, mock_smtp, mock_history_file, monkeypatch
    ):
        """Test full monitoring cycle with all triggers active."""
        # Patch the email address to match the expected value
        monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "test_password")

        # Reload the module to pick up the mocked environment variables
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # Set up mocks for the reloaded module
        with patch("main.C.HISTORY_FILE", mock_history_file["path"]):
            with patch(
                "main.get_coingecko_global",
                return_value=(44.0, 20.0, 2000000000000),
            ):
                with patch("main.get_fear_greed", return_value=95):
                    with patch(
                        "main.get_m2_series",
                        return_value=[100.0, 100.001, 100.002],
                    ):
                        with patch("main.google_trends_hype", return_value=True):
                            with patch("main.coinbase_app_top", return_value=True):
                                with patch(
                                    "main.check_alt_pullback", return_value=True
                                ):
                                    # Run the main function
                                    main_module.main()

                                    # Should have 4 email calls (3 individual alerts + full exit)
                                    # Reset the mock to check only the call count for send_message
                                    mock_smtp.reset_mock()

                                    # Run the main function again
                                    main_module.main()

                                    # Now check the call count
                                    assert (
                                        mock_smtp.return_value.__enter__.return_value.send_message.call_count
                                        == 4
                                    )

                                    # Verify the full exit email was sent
                                    calls = (
                                        mock_smtp.return_value.__enter__.return_value.send_message.call_args_list
                                    )
                                    subjects = [
                                        call.args[0]["Subject"] for call in calls
                                    ]
                                    assert "🚨 FULL EXIT SIGNAL" in subjects

    def test_main_no_triggers(self, mock_requests, mock_smtp, monkeypatch):
        """Test full monitoring cycle with no triggers active."""
        # Patch the email address to match the expected value
        monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "test_password")

        # Reload the module to pick up the mocked environment variables
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # Set up mocks for the reloaded module
        with patch(
            "main.get_coingecko_global",
            return_value=(46.0, 20.0, 2000000000000),
        ):
            with patch("main.get_fear_greed", return_value=50):
                with patch("main.get_m2_series", return_value=[100.0, 110.0, 120.0]):
                    with patch("main.google_trends_hype", return_value=False):
                        with patch("main.coinbase_app_top", return_value=False):
                            with patch("main.check_alt_pullback", return_value=False):
                                # Run the main function
                                main_module.main()

                                # Should have no email calls
                                assert mock_smtp.call_count == 0

    @pytest.mark.parametrize(
        "btc_dom,m2_flat,fear_greed,social_hype,coinbase_top,alt_pullback,expected_emails",
        [
            (
                44.0,
                True,
                95,
                True,
                True,
                True,
                4,
            ),  # All triggers - 3 individual + full exit
            (
                44.0,
                True,
                95,
                False,
                False,
                True,
                3,
            ),  # 3 triggers, no full exit (missing social/coinbase)
            (
                44.0,
                True,
                85,
                True,
                True,
                True,
                3,
            ),  # 3 triggers, no full exit (fear & greed < 90)
            (46.0, True, 95, True, True, True, 2),  # M2 flat and alt pullback triggers
            (
                44.0,
                False,
                95,
                True,
                True,
                True,
                2,
            ),  # BTC dom and alt pullback triggers
            (46.0, False, 50, False, False, False, 0),  # No triggers
        ],
    )
    def test_main_various_conditions(
        self,
        mock_requests,
        mock_smtp,
        mock_history_file,
        monkeypatch,
        btc_dom,
        m2_flat,
        fear_greed,
        social_hype,
        coinbase_top,
        alt_pullback,
        expected_emails,
    ):
        """Test main function with various combinations of conditions."""
        # Patch the email address to match the expected value
        monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "test_password")

        # Reload the module to pick up the mocked environment variables
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # Set up mocks for the reloaded module
        with patch("main.C.HISTORY_FILE", mock_history_file["path"]):
            with patch(
                "main.get_coingecko_global",
                return_value=(btc_dom, 20.0, 2000000000000),
            ):
                with patch("main.get_fear_greed", return_value=fear_greed):
                    with patch("main.is_m2_flat", return_value=m2_flat):
                        with patch("main.google_trends_hype", return_value=social_hype):
                            with patch(
                                "main.coinbase_app_top",
                                return_value=coinbase_top,
                            ):
                                with patch(
                                    "main.check_alt_pullback",
                                    return_value=alt_pullback,
                                ):
                                    # Run the main function
                                    main_module.main()

                                    # Reset the mock to check only the call count for send_message
                                    mock_smtp.reset_mock()

                                    # Run the main function again
                                    main_module.main()

                                    # Verify the expected number of emails
                                    if expected_emails > 0:
                                        assert (
                                            mock_smtp.return_value.__enter__.return_value.send_message.call_count
                                            == expected_emails
                                        )
                                    else:
                                        assert mock_smtp.call_count == 0

    def test_main_with_api_errors(self, mock_smtp, monkeypatch):
        """Test main function handling of API errors."""
        # Patch the email address to match the expected value
        monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")
        monkeypatch.setenv("EMAIL_PASSWORD", "test_password")

        # Reload the module to pick up the mocked environment variables
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # The main function should handle API errors gracefully
        with patch("main.get_coingecko_global") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("API error")
            with pytest.raises(requests.exceptions.RequestException):
                main_module.main()
