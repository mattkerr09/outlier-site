#!/bin/bash
# Site-wide version bump that CANNOT rewrite measurement provenance.
#
# WHY THIS EXISTS (2026-08-09). The bump used to be a bare
#   grep -rl OLD . | xargs sed -i '' 's/OLD/NEW/g'
# and it silently rewrote the benchmark table's "measured on v1.11.757" labels
# to 758 — claiming MMLU and SWE-bench were run against a build that did not
# exist when they ran. The numbers were real; the sed turned their provenance
# into a false claim on a public pricing page.
#
# A version string that tracks the release and a version string that records
# WHEN A MEASUREMENT HAPPENED look identical to sed and are opposites in
# meaning. This script keeps them apart:
#   * the benchmark dataset directory is never touched
#   * lines carrying a provenance marker are never touched
#   * afterwards it re-checks that provenance still matches dataset.json
#
# Usage:  scripts/bump_version.sh 1.11.757 1.11.775
set -euo pipefail

OLD="${1:?usage: bump_version.sh OLD NEW}"
NEW="${2:?usage: bump_version.sh OLD NEW}"
cd "$(dirname "$0")/.."

# Lines that state when something was MEASURED. Never bumped.
PROVENANCE_RE='measured on|app path|blind · official|Re-run against the shipping|app_version|measured against'
# Paths whose whole purpose is to record a past measurement. Never bumped.
EXCLUDE_DIRS='./data/outlier-tier-benchmarks'

echo ">>> bumping $OLD -> $NEW (provenance protected)"
CHANGED=0; SKIPPED=0
while IFS= read -r f; do
  case "$f" in
    $EXCLUDE_DIRS*) echo "    skip (measurement record): $f"; SKIPPED=$((SKIPPED+1)); continue ;;
  esac
  # Rewrite only lines that do NOT carry a provenance marker.
  before=$(grep -c "$OLD" "$f" || true)
  python3 - "$f" "$OLD" "$NEW" "$PROVENANCE_RE" <<'PY'
import re, sys
path, old, new, prov = sys.argv[1:5]
rx = re.compile(prov)
out = []
for line in open(path, encoding="utf-8").read().split("\n"):
    out.append(line if rx.search(line) else line.replace(old, new))
open(path, "w", encoding="utf-8").write("\n".join(out))
PY
  after=$(grep -c "$OLD" "$f" || true)
  [ "$before" != "$after" ] && CHANGED=$((CHANGED+1))
  [ "$after" != "0" ] && echo "    kept $after provenance mention(s) in $f"
done < <(grep -rl "$OLD" . --exclude-dir=.git 2>/dev/null || true)

echo ">>> files rewritten: $CHANGED   measurement records skipped: $SKIPPED"

# The guard: whatever the page says it measured on must equal what the dataset
# says it measured on. If a future edit drifts one, this fails loudly.
echo ">>> verifying provenance still agrees with the dataset"
python3 - <<'PY'
import json, pathlib, re, sys
ds = pathlib.Path("data/outlier-tier-benchmarks-2026-08/dataset.json")
if not ds.exists():
    print("    no benchmark dataset — nothing to check"); sys.exit(0)
want = json.loads(ds.read_text())["app_version"]
html = pathlib.Path("index.html").read_text()
found = set(re.findall(r"v(\d+\.\d+\.\d+)(?=\s*</div>|\s+app path|\s+build on)", html))
bad = {v for v in found if v != want}
print(f"    dataset app_version = {want}; provenance versions in index.html = {sorted(found) or 'none'}")
if bad:
    print(f"    FAIL: provenance disagrees with the dataset: {sorted(bad)}"); sys.exit(1)
print("    OK — provenance and dataset agree")
PY
echo ">>> done. Verify live with:  curl -sL -H 'Cache-Control: no-cache' https://outlier.host/"
echo "    (a ?cb= query string does NOT bust this CDN)"
