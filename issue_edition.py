"""Issue a report edition: freeze the files the report pages read.

    python issue_edition.py            # freeze sources.EDITION, cut at sources.CUTOFF
    python issue_edition.py --check    # verify a frozen edition against its manifest

The report is dated one edition and must not move once issued. The cut-off
(sources.CUTOFF) keeps later months out, but a Google Trends re-pull rewrites
the whole span and a METI revision rewrites months already published, so the
live files can change under an issued edition. Issuing therefore copies every
data file in dashboard/assets into dashboard/assets/editions/<EDITION>/ and
writes manifest.json: the edition, its cut-off, the day it was issued, and
each file's sha256. Report pages read only that folder; monitor pages read the
live files. The public DB is not copied: the app never opens it.

An edition folder is written once. The script refuses if it exists; a new
edition is a new EDITION (and CUTOFF) in dashboard/bp/sources.py, then this
script.
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "dashboard" / "assets"
sys.path.insert(0, str(ROOT / "dashboard"))
from bp import sources  # noqa: E402

SKIP = ("signal_pulse_public",)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_files():
    return sorted(f for f in ASSETS.iterdir()
                  if f.is_file() and f.suffix in (".csv", ".png") and not f.name.startswith(SKIP))


def issue() -> int:
    dest = sources.edition_assets(ASSETS)
    if dest.exists():
        print(f"{dest.relative_to(ROOT)} exists: an issued edition is never rewritten")
        return 1
    dest.mkdir(parents=True)
    files = {}
    for f in data_files():
        shutil.copy2(f, dest / f.name)
        files[f.name] = sha256(dest / f.name)
    manifest = {"edition": sources.EDITION, "cutoff": sources.CUTOFF,
                "issued": date.today().isoformat(), "files": files}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
                                        encoding="utf-8")
    print(f"froze {len(files)} files into {dest.relative_to(ROOT)} "
          f"(edition {sources.EDITION}, cut-off {sources.CUTOFF})")
    return 0


def check() -> int:
    dest = sources.edition_assets(ASSETS)
    m = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    bad = [n for n, h in m["files"].items() if sha256(dest / n) != h]
    extra = {f.name for f in dest.iterdir()} - set(m["files"]) - {"manifest.json"}
    for n in bad:
        print(f"  changed: {n}")
    for n in sorted(extra):
        print(f"  not in the manifest: {n}")
    print(f"{len(m['files'])} files, {len(bad)} changed, {len(extra)} unlisted")
    return 1 if bad or extra else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    raise SystemExit(check() if ap.parse_args().check else issue())
