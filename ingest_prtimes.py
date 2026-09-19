"""PR TIMES launch layer — hand-run ingest. Weekly, on the NB02c cadence.

    python ingest_prtimes.py resolve          # issuer → company_id candidates, verified by feed title
    python ingest_prtimes.py resolve --apply  # write exact matches into config/sources.xlsx
    python ingest_prtimes.py fetch            # active feeds → data/prtimes.db + feed-health record

Nothing here is scheduled or called by the dashboard. Titles and excerpts stay
in data/prtimes.db (gitignored); the feed-health record goes to data/interim/
(gitignored) because it carries per-issuer counts only for review, not for the page.
Design of record: recon/2026-09-18_intent-brief_emergence-layer.md.
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src import prtimes as pt            # noqa: E402
from src.utils import polite_sleep, log   # noqa: E402

TODAY = date.today().isoformat()


def cmd_resolve(apply: bool) -> None:
    roster = pt.load_roster()
    rows = []
    for r in roster.itertuples():
        if r.company_id:
            continue
        words = pt._split(r.search_words) or [r.entity]
        res = pt.resolve(r.entity, words)
        res.update(role=r.role, active=r.active)
        rows.append(res)
        log.info("%-40s %-9s %s %s", r.entity, res["status"], res["company_id"], res["feed_corp"])
    out = pd.DataFrame(rows)
    path = pt.HEALTH_DIR / f"prtimes_resolution_{TODAY}.csv"
    out.to_csv(path, index=False)
    log.info("resolution report -> %s", path)
    if apply:
        _apply(out)


def _apply(res: pd.DataFrame) -> None:
    """Exact matches only. A bracketed placeholder row ([importer of X]) is
    never filled automatically: its search finds whoever publishes about the
    brand, which may be a retailer or a reseller, and that needs a person."""
    xl = pt.CONFIG / "sources.xlsx"
    sheets = pd.read_excel(xl, sheet_name=None, dtype=str)
    feeds = sheets["feeds"].fillna("")
    hits = res[(res["status"] == "exact") & ~res["entity"].str.startswith("[")]
    for h in hits.itertuples():
        m = feeds["entity"] == h.entity
        feeds.loc[m, "company_id"] = h.company_id
        feeds.loc[m, "url"] = pt.FEED_URL.format(company_id=h.company_id)
        feeds.loc[m, "resolution"] = f"exact: feed corp '{h.feed_corp}'"
        feeds.loc[m, "verified_date"] = TODAY
    for h in res[res["status"] != "exact"].itertuples():
        m = (feeds["entity"] == h.entity) & (feeds["company_id"] == "")
        feeds.loc[m, "resolution"] = (f"{h.status}: {h.feed_corp} ({h.company_id})"
                                      if h.company_id else "not_found")
    sheets["feeds"] = feeds
    with pd.ExcelWriter(xl) as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
    log.info("applied %d exact matches to %s", len(hits), xl)


def _tag_counts(items: list[dict], mt: dict) -> dict:
    """Per-issuer counts for the feed-health record, through the launch gate
    (src/prtimes.gate). The key keeps its v1 name so health files compare."""
    n = dict(beauty_scope=0, launch_term=0, provisional_launch=0, ingredient=0)
    months = []
    for it in items:
        g = pt.gate(it["title"], it["excerpt"], mt)
        n["beauty_scope"] += g["scope"]
        n["launch_term"] += g["launch_term"]
        n["ingredient"] += bool(g["ingredients"])
        if g["is_launch"]:
            n["provisional_launch"] += 1
            months.append(pt.jst_date(it["published"])[:7])
    n["provisional_launch_months"] = months
    return n


def cmd_fetch() -> None:
    roster = pt.load_roster(active_only=True)
    rv = pt.roster_version()
    mt = pt.load_matchers()
    conn = pt.connect()
    health = []
    for r in roster.itertuples():
        polite_sleep(pt.DELAY_S)
        rec = {"entity": r.entity, "company_id": r.company_id, "role": r.role,
               "origin": r.origin, "tier": r.tier, "pr_times": r.pr_times}
        try:
            status, corp, items = pt.fetch_feed(r.company_id)
        except Exception as e:                            # noqa: BLE001 — recorded, run continues
            rec.update(http_status=None, error=str(e)[:200], items=0)
            health.append(rec)
            log.warning("%s (%s): %s", r.entity, r.company_id, e)
            continue
        dates = sorted(pt.jst_date(i["published"]) for i in items if i["published"])
        new = pt.store(conn, items, TODAY, rv)
        rec.update(http_status=status, feed_corp=corp, items=len(items), new_items=new,
                   feed_reach=dates[0] if dates else "", newest=dates[-1] if dates else "",
                   history_complete=len(items) < pt.FEED_CAP, error="",
                   **_tag_counts(items, mt))
        conn.execute("""INSERT OR REPLACE INTO fetch_log VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (TODAY, r.company_id, r.entity, status, corp, len(items), new,
                      rec["feed_reach"], rec["newest"], int(rec["history_complete"]), "", rv))
        health.append(rec)
        log.info("%-38s items=%3d new=%3d reach=%s complete=%s launch≈%d",
                 r.entity, len(items), new, rec["feed_reach"], rec["history_complete"],
                 rec["provisional_launch"])
    conn.commit()
    conn.close()
    # Intended issuers with no PR TIMES feed are part of the record: a prestige
    # house or a Qoo10 brand that does not publish there is a coverage finding.
    full = pt.load_roster()
    for r in full[(full["active"].str.lower() == "yes") & (full["company_id"] == "")].itertuples():
        health.append({"entity": r.entity, "company_id": "", "role": r.role, "origin": r.origin,
                       "tier": r.tier, "pr_times": r.pr_times, "http_status": None, "items": 0,
                       "error": "no_feed", "resolution": r.resolution})
    path = pt.HEALTH_DIR / f"prtimes_feed_health_{TODAY}.json"
    path.write_text(json.dumps({"run_date": TODAY, "roster_version": rv,
                                "generated_at": datetime.now().isoformat(timespec="seconds"),
                                "rows": health}, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("feed health -> %s", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["resolve", "fetch"])
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cmd_resolve(a.apply) if a.cmd == "resolve" else cmd_fetch()
