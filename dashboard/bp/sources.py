"""Source registry: each source the site uses, dated by its own data.

Every exhibit's source line and the Sources page read from here. What a source
is — its name, whether it is a series or a snapshot, which pages use it — is
declared below. Every date, cadence and collection count is read from the data
when build_registry() runs, so a refresh moves them with no edit:

  meti            estat_meti_cosmetics.csv: newest month, and the edition it came from
  trade           estat_trade_hs3304.csv: newest year
  trends          the monthly Trends assets: newest month; source_dates.csv: pull date
  trends_related  nb07_blockc.csv carries no date and no pull was recorded
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

# key: (English name, Japanese name, kind, pages that use it)
DECLARED = {
    "meti":           ("METI 生産動態統計", "経済産業省 生産動態統計", "series",
                       ("market", "timing", "funnel", "categories")),
    "trade":          ("財務省 貿易統計 HS 3304", "財務省 貿易統計 HS 3304", "series",
                       ("market",)),
    "trends":         ("Google Trends JP", "Googleトレンド（日本）", "series",
                       ("demand", "timing", "funnel", "categories")),
    "trends_related": ("Google Trends related searches", "Googleトレンド 関連キーワード",
                       "snapshot", ("demand",)),
    "prtimes":        ("PR TIMES", "PR TIMES", "series",
                       ("supply", "timing", "funnel", "categories")),
    "rakuten":        ("Rakuten Ichiba", "楽天市場", "series", ("supply",)),
    "cosme":          ("@cosme", "@cosme", "snapshot", ("consumer", "funnel")),
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


def build_registry(ASSETS: Path) -> dict:
    """Every source, keyed as in DECLARED, dated from the assets in ASSETS."""
    ex = _exported(ASSETS)
    ts = lambda v: pd.Timestamp(v) if v is not None else None
    found = {}

    meti = pd.read_csv(ASSETS / "estat_meti_cosmetics.csv",
                       usecols=["year", "month", "edition"])
    meti = meti[meti["month"] >= 1]
    months = pd.to_datetime(dict(year=meti["year"], month=meti["month"], day=1))
    found["meti"] = dict(data_to=months.max(), precision="month",
                         cadence=_cadence(months), first=months.min(),
                         edition=str(meti.loc[months.idxmax(), "edition"]))

    years = pd.read_csv(ASSETS / "estat_trade_hs3304.csv", usecols=["year"])["year"]
    stamps = pd.to_datetime(years.astype(str) + "-01-01")
    found["trade"] = dict(data_to=stamps.max(), precision="year",
                          cadence=_cadence(stamps), first=stamps.min())

    # The newest month every Trends exhibit reaches: if one asset were rebuilt
    # and another not, the older one bounds what the site shows.
    tr = [pd.read_csv(ASSETS / f, usecols=["week_start"], parse_dates=["week_start"])
          ["week_start"] for f in TRENDS_ASSETS]
    found["trends"] = dict(data_to=min(s.max() for s in tr), precision="month",
                           cadence=_cadence(tr[0]), first=max(s.min() for s in tr),
                           collected=ts(ex.get(("trends", "collected"))))

    found["trends_related"] = dict(data_to=None, precision=None, cadence=None)

    launches = pd.read_csv(ASSETS / "prtimes_launches.csv", usecols=["published"])
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
