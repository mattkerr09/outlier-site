#!/usr/bin/env python3
"""Offline checks for the O4, O9 and O10 measured answers, including pre-push.

The hook archives a commit. A temporary index and object store give it a snapshot
of the working files without changing this checkout's index, commits or hooks.
"""
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from urllib.parse import urlsplit


# Retired the O4, O9 and O10 measured-answer job's old-base scope and byte pins:
# later reviewed sitewide edits make those byte pins wrong.
ROOT = Path(__file__).resolve().parent.parent
PAGES = (
    "how-to/run-qwen-locally-mac/index.html",
    "how-to/run-ai-on-16gb-mac/index.html",
    "best/local-ai-for-mac/index.html",
)
TEST = "scripts/test_measured_answers.py"
SOURCE = "/data/local-ai-benchmarks-mac-2026/"
QUICK = re.compile(r'<div class="quick-answer">.*?</div>', re.S)
NUMBER = re.compile(r"(?<![\d.])\d+(?:[,.]\d+)*(?![\d.])")


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.skip = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.skip.append(tag)
        if tag == "a" and not self.skip:
            self.links.append([dict(attrs).get("href", ""), []])
        if tag in {"p", "td", "th", "li", "br"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.skip and tag == self.skip[-1]:
            self.skip.pop()
        if tag in {"p", "td", "th", "li"}:
            self.parts.append(" ")
        if tag == "a" and self.links:
            self.links[-1][1] = "".join(self.links[-1][1])

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)
            if self.links and isinstance(self.links[-1][1], list):
                self.links[-1][1].append(data)

    @property
    def text(self):
        return " ".join("".join(self.parts).split())


def visible(raw):
    page = Visible()
    page.feed(raw)
    page.close()
    return page


def git(*args, **kwargs):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, **kwargs).stdout


def check_answer(raw):
    matches = list(QUICK.finditer(raw))
    assert len(matches) == 1, "expected one quick answer"
    quick = matches[0]
    assert raw.index("<h1") < quick.start() < quick.end() < raw.index("<h2"), \
        "quick answer must precede the first h2"
    assert quick.end() < raw.index('data-pbox="answer"'), "answer must precede the product box"
    assert len(visible(raw[raw.index("<article>"):quick.start()]).text.split()) < 70, \
        "too much prose before the answer"
    paragraphs = re.findall(r"<p>(.*?)</p>", quick.group(), re.S)
    assert len(paragraphs) == 1, "expected one short answer paragraph"
    answer = visible(paragraphs[0])
    assert 2 <= len(re.split(r"(?<=[.!?])\s+(?=[A-Z])", answer.text)) <= 4, \
        "expected two to four sentences"
    assert not re.search(r"[\u2013\u2014()]", answer.text), "use plain punctuation"
    sources = []
    for href, label in answer.links:
        url = urlsplit(href)
        assert not url.query and not url.fragment, "answer links must have no tracking or fragments"
        assert url.hostname in {None, "outlier.host"}, "answer links must stay on this site"
        target = ROOT / url.path.lstrip("/") / "index.html"
        assert target.is_file(), f"missing linked page: {href}"
        if url.path.startswith("/data/"):
            assert label.strip(), "data link must have visible text"
            sources.append(visible(target.read_text(encoding="utf-8")).text)
    assert sources, "missing data link"
    figures = NUMBER.findall(answer.text)
    assert figures, "answer has no number"
    sourced = {number for source in sources for number in NUMBER.findall(source)}
    for figure in figures:
        assert figure in sourced, f"unsourced number: {figure}"
    assert "M1 Ultra with 64 GB" in answer.text, "measurement must name its Mac"
    return quick, answer


class MeasuredAnswers(unittest.TestCase):
    def test_answers_and_controls(self):
        for rel in PAGES:
            with self.subTest(page=rel):
                raw = (ROOT / rel).read_text(encoding="utf-8")
                quick, answer = check_answer(raw)
                self.assertIn(SOURCE, [href for href, _label in answer.links])
                if "16gb" in rel:
                    facts = (("Nano 4B", "~4 GB"), ("Lite 9B", "~7 GB"))
                elif "qwen" in rel:
                    facts = (("Nano 4B", "71.7"), ("Lite 9B", "53.4"))
                else:
                    facts = (("Nano 4B", "71.7"),)
                source = (ROOT / SOURCE.lstrip("/") / "index.html").read_text()
                for model, figure in facts:
                    self.assertIn(model, answer.text)
                    self.assertIn(figure, answer.text)
                    row = re.search(r"<tr><td>" + re.escape(model) + r"</td>.*?</tr>", source, re.S)
                    self.assertIsNotNone(row)
                    self.assertIn(figure, visible(row.group()).text)
                invented = quick.group().replace("</p>", " Invented result: 987654.321 tok/s.</p>")
                self.assertNotIn("987654.321", source)
                with self.assertRaisesRegex(AssertionError, "unsourced number: 987654.321"):
                    check_answer(raw[:quick.start()] + invented + raw[quick.end():])
                missing = quick.group().replace(f'<a href="{SOURCE}">Mac benchmarks</a>', "Mac benchmarks")
                self.assertNotEqual(missing, quick.group(), "missing-link plant did not land")
                with self.assertRaisesRegex(AssertionError, "missing data link"):
                    check_answer(raw[:quick.start()] + missing + raw[quick.end():])
                print(f"{rel}: sourced answer passes; invented figure and missing data link fail", flush=True)

    def test_pre_push_to_next(self):
        with tempfile.TemporaryDirectory(prefix="outlier-measured-answers-") as temp:
            objects = Path(temp) / "objects"
            objects.mkdir()
            shared_objects = git("rev-parse", "--git-path", "objects", text=True).strip()
            env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp) / "index"),
                       GIT_OBJECT_DIRECTORY=str(objects),
                       GIT_ALTERNATE_OBJECT_DIRECTORIES=str((ROOT / shared_objects).resolve()),
                       GIT_AUTHOR_NAME="Measured answer test", GIT_AUTHOR_EMAIL="test@example.invalid",
                       GIT_COMMITTER_NAME="Measured answer test", GIT_COMMITTER_EMAIL="test@example.invalid",
                       PYTHONDONTWRITEBYTECODE="1")
            git("read-tree", "HEAD", env=env)
            git("add", "--", *PAGES, TEST, env=env)
            tree = git("write-tree", env=env, text=True).strip()
            sha = git("-c", "commit.gpgsign=false", "commit-tree", tree, "-p", "HEAD",
                      input="Measured answer hook fixture\n", env=env, text=True).strip()
            # Git's four stdin fields: local ref, local SHA, remote ref, remote SHA.
            line = f"HEAD {sha} refs/heads/next {'0' * 40}\n"
            result = subprocess.run(["sh", "scripts/githooks/pre-push", "origin", "."],
                                    cwd=ROOT, input=line, text=True, env=env)
            print(f"pre-push to next: exit {result.returncode}", flush=True)
            self.assertEqual(result.returncode, 0, "pre-push returned nonzero")


if __name__ == "__main__":
    unittest.main(verbosity=2)
