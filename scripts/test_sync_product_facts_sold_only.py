#!/usr/bin/env python3
"""Offline regression checks for the sold-product family prices."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PRODUCTS = {
    "pdt_0Nlgdu1f0s30YekSmpGwA": {
        "name": "Outlier \u2014 Lifetime Licence",
        "price_cents": 2900,
        "activations_limit_product": 3,
        "activations_limit_entitlement": 3,
        "seats": 3,
        "activation_message_entitlement": "Covers up to 3 machines.",
    },
    "pdt_0Nlgdu6xbdzeG5tDAWx79": {
        "name": "Check Engine SEO \u2014 Lifetime Licence", "price_cents": 3900,
    },
    "pdt_0NlgdruM2dusRx82wfrmQ": {
        "name": "Crisp Pro \u2014 Lifetime Licence", "price_cents": 1900,
    },
    "pdt_0Nrgv6lKuWERrWrdtRtqu": {
        "name": "Mind the Minutes, Lifetime Licence", "price_cents": 3900,
    },
    "pdt_0NlgduBtaHbj0V2WvTCqG": {
        "name": "AdPlaybook \u2014 Unlimited Websites", "price_cents": 14900,
    },
}
EXPECTED = {
    "Outlier \u2014 Lifetime Licence": 2900,
    "Crisp Pro \u2014 Lifetime Licence": 1900,
    "Check Engine SEO \u2014 Lifetime Licence": 3900,
}
SOLD_IDS = tuple(PRODUCTS)[:3]
READ_AT = "2026-11-20T03:14:24Z"


class SoldOnly(unittest.TestCase):
    def run_sync(self, products):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            output = Path(tmp) / "output.json"
            source.write_text(json.dumps({
                "products": products, "read_at": READ_AT, "source": "test fixture",
            }), encoding="utf-8")
            # Exercise the real entry point and exit code with isolated paths.
            result = subprocess.run([
                sys.executable, "-B", "-c",
                "import pathlib, sys; import sync_product_facts as sync; "
                "sync.SOURCE = pathlib.Path(sys.argv[1]); "
                "sync.OUT = pathlib.Path(sys.argv[2]); "
                "sys.exit(sync.main([]))",
                str(source), str(output),
            ], cwd=Path(__file__).resolve().parent, capture_output=True, text=True)
            facts = json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
            return result, facts

    def test_five_products_produce_exactly_three_sold(self):
        result, facts = self.run_sync(PRODUCTS)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(facts["family_price_cents"], EXPECTED)
        self.assertEqual(facts["read_at"], READ_AT)
        outlier = PRODUCTS[SOLD_IDS[0]]
        self.assertEqual(facts["product_id"], SOLD_IDS[0])
        self.assertEqual(facts["product_name"], outlier["name"])
        self.assertEqual(facts["price_cents"], outlier["price_cents"])
        self.assertEqual(facts["seats"], outlier["seats"])
        self.assertEqual(facts["activation_message"], outlier["activation_message_entitlement"])

    def test_missing_sold_id_exits_one(self):
        for product_id in SOLD_IDS:
            with self.subTest(product_id=product_id):
                products = {key: value for key, value in PRODUCTS.items() if key != product_id}
                result, facts = self.run_sync(products)
                self.assertEqual(result.returncode, 1)
                self.assertIn(product_id, result.stderr)
                self.assertIsNone(facts)

    def test_extra_unsold_product_is_excluded(self):
        products = dict(PRODUCTS)
        products["pdt_unsold_control"] = {"name": "Unsold control", "price_cents": 1234}
        result, facts = self.run_sync(products)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(facts["family_price_cents"], EXPECTED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
