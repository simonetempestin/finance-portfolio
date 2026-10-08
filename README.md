# Quantitative Finance Toolkit

Three finance tools built in Python and served through a FastAPI backend, with a React frontend.

- **Portfolio optimisation**: Markowitz mean-variance, long-only. Minimum-volatility and maximum-Sharpe portfolios, efficient frontier, correlation matrix, per-stock drawdown.
- **DCF valuation**: FCF projection, WACC discounting, Gordon-growth terminal value, EV-to-equity bridge, WACC x terminal growth sensitivity table.
- **Option pricing**: Black-Scholes-Merton with dividend yield and Greeks, validated against a Monte Carlo simulation (200,000 paths, antithetic variates).

**Live demo:** https://simonetempestin!.github.io/finance-portfolio/
(The API runs on a free tier and sleeps when idle: the first request can take up to a minute.)

## Methodology

| Tool | Method |
|---|---|
| Portfolio | Annualised mean and covariance of daily simple returns (252 days). SLSQP optimisation with weights in [0,1] summing to 1. Frontier built by minimising variance for 30 target returns. |
| DCF | `FCF_t = FCF_0 (1+g)^t`, discounted at WACC. `TV = FCF_N (1+g_T) / (WACC - g_T)`. Equity value = EV - net debt. Base FCF = operating cash flow - capex (Yahoo Finance). |
| Options | Closed-form BSM price and Greeks. Monte Carlo under the risk-neutral measure. Vega is per vol point, theta per calendar day, rho per 1%. |

## Tests

```bash
cd backend && python -m pytest -q
```
Covers put-call parity, a textbook Black-Scholes benchmark (10.4506), Monte Carlo convergence to the closed form, a hand-computed DCF, portfolio weight constraints and optimality ordering, and the API endpoints with mocked market data.

## Run locally

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload            # http://localhost:8000/docs

# frontend (new terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev                          # http://localhost:5173
```

## Deploy

1. **Backend on Render**: New > Blueprint, select this repo (it reads `render.yaml`). Set `ALLOWED_ORIGINS` to `https://simonetempestin!.github.io`. Copy the service URL.
2. **Frontend on GitHub Pages**: repo Settings > Pages > Source: *GitHub Actions*. Then Settings > Secrets and variables > Actions > Variables > add `VITE_API_URL` = your Render URL. Push to `main` and the workflow publishes the site.

## Limitations

- Data from Yahoo Finance via `yfinance` (unofficial, can occasionally fail or change). Results are historical and educational, not investment advice.
- Mean-variance inputs are estimated from past data and are sensitive to the sample period.
- The DCF uses a single-stage growth rate and the latest reported FCF; it is not a substitute for a full operating model.

## Stack

Python 3.12, FastAPI, pandas, NumPy, SciPy, yfinance, pytest · React 18, Vite, Recharts · GitHub Actions, Render.
