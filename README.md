# Crypto Market Monitor

A Python tool that monitors cryptocurrency market conditions and sends email alerts based on configurable thresholds and market indicators.

## Features

- **Bitcoin Dominance Monitoring**: Alerts when BTC dominance falls below a configurable threshold
- **M2 Money Supply Analysis**: Detects flattening in global M2 money supply
- **Altcoin Market Pullback Detection**: Identifies significant drops in altcoin market capitalization
- **Social Media & App Store Trend Analysis**: Monitors Google Trends and App Store rankings for crypto hype
- **Fear & Greed Index Integration**: Incorporates market sentiment analysis
- **Email Alerts**: Sends customized email notifications for different market conditions

## Prerequisites

- Python 3.13 or higher
- Email account for sending alerts (Gmail recommended)
- FRED API key (for M2 money supply data)

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management. If you don't have uv installed, you can install it following the instructions on the [uv documentation](https://github.com/astral-sh/uv).

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/crypto.git
   cd crypto
   ```

2. Initialize the project with uv:

   ```bash
   uv init
   ```

3. Install the required dependencies:

   ```bash
   uv pip install requests python-dotenv
   ```

4. For development and testing, install the development dependencies:
   ```bash
   uv pip install pytest pytest-cov
   ```

## Configuration

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:

   ```
   # Email/Gmail SMTP Auth
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password  # For Gmail, use an App Password

   # API Keys
   FRED_API_KEY=your-fred-api-key

   # Strategy Thresholds
   BTC_DOM_THRESHOLD=45.0
   M2_FLAT_THRESHOLD=0.001
   ALT_PULLBACK=0.90
   TRENDS_HITS_REQ=2

   # Social Terms (comma-separated)
   SOCIAL_TERMS=bitcoin,crypto,ethereum,altcoin,nft

   # External Endpoints & Files
   APP_STORE_RSS=https://rss.applemarketingtools.com/api/v2/us/apps/top-free/10/apps.json
   FEAR_GREED_API=https://api.alternative.me/fng/?limit=1
   HISTORY_FILE=alt_history.json
   ```

### Gmail Configuration Notes

If you're using Gmail, you'll need to:

1. Enable 2-Step Verification for your Google account
2. Generate an App Password for this application
3. Use that App Password in the `.env` file

## Running the Application

Run the application using uv:

```bash
uv run main.py
```

The application will:

1. Check various market metrics
2. Send email alerts if configured thresholds are triggered
3. Print a summary of triggered alerts to the console

### Scheduling with Systemd Timer

For continuous monitoring, you can set up a systemd timer to run the application twice daily at 12 noon and 12 midnight.

1. Create a service file at `~/.config/systemd/user/crypto-monitor.service`:

```ini
[Unit]
Description=Crypto Market Monitor Service
After=network.target

[Service]
Type=oneshot
WorkingDirectory=%h/Projects/Python/crypto
ExecStart=/usr/bin/uv run %h/Projects/Python/crypto/main.py
Environment="PATH=%h/.local/bin:/usr/bin"

[Install]
WantedBy=default.target
```

2. Create a timer file at `~/.config/systemd/user/crypto-monitor.timer`:

```ini
[Unit]
Description=Run Crypto Market Monitor twice daily

[Timer]
OnCalendar=*-*-* 00:00:00
OnCalendar=*-*-* 12:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. Enable and start the timer:

```bash
systemctl --user daemon-reload
systemctl --user enable crypto-monitor.timer
systemctl --user start crypto-monitor.timer
```

4. Verify the timer is active:

```bash
systemctl --user list-timers
```

### Alternative: Cron Job

If you prefer using cron instead of systemd:

```
0 0,12 * * * cd /path/to/crypto && /path/to/uv run main.py
```

## Testing

Run the test suite using pytest through uv:

```bash
uv run -m pytest
```

### Running Specific Tests

To run specific test files:

```bash
uv run -m pytest tests/test_fetchers.py
```

To run tests with coverage report:

```bash
uv run -m pytest --cov=.
```

## Project Structure

- `main.py`: Main application code with all functionality
- `tests/`: Test directory
  - `conftest.py`: Test fixtures and configuration
  - `test_config.py`: Tests for configuration handling
  - `test_fetchers.py`: Tests for data fetching functions
  - `test_monitors.py`: Tests for monitoring and alert functions
- `.env.example`: Example environment configuration
- `pytest.ini`: Pytest configuration

## Alert Types

The application sends different types of email alerts:

1. **Trim Risky Alts**: When Bitcoin dominance falls below threshold
2. **Rotate Out of Midcaps**: When M2 money supply is flattening
3. **Altcoin Pullback**: When altcoin market cap drops significantly from recent high
4. **FULL EXIT SIGNAL**: When multiple critical conditions are met simultaneously

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Lab Of Crypto YouTube Channel](https://www.youtube.com/watch?v=xz2WfAcurGg) for inspiration and market analysis techniques
