"""
daily_pipeline.py — Full daily paper update pipeline.

Orchestrates: fetch → cleanup → digest (LLM) → overview → site build → push notification.

Usage:
    python survey/scripts/daily_pipeline.py              # full run
    python survey/scripts/daily_pipeline.py --dry-run    # skip push notification
    python survey/scripts/daily_pipeline.py --no-download  # skip PDF download
    python survey/scripts/daily_pipeline.py --no-llm     # skip LLM calls in digest
"""

import subprocess
import sys
import re
import yaml
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SURVEY_DIR = SCRIPTS_DIR.parent
PROJECT_DIR = SURVEY_DIR.parent
CONFIG_FILE = PROJECT_DIR / "config.yaml"
REPORTS_DIR = SURVEY_DIR / "reports" / "daily"
PYTHON = sys.executable


def load_config():
    """Load survey config from config.yaml."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("survey", {})
    return {}


def run_step(name, script, args=None):
    """Run a pipeline step and return (success, stdout)."""
    cmd = [PYTHON, "-u", str(SCRIPTS_DIR / script)]
    if args:
        cmd.extend(args)

    print(f"\n{'='*60}")
    print(f"  Step: {name}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_DIR),
            capture_output=True,
            timeout=300,  # 5min to allow LLM calls
            env=env,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        if stdout:
            print(stdout)
        if stderr:
            print(f"  STDERR: {stderr[:500]}", file=sys.stderr)

        if result.returncode != 0:
            print(f"  [WARN] Step '{name}' returned code {result.returncode}")
            return False, stdout
        return True, stdout
    except subprocess.TimeoutExpired:
        print(f"  [ERROR] Step '{name}' timed out after 120s")
        return False, ""
    except Exception as e:
        print(f"  [ERROR] Step '{name}' failed: {e}")
        return False, ""


def extract_new_count(fetch_output):
    """Extract number of new papers from daily_fetch output."""
    match = re.search(r"Added (\d+) new papers", fetch_output)
    if match:
        return int(match.group(1))
    if "No new matching papers" in fetch_output:
        return 0
    return -1  # unknown


def extract_highlights(report_date):
    """Extract highlight paper titles from the daily digest."""
    report_path = REPORTS_DIR / f"{report_date}.md"
    if not report_path.exists():
        return []

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    highlights = []
    # Extract from "⭐ 重点推荐" section — headings like ### 1. [title](url)
    for match in re.finditer(r'### \d+\.\s*\[([^\]]+)\]', content):
        title = match.group(1)
        if len(title) > 60:
            title = title[:57] + "..."
        highlights.append(title)
        if len(highlights) >= 3:
            break

    return highlights


def main():
    dry_run = "--dry-run" in sys.argv
    no_download = "--no-download" in sys.argv
    no_llm = "--no-llm" in sys.argv

    config = load_config()
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"╔{'═'*58}╗")
    print(f"║  CryptoLLM Daily Paper Pipeline                        ║")
    print(f"║  Date: {today}                                    ║")
    print(f"║  Mode: {'DRY RUN' if dry_run else 'LIVE':>8}                                   ║")
    print(f"╚{'═'*58}╝")

    # Step 1: Fetch new papers from ePrint
    fetch_args = ["--no-download"] if no_download else []
    ok, fetch_out = run_step("Fetch ePrint RSS", "daily_fetch.py", fetch_args)
    if not ok:
        print("\n❌ Fetch failed, aborting pipeline.")
        sys.exit(1)

    new_count = extract_new_count(fetch_out)
    print(f"\n  📊 New papers found: {new_count}")

    # Step 2: Cleanup false positives
    run_step("Cleanup False Positives", "cleanup_fp.py")

    # Step 3: Generate daily digest (LLM-powered)
    digest_args = [today]
    if no_llm:
        digest_args.append("--no-llm")
    run_step("Generate Daily Digest", "daily_digest.py", digest_args)

    # Step 4: Regenerate overview
    run_step("Update Overview", "render_overview.py")

    # Step 5: Build static site (with daily reports)
    run_step("Build Static Site", "build_site.py")

    # Step 6: Push notification
    if dry_run:
        print(f"\n{'='*60}")
        print("▶ Step: Push Notification [SKIPPED - dry run]")
        print(f"{'='*60}")
    else:
        highlights = extract_highlights(today)
        bark_key = config.get("bark_key", "")
        site_base_url = config.get("site_base_url", "")

        if not bark_key:
            print(f"\n{'='*60}")
            print("▶ Step: Push Notification [SKIPPED - no bark_key configured]")
            print(f"{'='*60}")
        else:
            from push_notify import send_daily_summary
            send_daily_summary(
                new_count=max(new_count, 0),
                highlights=highlights,
                report_date=today,
                site_base_url=site_base_url,
                bark_key=bark_key,
            )

    # Summary
    print(f"\n{'═'*60}")
    print(f"✅ Pipeline complete!")
    print(f"   Date:       {today}")
    print(f"   New papers: {new_count}")
    report_path = REPORTS_DIR / f"{today}.md"
    if report_path.exists():
        print(f"   Report:     {report_path}")
    print(f"{'═'*60}")


if __name__ == "__main__":
    main()
