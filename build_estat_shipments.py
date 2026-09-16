"""Pull METI 生産動態統計 cosmetics shipments from e-Stat into a tidy CSV.

METHODOLOGY caveat 12 names this as the validation layer: Google Trends measures
attention, this measures shipped volume and value. The two answering the same way
is evidence; the two diverging is also evidence.

    python build_estat_shipments.py           # writes dashboard/assets/estat_meti_cosmetics.csv

Two channels. Complete years come from the per-year 時系列表 in the e-Stat
database. Months after the last of those come from the newest monthly 確報
workbook, which e-Stat lists in its data catalog rather than the database. 確報
figures are revised when the year's 時系列表 opens: checked on 2025, the
monthly total moved by under 0.2% and single lines by up to 4% (口紅). The
`edition` column records which channel each row came from.

Table IDs are NOT stable across survey revisions, so they are listed with the
date they were confirmed and the script re-resolves each one's metadata rather
than assuming a layout — the 2019/2020 tables and the 2021+ 化粧品月報 tables
carry their dimensions differently.
"""

import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.utils import load_env, get_estat_app_id          # noqa: E402

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"
STATS_CODE = "00550200"                     # 経済産業省生産動態統計調査
FORM = "6175"                               # 調査票番号: 化粧品
FILE_DL = "https://www.e-stat.go.jp/stat-search/file-download"
RAW_DIR = Path(__file__).resolve().parent / "data" / "raw" / "estat"

# statsDataId per survey year, confirmed against getStatsList (2019–2024 on
# 2026-09-06, 2025 on 2026-09-16). Each year's 時系列表 opens around the end of
# June the following year; months after the last table come from the monthly
# 確報 workbooks (see file_channel below).
TABLES = {
    2019: "0003416134",   # 2019年 製品統計表(時系列) (10)化粧品
    2020: "0003437034",   # 2020年 同上
    2021: "0004001069",   # 2021年 時系列表(6175_化粧品月報)
    2022: "0004014489",
    2023: "0004019835",
    2024: "0004032992",
    2025: "0004061875",   # opened 2026-06-30
}

# The two table generations name things differently; both normalise to these.
# Unit is fixed by measure in both table generations; the item name always says
# "(kg)" regardless, so deriving it from the item is wrong for value and count.
UNIT_BY_MEASURE = {
    "生産": "kg", "受入": "kg", "販売数量": "kg", "出荷その他": "kg",
    "月末在庫": "kg", "販売個数": "十個", "販売金額": "千円",
}

MEASURE_MAP = {
    "生産": "生産", "受入": "受入",
    "出荷販売個数": "販売個数", "販売個数": "販売個数",
    "出荷販売数量": "販売数量", "販売数量": "販売数量",
    "出荷販売金額": "販売金額", "販売金額": "販売金額",
    "出荷その他": "出荷その他", "その他": "出荷その他",
    "月末在庫": "月末在庫", "在庫": "月末在庫",
}


def _clean(s: str) -> str:
    """Drop unit and item-number parentheticals, normalise separators."""
    s = re.sub(r"[（(]\s*(kg|千円|十個|10個|個)\s*[)）]", "", s)
    s = re.sub(r"[（(][0-9０-９~～\-\s]+[)）]", "", s)
    return s.replace("･", "・").replace("（", "(").replace("）", ")").strip()


def _canon_item(name: str) -> str | None:
    """'化粧品 皮膚用化粧品 美容液(18) (kg)' and '美容液' -> '美容液'."""
    t = [x for x in _clean(name).split() if x]
    if not t:
        return None
    if t[0] == "化粧品" and len(t) > 1:
        t = t[1:]
    leaf = t[-1]
    if leaf in ("計", "合計") and len(t) > 1:          # '皮膚用化粧品 計' -> subtotal
        return re.sub(r"\s+", "", t[-2]) + "計"
    if leaf == "合計":
        return "化粧品合計"
    return re.sub(r"\s+", "", leaf)


def _canon_measure(name: str) -> str | None:
    return MEASURE_MAP.get(re.sub(r"\s+", "", _clean(name)))


def _period_from(token: str):
    """YYYY + kind(00=CY,10=FY) + MM + MM. Returns (year, month) or None."""
    m = re.search(r"(\d{4})(\d{2})(\d{2})(\d{2})", token or "")
    if not m:
        return None
    yr, kind, m1, m2 = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
    if kind != "00":                       # fiscal-year rows: skip
        return None
    if m1 == 0 and m2 == 0:
        return (yr, 0)                     # calendar-year total
    if m1 == m2 and 1 <= m1 <= 12:
        return (yr, m1)
    return None                            # quarters and other ranges


def _class_map(app_id: str, sid: str) -> dict:
    j = requests.get(f"{BASE}/getMetaInfo",
                     params={"appId": app_id, "statsDataId": sid, "lang": "J"},
                     timeout=120).json()["GET_META_INFO"]
    assert j["RESULT"]["STATUS"] == 0, j["RESULT"]
    out = {}
    for c in j["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]:
        cl = c["CLASS"] if isinstance(c["CLASS"], list) else [c["CLASS"]]
        out[c["@id"]] = {x["@code"]: x["@name"] for x in cl}
    return out


def _values(app_id: str, sid: str) -> list:
    out, start = [], 1
    while True:
        j = requests.get(f"{BASE}/getStatsData",
                         params={"appId": app_id, "statsDataId": sid, "lang": "J",
                                 "limit": 100000, "startPosition": start},
                         timeout=300).json()["GET_STATS_DATA"]
        assert j["RESULT"]["STATUS"] == 0, j["RESULT"]
        inf = j["STATISTICAL_DATA"]["DATA_INF"]
        v = inf["VALUE"]
        out += v if isinstance(v, list) else [v]
        nxt = inf.get("NEXT_KEY")
        if not nxt:
            return out
        start = nxt


def _decode(v: dict, cls: dict):
    """One value row -> (year, month, item, measure, unit) or None."""
    item = measure = unit = period = None
    for dim, codes in cls.items():
        key = f"@{dim}"
        if key not in v:
            continue
        code, name = v[key], codes.get(v[key], "")
        parts = name.split("_")
        if parts[0] == "製品" and len(parts) >= 6:        # 2021+ combined side
            item = _canon_item("_".join(parts[2:-3]) or parts[2])
            measure = MEASURE_MAP.get(parts[-2])
            unit = parts[-1]
            continue
        p = _period_from(name) or _period_from(code)      # time, from name or code
        if p:
            period = p
            continue
        m = _canon_measure(name)
        if m:
            measure = m
            continue
        it = _canon_item(name)
        if it:
            item = it
            u = re.findall(r"[（(]\s*(kg|千円|十個|10個|個)\s*[)）]", name)
            unit = unit or (u[0] if u else "")
    if not (item and measure and period):
        return None
    return period[0], period[1], item, measure, UNIT_BY_MEASURE.get(measure, unit or "")


def _field(v) -> str:
    return str(v.get("$", "")).strip() if isinstance(v, dict) else ("" if v is None else str(v).strip())


def _as_list(x) -> list:
    return [] if x is None else (x if isinstance(x, list) else [x])


def newest_kakuho(app_id: str) -> tuple[int, str] | None:
    """(yyyymm, statInfId) of the newest monthly 確報 統計表 workbook.

    The statInfId is read from the resource's download URL; the resource @id is
    a different identifier and does not resolve against file-download."""
    found, start = {}, 1
    while True:
        j = requests.get(f"{BASE}/getDataCatalog",
                         params={"appId": app_id, "statsCode": STATS_CODE, "lang": "J",
                                 "limit": 100, "startPosition": start},
                         timeout=120).json()["GET_DATA_CATALOG"]
        dl = j.get("DATA_CATALOG_LIST_INF", {})
        for ds in _as_list(dl.get("DATA_CATALOG_INF")):
            title = (ds.get("DATASET") or {}).get("TITLE") or {}
            ym = _field(title.get("SURVEY_DATE"))
            if "確報_月次" not in _field(title.get("NAME")) or not re.fullmatch(r"\d{6}", ym):
                continue
            for res in _as_list((ds.get("RESOURCES") or {}).get("RESOURCE")):
                name = _field((res.get("TITLE") or {}).get("NAME"))
                m = re.search(r"statInfId=(\d+)", str(res.get("URL") or ""))
                if m and "統計表_確報" in name and "機械" not in name:
                    found[int(ym)] = m.group(1)
        nxt = dl.get("RESULT_INF", {}).get("NEXT_KEY")
        if not nxt:
            break
        start = int(nxt)
    if not found:
        return None
    ym = max(found)
    return ym, found[ym]


def kakuho_rows(app_id: str, after_year: int, items: set) -> list:
    """Cosmetics rows from the newest 確報 workbook, for years after after_year."""
    hit = newest_kakuho(app_id)
    if not hit or hit[0] // 100 <= after_year:
        return []
    ym, sid = hit
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"seidou_kakuho_{ym}.xlsx"
    if not path.exists():
        blob = requests.get(FILE_DL, params={"statInfId": sid, "fileKind": "0"},
                            timeout=300).content
        if not blob.startswith(b"PK"):             # error pages arrive as HTTP 200
            raise RuntimeError(f"statInfId {sid}: response is not an xlsx")
        path.write_bytes(blob)

    raw = pd.read_excel(path, sheet_name="実数表", header=None, dtype=object, engine="openpyxl")
    hdr = next(i for i in range(6) if str(raw.iat[i, 0]).strip() == "調査票番号")
    raw.columns = [str(h).strip() for h in raw.iloc[hdr]]
    body = raw.iloc[hdr + 1:]
    body = body[body["調査票番号"].astype(str).str.replace(".0", "", regex=False) == FORM]
    months = [c for c in raw.columns if re.fullmatch(r"\d{6}", c) and int(c[:4]) > after_year]

    rows, unknown = [], set()
    for _, r in body.iterrows():
        item = _canon_item(str(r["品目名"]))
        measure = MEASURE_MAP.get(str(r["アイテム名"]).strip())
        if not measure:
            continue                               # 従事者数, regional 生産金額
        if item not in items:
            unknown.add(item)
            continue
        for c in months:
            v = r[c]
            if v is None or (isinstance(v, float) and v != v) or str(v).strip() == "":
                continue                           # month not yet published
            try:
                val = float(str(v).replace(",", ""))
            except ValueError:
                continue                           # suppressed (X)
            rows.append((int(c[:4]), int(c[4:]), item, measure,
                         UNIT_BY_MEASURE[measure], val, int(c[:4]), f"確報 {ym}"))
    regions = {"企業", "全国計"} | {u for u in unknown if u.endswith(("県", "都", "府", "道", "局"))}
    if unknown - regions - {"化粧品部門"}:
        raise RuntimeError(f"確報 {ym}: product lines not in the 時系列表: {sorted(unknown - regions)}")
    print(f"  確報 {ym} ({sid}): {len(rows):>6} values for months after {after_year}", flush=True)
    return rows


def main() -> Path:
    load_env()
    app = get_estat_app_id()
    rows = []
    for year, sid in TABLES.items():
        cls = _class_map(app, sid)
        vals = _values(app, sid)
        kept = 0
        for v in vals:
            d = _decode(v, cls)
            if not d:
                continue
            try:
                val = float(str(v["$"]).replace(",", ""))
            except ValueError:
                continue
            rows.append((*d, val, year, "時系列表"))
            kept += 1
        print(f"  {year} ({sid}): {len(vals):>6} values -> {kept:>6} decoded", flush=True)
        time.sleep(0.5)

    known = {r[2] for r in rows}
    rows += kakuho_rows(app, max(TABLES), known)

    df = pd.DataFrame(rows, columns=["year", "month", "item", "measure", "unit",
                                     "value", "source_table_year", "edition"])
    # Later tables restate earlier years; keep the most recent publication.
    df = (df.sort_values("source_table_year")
            .drop_duplicates(subset=["year", "month", "item", "measure"], keep="last"))
    out = ROOT / "dashboard" / "assets" / "estat_meti_cosmetics.csv"
    df.sort_values(["item", "measure", "year", "month"]).to_csv(out, index=False)
    print(f"\n{len(df):,} rows -> {out.relative_to(ROOT)}")
    print(f"  items    : {df['item'].nunique()}")
    print(f"  measures : {sorted(df['measure'].unique())}")
    print(f"  years    : {sorted(df['year'].unique())}")
    print(f"  monthly  : {sorted(df[df.month>0]['year'].unique())}")
    return out


if __name__ == "__main__":
    main()
