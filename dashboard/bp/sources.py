"""Source registry: each source the site uses, dated by its own data.

Every exhibit's source line and the Sources page read from here. What a source
is — its name, whether it is a series or a snapshot, which pages use it — is
declared below. Every date, cadence and collection count is read from the data
when build_registry() runs, so a refresh moves them with no edit:

  meti            estat_meti_cosmetics.csv: newest month, and the edition it came from
  trade           estat_trade_hs3304.csv: newest year
  trends          the monthly Trends assets: newest month; source_dates.csv: pull date
  trends_related  trends_related_seeds.csv (ingest_trends_related.py export): the
                  window and each pull's time. An edition without that file (2026-09
                  holds nb07_blockc.csv, which records neither) has no date
  prtimes         prtimes_launches.csv: newest release; prtimes_feeds.csv: last fetch
  rakuten, cosme, youtube, amazon
                  source_dates.csv, exported from the database by
                  build_source_dates.py, because the app image does not ship it

A series is refreshed when its publisher releases new data, and its exhibits
move. A snapshot was collected once (or a few times, for the same frame), and
its date dates every finding that uses it.

Like data.py, this imports no UI framework and computes nothing at import.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .data import LAUNCH_WINDOW_START

# Every page on the site, report then monitor. used_on names only these.
REPORT_PAGES = ("brief", "market", "demand", "supply", "consumer", "timing", "method")
MONITOR_PAGES = ("funnel", "categories", "sources")
PAGES = REPORT_PAGES + MONITOR_PAGES

# The report's edition and its data cut-off, both "YYYY-MM". EDITION is the
# month the report carries on every page. CUTOFF is the last month complete in
# every source the report reads when the edition was issued: report pages
# compute on data dated up to its end, so a month still arriving (September
# launch releases, before the October fetch) cannot move a published edition.
# Monitor pages compute on the latest data and carry each source's own date.
# Issuing a new edition is these two lines; the cadence is Stan's decision.
EDITION = "2026-09"
CUTOFF = "2026-08"


def edition_assets(ASSETS: Path) -> Path:
    """The issued edition's frozen copy of the assets (issue_edition.py).
    Report pages read only this folder; monitor pages read ASSETS itself."""
    return ASSETS / "editions" / EDITION

# key: (English name, Japanese name, kind, pages that use it)
DECLARED = {
    "meti":           ("METI 生産動態統計", "経済産業省 生産動態統計", "series",
                       ("brief", "market", "timing", "method", "funnel", "categories")),
    "trade":          ("財務省 貿易統計 HS 3304", "財務省 貿易統計 HS 3304", "series",
                       ("market",)),
    "trends":         ("Google Trends JP", "Googleトレンド（日本）", "series",
                       ("brief", "demand", "timing", "method", "funnel", "categories")),
    # Used by no page yet. The 2026-09 edition's pull records no date and no
    # window (METHODOLOGY Revision 17); the October 2026 re-pull records both and
    # waits for the next edition and the Demand exhibit.
    "trends_related": ("Google Trends related searches", "Googleトレンド 関連キーワード",
                       "snapshot", ()),
    "prtimes":        ("PR TIMES", "PR TIMES", "series",
                       ("brief", "supply", "timing", "method", "funnel", "categories")),
    # Collected, and used by no page in this edition: its snapshot postdates the
    # cut-off and its genres mix levels. It returns on the monitor (Phase 4).
    "rakuten":        ("Rakuten Ichiba", "楽天市場", "series", ()),
    "cosme":          ("@cosme", "@cosme", "snapshot", ("consumer", "method", "funnel")),
    "youtube":        ("YouTube", "YouTube", "snapshot", ("consumer",)),
    # Collected, and used by no finding or chart: its products carry no category.
    "amazon":         ("Amazon JP", "Amazon.co.jp", "snapshot", ()),
}

# The monthly Trends series the exhibits plot. The annual file
# (nb04b_attention_annual.csv) holds full years only, so it cannot say how far
# the data runs.
TRENDS_ASSETS = ("nb07_trends_crossover.csv", "nb07_ingredient_surge.csv",
                 "nb07_makeup_rebound.csv")

ANALYSIS = {"en": "Beauty Pulse analysis", "ja": "Beauty Pulse分析"}


@dataclass(frozen=True)
class Source:
    key: str
    name_en: str
    name_ja: str
    kind: str                      # "series" | "snapshot"
    used_on: tuple
    data_to: pd.Timestamp | None   # newest data; None when nothing records it
    precision: str | None          # "day" | "month" | "year": how data_to is dated
    cadence: str | None            # "weekly" | "monthly" | "annual" | "per_release"; None for a snapshot
    first: pd.Timestamp | None = None      # where the stored series starts
    collected: pd.Timestamp | None = None  # last pull, where it is not data_to
    collections: int | None = None         # pulls stored, where more than one
    edition: str | None = None             # METI: the release the newest month came from

    def name(self, lang="en"):
        return self.name_ja if lang == "ja" else self.name_en


def _cadence(dates):
    """Name the spacing of a source's observation or pull dates."""
    d = pd.Series(sorted(set(pd.to_datetime(dates)))).diff().dt.days.dropna()
    return _name_gap(d.median()) if len(d) else None


def _name_gap(gap):
    if gap <= 10:
        return "weekly"
    if 25 <= gap <= 35:
        return "monthly"
    if 330 <= gap <= 400:
        return "annual"
    raise ValueError(f"no cadence name for a median gap of {gap:.0f} days")


def _exported(ASSETS: Path):
    """source_dates.csv as {(source, date_kind): value}."""
    df = pd.read_csv(ASSETS / "source_dates.csv", dtype=str)
    return {(r.source, r.date_kind): r.value for r in df.itertuples()}


def build_registry(ASSETS: Path, cutoff=None) -> dict:
    """Every source, keyed as in DECLARED, dated from the assets in ASSETS.

    With a cutoff ("YYYY-MM"), the series sources the report reads (METI, trade,
    Trends, PR TIMES) are dated on their rows up to that month, so a report
    page's source line states the data it computed on. The others are dated
    only by the weekly export, which keeps no history, and are left as they are:
    no report exhibit reads them yet."""
    ex = _exported(ASSETS)
    c = int(cutoff.replace("-", "")) if cutoff else None
    upto = (lambda ym: ym <= c) if c else (lambda ym: ym == ym)
    ts = lambda v: pd.Timestamp(v) if v is not None else None
    found = {}

    meti = pd.read_csv(ASSETS / "estat_meti_cosmetics.csv",
                       usecols=["year", "month", "edition"])
    meti = meti[(meti["month"] >= 1) & upto(meti["year"] * 100 + meti["month"])]
    months = pd.to_datetime(dict(year=meti["year"], month=meti["month"], day=1))
    found["meti"] = dict(data_to=months.max(), precision="month",
                         cadence=_cadence(months), first=months.min(),
                         edition=str(meti.loc[months.idxmax(), "edition"]))

    years = pd.read_csv(ASSETS / "estat_trade_hs3304.csv", usecols=["year"])["year"]
    years = years[upto(years * 100 + 12)]
    stamps = pd.to_datetime(years.astype(str) + "-01-01")
    found["trade"] = dict(data_to=stamps.max(), precision="year",
                          cadence=_cadence(stamps), first=stamps.min())

    # The newest month every Trends exhibit reaches: if one asset were rebuilt
    # and another not, the older one bounds what the site shows.
    tr = [pd.read_csv(ASSETS / f, usecols=["week_start"], parse_dates=["week_start"])
          ["week_start"] for f in TRENDS_ASSETS]
    tr = [t[upto(t.dt.year * 100 + t.dt.month)] for t in tr]
    found["trends"] = dict(data_to=min(s.max() for s in tr), precision="month",
                           cadence=_cadence(tr[0]), first=max(s.min() for s in tr),
                           collected=ts(ex.get(("trends", "collected"))))

    # The window's last year is how far the data runs; the pulls are when it was
    # collected. Absent from an edition that predates the re-pull.
    rel = ASSETS / "trends_related_seeds.csv"
    if rel.exists():
        rs = pd.read_csv(rel, dtype=str)
        start, end = rs["window"].iloc[0].split()
        pulled = pd.to_datetime(pd.concat([rs["pulled_at_1"], rs["pulled_at_2"]]), utc=True)
        found["trends_related"] = dict(
            data_to=pd.Timestamp(end), precision="year", cadence=None, first=pd.Timestamp(start),
            collected=pulled.max().tz_convert("Asia/Tokyo").tz_localize(None).normalize(),
            collections=int(rs[["pull_1", "pull_2"]].nunique().sum()))
    else:
        found["trends_related"] = dict(data_to=None, precision=None, cadence=None)

    launches = pd.read_csv(ASSETS / "prtimes_launches.csv", usecols=["published"])
    launches = launches[upto(launches["published"].str[:7].str.replace("-", "").astype(int))]
    feeds = pd.read_csv(ASSETS / "prtimes_feeds.csv", usecols=["fetched"])
    found["prtimes"] = dict(data_to=pd.Timestamp(launches["published"].max()),
                            precision="day", cadence="per_release",
                            first=pd.Timestamp(LAUNCH_WINDOW_START + "-01"),
                            collected=pd.Timestamp(feeds["fetched"].max()))

    first, last = ts(ex[("rakuten", "first")]), ts(ex[("rakuten", "data_to")])
    n = int(ex[("rakuten", "collections")])
    # Only the span and count are exported; their mean spacing names the cadence.
    found["rakuten"] = dict(data_to=last, precision="day", first=first, collections=n,
                            cadence=_name_gap((last - first).days / (n - 1)) if n > 1 else None)

    for key in ("cosme", "youtube", "amazon"):
        n = ex.get((key, "collections"))
        found[key] = dict(data_to=ts(ex[(key, "data_to")]), precision="day",
                          cadence=None, collections=int(n) if n else None)

    return {key: Source(key, en, ja, kind, used_on, **found[key])
            for key, (en, ja, kind, used_on) in DECLARED.items()}


_MONTHS_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def date_label(ts: pd.Timestamp, precision: str, lang="en") -> str:
    """'18 Sep 2026' / 'Jul 2026' / '2025', or the Japanese form."""
    if lang == "ja":
        return {"day": f"{ts.year}年{ts.month}月{ts.day}日",
                "month": f"{ts.year}年{ts.month}月", "year": f"{ts.year}年"}[precision]
    return {"day": f"{ts.day} {_MONTHS_EN[ts.month - 1]} {ts.year}",
            "month": f"{_MONTHS_EN[ts.month - 1]} {ts.year}",
            "year": str(ts.year)}[precision]


def data_to_label(src: Source, lang="en") -> str:
    """How current one source is, as an exhibit's source line states it."""
    if src.data_to is None:
        return "取得日の記録なし" if lang == "ja" else "pull date not recorded"
    label = date_label(src.data_to, src.precision, lang)
    return f"{label}まで" if lang == "ja" else f"data to {label}"


def source_line(keys, registry: dict, lang="en") -> str:
    """'Source: METI 生産動態統計 (data to Jul 2026); Beauty Pulse analysis'.

    Sources appear in the order given; the analysis credit is always last."""
    parts = []
    for k in keys:
        src = registry[k]
        if lang == "ja":
            parts.append(f"{src.name('ja')}（{data_to_label(src, 'ja')}）")
        else:
            parts.append(f"{src.name('en')} ({data_to_label(src, 'en')})")
    if lang == "ja":
        return "出典：" + "、".join(parts + [ANALYSIS["ja"]])
    return "Source: " + "; ".join(parts + [ANALYSIS["en"]])
