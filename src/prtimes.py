"""
signal_pulse/src/prtimes.py
───────────────────────────
PR TIMES launch layer: roster, company-feed fetch, release store, text tagging.

The fetch → store → tag logic follows arkema-recon's intel.py direct lane,
adapted to one source. Design of record:
recon/2026-09-18_intent-brief_emergence-layer.md.

The source (verified 2026-09-18):
  - company feed  https://prtimes.jp/companyrdf.php?company_id={id} — RSS 1.0,
    the company's latest 200 releases; title, link, a ~120-character
    description excerpt, dc:corp, business_form, dc:date. No body.
  - release URL   /main/html/rd/p/{release_no}.{company_id}.html — the key.
  - keyword search /main/action.php?run=html&page=searchkey — static HTML,
    used only to find candidate company ids for the roster.

Title and excerpt are stored in data/prtimes.db, which is gitignored (data/*.db).
Nothing text-bearing leaves this module for a committed file.
"""

from __future__ import annotations

import collections
import re
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

from src.utils import get_with_retry, polite_sleep, log, ROOT

CONFIG = ROOT / "config"
DB_PATH = ROOT / "data" / "prtimes.db"
HEALTH_DIR = ROOT / "data" / "interim"

FEED_URL = "https://prtimes.jp/companyrdf.php?company_id={company_id}"
SEARCH_URL = "https://prtimes.jp/main/action.php"
RELEASE_RE = re.compile(r"/main/html/rd/p/(\d+)\.(\d+)\.html")
FEED_CAP = 200                 # a feed returning this many items is truncated
DELAY_S = 2.0                  # config/project.yml scraping.*_delay_seconds
JST = timezone(timedelta(hours=9))

# First month of the core panel's history (brief §1, window policy). The
# earliest month at which the core — feeds with complete history, plus
# truncated feeds reaching back to it — carries at least CORE_SHARE_MIN of
# gate launches in the latest 12 complete months. Derived 2026-09-19 with gate
# v2 on the 2026-09-18 store: core share 51.9% at 2021-09 (49.9% at 2021-08),
# 41 of 55 feeds. Re-deriving it is a dated revision, like a METI edition change.
WINDOW_START = "2021-09"
CORE_SHARE_MIN = 0.5

NS = {"rss": "http://purl.org/rss/1.0/",
      "dc": "http://purl.org/dc/elements/1.1/",
      "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}


# ── Config ────────────────────────────────────────────────────────────────────

def load_roster(active_only: bool = False) -> pd.DataFrame:
    """config/sources.xlsx!feeds — one row per issuer. company_id stays a
    string: PR TIMES ids carry no meaning as numbers, and Excel would drop
    nothing today but would the day an id gains a leading zero."""
    df = pd.read_excel(CONFIG / "sources.xlsx", sheet_name="feeds", dtype=str).fillna("")
    df = df.apply(lambda c: c.str.strip())
    if active_only:
        df = df[(df["active"].str.lower() == "yes") & (df["company_id"] != "")]
    return df.reset_index(drop=True)


def roster_version() -> str:
    meta = pd.read_excel(CONFIG / "sources.xlsx", sheet_name="meta", dtype=str).fillna("")
    return dict(zip(meta["key"], meta["value"])).get("roster_version", "")


def _split(cell: str) -> list[str]:
    return [t.strip() for t in str(cell).split("|") if t.strip()]


# ── Matching ──────────────────────────────────────────────────────────────────

def norm(text: str) -> str:
    """NFKC: full-width ASCII and half-width kana to one form, so ＣＣ and CC,
    ﾒﾗﾉ and メラノ match the same variant."""
    return unicodedata.normalize("NFKC", str(text or ""))


_KATA = r"゠-ヿ"          # katakana block, including ー and ・


class Matcher:
    """Variant → canonical tagger over one vocabulary.

    Longest variant first, and a matched span is consumed, so リップクリーム is
    tagged once as itself and never also as クリーム.

    mode="substring": kana/kanji variants match anywhere. Used for ingredients
    and categories, where compounds such as レチノールクリーム must still tag.
    mode="boundary": katakana variants may not touch another katakana
    character, so エスト does not match inside リクエスト. Used for brands.
    ASCII variants always need a non-alphanumeric boundary; those of three
    characters or fewer also match case-sensitively (DHC, CNP, est, DEW)."""

    def __init__(self, pairs: list[tuple[str, str]], mode: str = "substring"):
        pats = []
        for variant, canonical in sorted(pairs, key=lambda p: -len(norm(p[0]))):
            v = norm(variant)
            esc = re.escape(v)
            if v.isascii():
                flags = "" if len(v) <= 3 else "(?i)"
                pat = rf"{flags}(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])"
            elif mode == "boundary" and re.fullmatch(rf"[{_KATA}]+", v):
                pat = rf"(?<![{_KATA}]){esc}(?![{_KATA}])"
            else:
                pat = esc
            pats.append((re.compile(pat), canonical))
        self.pats = pats

    def tags(self, text: str) -> list[str]:
        t = norm(text)
        taken = [False] * len(t)
        found = []
        for pat, canonical in self.pats:
            for m in pat.finditer(t):
                if any(taken[m.start():m.end()]):
                    continue
                for i in range(m.start(), m.end()):
                    taken[i] = True
                if canonical not in found:
                    found.append(canonical)
        return found


def load_matchers() -> dict[str, Matcher]:
    ing = pd.read_excel(CONFIG / "ingredients.xlsx", sheet_name="ingredients", dtype=str).fillna("")
    brands = pd.read_excel(CONFIG / "brand_lexicon.xlsx", sheet_name="brands", dtype=str).fillna("")
    lt = {k: v.fillna("") for k, v in
          pd.read_excel(CONFIG / "launch_terms.xlsx", sheet_name=None, dtype=str).items()}
    cat, launch = lt["categories"], lt["launch"]

    def terms(sheet: str) -> Matcher:
        return Matcher([(t, t) for t in lt[sheet]["term"] if t])

    return {
        "ingredient": Matcher([(v, r.canonical) for r in ing.itertuples()
                               for v in _split(r.text_variants)]),
        "brand": Matcher([(v, r.brand_canonical) for r in brands.itertuples()
                          for v in _split(r.variants)], mode="boundary"),
        "brand_scope": Matcher([(v, r.brand_canonical) for r in brands.itertuples()
                                if r.mixed != "yes" for v in _split(r.variants)], mode="boundary"),
        "category": Matcher([(v, r.category) for r in cat.itertuples() for v in _split(r.terms)]),
        "launch": Matcher([(r.term, r.term) for r in launch.itertuples() if r.term]),
        "launch_strong": Matcher([(r.term, r.term) for r in launch.itertuples()
                                  if r.term and r.strength == "strong"]),
        "noise": terms("noise"),
        "scope_generic": terms("scope_generic"),
        "exclude": terms("exclude"),
        "channel_entry": terms("channel_entry"),
        "edition": terms("edition"),
    }


def gate(title: str, excerpt: str, mt: dict[str, Matcher]) -> dict:
    """Launch gate v2 (config/launch_terms.xlsx!meta 'rule').

    The title decides the vetoes: an excerpt mentioning a campaign or an event
    does not cancel a launch the title announces. A noise term in the title is
    overridden by any launch term there (the product-present rule: a named
    product going on sale counts whatever wraps it); a channel-entry term only
    by a strong one, since 販売開始 alone is what an existing product reaching
    a new shelf also says."""
    text = f"{title} {excerpt}"
    cat, ing = mt["category"].tags(text), mt["ingredient"].tags(text)
    scope = bool(cat or ing or mt["scope_generic"].tags(text) or mt["brand_scope"].tags(text))
    launch_any = bool(mt["launch"].tags(text))
    launch_title = bool(mt["launch"].tags(title))
    strong_title = bool(mt["launch_strong"].tags(title))
    excluded = bool(mt["exclude"].tags(text))
    noise_veto = bool(mt["noise"].tags(title)) and not launch_title
    channel_entry = bool(mt["channel_entry"].tags(title)) and not strong_title
    is_launch = scope and launch_any and not (excluded or noise_veto or channel_entry)
    return {
        "is_launch": int(is_launch),
        "edition_flag": int(is_launch and bool(mt["edition"].tags(title))),
        "renewal_flag": int(is_launch and "リニューアル" in norm(text)),
        "categories": cat, "ingredients": ing,
        "scope": int(scope), "launch_term": int(launch_any), "excluded": int(excluded),
        "noise_veto": int(noise_veto), "channel_entry": int(channel_entry),
    }


def clean_excerpt(description: str) -> str:
    """The feed prefixes every excerpt with '[issuer name] '. It names the
    issuer, not the product, so it is dropped before tagging."""
    return re.sub(r"^\s*\[[^\]]*\]\s*", "", str(description or ""))


# ── Feed ──────────────────────────────────────────────────────────────────────

def parse_feed(xml_bytes: bytes) -> tuple[str, list[dict]]:
    """RSS 1.0 → (channel corp name, items). The channel title reads
    '{corp}【プレスリリース】 by PR TIMES'; it is how a candidate id is verified."""
    root = ET.fromstring(xml_bytes)
    ch_title = root.findtext("rss:channel/rss:title", default="", namespaces=NS)
    corp = re.sub(r"【プレスリリース】.*$", "", ch_title).strip()
    items = []
    for it in root.findall("rss:item", NS):
        link = (it.findtext("rss:link", default="", namespaces=NS) or "").strip()
        m = RELEASE_RE.search(link)
        if not m:
            continue
        items.append({
            "release_id": f"{m.group(1)}.{m.group(2)}",
            "release_no": int(m.group(1)),
            "company_id": str(int(m.group(2))),
            "url": link,
            "title": (it.findtext("rss:title", default="", namespaces=NS) or "").strip(),
            "excerpt": clean_excerpt(it.findtext("rss:description", default="", namespaces=NS)),
            "issuer": (it.findtext("dc:corp", default="", namespaces=NS) or "").strip(),
            "business_form": (it.findtext("rss:business_form", default="", namespaces=NS) or "").strip(),
            "published": (it.findtext("dc:date", default="", namespaces=NS) or "").strip(),
        })
    return corp, items


def fetch_feed(company_id: str) -> tuple[int, str, list[dict]]:
    resp = get_with_retry(FEED_URL.format(company_id=company_id))
    corp, items = parse_feed(resp.content)
    return resp.status_code, corp, items


# ── Resolution: issuer name → company_id ─────────────────────────────────────

_SUFFIX = re.compile(r"(株式会社|\(株\)|合同会社|有限会社|グループ|ホールディングス)")


def core_name(name: str) -> str:
    """Comparable form of a company name: NFKC, legal-form words, spaces and
    separators removed, lower-cased."""
    n = _SUFFIX.sub("", norm(name))
    return re.sub(r"[\s・·\.,&＆']", "", n).lower()


def search_company_ids(word: str, top: int = 3) -> list[tuple[str, int]]:
    """Company ids behind the releases a keyword search returns, most frequent
    first. A candidate list only — every id is verified by resolve()."""
    resp = get_with_retry(SEARCH_URL, params={"run": "html", "page": "searchkey",
                                              "search_word": word})
    ids = collections.Counter(str(int(c)) for _, c in RELEASE_RE.findall(resp.text))
    return ids.most_common(top)


def resolve(entity: str, search_words: list[str]) -> dict:
    """Search each word, then fetch each candidate's feed and compare its own
    corp name with the issuer. 'exact' = same core name; 'partial' = one core
    name contains the other (review before activating); otherwise the
    candidates are reported and nothing is accepted."""
    want = core_name(entity)
    seen, tried = set(), []
    for word in search_words:
        polite_sleep(DELAY_S)
        try:
            cands = search_company_ids(word)
        except Exception as e:                       # noqa: BLE001 — reported, not raised
            tried.append(f"search '{word}' failed: {e}")
            continue
        for cid, n in cands:
            if cid in seen:
                continue
            seen.add(cid)
            polite_sleep(DELAY_S)
            try:
                _, corp, items = fetch_feed(cid)
            except Exception as e:                   # noqa: BLE001
                tried.append(f"{cid}: feed failed: {e}")
                continue
            got = core_name(corp)
            tried.append(f"{cid}={corp} ({n} hits for '{word}')")
            if got and got == want:
                return {"entity": entity, "status": "exact", "company_id": cid,
                        "feed_corp": corp, "items": len(items), "tried": " | ".join(tried)}
            if got and want and (got in want or want in got):
                return {"entity": entity, "status": "partial", "company_id": cid,
                        "feed_corp": corp, "items": len(items), "tried": " | ".join(tried)}
    return {"entity": entity, "status": "not_found", "company_id": "", "feed_corp": "",
            "items": 0, "tried": " | ".join(tried)}


# ── Store ─────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS releases (
    release_id     TEXT PRIMARY KEY,          -- '{release_no}.{company_id}' from the URL
    release_no     INTEGER NOT NULL,
    company_id     TEXT NOT NULL,
    issuer         TEXT,                      -- dc:corp
    business_form  TEXT,
    title          TEXT,                      -- third-party text: never exported
    excerpt        TEXT,                      -- third-party text: never exported
    published      TEXT,                      -- dc:date, ISO with +09:00
    published_date TEXT,                      -- JST calendar date
    url            TEXT NOT NULL,
    first_run      TEXT NOT NULL,             -- run date that first stored it
    roster_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fetch_log (
    run_date         TEXT NOT NULL,
    company_id       TEXT NOT NULL,
    entity           TEXT,
    http_status      INTEGER,
    feed_corp        TEXT,
    items            INTEGER,
    new_items        INTEGER,
    feed_reach       TEXT,                    -- earliest dc:date the feed returned
    newest           TEXT,
    history_complete INTEGER,                 -- items < FEED_CAP
    error            TEXT,
    roster_version   TEXT,
    PRIMARY KEY (run_date, company_id)
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def jst_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).astimezone(JST).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def store(conn: sqlite3.Connection, items: list[dict], run_date: str, rv: str) -> int:
    """INSERT OR IGNORE on release_id — re-fetching a feed that still carries
    last week's items adds nothing, the NB02c products_weekly rule."""
    before = conn.total_changes
    conn.executemany(
        """INSERT OR IGNORE INTO releases
           (release_id, release_no, company_id, issuer, business_form, title, excerpt,
            published, published_date, url, first_run, roster_version)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(i["release_id"], i["release_no"], i["company_id"], i["issuer"], i["business_form"],
          i["title"], i["excerpt"], i["published"], jst_date(i["published"]), i["url"],
          run_date, rv) for i in items])
    return conn.total_changes - before


# ── Window ────────────────────────────────────────────────────────────────────

def core_window(health: pd.DataFrame, releases: pd.DataFrame, last_month: str,
                share_min: float = CORE_SHARE_MIN) -> tuple[str, float]:
    """Locate WINDOW_START from a feed-health record and gated releases.

    health: one row per feed, with company_id, feed_reach and history_complete.
    releases: company_id, published_date and is_launch (the gate's output).
    Returns (month, core share of launches in the 12 months to last_month)."""
    l12 = pd.period_range(end=last_month, periods=12, freq="M").astype(str)
    rel = releases[(releases["is_launch"] == 1)
                   & releases["published_date"].str[:7].isin(l12)]
    per_feed = health["company_id"].map(rel.groupby("company_id").size()).fillna(0)
    total = per_feed.sum()
    complete = health["history_complete"].astype(bool)
    for month in pd.period_range("2010-01", last_month, freq="M").astype(str):
        share = per_feed[complete | (health["feed_reach"].str[:7] <= month)].sum() / total
        if share >= share_min:
            return month, float(share)
    return last_month, 1.0
