"""Offline checks for the sale checkout and its exact end time."""
import datetime as dt
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import checkout_price_gate as gate


ROOT = Path(__file__).resolve().parent.parent
SALE_LINE = "Black Friday sale: $16.99 once through December 2. Then $39."


def page(price=""):
    return f"<html><body>Outlier {price} {'x' * 2100}</body></html>"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        pytest.fail("a test tried to fetch the live checkout")
    monkeypatch.setattr(gate.subprocess, "run", refuse)


@pytest.fixture
def site(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    for name in ("product-facts.json", "founding_offer.json"):
        (data / name).write_bytes((ROOT / "data" / name).read_bytes())
    return tmp_path


def end(site):
    offer = json.loads((site / "data" / "founding_offer.json").read_text())
    return dt.datetime.fromisoformat(offer["ends"].replace("Z", "+00:00")).timestamp()


def change_offer(site, change):
    path = site / "data" / "founding_offer.json"
    offer = json.loads(path.read_text())
    change(offer)
    path.write_text(json.dumps(offer), encoding="utf-8")


@pytest.mark.parametrize("price,expected,reason", [
    ("2900", 0, "product-facts price"),
    ("$29.00", 0, "product-facts price"),
    ("$29", 0, "product-facts price"),
    ("1699", 0, "FOUNDINGOUTLIER sale price"),
    ("$16.99", 0, "FOUNDINGOUTLIER sale price"),
    ("16.99", 0, "FOUNDINGOUTLIER sale price"),
    ("3900", 1, ""),
    ("1000", 1, ""),
    ("$16.00", 1, ""),
    ("$16", 1, ""),
    ("$34.99", 1, ""),
])
def test_before_end(site, monkeypatch, capsys, price, expected, reason):
    monkeypatch.setattr(gate, "fetch_checkout", lambda: page(price))
    assert gate.main([str(site)], now=end(site) - 1) == expected
    output = capsys.readouterr().out
    assert output.startswith("PASS:" if expected == 0 else "FAIL:")
    if expected == 0:
        assert reason in output
        assert ("2900 cents" if "29" in price else "1699 cents") in output


@pytest.mark.parametrize("offset", [0, 1])
@pytest.mark.parametrize("price,expected", [
    ("3900", 0), ("$39", 0), ("$39.00", 0),
    ("1699", 1), ("$16.99", 1), ("2900", 1), ("$29", 1),
])
def test_from_end_on(site, monkeypatch, capsys, offset, price, expected):
    monkeypatch.setattr(gate, "fetch_checkout", lambda: page(price))
    assert gate.main([str(site)], now=end(site) + offset) == expected
    output = capsys.readouterr().out
    assert output.startswith("PASS:" if expected == 0 else "FAIL:")
    if expected == 0:
        assert "3900 cents" in output
        assert "stated post-sale price" in output


@pytest.mark.parametrize("offset", [-1, 0])
@pytest.mark.parametrize("invalid", [None, "not JSON", "{}", '{"offers": []}'])
def test_missing_or_invalid_offer_file(site, capsys, offset, invalid):
    now = end(site) + offset
    path = site / "data" / "founding_offer.json"
    if invalid is None:
        path.unlink()
    else:
        path.write_text(invalid, encoding="utf-8")
    assert gate.main([str(site)], now=now) == 1
    output = capsys.readouterr().out
    assert output.startswith("FAIL:")
    assert "founding_offer.json" in output


@pytest.mark.parametrize("change,message", [
    (lambda d: d.update(offers=[]), "offer missing"),
    (lambda d: d.update(ends="bad date"), "cannot read"),
    (lambda d: d["offers"][0].update(prices=["no price"]), "$N.NN sale price"),
    (lambda d: d["offers"][0].update(what="No later price given."), "Then $N price"),
    (lambda d: d["offers"][0].update(what="Then $39.999"), "Then $N price"),
])
def test_unparseable_offer_fails(site, capsys, change, message):
    now = end(site)
    change_offer(site, change)
    assert gate.main([str(site)], now=now) == 1
    output = capsys.readouterr().out
    assert output.startswith("FAIL:")
    assert message in output


def test_prices_come_from_the_named_offer(site, monkeypatch):
    def change(data):
        data["offers"].reverse()  # The bundle must not become the product offer.
        offer = data["offers"][1]
        offer.update(prices=["sale $18.75, reference $29.00"], what="Sale. Then $41.25.")
    change_offer(site, change)
    for offset, price, expected in [(-1, "$18.75", 0), (-1, "$16.99", 1),
                                    (0, "$41.25", 0), (0, "$39", 1)]:
        monkeypatch.setattr(gate, "fetch_checkout", lambda: page(price))
        assert gate.main([str(site)], now=end(site) + offset) == expected


@pytest.mark.parametrize("offset", [-1, 0])
def test_no_price_fails(site, monkeypatch, capsys, offset):
    monkeypatch.setattr(gate, "fetch_checkout", page)
    assert gate.main([str(site)], now=end(site) + offset) == 1
    assert "(none)" in capsys.readouterr().out


@pytest.mark.parametrize("price", ["11699", "16990", "169900", "$116.99", "$16.990", "1699.50"])
def test_fractional_near_misses_fail(site, monkeypatch, price):
    monkeypatch.setattr(gate, "fetch_checkout", lambda: page(price))
    assert gate.main([str(site)], now=end(site) - 1) == 1


@pytest.mark.parametrize("content", ["Outlier 1699", page("1699").replace("Outlier", "Other")])
def test_existing_page_checks(site, monkeypatch, content):
    monkeypatch.setattr(gate, "fetch_checkout", lambda: content)
    assert gate.main([str(site)], now=end(site) - 1) == 1


def test_fetch_stays_get_only(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout=page("1699"))

    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    assert gate.fetch_checkout() == page("1699")
    assert calls == [(["curl", "-sL", "--max-time", "45", "-A", gate.UA, gate.CHECKOUT],
                      {"capture_output": True, "text": True, "timeout": 60})]


def test_default_clock(site, monkeypatch):
    monkeypatch.setattr(gate.time, "time", lambda: end(site))
    monkeypatch.setattr(gate, "fetch_checkout", lambda: page("3900"))
    assert gate.main([str(site)]) == 0


@pytest.mark.parametrize("name", ["index.html", "llms.txt"])
def test_sale_copy(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    assert "applies the discount" not in text
    assert SALE_LINE in text
    assert "Checkout charges the sale price." in text
