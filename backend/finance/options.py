"""European option pricing: Black-Scholes-Merton (closed form) and Monte Carlo."""
import numpy as np
from scipy.stats import norm


def _d1_d2(S, K, T, r, sigma, q):
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return d1, d1 - sigma * np.sqrt(T)


def black_scholes(S, K, T, r, sigma, q=0.0, kind="call") -> dict:
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    disc_r, disc_q = np.exp(-r * T), np.exp(-q * T)
    pdf = norm.pdf(d1)
    if kind == "call":
        price = S * disc_q * norm.cdf(d1) - K * disc_r * norm.cdf(d2)
        delta = disc_q * norm.cdf(d1)
        theta = (-S * disc_q * pdf * sigma / (2 * np.sqrt(T))
                 - r * K * disc_r * norm.cdf(d2) + q * S * disc_q * norm.cdf(d1))
        rho = K * T * disc_r * norm.cdf(d2)
    else:
        price = K * disc_r * norm.cdf(-d2) - S * disc_q * norm.cdf(-d1)
        delta = -disc_q * norm.cdf(-d1)
        theta = (-S * disc_q * pdf * sigma / (2 * np.sqrt(T))
                 + r * K * disc_r * norm.cdf(-d2) - q * S * disc_q * norm.cdf(-d1))
        rho = -K * T * disc_r * norm.cdf(-d2)
    gamma = disc_q * pdf / (S * sigma * np.sqrt(T))
    vega = S * disc_q * pdf * np.sqrt(T)
    return {
        "price": float(price),
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega / 100),    # per 1 vol point
        "theta": float(theta / 365),  # per calendar day
        "rho": float(rho / 100),      # per 1% rate move
    }


def monte_carlo(S, K, T, r, sigma, q=0.0, kind="call", n=200_000, seed=42) -> dict:
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n // 2)
    z = np.concatenate([z, -z])  # antithetic variates
    ST = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)
    payoff = np.maximum(ST - K, 0) if kind == "call" else np.maximum(K - ST, 0)
    disc = np.exp(-r * T) * payoff
    return {"price": float(disc.mean()), "std_error": float(disc.std(ddof=1) / np.sqrt(len(disc))), "paths": int(len(disc))}


def payoff_curve(S, K, T, r, sigma, q=0.0, kind="call", points=41) -> list:
    out = []
    for s in np.linspace(0.5 * K, 1.5 * K, points):
        intrinsic = max(s - K, 0) if kind == "call" else max(K - s, 0)
        out.append({"spot": float(s), "payoff": float(intrinsic),
                    "value": black_scholes(s, K, T, r, sigma, q, kind)["price"]})
    return out
