"""
signal_pulse/src/utils.py
─────────────────────────
Shared utilities across all Signal/Pulse notebooks.
Handles credentials, paths, Japanese text helpers, HTTP with retry,
and the feasibility matrix schema used in NB01.
"""

import os
import re
import time
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("signal_pulse")


# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW     = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
OUTPUTS      = ROOT / "outputs"

for _d in [DATA_RAW, DATA_INTERIM, OUTPUTS]:
    _d.mkdir(parents=True, exist_ok=True)


# ── Credentials ───────────────────────────────────────────────────────────────

def load_env() -> None:
    """Load .env from project root. Call once at notebook startup."""
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        log.info(".env loaded from %s", env_path)
    else:
        log.warning(".env not found at %s — using environment variables only", env_path)


def get_rakuten_app_id() -> str:
    v = os.getenv("RAKUTEN_APP_ID", "")
    if not v:
        raise EnvironmentError("RAKUTEN_APP_ID not set. See .env.example.")
    return v

def get_rakuten_access_key() -> str:
    v = os.getenv("RAKUTEN_ACCESS_KEY", "")
    if not v:
        raise EnvironmentError("RAKUTEN_ACCESS_KEY not set. See .env.example.")
    return v

def get_youtube_api_key() -> str:
    v = os.getenv("YOUTUBE_API_KEY", "")
    if not v:
        raise EnvironmentError("YOUTUBE_API_KEY not set. See .env.example.")
    return v


def get_apify_token() -> Optional[str]:
    return os.getenv("APIFY_API_TOKEN", None)


# ── HTTP with retry ───────────────────────────────────────────────────────────

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
})


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def get_with_retry(url: str, params: Optional[dict] = None, **kwargs) -> requests.Response:
    """GET with exponential backoff retry. Redacts credentials from error messages."""
    try:
        resp = SESSION.get(url, params=params, timeout=20, **kwargs)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 10))
            log.warning("Rate limited — sleeping %ds", retry_after)
            time.sleep(retry_after)
            resp.raise_for_status()
        resp.raise_for_status()
        return resp
    except (requests.HTTPError, requests.ConnectionError) as e:
        sanitised = str(e)
        for secret in ["applicationId", "accessKey", "key", "token", "api_key"]:
            import re
            sanitised = re.sub(rf"({secret}=)[^&\s]+", r"\1***REDACTED***", sanitised)
        raise type(e)(sanitised) from None


def polite_sleep(seconds: float = 1.5) -> None:
    """Pause between requests. Be a good citizen."""
    time.sleep(seconds)


# ── Japanese text helpers ─────────────────────────────────────────────────────

def detect_script(text: str) -> dict:
    """
    Count characters by Japanese script type.
    Useful for validating that scraped text is actually Japanese.
    """
    counts = {"hiragana": 0, "katakana": 0, "kanji": 0, "ascii": 0, "other": 0}
    for ch in text:
        cp = ord(ch)
        if 0x3041 <= cp <= 0x309F:
            counts["hiragana"] += 1
        elif 0x30A0 <= cp <= 0x30FF:
            counts["katakana"] += 1
        elif 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            counts["kanji"] += 1
        elif cp < 128:
            counts["ascii"] += 1
        else:
            counts["other"] += 1
    total = max(len(text), 1)
    counts["jp_ratio"] = (counts["hiragana"] + counts["katakana"] + counts["kanji"]) / total
    return counts


def is_japanese(text: str, threshold: float = 0.2) -> bool:
    """Return True if text contains enough Japanese characters."""
    return detect_script(text)["jp_ratio"] >= threshold


# ── NB01 Feasibility Matrix ───────────────────────────────────────────────────

FEASIBILITY_SCHEMA = {
    "source": str,           # "Rakuten", "@cosme", "Amazon JP", "Google Trends", "YouTube JP"
    "time_series": str,      # "Yes (2020–2025)" / "No (live only)" / "Partial"
    "volume": str,           # "High / Medium / Low / Unknown"
    "richness": str,         # Fields available: text, ratings, prices, categories, etc.
    "access_reliability": str,  # "High / Medium / Low — notes on blocking, rate limits"
    "role": str,             # "Primary / Supporting / Benchmark / Dropped"
    "notes": str,            # Key findings or caveats from NB01
}


def save_feasibility_row(row: dict, output_path: Optional[Path] = None) -> None:
    """Append a source assessment row to the feasibility matrix JSON."""
    path = output_path or OUTPUTS / "nb01_feasibility_matrix.json"
    existing = []
    if path.exists():
        with open(path) as f:
            existing = json.load(f)
    # Replace if source already exists
    existing = [r for r in existing if r.get("source") != row.get("source")]
    existing.append({**row, "_assessed_at": datetime.utcnow().isoformat()})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    log.info("Feasibility row saved for: %s", row.get("source"))


def load_feasibility_matrix(output_path: Optional[Path] = None) -> list:
    path = output_path or OUTPUTS / "nb01_feasibility_matrix.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


# ── Snapshot-dated raw files ──────────────────────────────────────────────────
# Scrape notebooks stamp every output with the run date (…_YYYY-MM-DD.json), so
# a re-run on a new day produces a fresh snapshot while older snapshots remain
# on disk as history. The skip-if-exists guards then mean "resume today's run",
# not "never refresh". Readers use latest_snapshot() to load only the newest
# version of each file.

SNAPSHOT_DATE_RE = re.compile(r"_(\d{4}-\d{2}-\d{2})$")


def snapshot_date_of(path: Path) -> Optional[str]:
    """Trailing _YYYY-MM-DD snapshot date of a raw file, or None if undated."""
    m = SNAPSHOT_DATE_RE.search(Path(path).stem)
    return m.group(1) if m else None


def strip_snapshot_date(stem: str) -> str:
    """Remove a trailing _YYYY-MM-DD from a filename stem."""
    return SNAPSHOT_DATE_RE.sub("", stem)


def latest_snapshot(directory: Path, pattern: str = "*.json") -> list:
    """
    The newest version of each distinct raw file in `directory`.

    Files are keyed by their name with the snapshot date removed; for each key
    the newest dated file wins, falling back to the undated ("legacy",
    pre-snapshot-convention) file when no dated one exists. Keying per file —
    rather than per snapshot date — means a partially-completed re-scrape
    degrades gracefully: items it didn't reach still load from the previous
    snapshot instead of disappearing.

    Warns when the result mixes more than one snapshot date, which usually
    means the latest scrape is incomplete (crashed or still running).
    """
    directory = Path(directory)
    newest: dict = {}
    for f in sorted(directory.glob(pattern)):
        base = strip_snapshot_date(f.stem) + f.suffix
        prev = newest.get(base)
        if prev is None or (snapshot_date_of(f) or "") >= (snapshot_date_of(prev) or ""):
            newest[base] = f
    files = sorted(newest.values())  # Path ordering — matches sorted(dir.glob(...))
    dates = {snapshot_date_of(f) or "legacy" for f in files}
    if len(dates) > 1:
        log.warning(
            "latest_snapshot(%s/%s): mixing snapshots %s — the newest scrape "
            "may be incomplete (crashed or still running)",
            directory.name, pattern, sorted(dates),
        )
    return files


# ── Data serialisation helpers ────────────────────────────────────────────────

def save_raw(data, filename: str, subfolder: str = "") -> Path:
    """Save raw JSON data to data/raw/[subfolder]/filename."""
    dest = DATA_RAW / subfolder if subfolder else DATA_RAW
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Saved raw data → %s", path)
    return path


def load_raw(filename: str, subfolder: str = "") -> dict | list:
    src = DATA_RAW / subfolder if subfolder else DATA_RAW
    path = src / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)
