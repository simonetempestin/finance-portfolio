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


def _latest(df, names):
    """First non-null value of the first matching row in a yfinance statement."""
    if df is None or getattr(df, "empty", True):
        return None
    for name in names:
        if name in df.index:
            series = df.loc[name].dropna()
            if len(series):
                return float(series.iloc[0])
    return None


def _safe(fn, default=None):
    try:
        value = fn()
        return default if value is None else value
    except Exception:
        return default


def get_fundamentals(ticker: str) -> dict:
    """Latest free cash flow, net debt, shares and price for a DCF.

    Yahoo's `info` endpoint is often blocked or empty on cloud servers, so every
    field has a fallback to the financial statements or `fast_info`.
    """

    def load():
        t = yf.Ticker(ticker)

        # Free cash flow
        cf = _safe(lambda: t.cashflow)
        fcf = _latest(cf, ["Free Cash Flow"])
        if fcf is None:
            ocf = _latest(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"])
            capex = _latest(cf, ["Capital Expenditure", "Capital Expenditures"])
            if ocf is None:
                raise ValueError(f"No cash-flow data found for '{ticker}'. Check the ticker symbol.")
            fcf = ocf + (capex or 0.0)  # capex is reported as a negative number

        # Balance sheet: debt, cash, shares
        bs = _safe(lambda: t.balance_sheet)
        info = _safe(lambda: t.info, {}) or {}
        fast = _safe(lambda: t.fast_info)

        debt = _latest(bs, ["Total Debt"])
        if debt is None:
            debt = float(info.get("totalDebt") or 0.0)
        cash = _latest(bs, ["Cash Cash Equivalents And Short Term Investments",
                            "Cash And Cash Equivalents", "Cash Financial"])
        if cash is None:
            cash = float(info.get("totalCash") or 0.0)

        shares = (
            _safe(lambda: fast["shares"])
            or info.get("sharesOutstanding")
            or _latest(bs, ["Ordinary Shares Number", "Share Issued"])
        )
        if not shares:
            raise ValueError(
                f"Could not find the share count for '{ticker}'. "
                "Yahoo Finance may be limiting requests: wait a minute and retry."
            )

        price = (
            _safe(lambda: fast["last_price"])
            or info.get("currentPrice")
            or info.get("regularMarketPrice")
        )
        if not price:
            hist = _safe(lambda: t.history(period="5d")["Close"].dropna())
            price = float(hist.iloc[-1]) if hist is not None and len(hist) else None

        return {
            "ticker": ticker.upper(),
            "name": info.get("longName") or info.get("shortName") or ticker.upper(),
            "currency": _safe(lambda: fast["currency"]) or info.get("currency", "USD"),
            "fcf": float(fcf),
            "net_debt": float(debt) - float(cash),
            "shares": float(shares),
            "price": float(price) if price else None,
        }

    return _cached(("fund", ticker.upper()), load)
