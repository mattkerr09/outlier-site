#!/usr/bin/env python3
"""seo/_data/models.csv must name the tiers the APP actually ships.

Shipped defect this exists for (2026-08-23): 1.11.798 folded Code into Core and
the app's catalog went to six tiers. models.csv kept its `code` row. Every other
tier check on this site derives "what ships" FROM models.csv, so tier_count_gate
read 7, compared the prose to 7, and printed

    shipping tiers: 7 (nano, lite, quick, compact, code, plus, vision38)
    PASS - every stated tier count matches what actually ships.

while the shipping app returned six and the hero drew a chip for a tier nobody
could select. A validator reading the same stale source as the thing it
validates agrees with it for the wrong reason. Nothing here was broken enough to
notice: the gate was correct, the CSV was well-formed, the prose matched the CSV.

So this gate is the only one that looks OUTSIDE the site. It compares models.csv
against TIER_DISPLAY_ORDER in desktop_app/backend/server.py - the list that
literally orders the model picker, i.e. what a customer sees.

TIER_DISPLAY_ORDER and not TIER_CATALOG on purpose: the catalog is a dict whose
values are expressions, and regexing one of those is how server.py got spliced
twice. This is a list of string literals, so ast.literal_eval is exact.

Missing app repo is a FAILURE, not a skip. A gate that quietly does nothing when
its reference is absent is indistinguishable from a gate that passes, which is
the whole failure mode above. Set OUTLIER_SKIP_CATALOG_SYNC=1 to opt out
deliberately in a standalone checkout.
"""
import ast
import csv
import os
import pathlib
import sys


def find_server_py(root):
    env = os.environ.get("OUTLIER_SERVER_PY")
    if env:
        p = pathlib.Path(env)
        return p if p.is_file() else None
    for cand in (root / ".." / "desktop_app" / "backend" / "server.py",
                 root / "desktop_app" / "backend" / "server.py"):
        if cand.is_file():
            return cand.resolve()
    return None


def shipped_tiers(server_py):
    """TIER_DISPLAY_ORDER as a list of tier ids, or None if it is not a literal."""
    tree = ast.parse(server_py.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "TIER_DISPLAY_ORDER":
                try:
                    return list(ast.literal_eval(node.value))
                except Exception:
                    return None
    return None


def csv_tiers(root):
    path = root / "seo" / "_data" / "models.csv"
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as fh:
        return [r["tier_id"].strip() for r in csv.DictReader(fh) if r.get("tier_id")]


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    if os.environ.get("OUTLIER_SKIP_CATALOG_SYNC") == "1":
        print("SKIP: OUTLIER_SKIP_CATALOG_SYNC=1 - models.csv was NOT checked "
              "against the app catalog.")
        return 0

    rows = csv_tiers(root)
    if rows is None:
        print("FAIL: seo/_data/models.csv not found - nothing to compare.")
        return 1

    server_py = find_server_py(root)
    if server_py is None:
        print("FAIL: cannot find desktop_app/backend/server.py, so the tier list "
              "on this site is unverifiable.")
        print("      Every other tier check here derives 'what ships' from "
              "models.csv, so without this one nothing compares the site to the "
              "app at all. Point OUTLIER_SERVER_PY at server.py, or set "
              "OUTLIER_SKIP_CATALOG_SYNC=1 if you really mean to skip it.")
        return 1

    shipped = shipped_tiers(server_py)
    if not shipped:
        print(f"FAIL: TIER_DISPLAY_ORDER not found as a list literal in "
              f"{server_py}. It may have been renamed or made dynamic; this gate "
              f"must be updated rather than removed.")
        return 1

    site, app = set(rows), set(shipped)
    print(f"app TIER_DISPLAY_ORDER : {len(shipped)} ({', '.join(shipped)})")
    print(f"site models.csv        : {len(rows)} ({', '.join(rows)})")

    only_site, only_app = sorted(site - app), sorted(app - site)
    if not only_site and not only_app:
        print("\nPASS - the site lists exactly the tiers the app ships.")
        return 0

    print("\nFAIL: models.csv and the shipping catalog disagree.")
    if only_site:
        print(f"  the SITE advertises but the app does NOT ship: {only_site}")
        print("     Customers are being sold a tier that will not appear in the "
              "picker. Remove the row, then re-run render.py and the tier gates - "
              "they derive their counts from this file and will name every page "
              "that needs updating.")
    if only_app:
        print(f"  the APP ships but the site never mentions: {only_app}")
        print("     A tier nobody can find is a tier nobody buys.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
