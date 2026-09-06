"""Pull 財務省 貿易統計 HS 3304 cosmetics trade (both directions) from e-Stat.

NB04b found domestic shipments falling while attention rose. METI counts what
domestic establishments ship and does not count imports, so a shift of
consumption toward imported product appears there as a fall. This is the test:
domestic shipments + imports = apparent consumption.

    python build_estat_imports.py    # -> dashboard/assets/estat_trade_hs3304.csv

HS 3304 is beauty/make-up/skin-care preparations:
  3304.10 lip · 3304.20 eye · 3304.30 manicure/pedicure · 3304.91 powders
  3304.99 other — where the bulk of skincare sits, a heterogeneous catch-all.
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.utils import load_env, get_estat_app_id          # noqa: E402

BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"

# 品別国別表, confirmed against getStatsList 2026-09-06.
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
# (import splits 3304.99 into 011/012/019/090, export into 100/200/900), so the
# codes are resolved from each table's own metadata rather than hardcoded.
# Filtering the export table with import codes silently drops its largest lines.
HS_PREFIX = "3304"
ANNUAL_VALUE = "140"             # 合計_金額, 千円


def _codes(app: str, sid: str, cls_id: str) -> dict:
    j = requests.get(f"{BASE}/getMetaInfo", params={"appId": app, "statsDataId": sid,
                                                    "lang": "J"}, timeout=300).json()
    for c in j["GET_META_INFO"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]:
        if c["@id"] == cls_id:
            cl = c["CLASS"] if isinstance(c["CLASS"], list) else [c["CLASS"]]
            return {x["@code"]: x["@name"] for x in cl}
    return {}


def main() -> Path:
    load_env()
    app = get_estat_app_id()
    rows = []
    for (flow, label), sid in TABLES.items():
        areas = _codes(app, sid, "area")
        items = _codes(app, sid, "cat01")
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
                area = areas.get(v.get("@area", ""), v.get("@area", ""))
                rows.append({
                    "flow": flow,
                    "year": int(str(v.get("@time", ""))[:4]),
                    "hs_code": v.get("@cat01", ""),
                    "hs_name": items.get(v.get("@cat01", ""), ""),
                    "country_code": v.get("@area", ""),
                    "country": area.split("_", 1)[-1] if "_" in area else area,
                    "value_1000jpy": amount,
                })
            got += len(vals)
            nxt = inf.get("NEXT_KEY")
            if not nxt:
                break
            start = nxt
        print(f"  {flow:6} {label} ({sid}): {got:,} values from {len(hs)} HS codes", flush=True)
        time.sleep(0.5)

    df = pd.DataFrame(rows).drop_duplicates(
        subset=["flow", "year", "hs_code", "country_code"], keep="last")
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
