"""Offline tests using real git ranges and one replaceable HTTP boundary."""
import importlib.util
from http.client import IncompleteRead
import io
import json
from pathlib import Path
import subprocess
from urllib.error import HTTPError, URLError
from xml.sax.saxutils import escape

import pytest


SPEC = importlib.util.spec_from_file_location(
    "indexnow_after_deploy", Path(__file__).with_name("indexnow_after_deploy.py"),
)
indexnow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(indexnow)
HTTP_REQUEST = indexnow.http_request
HOST = "example.invalid"
SITE = f"https://{HOST}"
KEY = "public-key-12345"


def sitemap(paths):
    return ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
            "".join(f"<url><loc>{escape(SITE + path)}</loc></url>" for path in paths) +
            "</urlset>")


class Repo:
    def __init__(self, path):
        self.path = path
        self.git("init", "-q")
        self.initial = self.commit({
            "index.html": "<h1>Home</h1>", "sitemap.xml": sitemap(["/"]),
            f"{KEY}.txt": KEY,
        })

    def git(self, *args):
        return subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
             "-c", "user.name=IndexNow test", "-c", "user.email=test@example.invalid",
             "-C", str(self.path), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def commit(self, files):
        for name, content in files.items():
            path = self.path / name
            if content is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        names = list(files)
        for offset in range(0, len(names), 500):
            self.git("add", "--", *names[offset:offset + 500])
        self.git("commit", "-q", "-m", "test pages")
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected HTTP call")
    monkeypatch.setattr(indexnow, "http_request", forbidden)
    # Even the transport tests below must never reach an actual socket.
    monkeypatch.setattr(indexnow, "urlopen", forbidden)


def run(repo, start="HEAD~1", end="HEAD", dry=False):
    args = ["--host", HOST, "--repo", str(repo.path), "--from", start, "--to", end]
    if dry:
        args.append("--dry")
    return indexnow.main(args)


def output(capsys):
    captured = capsys.readouterr()
    first, _, plain = captured.out.partition("\n")
    return json.loads(first), plain, captured.err


def fake_http(monkeypatch, post_status=202, post_body="queued", get_results=None):
    calls = []
    results = iter(get_results) if get_results is not None else None

    def request(method, url, body=None):
        calls.append((method, url, body))
        if method == "GET":
            result = next(results) if results is not None else (200, KEY)
            if isinstance(result, Exception):
                raise result
            return result
        assert method == "POST"
        assert url == indexnow.ENDPOINT
        if isinstance(post_status, Exception):
            raise post_status
        return post_status, post_body

    monkeypatch.setattr(indexnow, "http_request", request)
    return calls


@pytest.mark.parametrize(("path", "expected"), [
    ("index.html", "/"), ("a/index.html", "/a/"), ("a/b/index.html", "/a/b/"),
    ("privacy.html", "/privacy.html"), ("llms.txt", "/llms.txt"),
    ("a b/index.html", "/a%20b/"), ("a#b/index.html", "/a%23b/"),
    ("scripts/index.html", None), ("scripts/a/index.html", None),
    ("_seo_build/index.html", None), ("seo/_data/index.html", None),
    (".github/index.html", None), (".hidden.html", None),
    ("a/.hidden/index.html", None), ("a/.hidden.html", None),
    ("_draft.html", None), ("a/_draft/index.html", None),
    ("a/_draft.html", None), ("README.md", None), ("a/README.md", None),
    ("style.css", None), ("app.js", None), ("image.png", None),
    ("image.jpg", None), ("image.jpeg", None), ("image.gif", None),
    ("image.svg", None), ("image.webp", None), ("image.ico", None),
    ("data.json", None), ("sitemap.xml", None),
    ("google123456.html", None), ("a/google123456.html", None),
    ("404.html", None), ("a/404.html", None), ("a/page.html", None),
    ("robots.txt", None), (f"{KEY}.txt", None), ("a/llms.txt", None),
])
def test_mapping(path, expected):
    actual = indexnow.page_url(path, HOST)
    assert actual == (SITE + expected if expected is not None else None)


def test_three_real_changed_pages_are_not_silently_lost(repo, monkeypatch, capsys):
    """An empty mapper must fail this test, even if it returns success."""
    end = repo.commit({
        "index.html": "<h1>New home</h1>", "a/b/index.html": "<h1>New page</h1>",
        "privacy.html": "<h1>Privacy</h1>",
        "sitemap.xml": sitemap(["/", "/a/b/", "/privacy.html"]),
    })
    calls = fake_http(monkeypatch)
    assert run(repo, "HEAD~1", "HEAD") == 0
    report, plain, err = output(capsys)
    expected = [SITE + "/", SITE + "/a/b/", SITE + "/privacy.html"]
    assert report == {"host": HOST, "from": repo.initial, "to": end,
                      "sent": 3, "deleted": 0, "status": [202], "urls": expected}
    assert "accepted for processing" in plain
    assert "indexed" not in plain
    assert not err
    assert len(calls) == 2
    assert calls[0] == ("GET", f"{SITE}/{KEY}.txt", None)
    assert json.loads(calls[1][2]) == {
        "host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt",
        "urlList": expected,
    }


def test_noindexed_and_skipped_paths_even_when_listed(repo, capsys):
    repo.commit({
        "hidden/index.html": '<meta name="robots" content="noindex">',
        "scripts/index.html": "internal", "_seo_build/index.html": "internal",
        "seo/_data/index.html": "internal", ".github/index.html": "internal",
        "googlecheck.html": "verification", "404.html": "not found",
        "sitemap.xml": sitemap(["/", "/scripts/", "/_seo_build/", "/seo/_data/",
                                "/.github/", "/googlecheck.html", "/404.html"]),
    })
    assert run(repo) == 0
    report, plain, _ = output(capsys)
    assert report["urls"] == []
    assert report["sent"] == 0
    assert plain.strip() == "no indexable page changed"


def test_uses_to_sitemap_not_working_tree(repo, monkeypatch, capsys):
    repo.commit({"hidden/index.html": "before", "sitemap.xml": sitemap(["/", "/hidden/"])})
    repo.commit({"hidden/index.html": "after", "sitemap.xml": sitemap(["/"])})
    (repo.path / "sitemap.xml").write_text(sitemap(["/hidden/"]))
    assert run(repo) == 0
    assert output(capsys)[0]["urls"] == []
    repo.commit({"sitemap.xml": sitemap(["/", "/hidden/"]), "hidden/index.html": "again"})
    (repo.path / "sitemap.xml").write_text("broken working sitemap")
    calls = fake_http(monkeypatch)
    assert run(repo) == 0
    assert output(capsys)[0]["urls"] == [SITE + "/hidden/"]
    assert len(calls) == 2


def test_deleted_pages_use_from_sitemap(repo, monkeypatch, capsys):
    repo.commit({
        "gone/index.html": "gone", "private/index.html": "noindex", "llms.txt": "text",
        "sitemap.xml": sitemap(["/", "/gone/"]),
    })
    repo.commit({"gone/index.html": None, "private/index.html": None,
                 "llms.txt": None, "sitemap.xml": sitemap(["/", "/private/"])})
    fake_http(monkeypatch)
    assert run(repo) == 0
    report, _, _ = output(capsys)
    assert report["urls"] == [SITE + "/gone/"]
    assert report["sent"] == report["deleted"] == 1


def test_llms_changed_always_sent(repo, monkeypatch, capsys):
    repo.commit({"llms.txt": "new text"})
    fake_http(monkeypatch)
    assert run(repo) == 0
    report, _, _ = output(capsys)
    assert report["urls"] == [SITE + "/llms.txt"]
    assert report["deleted"] == 0


def test_deleted_llms_sent_when_previously_listed(repo, monkeypatch, capsys):
    repo.commit({"llms.txt": "text", "sitemap.xml": sitemap(["/", "/llms.txt"])})
    repo.commit({"llms.txt": None, "sitemap.xml": sitemap(["/"])})
    fake_http(monkeypatch)
    assert run(repo) == 0
    report, _, _ = output(capsys)
    assert report["urls"] == [SITE + "/llms.txt"]
    assert report["deleted"] == 1


@pytest.mark.parametrize("case", ["none", "two", "mismatch"])
def test_bad_key_exits_two_without_http(repo, capsys, case):
    repo.commit({"index.html": "changed"})
    key_file = repo.path / f"{KEY}.txt"
    if case == "none":
        key_file.unlink()
    elif case == "two":
        (repo.path / "second-key-123.txt").write_text("second-key-123")
    else:
        key_file.write_text("DO NOT PRINT THIS CONTENT")
    assert run(repo) == 2
    report, plain, _ = output(capsys)
    assert "expected one" in plain
    assert "DO NOT PRINT THIS CONTENT" not in plain
    assert report["sent"] == 0
    if case == "mismatch":
        assert "content does not match filename" in plain


def test_key_discovery_uses_name_pattern_and_stripped_content(repo, capsys):
    repo.commit({"index.html": "changed"})
    (repo.path / f"{KEY}.txt").write_text(f"\n{KEY}\n")
    for name, content in [("short.txt", "short"), ("bad_key_name.txt", "bad_key_name"),
                          ("x" * 129 + ".txt", "x" * 129),
                          ("mismatched-public-key.txt", "DO NOT PRINT THIS")]:
        (repo.path / name).write_text(content)
    assert run(repo, dry=True) == 0
    report, plain, _ = output(capsys)
    assert f"key file: {KEY}.txt" in plain
    assert "DO NOT PRINT THIS" not in plain
    assert report["sent"] == 0


@pytest.mark.parametrize("result", [(404, "not deployed"), (200, "wrong key"),
                                    (200, KEY + "x"), (200, "x" + KEY), URLError("offline"),
                                    IncompleteRead(b"partial")])
def test_bad_live_key_retries_and_never_posts(repo, monkeypatch, capsys, result):
    repo.commit({"index.html": "changed"})
    sleeps = []
    monkeypatch.setattr(indexnow.time, "sleep", sleeps.append)
    calls = fake_http(monkeypatch, get_results=[result] * 6)
    assert run(repo) == 1
    report, plain, _ = output(capsys)
    assert [c[0] for c in calls] == ["GET"] * 6
    assert sleeps == [20] * 5
    assert "live key check failed after 6 tries" in plain
    assert report["sent"] == 0
    assert report["status"] == []


def test_live_key_with_trailing_newline_is_accepted(repo, monkeypatch, capsys):
    """outlier.host serves the key file with a trailing newline (33 bytes, read live 2026-11-20). An exact-bytes compare
    would refuse it forever and nothing would ever be sent."""
    repo.commit({"index.html": "changed"})
    monkeypatch.setattr(indexnow.time, "sleep", lambda _s: None)
    calls = fake_http(monkeypatch, get_results=[(200, KEY + "\n")])
    assert run(repo) == 0
    assert [c[0] for c in calls] == ["GET", "POST"]
    assert output(capsys)[0]["sent"] == 1


def test_live_key_becomes_ready_on_sixth_try(repo, monkeypatch, capsys):
    repo.commit({"index.html": "changed"})
    sleeps = []
    monkeypatch.setattr(indexnow.time, "sleep", sleeps.append)
    calls = fake_http(monkeypatch, get_results=[(404, "wait")] * 5 + [(200, KEY)])
    assert run(repo) == 0
    assert [c[0] for c in calls] == ["GET"] * 6 + ["POST"]
    assert sleeps == [20] * 5
    assert output(capsys)[0]["sent"] == 1


@pytest.mark.parametrize("status", [200, 202, 400, 403, 422, 429, 500, 503])
def test_submit_statuses_and_body_limit(repo, monkeypatch, capsys, status):
    repo.commit({"index.html": "changed"})
    fake_http(monkeypatch, post_status=status, post_body="x" * 300 + "NOT PRINTED")
    accepted = status in {200, 202}
    assert run(repo) == (0 if accepted else 1)
    report, plain, _ = output(capsys)
    assert report["status"] == [status]
    assert report["sent"] == int(accepted)
    if accepted:
        assert "accepted for processing" in plain
    else:
        assert f"HTTP {status}: " + "x" * 300 in plain
        assert "NOT PRINTED" not in plain


@pytest.mark.parametrize("error", [URLError("offline"), IncompleteRead(b"partial")])
def test_post_network_error(repo, monkeypatch, capsys, error):
    repo.commit({"index.html": "changed"})
    fake_http(monkeypatch, post_status=error)
    assert run(repo) == 1
    report, plain, _ = output(capsys)
    assert "network error" in plain
    assert str(error) in plain
    assert report["status"] == ["network error"]
    assert report["sent"] == 0


def test_batches_at_ten_thousand(repo, monkeypatch, capsys):
    paths = [f"/page-{i:05d}/" for i in range(10_001)]
    repo.commit({**{f"page-{i:05d}/index.html": "page" for i in range(10_001)},
                 "sitemap.xml": sitemap(paths)})
    calls = fake_http(monkeypatch)
    assert run(repo) == 0
    batches = [json.loads(body)["urlList"] for method, _, body in calls if method == "POST"]
    assert [len(batch) for batch in batches] == [10_000, 1]
    assert batches[0] + batches[1] == [SITE + path for path in paths]
    report, plain, _ = output(capsys)
    assert report["sent"] == 10_001
    assert report["status"] == [202, 202]
    assert report["urls"] == [SITE + path for path in paths[:25]]
    assert "accepted for processing" in plain


def test_failed_batch_stops_and_counts_only_accepted_urls(repo, monkeypatch, capsys):
    repo.commit({"a/index.html": "old", "sitemap.xml": sitemap(["/a/"])})
    repo.commit({"a/index.html": None, "b/index.html": "new", "c/index.html": "new",
                 "sitemap.xml": sitemap(["/b/", "/c/"])})
    monkeypatch.setattr(indexnow, "BATCH_SIZE", 1)
    posts = []

    def request(method, url, body=None):
        if method == "GET":
            return 200, KEY
        posts.append(json.loads(body)["urlList"])
        return (202, "queued") if len(posts) == 1 else (429, "slow down")

    monkeypatch.setattr(indexnow, "http_request", request)
    assert run(repo) == 1
    report, plain, _ = output(capsys)
    assert posts == [[SITE + "/a/"], [SITE + "/b/"]]
    assert report["status"] == [202, 429]
    assert report["sent"] == report["deleted"] == 1
    assert "HTTP 429: slow down" in plain


def test_nul_separated_paths_with_spaces_newlines_and_unicode(repo, monkeypatch, capsys):
    repo.commit({"a b/index.html": "page", "a\nb/index.html": "page",
                 "caf\u00e9/index.html": "page",
                 "sitemap.xml": sitemap(["/a%20b/", "/a%0Ab/", "/caf%C3%A9/"])})
    fake_http(monkeypatch)
    assert run(repo) == 0
    report, _, _ = output(capsys)
    assert report["urls"] == [SITE + "/a%0Ab/", SITE + "/a%20b/", SITE + "/caf%C3%A9/"]
    assert report["sent"] == 3


def test_dry_prints_full_lists_and_never_calls_http(repo, capsys):
    repo.commit({"old/index.html": "old", "sitemap.xml": sitemap(["/", "/old/"])})
    paths = [f"/page-{i:02d}/" for i in range(26)]
    repo.commit({**{f"page-{i:02d}/index.html": "page" for i in range(26)},
                 "old/index.html": None, "sitemap.xml": sitemap(paths)})
    assert run(repo, dry=True) == 0
    report, plain, _ = output(capsys)
    assert report["sent"] == report["deleted"] == 0
    assert report["status"] == []
    assert len(report["urls"]) == 25
    assert f"key file: {KEY}.txt" in plain
    assert "changed/added URLs: 26" in plain
    assert "deleted URLs: 1" in plain
    assert SITE + "/old/" in plain
    for path in paths:
        assert SITE + path in plain


@pytest.mark.parametrize("dry", [False, True])
def test_identical_range_makes_no_http_call(repo, capsys, dry):
    assert run(repo, "HEAD", "HEAD", dry=dry) == 0
    report, plain, _ = output(capsys)
    assert report["urls"] == []
    assert report["sent"] == 0
    assert "no indexable page changed" in plain


def test_nonancestor_range_warns_but_sends(repo, monkeypatch, capsys):
    newer = repo.commit({"index.html": "newer"})
    fake_http(monkeypatch)
    assert run(repo, "HEAD", "HEAD~1") == 0
    report, _, err = output(capsys)
    assert report["from"] == newer
    assert report["to"] == repo.initial
    assert report["sent"] == 1
    assert "warning:" in err and "not an ancestor" in err


def test_rename_is_delete_and_add(repo, monkeypatch, capsys):
    repo.commit({"old/index.html": "same content", "sitemap.xml": sitemap(["/old/"])})
    repo.commit({"old/index.html": None, "new/index.html": "same content",
                 "sitemap.xml": sitemap(["/new/"])})
    fake_http(monkeypatch)
    assert run(repo) == 0
    report, _, _ = output(capsys)
    assert report["urls"] == [SITE + "/new/", SITE + "/old/"]
    assert report["sent"] == 2 and report["deleted"] == 1


@pytest.mark.parametrize("case", ["bad-revision", "missing-sitemap", "bad-sitemap"])
def test_bad_git_input_fails_without_http(repo, capsys, case):
    repo.commit({"index.html": "changed"})
    if case == "missing-sitemap":
        repo.commit({"sitemap.xml": None})
    elif case == "bad-sitemap":
        repo.commit({"sitemap.xml": "broken xml"})
    assert run(repo, end="missing-ref" if case == "bad-revision" else "HEAD") == 2
    report, plain, _ = output(capsys)
    assert report["sent"] == 0
    assert "failed" in plain or "invalid sitemap" in plain


def test_http_transport_headers_and_error_body(monkeypatch):
    calls = []

    class Response(io.BytesIO):
        status = 202

    def open_fake(request, timeout):
        calls.append((request, timeout))
        return Response(b"queued")

    monkeypatch.setattr(indexnow, "urlopen", open_fake)
    # Use the real transport here while its socket boundary stays replaced.
    assert HTTP_REQUEST("POST", indexnow.ENDPOINT, b"{}") == (202, "queued")
    request, timeout = calls[0]
    assert request.get_header("User-agent") == indexnow.USER_AGENT
    assert request.get_header("Content-type") == "application/json; charset=utf-8"
    assert request.data == b"{}" and timeout == 30
    assert HTTP_REQUEST("GET", f"{SITE}/{KEY}.txt") == (202, "queued")
    assert calls[1][0].get_header("User-agent") == indexnow.USER_AGENT

    def error_fake(request, timeout):
        raise HTTPError(request.full_url, 422, "bad URLs", {}, io.BytesIO(b"bad URLs"))

    monkeypatch.setattr(indexnow, "urlopen", error_fake)
    assert HTTP_REQUEST("POST", indexnow.ENDPOINT, b"{}") == (422, "bad URLs")
