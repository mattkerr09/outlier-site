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


ROOT = Path(__file__).resolve().parent.parent
BASE = "afb2e8a834a3eecc9ed2b630933cc977a2d176eb"
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

    def test_only_answer_and_page_dates_changed(self):
        for rel in PAGES:
            with self.subTest(page=rel):
                before = git("show", f"{BASE}:{rel}", text=True)
                after = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn("Last updated 2026-11-16", after)
                self.assertRegex(after, r'"dateModified":\s*"2026-11-16"')
                self.assertIn('name="last-modified" content="2026-11-16"', after)
                if rel == "learn/own-your-ai/index.html":
                    # Preserve all original ownership and licence wording verbatim.
                    old_list = re.search(r'      <ul>.*?</ul>', QUICK.search(before).group(), re.S).group()
                    anchor = '    <h2>Rented AI changes underneath you</h2>\n'
                    self.assertEqual(after.count(anchor + old_list + "\n"), 1)
                    after = after.replace(anchor + old_list + "\n", anchor, 1)

                def unchanged(raw):
                    raw = QUICK.sub("<answer>", raw)
                    raw = re.sub(r'("dateModified":\s*")[^"]+', r'\1<date>', raw)
                    raw = re.sub(r'(name="last-modified" content=")[^"]+', r'\1<date>', raw)
                    return re.sub(r'Last updated \d{4}-\d{2}-\d{2}', "Last updated <date>", raw)

                # This also pins prices, sale lines, licence terms, legal text,
                # FAQ prose/schema, publication dates, CSS and existing links.
                self.assertEqual(unchanged(before), unchanged(after))

    def test_round_one_untouched(self):
        protected = git("diff-tree", "--no-commit-id", "--name-only", "-r", BASE, text=True).splitlines()
        self.assertTrue(protected)
        self.assertFalse(set(protected) & {*PAGES, TEST})
        for rel in protected:
            with self.subTest(page=rel):
                self.assertEqual(git("show", f"{BASE}:{rel}"), (ROOT / rel).read_bytes())

    def test_changed_paths(self):
        changed = set(git("diff", "--name-only", "-z", BASE, "--").decode().split("\0"))
        changed.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
        changed.discard("")
        self.assertEqual(changed, {*PAGES, TEST}, f"unexpected changed paths: {changed}")

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
