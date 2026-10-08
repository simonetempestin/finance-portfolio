"""Quantitative finance API: portfolio optimisation, DCF valuation, option pricing."""
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from finance import data, dcf, options, portfolio

app = FastAPI(
    title="Finance Toolkit API",
    description="Portfolio optimisation (Markowitz), DCF valuation and option pricing.",
    version="1.0.0",
)

# Comma-separated list of allowed frontend origins, e.g. "https://user.github.io"
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/portfolio")
def portfolio_endpoint(
    tickers: str = Query(..., description="Comma-separated, e.g. AAPL,MSFT,JPM"),
    years: int = Query(3, ge=1, le=10),
    rf: float = Query(0.03, ge=0, le=0.2, description="Annual risk-free rate"),
):
    symbols = list(dict.fromkeys(t.strip().upper() for t in tickers.split(",") if t.strip()))
    if not 2 <= len(symbols) <= 10:
        raise HTTPException(400, "Provide between 2 and 10 tickers.")
    try:
        prices = data.get_prices(symbols, years)
        return portfolio.analyze(prices, rf)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(502, "Could not download market data. Check the tickers and retry.")


@app.get("/dcf/{ticker}")
def dcf_endpoint(
    ticker: str,
    growth: float = Query(0.08, ge=-0.5, le=1.0, description="FCF growth, explicit period"),
    terminal_growth: float = Query(0.025, ge=-0.05, le=0.06),
    wacc: float = Query(0.09, gt=0, le=0.3),
    years: int = Query(5, ge=1, le=15),
    fcf: float | None = Query(None, description="Override base-year free cash flow"),
):
    try:
        f = data.get_fundamentals(ticker)
        base = fcf if fcf is not None else f["fcf"]
        if base <= 0:
            raise ValueError("Base free cash flow is not positive: DCF is not meaningful. Pass an 'fcf' override.")
        args = (base, growth, terminal_growth, wacc, years, f["net_debt"], f["shares"])
        result = dcf.dcf_value(*args)
        price = f["price"]
        return {
            "company": {k: f[k] for k in ("ticker", "name", "currency", "price")},
            "inputs": {"fcf0": base, "growth": growth, "terminal_growth": terminal_growth,
                       "wacc": wacc, "years": years, "net_debt": f["net_debt"], "shares": f["shares"]},
            **result,
            "upside": (result["value_per_share"] / price - 1) if price else None,
            "sensitivity": dcf.sensitivity(*args),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(502, "Could not retrieve fundamentals for this ticker.")


@app.get("/options")
def options_endpoint(
    spot: float = Query(100, gt=0),
    strike: float = Query(100, gt=0),
    maturity: float = Query(1.0, gt=0, le=10, description="Years"),
    rate: float = Query(0.03, ge=-0.05, le=0.3),
    vol: float = Query(0.2, gt=0, le=3),
    dividend: float = Query(0.0, ge=0, le=0.3),
    kind: str = Query("call", pattern="^(call|put)$"),
):
    args = (spot, strike, maturity, rate, vol, dividend, kind)
    bs = options.black_scholes(*args)
    mc = options.monte_carlo(*args)
    return {"black_scholes": bs, "monte_carlo": mc, "payoff": options.payoff_curve(*args)}
