"""Phrasings of retired measures, shared by the docs test and the Shift page test.

Each entry is (regex, what it retired, where). A measure leaves this site when
its revision retires it; these keep its wording from coming back. The sweep in
recon/2026-09-27_sweep_retired-measures-as-shift-evidence.md lists claims still
open; each is added here when it is fixed, so the list only ever grows.
"""

RETIRED = [
    (r"shelf[- ]?(share|space)|棚占有|棚シェア|SKU棚",
     "Rakuten shelf share: counted the pull, not Rakuten (Revision 11)"),
    (r"(Rakuten|楽天)[^.。]{0,40}(lists|掲載)[^.。]{0,40}(more|倍)",
     "Rakuten listing ratio (Revision 11)"),
    (r"\bfive (independent )?sources\b|5つの(独立した)?(ソース|情報源)",
     "'five sources': three of them were retired (Revisions 2, 3, 11)"),
    (r"review[- ]volume (growth )?(is|as) a (market )?signal",
     "@cosme review-volume share as a signal (Revision 2)"),
]

# The sources a "moved toward skincare after 2020" sentence may not cite:
# no Rakuten data before March 2026; @cosme review-volume share retired.
NOT_SHIFT_EVIDENCE = r"Rakuten|楽天|@cosme|review"
