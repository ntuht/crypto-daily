"""
push_notify.py — Send push notifications via Bark (iOS).

Bark is a simple push notification service for iPhone.
Install Bark from App Store, copy your device key, and set it in config.yaml.

Usage:
    python survey/scripts/push_notify.py --test          # send test notification
    python survey/scripts/push_notify.py --title "..." --body "..."
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import yaml
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config.yaml"


def load_bark_config():
    """Load Bark key and site URL from config.yaml."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config.get("survey", {})


def send_bark(title, body, url=None, group="每日论文", bark_key=None):
    """
    Send a push notification via Bark.

    Args:
        title: Notification title (shown prominently)
        body: Notification body text
        url: Optional URL to open when notification is tapped
        group: Grouping label in Bark app
        bark_key: Bark device key (loaded from config if not provided)

    Returns:
        True if sent successfully, False otherwise
    """
    if not bark_key:
        config = load_bark_config()
        bark_key = config.get("bark_key", "")

    if not bark_key:
        print("⚠️  Bark key not configured. Set survey.bark_key in config.yaml")
        print("   Or pass --bark-key <key> as argument.")
        return False

    # Build the Bark API URL
    api_url = f"https://api.day.app/{bark_key}"

    payload = {
        "title": title,
        "body": body,
        "group": group,
        "sound": "minuet",  # gentle notification sound
        "icon": "https://raw.githubusercontent.com/nicpottier/cryptoicons/master/SVG/AES.svg",
    }

    if url:
        payload["url"] = url

    data = json.dumps(payload).encode("utf-8")

    try:
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "CryptoLLM-Survey/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 200:
                print(f"✅ Bark push sent: {title}")
                return True
            else:
                print(f"⚠️  Bark returned: {result}")
                return False

    except urllib.error.URLError as e:
        print(f"❌ Bark push failed (network): {e}")
        return False
    except Exception as e:
        print(f"❌ Bark push failed: {e}")
        return False


def send_daily_summary(new_count, highlights, report_date, site_base_url=None, bark_key=None):
    """
    Send a daily paper summary notification.

    Args:
        new_count: Number of new papers found
        highlights: List of highlight strings (top 3 papers)
        report_date: Date string (YYYY-MM-DD)
        site_base_url: Base URL for GitHub Pages site
        bark_key: Bark device key
    """
    if new_count == 0:
        title = f"📄 {report_date} 无新论文"
        body = "今日 ePrint 未发现对称密码相关新论文。"
    else:
        title = f"📄 今日新论文 {new_count} 篇"
        body_parts = []
        for h in highlights[:3]:
            body_parts.append(f"⭐ {h}")
        if new_count > 3:
            body_parts.append(f"...及其他 {new_count - 3} 篇")
        body = "\n".join(body_parts)

    # Build URL to the daily report page
    url = None
    if site_base_url:
        url = f"{site_base_url.rstrip('/')}/daily/{report_date}.html"

    return send_bark(title, body, url=url, bark_key=bark_key)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Send Bark push notifications")
    parser.add_argument("--test", action="store_true", help="Send a test notification")
    parser.add_argument("--title", default="CryptoLLM Test", help="Notification title")
    parser.add_argument("--body", default="", help="Notification body")
    parser.add_argument("--url", default=None, help="URL to open on tap")
    parser.add_argument("--bark-key", default=None, help="Bark device key")
    args = parser.parse_args()

    if args.test:
        success = send_bark(
            "🔐 CryptoLLM Push Test",
            "如果你看到这条消息，说明推送配置成功！\n点击可打开 ePrint.",
            url="https://eprint.iacr.org/",
            bark_key=args.bark_key,
        )
        sys.exit(0 if success else 1)

    if args.body:
        success = send_bark(args.title, args.body, url=args.url, bark_key=args.bark_key)
        sys.exit(0 if success else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
