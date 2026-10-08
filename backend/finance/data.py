"""Market-data access (Yahoo Finance via yfinance) with a small in-memory cache."""
import time
import pandas as pd
import yfinance as yf

_CACHE: dict = {}
_TTL = 60 * 30  # 30 minutes


def _cached(key, loader):
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]
    value = loader()
    _CACHE[key] = (time.time(), value)
    return value


def get_prices(tickers: list[str], years: int = 3) -> pd.DataFrame:
    """Adjusted close prices, one column per ticker."""
    key = ("prices", tuple(tickers), years)

    def load():
        df = yf.download(
            tickers, period=f"{years}y", auto_adjust=True, progress=False
        )["Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
        df = df.dropna(how="all").dropna(axis=1, how="all").ffill().dropna()
        return df

    df = _cached(key, load)
    if df.shape[1] < 2:
        raise ValueError("Need at least 2 tickers with valid price data.")
    return df


def get_fundamentals(ticker: str) -> dict:
    """Latest free cash flow, net debt, shares and price for a DCF."""

    def load():
        t = yf.Ticker(ticker)
        cf = t.cashflow
        if cf is None or cf.empty:
            raise ValueError(f"No cash-flow data found for '{ticker}'.")
        if "Free Cash Flow" in cf.index:
            fcf = float(cf.loc["Free Cash Flow"].dropna().iloc[0])
        else:
            ocf = float(cf.loc["Operating Cash Flow"].dropna().iloc[0])
            capex = float(cf.loc["Capital Expenditure"].dropna().iloc[0])
            fcf = ocf + capex  # capex is reported as a negative number
        info = t.info or {}
        debt = float(info.get("totalDebt") or 0.0)
        cash = float(info.get("totalCash") or 0.0)
        shares = info.get("sharesOutstanding")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not shares:
            raise ValueError(f"No share count found for '{ticker}'.")
        return {
            "ticker": ticker.upper(),
            "name": info.get("longName") or ticker.upper(),
            "currency": info.get("currency", "USD"),
            "fcf": fcf,
            "net_debt": debt - cash,
            "shares": float(shares),
            "price": float(price) if price else None,
        }

    return _cached(("fund", ticker.upper()), load)
