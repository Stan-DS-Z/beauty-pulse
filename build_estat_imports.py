"""Pull 財務省 貿易統計 HS 3304 cosmetics trade (both directions) from e-Stat.

NB04b found domestic shipments falling while attention rose. METI counts what
domestic establishments ship and does not count imports, so a shift of
consumption toward imported product appears there as a fall. This is the test:
domestic shipments + imports = apparent consumption.

    python build_estat_imports.py    # -> dashboard/assets/estat_trade_hs3304.csv

HS 3304 is beauty/make-up/skin-care preparations:
  3304.10 lip · 3304.20 eye · 3304.30 manicure/pedicure · 3304.91 powders
  3304.99 other — where the bulk of skincare sits, a heterogeneous catch-all.

Two channels, checked against each other. The e-Stat database is the primary
source. Each year's table is also published as a CSV file, one per 部, listed in
e-Stat's data catalog. The database can omit a code that the file carries: on
2024-01-01 the import schedule merged 3304.99-011/012/019 into 3304.99-010, and
the database never added 010 (about 1,070億円 a year in 2024 and 2025). Every
(code, country) the two channels share must agree to the 千円; codes only the
file carries are taken from it and named in the run output.
"""

import io
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.utils import load_env, get_estat_app_id          # noqa: E402

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"
STATS_CODE = "00350300"                     # 普通貿易統計
FILE_PART = "28-38類"                        # 第6部, which holds chapter 33
RAW_DIR = ROOT / "data" / "raw" / "estat"

# 品別国別表, confirmed against getStatsList 2026-09-06 and again 2026-09-27
# (0003425294 still the only national import table for 2021-25, updated 2026-08-28).
# Exports matter as much as imports here: METI's domestic shipment figure
# includes product that is subsequently exported, so consumption inside Japan is
# shipments - exports + imports. Japan's cosmetics exports moved sharply over
# this window, which makes the export leg the larger correction.
TABLES = {
    ("import", "2016-2020"): "0003313966",
    ("import", "2021-2025"): "0003425294",   # 2021-24 確定, 2025 確々報
    ("export", "2016-2020"): "0003313965",
    ("export", "2021-2025"): "0003425293",
}
# The import and export commodity tables carry DIFFERENT 3304 sub-codes
# (import splits 3304.99 into 010/090 from 2024 and 011/012/019/090 before,
# export into 100/200/900), so the codes are resolved from each table's own
# metadata rather than hardcoded. Filtering the export table with import codes
# silently drops its largest lines.
HS_PREFIX = "3304"
ANNUAL_VALUE = "140"             # 合計_金額, 千円
FLOW_JA = {"import": "輸入", "export": "輸出"}


def _codes(app: str, sid: str, cls_id: str) -> dict:
    j = requests.get(f"{BASE}/getMetaInfo", params={"appId": app, "statsDataId": sid,
                                                    "lang": "J"}, timeout=300).json()
    for c in j["GET_META_INFO"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]:
        if c["@id"] == cls_id:
            cl = c["CLASS"] if isinstance(c["CLASS"], list) else [c["CLASS"]]
            return {x["@code"]: x["@name"] for x in cl}
    return {}


def _as_list(x) -> list:
    return x if isinstance(x, list) else [x]


def file_url(app: str, flow: str, year: int) -> tuple[str, str]:
    """(statInfId, URL) of the year's full-year 第6部 CSV from the data catalog."""
    j = requests.get(f"{BASE}/getDataCatalog", params={
        "appId": app, "statsCode": STATS_CODE, "searchWord": f"品別国別表 {FLOW_JA[flow]}",
        "surveyYears": str(year), "lang": "J", "limit": 100}, timeout=300).json()
    dataset = f"貿易統計_全国分_品別国別表_{FLOW_JA[flow]}_月次_{year}年12月"
    found = []
    for d in _as_list(j["GET_DATA_CATALOG"].get("DATA_CATALOG_LIST_INF", {})
                      .get("DATA_CATALOG_INF", [])):
        if d["DATASET"]["TITLE"]["NAME"] != dataset:
            continue
        for r in _as_list(d["RESOURCES"]["RESOURCE"]):
            if r.get("FORMAT") == "CSV" and FILE_PART in r["TITLE"]["NAME"]:
                found.append((r["URL"].split("statInfId=")[1].split("&")[0], r["URL"]))
    if len(found) != 1:
        raise RuntimeError(f"{flow} {year}: expected one {FILE_PART} CSV in {dataset}, found {found}")
    return found[0]


def file_rows(app: str, flow: str, year: int) -> pd.DataFrame:
    """HS 3304 rows of the year's CSV file: hs_code, country_code, value_1000jpy."""
    inf_id, url = file_url(app, flow, year)
    path = RAW_DIR / f"trade_{flow}_{year}_{inf_id}.csv"     # a revision gets a new statInfId
    if not path.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(requests.get(url, timeout=300).content)
        time.sleep(0.5)
    f = pd.read_csv(io.BytesIO(path.read_bytes()), encoding="cp932",
                    dtype={"HS": str, "Country": str})
    f["hs_code"] = f["HS"].str.strip().str.strip("'")
    f = f[f["hs_code"].str.startswith(HS_PREFIX) & (f["Year"] == year)]
    return pd.DataFrame({"hs_code": f["hs_code"],
                         "country_code": "50" + f["Country"].str.strip().str.zfill(3),
                         "value_1000jpy": f["Value-Year"].astype(float)})


def main() -> Path:
    load_env()
    app = get_estat_app_id()
    rows, areas, items_by_flow = [], {}, {}
    for (flow, label), sid in TABLES.items():
        areas.update(_codes(app, sid, "area"))
        items = _codes(app, sid, "cat01")
        items_by_flow.setdefault(flow, {}).update(items)
        hs = sorted(c for c in items if str(c).startswith(HS_PREFIX))
        assert hs, f"no {HS_PREFIX} codes in {sid}"
        got, start = 0, 1
        while True:
            p = {"appId": app, "statsDataId": sid, "lang": "J",
                 "cdCat01": ",".join(hs), "cdCat02": ANNUAL_VALUE,
                 "limit": 100000, "startPosition": start}
            j = requests.get(f"{BASE}/getStatsData", params=p, timeout=300).json()["GET_STATS_DATA"]
            assert j["RESULT"]["STATUS"] == 0, j["RESULT"]
            inf = j["STATISTICAL_DATA"]["DATA_INF"]
            vals = inf["VALUE"]
            vals = vals if isinstance(vals, list) else [vals]
            for v in vals:
                try:
                    amount = float(str(v["$"]).replace(",", ""))
                except (ValueError, KeyError):
                    continue
                rows.append({
                    "flow": flow,
                    "year": int(str(v.get("@time", ""))[:4]),
                    "hs_code": v.get("@cat01", ""),
                    "country_code": v.get("@area", ""),
                    "value_1000jpy": amount,
                })
            got += len(vals)
            nxt = inf.get("NEXT_KEY")
            if not nxt:
                break
            start = nxt
        print(f"  {flow:6} {label} ({sid}): {got:,} values from {len(hs)} HS codes", flush=True)
        time.sleep(0.5)

    db = pd.DataFrame(rows).drop_duplicates(
        subset=["flow", "year", "hs_code", "country_code"], keep="last")

    # Reconcile each flow-year with its CSV file, and take what only the file has.
    key = ["hs_code", "country_code"]
    parts = []
    for (flow, year), d in db.groupby(["flow", "year"]):
        f = file_rows(app, flow, int(year))
        m = d.merge(f, on=key, how="outer", suffixes=("_db", "_file"), indicator=True)
        both = m[m["_merge"] == "both"]
        off = both[both["value_1000jpy_db"] != both["value_1000jpy_file"]]
        if len(off):
            raise RuntimeError(f"{flow} {year}: database and file disagree on {len(off)} rows:\n{off.head()}")
        db_only = m[m["_merge"] == "left_only"]
        if len(db_only):
            raise RuntimeError(f"{flow} {year}: {len(db_only)} database rows missing from the file:\n{db_only.head()}")
        extra = m[m["_merge"] == "right_only"]
        if len(extra):
            for code, e in extra.groupby("hs_code"):
                print(f"  {flow:6} {year}: {code} is in the file but not the database — "
                      f"{len(e)} rows, {e['value_1000jpy_file'].sum() / 1e5:,.0f}億円 taken from the file",
                      flush=True)
            parts.append(pd.DataFrame({"flow": flow, "year": int(year),
                                       "hs_code": extra["hs_code"],
                                       "country_code": extra["country_code"],
                                       "value_1000jpy": extra["value_1000jpy_file"]}))
    df = pd.concat([db, *parts], ignore_index=True)

    unknown = set(df["country_code"]) - set(areas)
    assert not unknown, f"country codes with no name in the table metadata: {sorted(unknown)}"
    df["hs_name"] = [items_by_flow[fl].get(c, c) for fl, c in zip(df["flow"], df["hs_code"])]
    df["country"] = [areas[c].split("_", 1)[-1] if "_" in areas[c] else areas[c]
                     for c in df["country_code"]]
    df = df[["flow", "year", "hs_code", "hs_name", "country_code", "country", "value_1000jpy"]]

    out = ROOT / "dashboard" / "assets" / "estat_trade_hs3304.csv"
    df.sort_values(["flow", "year", "hs_code", "country"]).to_csv(out, index=False)
    print(f"\n{len(df):,} rows -> {out.relative_to(ROOT)}")
    print(f"  years    : {sorted(df.year.unique())}")
    print(f"  hs codes : {sorted(df.hs_code.unique())}")
    print(f"  countries: {df.country.nunique()}")
    print(df.groupby(["flow", "year"])["value_1000jpy"].sum().div(1e5).round(0).unstack().to_string())
    return out


if __name__ == "__main__":
    main()
