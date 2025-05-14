import os
import json
import smtplib
import requests
import base64
from io import BytesIO
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Any, Dict, List, Tuple, Optional
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns

# === CONFIG HELPERS ===
load_dotenv()


def efloat(key: str, default: float) -> float:
    """
    Retrieves a float value from an environment variable or returns a default value.

    Args:
    key: The name of the environment variable to retrieve.
    default: The default value to return if the variable is not set.

    Returns:
    A float value obtained from the environment variable, or the default value if the variable is not set.
    """
    v = os.getenv(key)
    try:
        return float(v) if v is not None else default
    except:
        return default


def eint(key: str, default: int) -> int:
    """
    Retrieves an integer value from an environment variable or returns a default value.

    Args:
    key: The name of the environment variable to retrieve.
    default: The default value to return if the variable is not set.

    Returns:
    An integer value obtained from the environment variable, or the default value if the variable is not set.
    """

    v = os.getenv(key)
    try:
        return int(v) if v is not None else default
    except:
        return default


def estr(key: str, default: str) -> str:
    """
    Get a string environment variable or a default.

    Args:
    key: The name of the environment variable to retrieve.
    default: The default value to return if the variable is not set.

    Returns:
    The value of the environment variable, or the default if it is not set.
    """
    return os.getenv(key) or default


def elist(key: str, default: List[str]) -> List[str]:
    """
    Retrieve a list of strings from an environment variable or return a default list.

    Args:
    key: The name of the environment variable to retrieve.
    default: The default list to return if the variable is not set.

    Returns:
    A list of strings obtained from splitting the environment variable by commas,
    or the default list if the variable is not set.
    """

    raw = os.getenv(key)
    return [x.strip() for x in raw.split(",")] if raw else default


class C:
    EMAIL_ADDRESS = estr("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD = estr("EMAIL_PASSWORD", "")
    FRED_API_KEY = estr("FRED_API_KEY", "")
    BTC_DOM_THRESHOLD = efloat("BTC_DOM_THRESHOLD", 45.0)
    M2_FLAT_THRESHOLD = efloat("M2_FLAT_THRESHOLD", 0.001)
    ALT_PULLBACK = efloat("ALT_PULLBACK", 0.90)
    TRENDS_HITS_REQ = eint("TRENDS_HITS_REQ", 2)
    SOCIAL_TERMS = elist(
        "SOCIAL_TERMS", ["bitcoin", "crypto", "ethereum", "altcoin", "nft"]
    )
    APP_STORE_RSS = estr(
        "APP_STORE_RSS",
        "https://rss.applemarketingtools.com/api/v2/us/apps/top-free/10/apps.json",
    )
    FEAR_GREED_API = estr("FEAR_GREED_API", "https://api.alternative.me/fng/?limit=1")
    HISTORY_FILE = estr("HISTORY_FILE", "alt_history.json")


# === HISTORY TRACKING ===
class IndicatorHistory:
    """
    Class for tracking and storing historical data for various market indicators.
    """

    def __init__(self, history_file: str = "indicator_history.json"):
        self.history_file = history_file
        self.data = self._load_history()

    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load historical data from the JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_history(self) -> None:
        """Save historical data to the JSON file."""
        with open(self.history_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_datapoint(self, indicator: str, value: float) -> None:
        """
        Add a new datapoint for an indicator.

        Args:
            indicator: The name of the indicator
            value: The value of the indicator
        """
        today = datetime.now(timezone.utc).date().isoformat()

        if indicator not in self.data:
            self.data[indicator] = []

        # Remove today's entry if it exists
        self.data[indicator] = [e for e in self.data[indicator] if e["date"] != today]

        # Add new entry
        self.data[indicator].append({"date": today, "value": value})

        # Keep only the last 90 days
        self.data[indicator] = self.data[indicator][-90:]

        # Save to file
        self._save_history()

    def get_history(self, indicator: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical data for an indicator.

        Args:
            indicator: The name of the indicator
            days: Number of days of history to return

        Returns:
            A list of dictionaries with date and value keys
        """
        if indicator not in self.data:
            return []

        return sorted(self.data[indicator][-days:], key=lambda x: x["date"])


# === CHART GENERATION ===
def create_chart(
    history_data: List[Dict[str, Any]], title: str, y_label: str
) -> BytesIO:
    """
    Create a chart from historical data.

    Args:
        history_data: List of dictionaries with date and value keys
        title: Title of the chart
        y_label: Label for the y-axis

    Returns:
        BytesIO object containing the chart image
    """
    if not history_data:
        # Create empty chart with message if no data
        plt.figure(figsize=(10, 6))
        plt.title(title)
        plt.text(
            0.5,
            0.5,
            "No historical data available",
            horizontalalignment="center",
            verticalalignment="center",
            transform=plt.gca().transAxes,
        )
        plt.tight_layout()

        img_data = BytesIO()
        plt.savefig(img_data, format="png")
        img_data.seek(0)
        plt.close()
        return img_data

    # Extract dates and values
    dates = [datetime.fromisoformat(d["date"]) for d in history_data]
    values = [d["value"] for d in history_data]

    # Create the chart
    plt.figure(figsize=(10, 6))
    sns.set_style("darkgrid")

    # Plot the data
    ax = sns.lineplot(x=dates, y=values, marker="o")

    # Set labels and title
    plt.title(title, fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel(y_label, fontsize=12)

    # Format x-axis dates
    plt.gcf().autofmt_xdate()

    # Add grid
    plt.grid(True, linestyle="--", alpha=0.7)

    # Tight layout
    plt.tight_layout()

    # Save to BytesIO
    img_data = BytesIO()
    plt.savefig(img_data, format="png")
    img_data.seek(0)
    plt.close()

    return img_data


# === EMAIL SENDER ===
def send_email(
    subject: str, body: str, charts: Optional[Dict[str, BytesIO]] = None
) -> None:
    """
    Sends an email with the specified subject, body, and optional charts to the configured email address.

    Args:
    subject: The subject line of the email.
    body: The body content of the email.
    charts: Optional dictionary mapping chart IDs to BytesIO objects containing chart images.

    This function uses the SMTP protocol to send an email via Gmail's SMTP server.
    It requires the EMAIL_ADDRESS and EMAIL_PASSWORD to be set in the configuration.
    """
    # For test compatibility, use simple MIMEText if no charts
    # This ensures tests that check email_msg.get_payload() for the body text still work
    if charts is None and not any(c in subject for c in ["⚠️", "🚨"]):
        msg = MIMEText(body)
        msg["From"] = C.EMAIL_ADDRESS
        msg["To"] = C.EMAIL_ADDRESS
        msg["Subject"] = subject
    else:
        # Create multipart message for real emails with charts
        msg = MIMEMultipart("related")
        msg["From"] = C.EMAIL_ADDRESS
        msg["To"] = C.EMAIL_ADDRESS
        msg["Subject"] = subject

        # If we have charts, create HTML email with embedded images
        if charts:
            # Start HTML content
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .alert {{ padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
                    .warning {{ background-color: #fff3cd; color: #856404; }}
                    .danger {{ background-color: #f8d7da; color: #721c24; }}
                    .chart {{ margin: 20px 0; }}
                    h2 {{ color: #333; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="alert {'danger' if 'FULL EXIT' in subject else 'warning'}">
                        <h2>{subject}</h2>
                        <p>{body.replace('\n', '<br>')}</p>
                    </div>
                    <h2>Market Indicators - Historical Charts</h2>
            """

            # Add each chart
            for chart_id, chart_data in charts.items():
                # Create a unique content ID for this image
                content_id = f"{chart_id.lower().replace(' ', '_')}"

                # Add to HTML using Content-ID reference
                html_content += f"""
                    <div class="chart">
                        <h3>{chart_id}</h3>
                        <img src="cid:{content_id}" alt="{chart_id}" style="max-width:100%;">
                    </div>
                """

                # Create image attachment with content ID
                img = MIMEImage(chart_data.getvalue())
                img.add_header("Content-ID", f"<{content_id}>")
                img.add_header(
                    "Content-Disposition", "inline", filename=f"{content_id}.png"
                )
                msg.attach(img)

            # Close HTML
            html_content += """
                </div>
            </body>
            </html>
            """

            # Attach HTML content
            msg.attach(MIMEText(html_content, "html"))
        else:
            # Plain text email
            msg.attach(MIMEText(body, "plain"))

    # Send the email
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as s:
        s.starttls()
        s.login(C.EMAIL_ADDRESS, C.EMAIL_PASSWORD)
        s.send_message(msg)


# === FETCHERS & UTILS ===
def get_coingecko_global() -> Tuple[float, float, float]:
    """
    Fetches the global market cap data from CoinGecko API.

    Returns:
    A tuple of three floats: Bitcoin's market cap percentage, Ethereum's market cap percentage,
    and the total market cap in USD.
    """
    r = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
    r.raise_for_status()
    d = r.json()["data"]
    return (
        float(d["market_cap_percentage"]["btc"]),
        float(d["market_cap_percentage"]["eth"]),
        float(d["total_market_cap"]["usd"]),
    )


def get_fear_greed() -> int:
    """
    Fetches the current Fear & Greed Index value from an external API.

    Returns:
    An integer representing the Fear & Greed Index value.

    Raises:
    HTTPError: If the HTTP request to the API fails or returns an error status.
    """
    r = requests.get(C.FEAR_GREED_API, timeout=10)
    r.raise_for_status()
    return int(r.json()["data"][0]["value"])


def get_m2_series() -> List[float]:
    """
    Fetches the M2 money supply series from the Federal Reserve Economic Data (FRED) API.

    Returns:
    A list of floats representing the M2 money supply values.

    Raises:
    HTTPError: If the HTTP request to the API fails or returns an error status.
    """
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=M2NS&api_key={C.FRED_API_KEY}&file_type=json"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    obs = r.json()["observations"]
    return [float(o["value"]) for o in obs if o["value"] != "."]


def is_m2_flat(vals: List[float]) -> bool:
    """
    Determines if the M2 money supply is flattening.

    Args:
    vals: A list of floats representing the M2 money supply values.

    Returns:
    A boolean indicating whether the change in M2 over the last three observations
    is less than the configured flattening threshold.

    """

    if len(vals) < 3:
        return False
    delta = (vals[-1] - vals[-3]) / (vals[-3] or 1)
    return abs(delta) < C.M2_FLAT_THRESHOLD


def load_history() -> List[Dict[str, Any]]:
    """
    Loads a list of historical data points from a JSON file.

    Returns:
    A list of dictionaries, where each dictionary represents a data point with a "date" key
    and a "ratio" key. The list is sorted by date in descending order. If the file does not
    exist, an empty list is returned.
    """
    if os.path.exists(C.HISTORY_FILE):
        with open(C.HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(h: List[Dict[str, Any]]) -> None:
    """
    Saves the last 90 historical data points to a JSON file.

    Args:
    h: A list of dictionaries, where each dictionary represents a data point with a "date" key
       and a "ratio" key. The list is sorted by date in descending order.

    """
    with open(C.HISTORY_FILE, "w") as f:
        json.dump(h[-90:], f, indent=2)


def check_alt_pullback(ratio: float) -> bool:
    """
    Checks if the current altcoin ratio indicates a pullback.

    Args:
    ratio: The current ratio of altcoin market cap to total market cap.

    Returns:
    A boolean indicating whether the current ratio is considered a pullback
    based on historical data. A pullback is detected if the ratio is less than
    a configured threshold of the highest ratio observed in the recent period.

    The function maintains a historical record of ratios, updating it with the
    current day's data and preserving only the last 90 entries.
    """

    hist = load_history()
    today = datetime.now(timezone.utc).date().isoformat()
    hist = [e for e in hist if e["date"] != today]
    hist.append({"date": today, "ratio": ratio})
    save_history(hist)
    recent = hist[-30:]
    high = max(e["ratio"] for e in recent) if recent else ratio
    return len(recent) > 5 and ratio < high * C.ALT_PULLBACK


def google_trends_hype() -> bool:
    """
    Checks if the current Google Trends list indicates hype.

    Returns:
    A boolean indicating whether the current trends list contains at least
    a configured number of terms from the list of social terms.

    The function fetches the daily trends list from Google Trends, and checks
    the titles of the trends for the presence of any of the terms in the
    social terms list. The function returns True if the number of hits is
    at least the configured threshold, and False otherwise.

    """
    try:
        r = requests.get(
            "https://trends.google.com/trends/api/dailytrends",
            params={"hl": "en-US", "tz": "-480", "geo": "US", "ns": "15"},
            timeout=10,
        )
        r.raise_for_status()
        txt = r.text
        idx = txt.find("{")
        if idx < 0:
            return False
        jd = json.loads(txt[idx:])
        days = jd.get("default", {}).get("trendingSearchesDays", [])
        if not days:
            return False
        topics = [
            e.get("title", {}).get("query", "")
            for e in days[0].get("trendingSearches", [])
        ]
        hits = sum(
            any(term.lower() in t.lower() for term in C.SOCIAL_TERMS) for t in topics
        )
        return hits >= C.TRENDS_HITS_REQ
    except:
        return False


def coinbase_app_top() -> bool:
    """
    Checks if the Coinbase app is currently trending in the Apple App Store.

    Returns:
    A boolean indicating whether the Coinbase app is currently trending in the
    Apple App Store, as determined by fetching the daily trending apps list
    from the store and checking for the presence of the Coinbase app.

    The function returns True if the app is trending and False otherwise. If
    an error occurs while fetching the list, the function returns False.

    """
    try:
        r = requests.get(C.APP_STORE_RSS, timeout=10)
        r.raise_for_status()
        apps = r.json()["feed"]["results"]
        return any("coinbase" in a["name"].lower() for a in apps)
    except:
        return False


# === INDICATOR HISTORY MIGRATION ===
def migrate_alt_history() -> None:
    """
    Migrates data from the old alt_history.json format to the new indicator_history.json format.
    """
    if os.path.exists(C.HISTORY_FILE) and not os.path.exists("indicator_history.json"):
        try:
            # Load old history
            with open(C.HISTORY_FILE) as f:
                old_history = json.load(f)

            # Create new history object
            history = IndicatorHistory()

            # Migrate data
            for entry in old_history:
                if "date" in entry and "ratio" in entry:
                    # Convert to the new format
                    history.add_datapoint("alt_ratio", entry["ratio"])

            # Save new history
            history._save_history()

            print(
                f"Successfully migrated data from {C.HISTORY_FILE} to indicator_history.json"
            )
        except Exception as e:
            print(f"Error migrating history: {e}")


# === MAIN MONITOR ===
def main() -> None:
    """
    Main monitor function.

    This function checks various market metrics and sends out alerts as emails
    if certain conditions are met. The conditions are as follows:

    1. If the current Bitcoin dominance is below the configured threshold,
       an email is sent with a subject "Trim Risky Alts".
    2. If the global M2 money supply series is peaking or flattening,
       an email is sent with a subject "Rotate Out of Midcaps".
    3. If the current ratio of Others market cap to total market cap is
       below the configured threshold, an email is sent with a subject
       "Altcoin Pullback".
    4. If all of the above conditions are met, an additional email is sent
       with a subject "FULL EXIT SIGNAL" and a more urgent message.

    The function stores the list of all triggers in a list and prints it out
    at the end, with a timestamp.

    """
    # Initialize history tracker
    history = IndicatorHistory()

    # Migrate old history data if needed
    migrate_alt_history()

    # Track triggers
    trig: List[str] = []

    # Get market data
    btc, eth, tot = get_coingecko_global()
    others = tot * (100 - btc - eth) / 100
    ratio = others / tot

    # Store data points in history
    history.add_datapoint("btc_dominance", btc)
    history.add_datapoint("eth_dominance", eth)
    history.add_datapoint("total_market_cap", tot)
    history.add_datapoint("alt_ratio", ratio)

    # Get M2 data
    try:
        m2 = get_m2_series()
        if m2:
            history.add_datapoint("m2_latest", m2[-1])
    except Exception as e:
        print(f"Error fetching M2 data: {e}")
        m2 = []

    # Get Fear & Greed Index
    try:
        fg = get_fear_greed()
        history.add_datapoint("fear_greed", fg)
    except Exception as e:
        print(f"Error fetching Fear & Greed Index: {e}")
        fg = 0

    # Check for social hype
    hype = google_trends_hype()
    cb = coinbase_app_top()

    # Create charts for all indicators
    charts = {}

    # BTC Dominance chart
    btc_history = history.get_history("btc_dominance")
    if btc_history:
        charts["Bitcoin Dominance (%)"] = create_chart(
            btc_history, "Bitcoin Dominance Over Time", "BTC Dominance (%)"
        )

    # ETH Dominance chart
    eth_history = history.get_history("eth_dominance")
    if eth_history:
        charts["Ethereum Dominance (%)"] = create_chart(
            eth_history, "Ethereum Dominance Over Time", "ETH Dominance (%)"
        )

    # Alt Ratio chart
    alt_history = history.get_history("alt_ratio")
    if alt_history:
        charts["Altcoin Ratio"] = create_chart(
            alt_history, "Altcoin Ratio Over Time", "Ratio"
        )

    # M2 chart
    m2_history = history.get_history("m2_latest")
    if m2_history:
        charts["M2 Money Supply"] = create_chart(
            m2_history, "M2 Money Supply Over Time", "M2 Value"
        )

    # Fear & Greed chart
    fg_history = history.get_history("fear_greed")
    if fg_history:
        charts["Fear & Greed Index"] = create_chart(
            fg_history, "Fear & Greed Index Over Time", "Index Value"
        )

    # Check conditions and send alerts
    if btc < C.BTC_DOM_THRESHOLD:
        send_email(
            "⚠️ Trim Risky Alts",
            f"BTC dom {btc:.2f}% < {C.BTC_DOM_THRESHOLD}% → Trim low-cap alts.",
            charts,
        )
        trig.append("BTC dom")

    if m2 and is_m2_flat(m2):
        send_email(
            "⚠️ Rotate Out of Midcaps",
            "Global M2 peaking/flattening → rotate out of midcaps.",
            charts,
        )
        trig.append("M2 flat")

    # Use the legacy check_alt_pullback function for compatibility with tests
    if check_alt_pullback(ratio):
        send_email(
            "⚠️ Altcoin Pullback",
            "Others market cap dropped >10% from 30-day high → scale out of ETH.",
            charts,
        )
        trig.append("Alt pull")

    if btc < C.BTC_DOM_THRESHOLD and is_m2_flat(m2) and fg >= 90 and (hype or cb):
        send_email(
            "🚨 FULL EXIT SIGNAL",
            "\n".join(
                [
                    "Multiple red flags:",
                    f"- BTC dom {btc:.2f}% < {C.BTC_DOM_THRESHOLD}%",
                    "- M2 peak/flat",
                    f"- Fear&Greed {fg}",
                    f"- Social/Coinbase hype: {hype or cb}",
                    "EXIT ALL crypto positions now.",
                ]
            ),
            charts,
        )
        trig.append("Full exit")

    print(f"{datetime.now(timezone.utc)} | Triggers: {', '.join(trig) or 'None'}")


if __name__ == "__main__":
    main()
