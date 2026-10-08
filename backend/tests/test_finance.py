import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from finance import dcf, options, portfolio
from main import app


def test_put_call_parity():
    S, K, T, r, s, q = 100, 95, 1.5, 0.03, 0.25, 0.01
    c = options.black_scholes(S, K, T, r, s, q, "call")["price"]
    p = options.black_scholes(S, K, T, r, s, q, "put")["price"]
    assert c - p == pytest.approx(S * np.exp(-q * T) - K * np.exp(-r * T), abs=1e-9)


def test_black_scholes_reference_value():
    # Hull textbook-style benchmark: S=100,K=100,T=1,r=5%,sigma=20% -> call ~10.4506
    assert options.black_scholes(100, 100, 1, 0.05, 0.2)["price"] == pytest.approx(10.4506, abs=1e-3)


def test_monte_carlo_matches_closed_form():
    bs = options.black_scholes(100, 105, 1, 0.03, 0.2)["price"]
    mc = options.monte_carlo(100, 105, 1, 0.03, 0.2)
    assert abs(mc["price"] - bs) < 4 * mc["std_error"]


def test_dcf_known_value():
    r = dcf.dcf_value(100, 0.0, 0.0, 0.10, 1, 0, 1)
    # FCF=100 each year, 1y explicit + perpetuity: EV = 100/1.1 + (100/0.10)/1.1 = 1000
    assert r["enterprise_value"] == pytest.approx(1000.0)


def test_dcf_rejects_wacc_below_growth():
    with pytest.raises(ValueError):
        dcf.dcf_value(100, 0.05, 0.05, 0.04, 5, 0, 1)


def test_portfolio_weights_and_ordering():
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2022-01-03", periods=500)
    rets = rng.normal([0.0004, 0.0006, 0.0002], [0.01, 0.02, 0.008], size=(500, 3))
    prices = pd.DataFrame(100 * np.cumprod(1 + rets, axis=0), index=idx, columns=["A", "B", "C"])
    out = portfolio.analyze(prices, rf=0.02)
    for key in ("max_sharpe", "min_vol"):
        assert sum(out[key]["weights"].values()) == pytest.approx(1.0, abs=1e-6)
    assert out["max_sharpe"]["sharpe"] >= out["equal_weight"]["sharpe"] - 1e-9
    assert out["min_vol"]["vol"] <= out["equal_weight"]["vol"] + 1e-9


def test_api_options_and_health():
    c = TestClient(app)
    assert c.get("/health").json() == {"status": "ok"}
    r = c.get("/options?spot=100&strike=100&maturity=1&rate=0.05&vol=0.2&kind=call")
    assert r.status_code == 200
    assert r.json()["black_scholes"]["price"] == pytest.approx(10.4506, abs=1e-3)


def test_api_portfolio_and_dcf_with_mocked_data(monkeypatch):
    from finance import data
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("2023-01-02", periods=400)
    px = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0.0004, 0.012, (400, 3)), axis=0),
                      index=idx, columns=["AAA", "BBB", "CCC"])
    monkeypatch.setattr(data, "get_prices", lambda tickers, years: px)
    monkeypatch.setattr(data, "get_fundamentals", lambda t: {
        "ticker": "TEST", "name": "Test Corp", "currency": "USD",
        "fcf": 1_000.0, "net_debt": 500.0, "shares": 100.0, "price": 120.0})
    c = TestClient(app)
    r = c.get("/portfolio?tickers=AAA,BBB,CCC&years=2&rf=0.02")
    assert r.status_code == 200 and len(r.json()["frontier"]) == 30
    assert c.get("/portfolio?tickers=AAA").status_code == 400
    d = c.get("/dcf/TEST?growth=0.05&wacc=0.09&terminal_growth=0.02&years=5")
    assert d.status_code == 200
    body = d.json()
    assert body["value_per_share"] > 0 and len(body["sensitivity"]["values"]) == 5
    assert c.get("/dcf/TEST?wacc=0.02&terminal_growth=0.03").status_code == 400
