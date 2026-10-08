"""Mean-variance portfolio analytics (Markowitz)."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

TRADING_DAYS = 252


def _perf(w, mu, cov, rf):
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ cov @ w))
    return {"return": ret, "vol": vol, "sharpe": (ret - rf) / vol if vol > 0 else 0.0}


def _optimise(objective, n, extra=()):
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}, *extra]
    res = minimize(
        objective,
        np.full(n, 1 / n),
        method="SLSQP",
        bounds=[(0, 1)] * n,
        constraints=cons,
    )
    return res.x


def max_drawdown(series: pd.Series) -> float:
    running_max = series.cummax()
    return float((series / running_max - 1).min())


def analyze(prices: pd.DataFrame, rf: float = 0.03, n_random: int = 600, seed: int = 42) -> dict:
    tickers = list(prices.columns)
    n = len(tickers)
    rets = prices.pct_change().dropna()
    mu = rets.mean().values * TRADING_DAYS
    cov = rets.cov().values * TRADING_DAYS

    # Individual assets
    assets = []
    for i, t in enumerate(tickers):
        vol = float(np.sqrt(cov[i, i]))
        assets.append({
            "ticker": t,
            "return": float(mu[i]),
            "vol": vol,
            "sharpe": float((mu[i] - rf) / vol),
            "max_drawdown": max_drawdown(prices[t]),
        })

    # Key portfolios
    w_sharpe = _optimise(lambda w: -_perf(w, mu, cov, rf)["sharpe"], n)
    w_minvol = _optimise(lambda w: w @ cov @ w, n)
    w_equal = np.full(n, 1 / n)

    def pack(w):
        return {**_perf(w, mu, cov, rf), "weights": {t: float(x) for t, x in zip(tickers, w)}}

    # Efficient frontier
    r_min, r_max = _perf(w_minvol, mu, cov, rf)["return"], float(mu.max())
    frontier = []
    for target in np.linspace(r_min, r_max, 30):
        w = _optimise(
            lambda w: w @ cov @ w, n,
            extra=[{"type": "eq", "fun": lambda w, t=target: w @ mu - t}],
        )
        p = _perf(w, mu, cov, rf)
        frontier.append({"return": p["return"], "vol": p["vol"]})

    # Random portfolios (cloud for the chart)
    rng = np.random.default_rng(seed)
    cloud = []
    for w in rng.dirichlet(np.ones(n), size=n_random):
        p = _perf(w, mu, cov, rf)
        cloud.append({"return": p["return"], "vol": p["vol"], "sharpe": p["sharpe"]})

    corr = rets.corr()
    return {
        "tickers": tickers,
        "period": {"start": str(prices.index[0].date()), "end": str(prices.index[-1].date())},
        "risk_free": rf,
        "assets": assets,
        "max_sharpe": pack(w_sharpe),
        "min_vol": pack(w_minvol),
        "equal_weight": pack(w_equal),
        "frontier": frontier,
        "cloud": cloud,
        "correlation": {"labels": tickers, "matrix": corr.round(3).values.tolist()},
    }
