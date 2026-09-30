"""Phrasings of retired measures, shared by the docs test and the page tests.

Each entry is (regex, what it retired), or (regex, what it retired, SITE_ONLY)
for a measure the notebooks keep as the record of how it was made: those are
checked on the pages and in the docs, not in the notebooks. A measure leaves
this site when its revision retires it; these keep its wording from coming
back. The sweep in
recon/2026-09-27_sweep_retired-measures-as-shift-evidence.md lists claims still
open; each is added here when it is fixed, so the list only ever grows.
Notebook cells headed "## Revisions" record removals by name and are not
checked.
"""

import re

SITE_ONLY = "site only"

# Markdown emphasis inside a phrase must not hide it: "independent *attention*
# signals" is the phrase "independent attention signals". An underscore is
# emphasis only at a word's edge, so snake_case names are left alone.
_EMPHASIS = (re.compile(r"(\*{1,3})(?=\S)(.+?)(?<=\S)\1"),
             re.compile(r"(?<!\w)(_{1,3})(?=\S)(.+?)(?<=\S)\1(?!\w)"))


def plain(text: str) -> str:
    """The text with * and _ emphasis markers removed, as a reader sees it.
    Every check matches the patterns below against this."""
    prev = None
    while prev != text:
        prev = text
        for pat in _EMPHASIS:
            text = pat.sub(r"\2", text)
    return text


RETIRED = [
    (r"shelf[- ]?(share|space)|棚占有|棚シェア|SKU棚",
     "Rakuten shelf share: counted the pull, not Rakuten (Revision 11)"),
    (r"(Rakuten|楽天)[^.。]{0,40}(lists|掲載)[^.。]{0,40}(more|倍)",
     "Rakuten listing ratio (Revision 11)"),
    (r"\bfive (independent )?sources\b|5つの(独立した)?(ソース|情報源)",
     "'five sources': three of them were retired (Revisions 2, 3, 11)"),
    (r"review[- ]volume[^.。]{0,30}\bis a (market )?signal",
     "@cosme review-volume share as a signal (Revision 2)"),
    (r"(multiple|several|two|three|five) independent (\w+ )?(signals|sources)|複数の独立した",
     "'independent signals': the within-side instruments are not (Source roles)"),
    (r"YouTube comments?[^.。]{0,40}(moved toward|outnumbered)|YouTubeコメント[^。]{0,20}比重",
     "YouTube comment counts across sides: set by the query list (Source roles)"),
    (r"YoY growth confirms the inflection|structural shift is not a calendar artefact",
     "@cosme review volume as shift evidence (NB03; Revision 2)"),
    (r"Reviews per SKU|SKUあたりレビュー数|reviews per item, against|1商品あたりレビュー[\d.]+件（全",
     "reviews per item across genres: measures how deep the 3,000 cap reaches (Revision 13)"),
    (r"Vocabulary [Ss]hift \(|Vocabulary Shift — Pre vs Post|成分言及率の推移|Pre-COVID avg",
     "@cosme vocabulary or ingredient mentions compared across years (Revision 2, Source roles)"),
    (r"TF-IDF Delta 2019|[Dd]ouble-confirmed|DOUBLE-CONFIRMED|Vocabulary shift — TF-IDF delta",
     "pooled cross-period TF-IDF delta and its cross-checks (NB06 §1; Revision 2)"),
    (r"Avg review length|Review Engagement Quality",
     "@cosme review length compared across years (Source roles)"),
    (r"動画 \(video\), 参考 \(reference\), 思う \(think\)|しっとり \(moist\)|"
     r"動画・参考・思う|Top terms by platform|プラットフォーム別の上位語",
     "Discovery's register note on NB06 §6's term lists, whose tokeniser kept verbs "
     "(Revision 15)"),
    (r"share[sd]? more vocabulary|共有する語彙は|"
     r"(vocabulary|review language)[^.。]{0,40}\bconverg|\bconverg\w*[^.。]{0,20}\b(vocabulary|review)|"
     r"語彙[^。]{0,10}収束|収束[^。]{0,10}語彙|0\.252\s*(→|->|to)\s*0\.317",
     "skincare-makeup vocabulary convergence across periods: product-matched it does not hold "
     "(Revision 20); NB06 and NB07 keep the test", SITE_ONLY),
    (r"launch(es| releases)? peak(s|ed)? in|launch releases[^.。]{0,30}\bpeak|"
     r"(新商品)?リリースは[^。]{0,20}月に多い|リリースのピーク",
     "peak months of launch releases: each year's months are consistent with an even spread "
     "(chi-square, 7 of 8 side-years; Revision 21)"),
]

# Lines a page carries although a retired pattern matches them, by page path:
# string-table keys whose whole text is left out of that page's check. The
# Method page is the one place the withdrawn convergence is recorded (Revision
# 20), in one plain line; the architect ruled it exempt, not reworded (Timing
# ruling 5). Nothing else on any page is exempt.
EXEMPT = {"/method": ("me_cv_line",)}
