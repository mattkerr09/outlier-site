#!/usr/bin/env python3
"""Offline checks for the O6, O7 and O8 measured answers, including pre-push.

Reuse Round 1's visible-number and first-screen checks. The hook runs against a
temporary snapshot of the working files without changing the checkout's index.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from test_measured_answers import QUICK, SOURCE, check_answer, git, visible


# Retired the O6, O7 and O8 measured-answer job's old-base scope and byte pins:
# later reviewed sitewide edits make those byte pins wrong.
ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "how-to/use-ai-offline-mac/index.html": ("O6", "Nano 4B", "71.7"),
    "learn/own-your-ai/index.html": ("O7", "Core 27B", "20.7"),
    "best/private-ai-no-cloud/index.html": ("O8", "Nano 4B", "71.7"),
}
TEST = "scripts/test_measured_answers_2.py"


class MeasuredAnswersRoundTwo(unittest.TestCase):
    def test_answers_and_controls(self):
        source = (ROOT / SOURCE.lstrip("/") / "index.html").read_text(encoding="utf-8")
        for rel, (question, model, figure) in PAGES.items():
            with self.subTest(page=rel, question=question):
                raw = (ROOT / rel).read_text(encoding="utf-8")
                quick, answer = check_answer(raw)
                self.assertIn(SOURCE, [href for href, _label in answer.links])
                self.assertIn(model, answer.text)
                self.assertIn(figure + " tokens per second", answer.text)
                row = re.search(r"<tr><td>" + re.escape(model) + r"</td>.*?</tr>", source, re.S)
                self.assertIsNotNone(row, "model missing from the linked measurement table")
                self.assertIn(figure, visible(row.group()).text)
                self.assertIn("M1 Ultra 64 GB", visible(source).text)

                # Replace a figure rather than append a fifth sentence, so this
                # control reaches the provenance check, not the length check.
                invented = quick.group().replace(figure, "987654.321", 1)
                self.assertNotEqual(invented, quick.group(), "invented-figure plant did not land")
                self.assertNotIn("987654.321", source)
                with self.assertRaisesRegex(AssertionError, "unsourced number: 987654.321"):
                    check_answer(raw[:quick.start()] + invented + raw[quick.end():])

                missing = quick.group().replace(f'<a href="{SOURCE}">Mac benchmarks</a>', "Mac benchmarks")
                self.assertNotEqual(missing, quick.group(), "missing-link plant did not land")
                with self.assertRaisesRegex(AssertionError, "missing data link"):
                    check_answer(raw[:quick.start()] + missing + raw[quick.end():])
                print(f"{question} {rel}: sourced answer passes; invented figure and missing data link fail",
                      flush=True)

    def test_pre_push_to_next(self):
        with tempfile.TemporaryDirectory(prefix="outlier-measured-answers-2-") as temp:
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
                      input="Round two measured answer hook fixture\n", env=env, text=True).strip()
            line = f"HEAD {sha} refs/heads/next {'0' * 40}\n"
            result = subprocess.run(["sh", "scripts/githooks/pre-push", "origin", "."],
                                    cwd=ROOT, input=line, text=True, env=env)
            print(f"pre-push to next: exit {result.returncode}", flush=True)
            self.assertEqual(result.returncode, 0, "pre-push returned nonzero")


if __name__ == "__main__":
    unittest.main(verbosity=2)
