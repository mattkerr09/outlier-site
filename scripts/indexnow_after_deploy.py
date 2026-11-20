#!/usr/bin/env python3
"""Send pages changed by a deployed git range to IndexNow. Python 3.10+."""
from __future__ import annotations

import argparse
from http.client import HTTPException
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


USER_AGENT = "Mozilla/5.0 (compatible; outlier-site-indexnow/1)"
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH_SIZE = 10_000
KEY_NAME = re.compile(r"[A-Za-z0-9-]{8,128}\.txt")


class InputError(Exception):
    """The repo, revision range, sitemap, or public key cannot be used."""


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise InputError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def resolve(repo: Path, revision: str) -> str:
    return git(repo, "rev-parse", "--verify", "--end-of-options",
               f"{revision}^{{commit}}").decode("ascii").strip()


def page_url(path: str, host: str) -> str | None:
    """Map only public page paths, before applying the sitemap allowlist."""
    parts = path.split("/")
    if any(not part or part.startswith((".", "_")) for part in parts):
        return None
    if parts[0] == "scripts" or parts[:2] == ["seo", "_data"]:
        return None
    name = parts[-1]
    if name in {"README.md", "404.html"} or (
        name.startswith("google") and name.endswith(".html")
    ):
        return None
    if path == "llms.txt":
        suffix = path
    elif name == "index.html":
        suffix = path.removesuffix("index.html")
    elif len(parts) == 1 and name.endswith(".html"):
        suffix = path
    else:
        return None
    return f"https://{host}/{quote(suffix, safe='/')}"


def sitemap_urls(repo: Path, revision: str) -> set[str]:
    raw = git(repo, "show", f"{revision}:sitemap.xml")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise InputError(f"invalid sitemap.xml at {revision}: {exc}") from exc
    return {
        node.text.strip() for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text
    }


def changed_urls(repo: Path, host: str, start: str, end: str) -> tuple[list[str], list[str]]:
    def paths(diff_filter: str) -> list[str]:
        raw = git(repo, "diff", "--name-only", "-z", "--no-renames",
                  f"--diff-filter={diff_filter}", start, end, "--")
        return [p.decode("utf-8", errors="surrogateescape")
                for p in raw.split(b"\0") if p]

    current = sitemap_urls(repo, end)
    previous = sitemap_urls(repo, start)
    changed = {
        url for path in paths("AMT")
        if (url := page_url(path, host)) is not None
        and (path == "llms.txt" or url in current)
    }
    deleted = {
        url for path in paths("D")
        if (url := page_url(path, host)) is not None and url in previous
    }
    # A file move can map to the same URL on both sides. Submit that URL once.
    return sorted(changed), sorted(deleted - changed)


def discover_key(repo: Path) -> Path:
    matches = []
    mismatches = []
    for path in sorted(repo.iterdir()):
        if not KEY_NAME.fullmatch(path.name) or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except UnicodeError:
            mismatches.append(path.name)
            continue
        if content == path.stem:
            matches.append(path)
        else:
            mismatches.append(path.name)
    if len(matches) != 1:
        detail = f"found {len(matches)} valid IndexNow key files at the repo root; expected one"
        if mismatches:
            detail += "; content does not match filename: " + ", ".join(mismatches)
        raise InputError(detail)
    return matches[0]


def http_request(method: str, url: str, body: bytes | None = None) -> tuple[int, str]:
    """The single HTTP boundary. HTTP errors retain their status and body."""
    headers = {"User-Agent": USER_AGENT}
    if body is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        with exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")


def verify_live_key(host: str, key: str) -> tuple[bool, str]:
    url = f"https://{host}/{key}.txt"
    detail = ""
    for attempt in range(6):
        try:
            status, body = http_request("GET", url)
            # The live key file ends with a newline (33 bytes for a 32-character key, read 2026-11-20). IndexNow
            # itself reads the file's text, so compare the stripped body; a wrong or extended key still fails.
            if status == 200 and body.strip() == key:
                return True, ""
            detail = f"HTTP {status}: {body[:300]}"
        except (URLError, OSError, HTTPException) as exc:
            detail = f"network error: {str(exc)[:300]}"
        if attempt < 5:
            time.sleep(20)
    return False, f"live key check failed after 6 tries: {detail}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--from", dest="start", required=True)
    parser.add_argument("--to", dest="end", required=True)
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args(argv)
    summary = {"host": args.host, "from": args.start, "to": args.end,
               "sent": 0, "deleted": 0, "status": [], "urls": []}

    def finish(code: int, message: str) -> int:
        print(json.dumps(summary, ensure_ascii=True))
        print(message)
        return code

    try:
        # A host is a DNS name, without a scheme, port, path, or credentials.
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", args.host):
            raise InputError("--host must be a DNS name, such as outlier.host")
        repo = Path(git(args.repo, "rev-parse", "--show-toplevel").decode().strip())
        start = summary["from"] = resolve(repo, args.start)
        end = summary["to"] = resolve(repo, args.end)
        ancestry = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", start, end],
            capture_output=True, check=False,
        )
        if ancestry.returncode == 1:
            print(f"warning: {start} is not an ancestor of {end}; diffing them anyway",
                  file=sys.stderr)
        elif ancestry.returncode:
            raise InputError("git merge-base failed: " +
                             ancestry.stderr.decode("utf-8", errors="replace").strip())
        changed, deleted = changed_urls(repo, args.host, start, end)
        urls = sorted(set(changed + deleted))
        summary["urls"] = urls[:25]
        if not urls and not args.dry:
            return finish(0, "no indexable page changed")
        key_file = discover_key(repo)
        key = key_file.stem
        if args.dry:
            lines = [f"dry run; key file: {key_file.name}",
                     f"changed/added URLs: {len(changed)}", *changed,
                     f"deleted URLs: {len(deleted)}", *deleted]
            if not urls:
                lines.append("no indexable page changed")
            return finish(0, "\n".join(lines))
        ready, detail = verify_live_key(args.host, key)
        if not ready:
            return finish(1, detail)
        deleted_set = set(deleted)
        for offset in range(0, len(urls), BATCH_SIZE):
            batch = urls[offset:offset + BATCH_SIZE]
            payload = json.dumps({
                "host": args.host, "key": key,
                "keyLocation": f"https://{args.host}/{key_file.name}", "urlList": batch,
            }).encode("utf-8")
            try:
                status, body = http_request("POST", ENDPOINT, payload)
            except (URLError, OSError, HTTPException) as exc:
                summary["status"].append("network error")
                return finish(1, f"IndexNow network error: {str(exc)[:300]}")
            summary["status"].append(status)
            if status not in {200, 202}:
                return finish(1, f"IndexNow HTTP {status}: {body[:300]}")
            summary["sent"] += len(batch)
            summary["deleted"] += sum(url in deleted_set for url in batch)
        return finish(0, f"{summary['sent']} URLs accepted for processing; "
                      f"{summary['deleted']} deleted")
    except (InputError, OSError, UnicodeError) as exc:
        return finish(2, str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
