#!/usr/bin/env python3
"""Offline checks for O1, O2 and O3, preserving all earlier measured answers.

Reuse Round 1's provenance and first-screen checks. The LM Studio page also
styles its FAQ as quick-answer, so check the opening separately from that FAQ.
The hook gets a temporary commit of the working files, never a real push.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from test_measured_answers import QUICK, check_answer, git, visible


# Retired the Round 3b O1, O2 and O3 measured-answer job's old-base scope and byte pins:
# later reviewed sitewide edits make those byte pins wrong.
ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "vs/lm-studio-alternative/index.html":
        ("O2", "/data/local-ai-time-to-first-token-mac/", "first-token test", "0.90"),
    "vs/outlier-vs-ollama/index.html":
        ("O3", "/data/v11-streaming-engine-benchmarks/", "shipped-app test", "2.0"),
    "vs/mac-native-ai-comparison/index.html":
        ("O1", "/data/local-ai-math-word-problems-mac/", "word-problem test", "8.0"),
}
TEST = "scripts/test_measured_answers_3b.py"


def check_opening(raw):
    # The same placement, sentence, punctuation, link, visible-number and Mac
    # checks as Round 1, over the opening only. Keep the later FAQ untouched.
    return check_answer(raw[:raw.index("<h2")] + "<h2>")


class MeasuredAnswersRoundThreeB(unittest.TestCase):
    def test_answers_and_controls(self):
        for rel, (question, source_url, label, figure) in PAGES.items():
            with self.subTest(page=rel, question=question):
                raw = (ROOT / rel).read_text(encoding="utf-8")
                quick, answer = check_opening(raw)
                self.assertEqual(answer.links, [[source_url, label]])
                self.assertIn("Mac Studio M1 Ultra with 64 GB", answer.text)
                source = (ROOT / source_url.lstrip("/") / "index.html").read_text(encoding="utf-8")
                source_text = visible(source).text

                # Bind each result to its model, build and measurement method,
                # beyond checking whether every visible number is in the source.
                if question == "O2":
                    for text in ("Core began replying in 0.90 seconds", "build 1.11.908",
                                 "Canada question", "model loaded and saved prompt work reused",
                                 "your wait may differ", "not measured LM Studio on the same Mac"):
                        self.assertIn(text, answer.text)
                    table = re.search(r"<h3>Table 3:.*?</table>", source, re.S)
                    self.assertIsNotNone(table)
                    self.assertIn("1.11.908", table.group())
                    self.assertIn("908 ask 2 (s)", visible(table.group()).text)
                    row = re.search(r"<tr><td>Core</td><td>Capital of Canada, one word</td>.*?</tr>",
                                    table.group(), re.S)
                    self.assertIsNotNone(row)
                    self.assertEqual([visible(c).text for c in re.findall(r"<td>(.*?)</td>", row.group())],
                                     ["Core", "Capital of Canada, one word", "20.83", "0.90"])
                    self.assertIn("The model was already loaded in every run", source_text)
                elif question == "O3":
                    for text in ("Ollama alternative", "chat and a coding agent in one app",
                                 "build 1.11.593", "Plus 397B ran at 2.0 tokens per second",
                                 "18.0 GB of peak memory", "not tested Ollama on that model"):
                        self.assertIn(text, answer.text)
                    measured = visible(QUICK.search(source).group()).text
                    for text in ("Plus 397B runs at 2.0 tok/s at the shipped K=40 setting",
                                 "build 1.11.593, M1 Ultra with 64 GB", "18.0 GB peak"):
                        self.assertIn(text, measured)
                else:
                    for text in ("For local AI on an Apple silicon Mac, try Outlier",
                                 "build 1.11.908", "Lite got 20 of 20 right",
                                 "working each problem out first", "median reply took 8.0 seconds",
                                 "our own short problems in one run", "check its answers",
                                 "I make Outlier", "does not rank it against other apps"):
                        self.assertIn(text, answer.text)
                    table = re.search(r"<h3>Table 2:.*?</table>", source, re.S)
                    self.assertIsNotNone(table)
                    self.assertIn("Outlier Lite", table.group())
                    row = re.search(r"<tr><td>Works it out first.*?</tr>", table.group(), re.S)
                    self.assertIsNotNone(row)
                    self.assertEqual([visible(c).text for c in re.findall(r"<td>(.*?)</td>", row.group())],
                                     ["Works it out first, out of sight (1.11.908)",
                                      "20 of 20", "8.0 s", "479", "0 of 20"])
                    self.assertIn("Mac Studio with an M1 Ultra and 64 GB", source_text)
                    self.assertIn("one run per setup", source_text)

                invented = quick.group().replace(figure, "987654.321", 1)
                self.assertNotEqual(invented, quick.group(), "invented-figure plant did not land")
                self.assertNotIn("987654.321", source)
                with self.assertRaisesRegex(AssertionError, "unsourced number: 987654.321"):
                    check_opening(raw[:quick.start()] + invented + raw[quick.end():])

                missing = quick.group().replace(f'<a href="{source_url}">{label}</a>', label)
                self.assertNotEqual(missing, quick.group(), "missing-link plant did not land")
                with self.assertRaisesRegex(AssertionError, "missing data link"):
                    check_opening(raw[:quick.start()] + missing + raw[quick.end():])
                print(f"{question} {rel}: sourced answer passes; invented figure and missing data link fail",
                      flush=True)

    def test_pre_push_to_next(self):
        with tempfile.TemporaryDirectory(prefix="outlier-measured-answers-3b-") as temp:
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
                      input="Round 3b measured answer hook fixture\n", env=env, text=True).strip()
            # Git supplies local ref, local SHA, remote ref and remote SHA.
            line = f"HEAD {sha} refs/heads/next {'0' * 40}\n"
            result = subprocess.run(["sh", "scripts/githooks/pre-push", "origin", "."],
                                    cwd=ROOT, input=line, text=True, env=env)
            print(f"pre-push to next: exit {result.returncode}", flush=True)
            self.assertEqual(result.returncode, 0, "pre-push returned nonzero")


if __name__ == "__main__":
    unittest.main(verbosity=2)
