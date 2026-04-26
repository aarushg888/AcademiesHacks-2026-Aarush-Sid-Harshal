"""
market_data.py — Real-time fundamentals via yfinance with safe fallbacks.
"""
import time
from typing import Optional

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

# Simple in-memory cache (5 min TTL) — yfinance is rate-limited
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 300


def _fmt_b(v) -> str:
    """Format large numbers as $X.XB / $X.XM."""
    try:
        v = float(v)
        if v >= 1e12: return f"${v/1e12:.2f}T"
        if v >= 1e9:  return f"${v/1e9:.1f}B"
        if v >= 1e6:  return f"${v/1e6:.0f}M"
        return f"${v:,.0f}"
    except Exception:
        return "—"


def _fmt_pct(v) -> str:
    try:
        return f"{float(v)*100:.1f}%"
    except Exception:
        return "—"


def _fmt_num(v, suffix="") -> str:
    try:
        return f"{float(v):.2f}{suffix}"
    except Exception:
        return "—"


def get_fundamentals(ticker: str) -> Optional[dict]:
    """Return live fundamentals dict or None on failure."""
    if not YF_AVAILABLE or not ticker:
        return None

    ticker = ticker.upper().strip()
    now = time.time()
    if ticker in _cache:
        ts, data = _cache[ticker]
        if now - ts < CACHE_TTL:
            return data

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return None

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose") or price
        change_pct = ((price - prev_close) / prev_close * 100) if (price and prev_close) else 0

        # 30-day price history for sparkline
        hist = t.history(period="3mo")
        sparkline = []
        if not hist.empty:
            closes = hist["Close"].tolist()
            # Sample down to ~25 points
            step = max(1, len(closes) // 25)
            sparkline = [round(float(c), 2) for c in closes[::step]][-25:]

        data = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "price": round(float(price), 2) if price else None,
            "change_pct": round(change_pct, 2),
            "market_cap": info.get("marketCap"),
            "market_cap_fmt": _fmt_b(info.get("marketCap")),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio") or info.get("trailingPegRatio"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "free_cashflow": info.get("freeCashflow"),
            "free_cashflow_fmt": _fmt_b(info.get("freeCashflow")),
            "total_cash": info.get("totalCash"),
            "total_cash_fmt": _fmt_b(info.get("totalCash")),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "fifty_two_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_low": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "sparkline": sparkline,
            "live": True,
        }

        _cache[ticker] = (now, data)
        return data
    except Exception as e:
        print(f"[yfinance] {ticker} fetch failed: {e}")
        return None


def fundamentals_to_prompt(f: dict) -> str:
    """Format live fundamentals as a clean text block for the LLM."""
    if not f:
        return ""
    lines = [f"=== LIVE MARKET DATA: {f['ticker']} ({f.get('name','')}) ===",
             f"Price: ${f['price']} ({'+' if f['change_pct']>=0 else ''}{f['change_pct']}% today)" if f.get('price') else "",
             f"Market Cap: {f['market_cap_fmt']}",
             f"Sector: {f.get('sector','—')} / {f.get('industry','—')}"]
    if f.get('pe_ratio'):     lines.append(f"P/E (trailing): {_fmt_num(f['pe_ratio'])}")
    if f.get('forward_pe'):   lines.append(f"P/E (forward):  {_fmt_num(f['forward_pe'])}")
    if f.get('peg_ratio'):    lines.append(f"PEG Ratio: {_fmt_num(f['peg_ratio'])}")
    if f.get('profit_margin') is not None:    lines.append(f"Profit Margin: {_fmt_pct(f['profit_margin'])}")
    if f.get('operating_margin') is not None: lines.append(f"Operating Margin: {_fmt_pct(f['operating_margin'])}")
    if f.get('roe') is not None:              lines.append(f"ROE: {_fmt_pct(f['roe'])}")
    if f.get('debt_to_equity') is not None:   lines.append(f"Debt/Equity: {_fmt_num(f['debt_to_equity'])}")
    if f.get('revenue_growth') is not None:   lines.append(f"Revenue Growth (YoY): {_fmt_pct(f['revenue_growth'])}")
    if f.get('earnings_growth') is not None:  lines.append(f"Earnings Growth (YoY): {_fmt_pct(f['earnings_growth'])}")
    if f.get('free_cashflow'):                lines.append(f"Free Cash Flow: {f['free_cashflow_fmt']}")
    if f.get('total_cash'):                   lines.append(f"Total Cash: {f['total_cash_fmt']}")
    if f.get('beta') is not None:             lines.append(f"Beta: {_fmt_num(f['beta'])}")
    if f.get('fifty_two_high'):
        lines.append(f"52W Range: ${f.get('fifty_two_low','—')} – ${f.get('fifty_two_high','—')}")
    return "\n".join(l for l in lines if l)


def detect_ticker(text: str) -> Optional[str]:
    """Pull ticker from scenario text. Looks for (XYZ) pattern or known tickers."""
    if not text:
        return None
    import re
    # Match (TICKER) pattern first
    m = re.search(r'\(([A-Z]{1,5}(?:\.[A-Z])?)\)', text)
    if m:
        return m.group(1)
    # Match standalone uppercase tokens (NVDA, AAPL etc.)
    candidates = re.findall(r'\b[A-Z]{2,5}\b', text)
    # Filter out common non-ticker uppercase words
    blocklist = {"YOY", "AI", "P/E", "PEG", "ROE", "USD", "EPS", "GDP", "CEO", "CFO", "AAA",
                 "BUY", "SELL", "HOLD", "USA", "EU", "UK", "EV"}
    for c in candidates:
        if c not in blocklist and len(c) >= 2:
            return c
    return None
