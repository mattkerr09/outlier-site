#!/usr/bin/env python3
"""Offline checks for Round 3's O5 answer and its pre-push snapshot.

The best O1 page belongs to Round 1. The dedicated O2 and O3 pages are under
vs/, outside this job's allowed paths, so this round selects only O5.
Reuse Round 1's visible-number, source-link and first-screen checks.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from test_measured_answers import QUICK, check_answer, git, visible


ROOT = Path(__file__).resolve().parent.parent
BASE = "51bfb4530cbacd316266b127875baee5cc6483fb"
PAGES = ("best/free-local-ai-mac/index.html",)
TEST = "scripts/test_measured_answers_3.py"
SOURCE = "/data/local-ai-time-to-first-token-mac/"


class MeasuredAnswersRoundThree(unittest.TestCase):
    def test_answers_and_controls(self):
        source = (ROOT / SOURCE.lstrip("/") / "index.html").read_text(encoding="utf-8")
        for rel in PAGES:
            with self.subTest(page=rel, question="O5"):
                raw = (ROOT / rel).read_text(encoding="utf-8")
                quick, answer = check_answer(raw)
                self.assertEqual([SOURCE], [href for href, _label in answer.links])
                self.assertIn("for free on Apple silicon", answer.text)
                self.assertIn("Nano", answer.text)
                self.assertIn("build 1.11.908", answer.text)
                self.assertIn("0.31 to 0.33 seconds", answer.text)
                self.assertIn("Mac Studio M1 Ultra with 64 GB", answer.text)
                self.assertIn("four questions with the model loaded and saved prompt work reused", answer.text)
                self.assertIn("your wait may differ", answer.text)

                # Pin the model, build and column, not just numbers anywhere on
                # the source page. Table 3's second asks reused the saved work.
                table = re.search(r"<h3>Table 3:.*?</table>", source, re.S)
                self.assertIsNotNone(table)
                self.assertIn("1.11.908", table.group())
                self.assertIn("908 ask 2 (s)", visible(table.group()).text)
                rows = re.findall(r"<tr><td>Nano</td>.*?</tr>", table.group(), re.S)
                self.assertEqual(len(rows), 4)
                times = [visible(re.findall(r"<td>(.*?)</td>", row, re.S)[-1]).text for row in rows]
                self.assertEqual(times, ["0.32", "0.31", "0.31", "0.33"])
                self.assertIn("Hardware: Mac Studio, M1 Ultra, 64 GB unified memory", visible(source).text)
                self.assertIn("The model was already loaded in every run", visible(source).text)

                invented = quick.group().replace("0.31", "987654.321", 1)
                self.assertNotEqual(invented, quick.group(), "invented-figure plant did not land")
                self.assertNotIn("987654.321", source)
                with self.assertRaisesRegex(AssertionError, "unsourced number: 987654.321"):
                    check_answer(raw[:quick.start()] + invented + raw[quick.end():])

                missing = quick.group().replace(f'<a href="{SOURCE}">first-token test</a>', "first-token test")
                self.assertNotEqual(missing, quick.group(), "missing-link plant did not land")
                with self.assertRaisesRegex(AssertionError, "missing data link"):
                    check_answer(raw[:quick.start()] + missing + raw[quick.end():])
                print(f"O5 {rel}: sourced answer passes; invented figure and missing data link fail", flush=True)

    def test_only_answer_and_page_dates_changed(self):
        for rel in PAGES:
            with self.subTest(page=rel):
                before = git("show", f"{BASE}:{rel}", text=True)
                after = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn("Last updated 2026-11-16", after)
                self.assertRegex(after, r'"dateModified":\s*"2026-11-16"')
                self.assertIn('name="last-modified" content="2026-11-16"', after)

                # Keep the comparison list, including its price and licence
                # words, verbatim below the first h2, as in the earlier rounds.
                old_list = re.search(r'      <ul>.*?</ul>', QUICK.search(before).group(), re.S).group()
                anchor = "    <h2>What 'free' means for each</h2>\n"
                self.assertEqual(after.count(anchor + old_list + "\n"), 1)
                after = after.replace(anchor + old_list + "\n", anchor, 1)

                def unchanged(raw):
                    raw = QUICK.sub("<answer>", raw)
                    raw = re.sub(r'("dateModified":\s*")[^"]+', r'\1<date>', raw)
                    raw = re.sub(r'(name="last-modified" content=")[^"]+', r'\1<date>', raw)
                    return re.sub(r'Last updated \d{4}-\d{2}-\d{2}', "Last updated <date>", raw)

                # Pins prices, sale copy, terms, FAQ prose/schema, publication
                # dates, rival checked dates, legal text, styles and old links.
                self.assertEqual(unchanged(before), unchanged(after))

    def test_earlier_rounds_untouched(self):
        for commit in ("afb2e8a834a3eecc9ed2b630933cc977a2d176eb", BASE):
            protected = git("diff-tree", "--no-commit-id", "--name-only", "-r", commit, text=True).splitlines()
            self.assertTrue(protected)
            self.assertFalse(set(protected) & {*PAGES, TEST})
            for rel in protected:
                with self.subTest(commit=commit, page=rel):
                    self.assertEqual(git("show", f"{commit}:{rel}"), (ROOT / rel).read_bytes())

    def test_changed_paths(self):
        changed = set(git("diff", "--name-only", "-z", BASE, "--").decode().split("\0"))
        changed.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
        changed.discard("")
        self.assertEqual(changed, {*PAGES, TEST}, f"unexpected changed paths: {changed}")

    def test_pre_push_to_next(self):
        with tempfile.TemporaryDirectory(prefix="outlier-measured-answers-3-") as temp:
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
                      input="Round three measured answer hook fixture\n", env=env, text=True).strip()
            # Git supplies local ref, local SHA, remote ref and remote SHA.
            line = f"HEAD {sha} refs/heads/next {'0' * 40}\n"
            result = subprocess.run(["sh", "scripts/githooks/pre-push", "origin", "."],
                                    cwd=ROOT, input=line, text=True, env=env)
            print(f"pre-push to next: exit {result.returncode}", flush=True)
            self.assertEqual(result.returncode, 0, "pre-push returned nonzero")


if __name__ == "__main__":
    unittest.main(verbosity=2)
