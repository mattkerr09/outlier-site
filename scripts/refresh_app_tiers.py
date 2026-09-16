#!/usr/bin/env python3
"""Rewrite seo/_data/app_tiers.json from the app, for CI to check against.

WHY THIS EXISTS. tier_catalog_sync_gate compares the site's models.csv to the
app's TIER_DISPLAY_ORDER. CI has no app checkout, and for a few hours on
2026-09-16 it skipped the gate for that reason — which made its only enforcement
a no-op, because CI is the only thing that runs it. The snapshot is how CI sees
the reference instead of excusing it.

⚠️ RUN THIS AT EVERY VERSION BUMP. The snapshot records the version it was cut
from, and the gate refuses unless that matches the version the site advertises —
which is deliberate, because a stale copy would silently reintroduce the drift
the gate exists to catch. The cost is that a release which bumps the version and
forgets this will fail the gate. That failure is the guard working; this script
is the one-command answer to it.

    python3 scripts/refresh_app_tiers.py            # finds ../desktop_app/backend/server.py
    OUTLIER_SERVER_PY=<path> python3 scripts/refresh_app_tiers.py
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def find_server_py() -> pathlib.Path | None:
    env = os.environ.get("OUTLIER_SERVER_PY")
    if env:
        p = pathlib.Path(env)
        return p if p.is_file() else None
    for cand in (ROOT / ".." / "desktop_app" / "backend" / "server.py",
                 ROOT / "desktop_app" / "backend" / "server.py"):
        if cand.is_file():
            return cand.resolve()
    return None


def main() -> int:
    srv = find_server_py()
    if srv is None:
        print("FAIL: cannot find the app's server.py. Point OUTLIER_SERVER_PY at it.")
        return 1
    src = srv.read_text(encoding="utf-8", errors="replace")

    tiers = None
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "TIER_DISPLAY_ORDER":
                    try:
                        tiers = list(ast.literal_eval(node.value))
                    except Exception:
                        tiers = None
    if not tiers:
        print("FAIL: TIER_DISPLAY_ORDER is not a list literal in the app. This "
              "script must be updated rather than the gate weakened.")
        return 1

    m = re.search(r'APP_VERSION\s*=\s*"([\d.]+)"', src)
    if not m:
        print("FAIL: no APP_VERSION in the app; the snapshot would have nothing "
              "to date itself with, and an undated snapshot cannot go stale loudly.")
        return 1

    out = ROOT / "seo" / "_data" / "app_tiers.json"
    out.write_text(json.dumps({
        "_why": ("Written by scripts/refresh_app_tiers.py so CI can compare the site's "
                 "tier list to what the app ships. CI has no app checkout, and a gate "
                 "that cannot see its reference must not be skipped when it is the only "
                 "thing checking. cut_from_version is what stops this going stale "
                 "silently: the gate refuses unless it matches the version the site "
                 "advertises."),
        "cut_from_version": m.group(1),
        "tier_display_order": tiers,
    }, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)} — version {m.group(1)}, "
          f"{len(tiers)} tiers: {', '.join(tiers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
