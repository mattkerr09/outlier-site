#!/usr/bin/env python3
"""Offline regression tests. No live Buy or Download link is fetched."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import checkout_link_gate as checkout
import first_party_links_gate as gate
import hub_nofollow
import internal_link_gate
import product_box
import rival_price_in_source_gate as rival
import wrap_counting_links as wrap


class FirstPartyLinksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.page = self.root / "index.html"
        self.html = ('<a href="https://outlier.host/dl/outlier?src=x&amp;to=https://example.com/x%2Fdmg" '
                     'rel="external nofollow">Download</a>\n'
                     "<a href='https://outlier.host/buy/outlier?src=x&amp;x=1&amp;x=2' rel='nofollow'>Buy</a>\n"
                     "<a href='https://outlier.host/buy/outlier?src=x&amp;x=1&amp;x=2' rel='nofollow'>Buy again</a>\n")
        self.page.write_text(self.html)
        self.robots = self.root / "robots.txt"
        self.robots.write_text("User-agent: A\nUser-agent: B\nDisallow: /dl/\nDisallow: /buy/\n\n"
                               "User-agent: *\nAllow: /\nDisallow: /dl/\nDisallow: /buy/\n")
        fixture = self.root / "scripts/fixtures/first_party_links_before.json"
        fixture.parent.mkdir(parents=True)
        # Build the expected multiset from hub links, as in the base commit.
        before, _ = gate.query_multiset(self.html.replace("https://outlier.host", "https://" + gate.HUB_HOST))
        fixture.write_text(json.dumps({"base_commit": "test-base", "queries": {"index.html": before}}))

    def check(self, expected):
        with redirect_stdout(StringIO()):
            self.assertEqual(gate.check(self.root), expected)

    def test_valid_tree(self):
        self.check(0)

    def test_old_html_and_generator_links_fail(self):
        for name in ("extra.html", "scripts/rebuild.py", "scripts/rebuild", "_seo_build/template.tmpl", "seo/rebuild.js"):
            with self.subTest(name=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('url = "https://' + gate.HUB_HOST + '/buy/outlier?src=x"')
                self.check(1)
                path.unlink()

    def test_other_hub_paths_stay_allowed(self):
        with self.page.open("a") as f:
            for path in ("buy/crisp", "buy/docket", "buy/bundle", "snippet.js"):
                f.write(f'<a href="https://{gate.HUB_HOST}/{path}">Other</a>')
        self.check(0)

    def test_nofollow_on_both_outlier_routes(self):
        for old in ('rel="external nofollow"', "rel='nofollow'"):
            with self.subTest(attribute=old):
                self.page.write_text(self.html.replace(old, 'rel="external"'))
                self.check(1)

    def test_raw_query_changes_fail(self):
        for old, new in (("x%2Fdmg", "x%2fdmg"), ("src=x&amp;x=1", "x=1&amp;src=x"),
                         ("&amp;", "&"), ("x=2", "x=3"), ("src=x", "src=y")):
            with self.subTest(change=(old, new)):
                self.page.write_text(self.html.replace(old, new))
                self.check(1)

    def test_duplicate_removed_or_added_fails(self):
        for text in (self.html.splitlines(keepends=True)[0], self.html + self.html):
            self.page.write_text(text)
            self.check(1)

    def test_each_robots_group_needs_each_rule(self):
        text = self.robots.read_text()
        for rule in ("Disallow: /dl/\n", "Disallow: /buy/\n"):
            for count in (1, 2):
                self.robots.write_text(text.replace(rule, "", count))
                self.check(1)

    def test_missing_fixture_and_empty_tree_fail(self):
        (self.root / "scripts/fixtures/first_party_links_before.json").unlink()
        self.check(1)
        self.page.unlink()
        self.check(1)

    def test_attributes_are_parsed_without_decoy_href(self):
        text = ('<A title=\'href="https://example.com"\' data-href="unused" '
                'HREF="https://outlier.host/buy/outlier?src=x" REL="external NOFOLLOW">Buy</A>')
        self.assertEqual(gate.query_multiset(text), ({"/buy/outlier": {"src=x": 1}}, []))
        self.assertEqual(len(gate.query_multiset(text.replace('REL="external NOFOLLOW"', ''))[1]), 1)


class LinkToolsTests(unittest.TestCase):
    def test_internal_links_skip_only_the_two_cloudflare_routes(self):
        with tempfile.TemporaryDirectory() as temp:
            page = Path(temp) / "index.html"
            links = ''.join(f'<a href="https://outlier.host/{route}/outlier?src=x">Link</a>'
                            for route in ("dl", "buy"))
            page.write_text(links)
            with redirect_stdout(StringIO()):
                self.assertEqual(internal_link_gate.main(temp), 0)
            for path in ("buy/crisp", "buy/bundle", "dl/outlier-typo", "buy/outlier/missing", "missing/"):
                page.write_text(links + f'<a href="https://outlier.host/{path}">Broken</a>')
                with redirect_stdout(StringIO()):
                    self.assertEqual(internal_link_gate.main(temp), 1)

    def test_nofollow_and_wrapping_cover_both_hosts(self):
        for host in (hub_nofollow.HUB, hub_nofollow.FIRST_PARTY):
            for route in ("dl/outlier", "buy/outlier", "buy/crisp"):
                text = f'<a href="{host}/{route}?src=x" rel="external">Link</a>'
                fixed, count = hub_nofollow.add_nofollow(text)
                self.assertEqual(count, 1)
                self.assertIn('rel="external nofollow"', fixed)
                self.assertEqual(hub_nofollow.add_nofollow(fixed), (fixed, 0))
                self.assertEqual(wrap.wrap(fixed, "x"), fixed)
        dmg = "https://github.com/Outlier-host/outlier-app-releases/releases/download/v1.2.3/Outlier-1.2.3-arm64.dmg"
        wrapped = wrap.wrap(f'<a href="{dmg}">Download</a>', "test")
        self.assertIn('href="https://outlier.host/dl/outlier?src=test&amp;to=' + dmg + '" rel="nofollow"', wrapped)

    def test_generated_boxes_use_first_party_links(self):
        for text in (product_box.box("test", "answer", "1.2.3"), product_box.end_box("test", "1.2.3")):
            self.assertNotIn(gate.HUB_HOST, text)
            self.assertIn("https://outlier.host/buy/outlier?src=", text)
            self.assertEqual(gate.query_multiset(text)[1], [])

    def test_own_links_are_never_rival_sources(self):
        for host in (checkout.HUB, checkout.FIRST_PARTY):
            for route in ("dl/outlier", "buy/outlier", "buy/bundle"):
                self.assertEqual(rival.cited(f'<a href="{host}/{route}?src=x">link</a>'), [])

    def test_checkout_uses_only_unfollowed_head(self):
        calls = []
        hub = checkout.HUB + "/buy/outlier?src=test&extra=%2F&extra=two"
        door = "https://checkout.dodopayments.com/buy/" + checkout.WORKER_PRODUCT

        class Response:
            def __init__(self, status, loc):
                self.status, self.headers = status, {"Location": loc}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class Opener:
            def open(self, req, timeout):
                calls.append(req)
                return Response(302, hub) if req.full_url.startswith(checkout.FIRST_PARTY) else Response(303, door)

        first = checkout.FIRST_PARTY + hub[len(checkout.HUB):]
        with patch.object(checkout, "_OPENER", Opener()):
            self.assertEqual(checkout.checkout_head(first), (303, door))
            self.assertEqual(checkout.checkout_head(hub), (303, door))
        self.assertEqual([r.full_url for r in calls], [first, hub, hub])
        self.assertTrue(all(r.get_method() == "HEAD" for r in calls))
        self.assertTrue(all(r.get_header("User-agent") == checkout.HUB_UA["User-Agent"] for r in calls))
        self.assertIsNone(checkout._NoFollow().redirect_request(None, None, None, None, None, None))
        for bad in (hub.replace("extra=%2F", "extra=/"), "https://example.com/buy/outlier?src=test"):
            with patch.object(checkout, "head_no_follow", return_value=(302, bad)) as head:
                self.assertEqual(checkout.checkout_head(first), (302, bad))
                head.assert_called_once_with(first)
        self.assertEqual(checkout._self_check_retry(), [])

    def test_checkout_control_runs_first(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for host in (checkout.HUB, checkout.FIRST_PARTY):
                url = host + "/buy/outlier?src=test&extra=%2F&extra=two"
                href = url.replace("&", "&amp;")
                (root / "index.html").write_text(f'<a href="{href}">Buy</a>')
                requests = []

                def head(url):
                    requests.append(url)
                    if url == checkout.CONTROL_URL:
                        return 404, ""
                    if url.startswith(checkout.FIRST_PARTY):
                        return 302, checkout.HUB + url[len(checkout.FIRST_PARTY):]
                    return 303, ("https://checkout.dodopayments.com/buy/" + checkout.WORKER_PRODUCT
                                 + "?redirect_url=https://outlier.host/thank-you.html&metadata_src=test")

                with patch.object(checkout.sys, "argv", ["checkout_link_gate.py", temp]), \
                        patch.object(checkout, "head_no_follow", side_effect=head), \
                        patch.object(checkout, "_self_check_retry", return_value=[]), redirect_stdout(StringIO()):
                    self.assertEqual(checkout.main(), 0)
                self.assertEqual(requests[0], checkout.CONTROL_URL)
                self.assertEqual(requests[1], url)
                self.assertEqual(checkout.WORKER_HREF.search(f'href="{url}"').group(1), url)
                with patch.object(checkout.sys, "argv", ["checkout_link_gate.py", temp]), \
                        patch.object(checkout, "head_no_follow", return_value=(303,
                            "https://checkout.dodopayments.com/buy/" + checkout.WORKER_PRODUCT)) as bad_control, \
                        patch.object(checkout, "_self_check_retry", return_value=[]), redirect_stdout(StringIO()):
                    self.assertEqual(checkout.main(), 1)
                    bad_control.assert_called_once_with(checkout.CONTROL_URL)


if __name__ == "__main__":
    unittest.main()
