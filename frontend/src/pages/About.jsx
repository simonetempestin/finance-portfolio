import { PROFILE } from "../profile.js";

export default function About() {
  return (
    <section className="prose">
      <h2>About this project</h2>
      <p>
        Three tools I built to apply what I study in corporate finance, asset management and derivatives. Each runs live on
        market data through a Python API.
      </p>
      <h3>Portfolio optimisation</h3>
      <p>
        Downloads adjusted prices, estimates annualised returns and covariance, and solves the long-only mean-variance
        problem with SLSQP: minimum-volatility and maximum-Sharpe portfolios, the efficient frontier, and a cloud of
        random portfolios for comparison.
      </p>
      <h3>DCF valuation</h3>
      <p>
        Projects free cash flow, discounts at WACC, adds a Gordon-growth terminal value, bridges from enterprise value to
        equity value through net debt, and shows how the result moves with WACC and terminal growth.
      </p>
      <h3>Option pricing</h3>
      <p>
        Black-Scholes-Merton with dividend yield and the Greeks, cross-checked against a 200,000-path Monte Carlo with
        antithetic variates. Put-call parity and convergence are covered by unit tests.
      </p>
      <h3>Stack</h3>
      <p>Python (FastAPI, pandas, NumPy, SciPy, yfinance, pytest), React (Vite, Recharts), GitHub Actions.</p>
      <p>
        <a href={PROFILE.repo} target="_blank" rel="noreferrer">Source code on GitHub</a>
      </p>
      <p className="note">
        Educational tools using historical data from Yahoo Finance. Nothing here is investment advice.
      </p>
    </section>
  );
}
