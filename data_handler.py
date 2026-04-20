import yfinance as yf
import pandas as pd
import json
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Chemins données locales
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent
_DATA_DIR = _ROOT / "data"
_ACTIONS_DIR = _DATA_DIR / "actions"
_INDICES_DIR = _DATA_DIR / "indices"
_SOCIETE_DIR = _DATA_DIR / "societes"

_INDEX_SUFFIXES = ("^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^FCHI", "^GDAXI",
                   "^N225", "=X", "=F", "-USD")


def _is_index(ticker: str) -> bool:
    return ticker.startswith("^") or ticker.endswith("=X") or ticker.endswith("=F") or ticker.endswith("-USD")


def _safe_name(ticker: str) -> str:
    return ticker.replace(".", "_").replace("^", "IDX_").replace("=", "_").replace("-", "_")


def _local_csv_path(ticker: str) -> Path:
    d = _INDICES_DIR if _is_index(ticker) else _ACTIONS_DIR
    return d / f"{_safe_name(ticker)}_historique.csv"


def _local_info_path(ticker: str) -> Path:
    return _SOCIETE_DIR / f"{_safe_name(ticker)}_info.json"


def _load_local_history(ticker: str, period: str = "1y") -> pd.DataFrame | None:
    """Charge l'historique local CSV et filtre selon la période demandée."""
    path = _local_csv_path(ticker)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, sep=";", decimal=",", parse_dates=["Date"])
        df = df.sort_values("Date").set_index("Date")
        # Mapper la période vers un nombre de jours
        period_days = {
            "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
            "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 99999,
        }
        days = period_days.get(period, 365)
        if days < 99999:
            cutoff = df.index.max() - timedelta(days=days)
            df = df.loc[df.index >= cutoff]
        # Renommer vers format yfinance
        col_map = {"Ouverture": "Open", "Plus_Haut": "High", "Plus_Bas": "Low",
                   "Cloture": "Close", "Volume_Titres": "Volume"}
        df = df.rename(columns=col_map)
        keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        return df[keep] if not df.empty else None
    except Exception:
        return None


def _load_local_info(ticker: str) -> dict:
    """Charge le JSON info société local."""
    path = _local_info_path(ticker)
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def has_local_data() -> bool:
    """Vérifie si le dossier data/ contient des CSV."""
    return (_ACTIONS_DIR.exists() and any(_ACTIONS_DIR.glob("*_historique.csv"))) or \
           (_INDICES_DIR.exists() and any(_INDICES_DIR.glob("*_historique.csv")))
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Chemins données locales
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent
_DATA_DIR = _ROOT / "data"
_ACTIONS_DIR = _DATA_DIR / "actions"
_INDICES_DIR = _DATA_DIR / "indices"
_SOCIETE_DIR = _DATA_DIR / "societes"

_INDEX_SUFFIXES = ("^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^FCHI", "^GDAXI",
                   "^N225", "=X", "=F", "-USD")


def _is_index(ticker: str) -> bool:
    return ticker.startswith("^") or ticker.endswith("=X") or ticker.endswith("=F") or ticker.endswith("-USD")


def _safe_name(ticker: str) -> str:
    return ticker.replace(".", "_").replace("^", "IDX_").replace("=", "_").replace("-", "_")


def _local_csv_path(ticker: str) -> Path:
    d = _INDICES_DIR if _is_index(ticker) else _ACTIONS_DIR
    return d / f"{_safe_name(ticker)}_historique.csv"


def _local_info_path(ticker: str) -> Path:
    return _SOCIETE_DIR / f"{_safe_name(ticker)}_info.json"


def _load_local_history(ticker: str, period: str = "1y") -> pd.DataFrame | None:
    """Charge l'historique local CSV et filtre selon la période demandée."""
    path = _local_csv_path(ticker)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, sep=";", decimal=",", parse_dates=["Date"])
        df = df.sort_values("Date").set_index("Date")
        # Mapper la période vers un nombre de jours
        period_days = {
            "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
            "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 99999,
        }
        days = period_days.get(period, 365)
        if days < 99999:
            cutoff = df.index.max() - timedelta(days=days)
            df = df.loc[df.index >= cutoff]
        # Renommer vers format yfinance
        col_map = {"Ouverture": "Open", "Plus_Haut": "High", "Plus_Bas": "Low",
                   "Cloture": "Close", "Volume_Titres": "Volume"}
        df = df.rename(columns=col_map)
        keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        return df[keep] if not df.empty else None
    except Exception:
        return None


def _load_local_info(ticker: str) -> dict:
    """Charge le JSON info société local."""
    path = _local_info_path(ticker)
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def has_local_data() -> bool:
    """Vérifie si le dossier data/ contient des CSV."""
    return (_ACTIONS_DIR.exists() and any(_ACTIONS_DIR.glob("*_historique.csv"))) or \
           (_INDICES_DIR.exists() and any(_INDICES_DIR.glob("*_historique.csv")))

# ============================================================
# UNIVERS D'ACTIFS PAR SECTEUR
# ============================================================
SECTOR_TICKERS = {
    "Technology": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "META", "ORCL", "ADBE", "CRM", "CSCO",
        "INTC", "AMD", "AVGO", "QCOM", "TXN", "IBM", "NOW", "INTU", "MU", "AMAT",
        "LRCX", "KLAC", "ADI", "PANW", "CRWD", "SNOW", "PLTR", "SHOP", "UBER",
    ],
    "Financial Services": [
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "USB",
        "PNC", "TFC", "COF", "BK", "PYPL", "BRK-B", "AIG", "MET", "PRU",
    ],
    "Healthcare": [
        "JNJ", "UNH", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "DHR", "BMY",
        "AMGN", "GILD", "CVS", "CI", "ELV", "MDT", "ISRG", "VRTX", "REGN",
        "BIIB", "ZTS", "HCA", "SYK", "BDX", "BSX",
    ],
    "Consumer Cyclical": [
        "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG",
        "ABNB", "MAR", "F", "GM", "CMG", "ROST", "ORLY", "AZO", "YUM", "DHI",
        "LEN", "EBAY", "ETSY",
    ],
    "Consumer Defensive": [
        "WMT", "PG", "KO", "PEP", "COST", "MDLZ", "PM", "MO", "CL", "TGT",
        "KMB", "GIS", "SYY", "KHC", "STZ", "HSY", "KR", "ADM", "EL",
    ],
    "Communication Services": [
        "GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "TMUS", "CHTR",
        "EA", "TTWO", "WBD", "PARA", "SPOT", "PINS", "SNAP",
    ],
    "Energy": [
        "XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY",
        "HES", "WMB", "KMI", "OKE", "HAL", "BKR", "DVN", "FANG",
    ],
    "Industrials": [
        "BA", "CAT", "HON", "UNP", "RTX", "GE", "LMT", "DE", "UPS", "FDX",
        "NOC", "GD", "MMM", "ETN", "EMR", "ITW", "CSX", "NSC", "WM", "RSG",
        "PH", "CMI", "PCAR",
    ],
    "Basic Materials": [
        "LIN", "SHW", "APD", "FCX", "ECL", "NEM", "DOW", "DD", "NUE", "PPG",
        "MLM", "VMC", "STLD", "CF", "MOS", "ALB",
    ],
    "Real Estate": [
        "PLD", "AMT", "EQIX", "CCI", "PSA", "O", "SPG", "WELL", "DLR", "VICI",
        "AVB", "EQR", "EXR", "SBAC", "ARE", "INVH",
    ],
    "Utilities": [
        "NEE", "DUK", "SO", "SRE", "AEP", "D", "EXC", "XEL", "PEG", "ED",
        "WEC", "ES", "AWK", "PCG", "EIX",
    ],
    "Crypto & ETF": [
        "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD",
        "DOGE-USD", "SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "GLD", "SLV",
    ],
    "Indices & FX": [
        "^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^FCHI", "^GDAXI", "^N225",
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "CL=F", "GC=F", "SI=F",
    ],
}


def get_sector_options():
    return [{"label": s.upper(), "value": s} for s in SECTOR_TICKERS.keys()]


def get_ticker_options(sector):
    tickers = SECTOR_TICKERS.get(sector, [])
    options = []
    for t in tickers:
        name = _safe_short_name(t)
        label = f"{t} — {name}" if name else t
        options.append({"label": label, "value": t})
    return options


@lru_cache(maxsize=512)
def _safe_short_name(ticker):
    try:
        info = yf.Ticker(ticker).info or {}
        return info.get("shortName") or info.get("longName") or ""
    except Exception:
        return ""


def fetch_data(ticker, period="1y", interval="1d"):
    """Récupère l'historique OHLCV — local CSV d'abord, sinon yfinance."""
    # 1. Essayer les données locales
    if interval == "1d":
        local = _load_local_history(ticker, period)
        if local is not None and not local.empty:
            return local
    # 2. Fallback yfinance
    try:
        data = yf.download(
            ticker, period=period, interval=interval,
            progress=False, auto_adjust=True,
        )
        if data is None or data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        print(f"[fetch_data] Erreur {ticker}: {e}")
        return None


def calculate_indicators(df):
    """Indicateurs techniques complets : SMA, EMA, Bollinger, RSI, Stochastic RSI,
    MACD, ATR, ADX, CCI, Williams %R, Stochastic, OBV, VWAP, Ichimoku, Parabolic SAR,
    CMF, MFI, ROC, TRIX, DPO, Keltner, Donchian, Ulcer Index, Force Index, Aroon."""
    if df is None or df.empty:
        return None
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df.get("Volume", pd.Series(0, index=df.index))

    # ── SMA ──
    for n in [10, 20, 50, 100, 200]:
        df[f"SMA_{n}"] = close.rolling(n).mean()

    # ── EMA ──
    for n in [9, 12, 20, 26, 50, 200]:
        df[f"EMA_{n}"] = close.ewm(span=n, adjust=False).mean()

    # ── Bollinger Bands ──
    df["BB_Middle"] = df["SMA_20"]
    std20 = close.rolling(20).std()
    df["BB_Upper"] = df["BB_Middle"] + 2 * std20
    df["BB_Lower"] = df["BB_Middle"] - 2 * std20
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"] * 100
    df["BB_PctB"] = (close - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"])

    # ── RSI ──
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    # ── Stochastic RSI ──
    rsi_s = df["RSI"]
    rsi_min = rsi_s.rolling(14).min()
    rsi_max = rsi_s.rolling(14).max()
    stoch_rsi = (rsi_s - rsi_min) / (rsi_max - rsi_min).replace(0, 1e-9)
    df["StochRSI_K"] = stoch_rsi.rolling(3).mean() * 100
    df["StochRSI_D"] = df["StochRSI_K"].rolling(3).mean()

    # ── MACD ──
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # ── ATR ──
    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["TR"] = tr
    df["ATR"] = tr.rolling(14).mean()

    # ── ADX (Average Directional Index) ──
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    atr14 = df["ATR"].replace(0, 1e-9)
    plus_di = 100 * plus_dm.rolling(14).mean() / atr14
    minus_di = 100 * minus_dm.rolling(14).mean() / atr14
    df["Plus_DI"] = plus_di
    df["Minus_DI"] = minus_di
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9) * 100
    df["ADX"] = dx.rolling(14).mean()

    # ── CCI (Commodity Channel Index) ──
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(20).mean()
    mad = tp.rolling(20).apply(lambda x: (x - x.mean()).abs().mean(), raw=True)
    df["CCI"] = (tp - sma_tp) / (0.015 * mad.replace(0, 1e-9))

    # ── Williams %R ──
    h14 = high.rolling(14).max()
    l14 = low.rolling(14).min()
    df["Williams_R"] = -100 * (h14 - close) / (h14 - l14).replace(0, 1e-9)

    # ── Stochastic Oscillator ──
    df["Stoch_K"] = 100 * (close - l14) / (h14 - l14).replace(0, 1e-9)
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean()

    # ── OBV (On-Balance Volume) ──
    obv_sign = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    df["OBV"] = (obv_sign * volume).cumsum()

    # ── VWAP (Volume Weighted Average Price) ──
    cum_vol = volume.cumsum()
    cum_tp_vol = (tp * volume).cumsum()
    df["VWAP"] = cum_tp_vol / cum_vol.replace(0, 1e-9)

    # ── Ichimoku Cloud ──
    h9 = high.rolling(9).max()
    l9 = low.rolling(9).min()
    df["Ichimoku_Tenkan"] = (h9 + l9) / 2  # Conversion Line
    h26 = high.rolling(26).max()
    l26 = low.rolling(26).min()
    df["Ichimoku_Kijun"] = (h26 + l26) / 2  # Base Line
    df["Ichimoku_SpanA"] = ((df["Ichimoku_Tenkan"] + df["Ichimoku_Kijun"]) / 2).shift(26)
    h52 = high.rolling(52).max()
    l52 = low.rolling(52).min()
    df["Ichimoku_SpanB"] = ((h52 + l52) / 2).shift(26)
    df["Ichimoku_Chikou"] = close.shift(-26)

    # ── Parabolic SAR (simplified) ──
    df["PSAR"] = _parabolic_sar(high, low, close)

    # ── CMF (Chaikin Money Flow) ──
    mfv = ((close - low) - (high - close)) / (high - low).replace(0, 1e-9) * volume
    df["CMF"] = mfv.rolling(20).sum() / volume.rolling(20).sum().replace(0, 1e-9)

    # ── MFI (Money Flow Index) ──
    raw_mf = tp * volume
    pos_mf = raw_mf.where(tp > tp.shift(), 0).rolling(14).sum()
    neg_mf = raw_mf.where(tp < tp.shift(), 0).rolling(14).sum()
    mf_ratio = pos_mf / neg_mf.replace(0, 1e-9)
    df["MFI"] = 100 - (100 / (1 + mf_ratio))

    # ── ROC (Rate of Change) ──
    df["ROC"] = (close / close.shift(12) - 1) * 100

    # ── TRIX ──
    ema1 = close.ewm(span=15, adjust=False).mean()
    ema2 = ema1.ewm(span=15, adjust=False).mean()
    ema3 = ema2.ewm(span=15, adjust=False).mean()
    df["TRIX"] = ema3.pct_change() * 100

    # 1. Essayer le JSON local
    local = _load_local_info(ticker)
    if local:
        return {
            "shortName": local.get("Nom_Court") or local.get("Nom"),
            "longName": local.get("Nom"),
            "symbol": local.get("ticker", ticker),
            "sector": local.get("Secteur"),
            "industry": local.get("Industrie"),
            "country": local.get("Pays"),
            "city": local.get("Ville"),
            "website": local.get("Site_Web"),
            "currency": local.get("Devise"),
            "exchange": local.get("Bourse"),
            "fullTimeEmployees": local.get("Employes"),
            "longBusinessSummary": local.get("Description"),
        }
    # 2. Fallback yfinance
    # ── DPO (Detrended Price Oscillator) ──
    n_dpo = 20
    df["DPO"] = close.shift(n_dpo // 2 + 1) - close.rolling(n_dpo).mean()

    # ── Keltner Channel ──
    ema20_kc = close.ewm(span=20, adjust=False).mean()
    df["Keltner_Upper"] = ema20_kc + 2 * df["ATR"]
    df["Keltner_Mid"] = ema20_kc
    df["Keltner_Lower"] = ema20_kc - 2 * df["ATR"]

    # ── Donchian Channel ──
    df["Donchian_Upper"] = high.rolling(20).max()
    df["Donchian_Lower"] = low.rolling(20).min()
    df["Donchian_Mid"] = (df["Donchian_Upper"] + df["Donchian_Lower"]) / 2

    # ── Ulcer Index ──
    rolling_max_14 = close.rolling(14).max()
    pct_drawdown = (close - rolling_max_14) / rolling_max_14 * 100
    df["Ulcer_Index"] = (pct_drawdown.pow(2).rolling(14).mean()).pow(0.5)

    # ── Force Index ──
    df["Force_Index"] = close.diff() * volume
    df["Force_Index_13"] = df["Force_Index"].ewm(span=13, adjust=False).mean()

    # ── Aroon ──
    aroon_period = 25
    df["Aroon_Up"] = high.rolling(aroon_period + 1).apply(
        lambda x: x.argmax() / aroon_period * 100, raw=True)
    df["Aroon_Down"] = low.rolling(aroon_period + 1).apply(
        lambda x: x.argmin() / aroon_period * 100, raw=True)
    df["Aroon_Osc"] = df["Aroon_Up"] - df["Aroon_Down"]

    # ── Return ──
    df["Return"] = close.pct_change()
    return df


def _parabolic_sar(high: pd.Series, low: pd.Series, close: pd.Series,
                   af_start: float = 0.02, af_step: float = 0.02,
                   af_max: float = 0.20) -> pd.Series:
    """Compute Parabolic SAR."""
    length = len(close)
    sar = close.copy()
    af = af_start
    trend = 1  # 1 = up, -1 = down
    ep = low.iloc[0]
    sar.iloc[0] = high.iloc[0]

    for i in range(1, length):
        prev_sar = sar.iloc[i - 1]
        if trend == 1:
            sar.iloc[i] = prev_sar + af * (ep - prev_sar)
            sar.iloc[i] = min(sar.iloc[i], low.iloc[i - 1])
            if i >= 2:
                sar.iloc[i] = min(sar.iloc[i], low.iloc[i - 2])
            if high.iloc[i] > ep:
                ep = high.iloc[i]
                af = min(af + af_step, af_max)
            if low.iloc[i] < sar.iloc[i]:
                trend = -1
                sar.iloc[i] = ep
                ep = low.iloc[i]
                af = af_start
        else:
            sar.iloc[i] = prev_sar + af * (ep - prev_sar)
            sar.iloc[i] = max(sar.iloc[i], high.iloc[i - 1])
            if i >= 2:
                sar.iloc[i] = max(sar.iloc[i], high.iloc[i - 2])
            if low.iloc[i] < ep:
                ep = low.iloc[i]
                af = min(af + af_step, af_max)
            if high.iloc[i] > sar.iloc[i]:
                trend = 1
                sar.iloc[i] = ep
                ep = high.iloc[i]
                af = af_start
    return sar


# ============================================================
# INFO & FONDAMENTAUX
# ============================================================
def get_ticker_info(ticker):
    # 1. Essayer le JSON local
    local = _load_local_info(ticker)
    if local:
        return {
            "shortName": local.get("Nom_Court") or local.get("Nom"),
            "longName": local.get("Nom"),
            "symbol": local.get("ticker", ticker),
            "sector": local.get("Secteur"),
            "industry": local.get("Industrie"),
            "country": local.get("Pays"),
            "city": local.get("Ville"),
            "website": local.get("Site_Web"),
            "currency": local.get("Devise"),
            "exchange": local.get("Bourse"),
            "fullTimeEmployees": local.get("Employes"),
            "longBusinessSummary": local.get("Description"),
        }
    # 2. Fallback yfinance
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as e:
        print(f"[get_ticker_info] {ticker}: {e}")
        return {}
    return {
        "shortName": info.get("shortName"),
        "longName": info.get("longName"),
        "symbol": info.get("symbol", ticker),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "city": info.get("city"),
        "website": info.get("website"),
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
        "fullTimeEmployees": info.get("fullTimeEmployees"),
        "longBusinessSummary": info.get("longBusinessSummary"),
    }


def get_fundamentals(ticker):
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as e:
        print(f"[get_fundamentals] {ticker}: {e}")
        return {}

    keys = [
        "marketCap", "enterpriseValue", "trailingPE", "forwardPE", "pegRatio",
        "priceToBook", "priceToSalesTrailing12Months", "enterpriseToRevenue",
        "enterpriseToEbitda",
        "profitMargins", "operatingMargins", "grossMargins", "ebitdaMargins",
        "returnOnAssets", "returnOnEquity",
        "revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth",
        "totalCash", "totalDebt", "debtToEquity", "currentRatio", "quickRatio",
        "totalRevenue", "ebitda", "netIncomeToCommon", "freeCashflow",
        "operatingCashflow",
        "beta", "52WeekChange", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
        "fiftyDayAverage", "twoHundredDayAverage", "averageVolume",
        "sharesOutstanding", "floatShares",
        "dividendRate", "dividendYield", "payoutRatio", "fiveYearAvgDividendYield",
        "recommendationKey", "recommendationMean", "numberOfAnalystOpinions",
        "targetMeanPrice", "targetHighPrice", "targetLowPrice",
        "currentPrice", "previousClose", "regularMarketPrice",
    ]
    return {k: info.get(k) for k in keys}


def get_financial_statements(ticker):
    try:
        t = yf.Ticker(ticker)
        return {
            "income_statement": t.income_stmt,
            "balance_sheet": t.balance_sheet,
            "cashflow": t.cashflow,
        }
    except Exception as e:
        print(f"[get_financial_statements] {ticker}: {e}")
        return {"income_statement": None, "balance_sheet": None, "cashflow": None}


# ============================================================
# DONNÉES MULTI-TICKERS (pour pages performances / corrélations)
# ============================================================
def fetch_multiple_tickers(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    """Cours Close pour une liste de tickers — local d'abord, sinon yfinance."""
    # 1. Essayer depuis les CSVs locaux
    local_frames = {}
    missing = []
    for t in tickers:
        local = _load_local_history(t, period)
        if local is not None and "Close" in local.columns:
            local_frames[t] = local["Close"]
        else:
            missing.append(t)

    if not missing and local_frames:
        return pd.DataFrame(local_frames)

    # 2. Fallback yfinance pour les tickers manquants
    remote_df = pd.DataFrame()
    fetch_list = missing if local_frames else tickers
    if fetch_list:
        try:
            data = yf.download(
                fetch_list, period=period, interval="1d",
                progress=False, auto_adjust=True, threads=True,
            )
            if data is not None and not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    remote_df = data["Close"]
                else:
                    remote_df = data[["Close"]] if "Close" in data.columns else data
                    if len(fetch_list) == 1:
                        remote_df.columns = fetch_list
        except Exception as e:
            print(f"[fetch_multiple_tickers] Erreur: {e}")

    # 3. Combiner local + remote
    if local_frames:
        local_df = pd.DataFrame(local_frames)
        if not remote_df.empty:
            return local_df.join(remote_df, how="outer")
        return local_df
    return remote_df


def calculate_returns_for_period(prices: pd.DataFrame, period: str) -> pd.Series:
    """Calcule le rendement simple pour chaque colonne sur la période donnée."""
    period_days = {"1D": 1, "1W": 5, "1M": 22, "3M": 65, "6M": 130, "1Y": 252, "3Y": 756}
    n = period_days.get(period, 22)
    if prices.empty or len(prices) < 2:
        return pd.Series(dtype=float)
    start = prices.iloc[-min(n + 1, len(prices))]
    end = prices.iloc[-1]
    returns = (end / start - 1) * 100
    return returns.dropna()


def calculate_calendar_performance(prices: pd.DataFrame, perf_type: str) -> pd.Series:
    """Performances calendaires : WTD, MTD, QTD, STD, YTD."""
    if prices.empty:
        return pd.Series(dtype=float)
    last_date = prices.index[-1]
    if perf_type == "WTD":
        start = last_date - pd.Timedelta(days=last_date.weekday())
    elif perf_type == "MTD":
        start = pd.Timestamp(last_date.year, last_date.month, 1)
    elif perf_type == "QTD":
        q_month = ((last_date.month - 1) // 3) * 3 + 1
        start = pd.Timestamp(last_date.year, q_month, 1)
    elif perf_type == "STD":
        s_month = 1 if last_date.month <= 6 else 7
        start = pd.Timestamp(last_date.year, s_month, 1)
    elif perf_type == "YTD":
        start = pd.Timestamp(last_date.year, 1, 1)
    else:
        return pd.Series(dtype=float)
    # Find the last available price on or before start (reference price)
    prior = prices.loc[prices.index <= start]
    if prior.empty:
        prior = prices.iloc[:1]
    ref_price = prior.iloc[-1]
    last_price = prices.iloc[-1]
    return ((last_price / ref_price) - 1) * 100


def calculate_cumulative_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Retourne les prix normalisés base 100."""
    first_valid = prices.bfill().iloc[0]
    first_valid = first_valid.replace(0, pd.NA)
    return (prices / first_valid) * 100


def calculate_correlation_matrix(prices: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Matrice de corrélation des rendements quotidiens."""
    returns = prices.pct_change().dropna()
    return returns.corr(method=method)


def calculate_beta(stock_prices: pd.Series, index_prices: pd.Series,
                   period_days: int | None = None) -> float:
    """Bêta d'une action par rapport à un indice."""
    import numpy as np
    stock_ret = stock_prices.pct_change().dropna()
    index_ret = index_prices.pct_change().dropna()
    common = stock_ret.index.intersection(index_ret.index)
    if len(common) < 20:
        return float("nan")
    s = stock_ret.loc[common]
    m = index_ret.loc[common]
    if period_days:
        s = s.tail(period_days)
        m = m.tail(period_days)
    cov = s.cov(m)
    var = m.var()
    return float(cov / var) if var != 0 else float("nan")


def calculate_rolling_beta(stock_prices: pd.Series, index_prices: pd.Series,
                           window: int = 60) -> pd.Series:
    """Bêta glissant sur une fenêtre donnée."""
    stock_ret = stock_prices.pct_change().dropna()
    index_ret = index_prices.pct_change().dropna()
    common = stock_ret.index.intersection(index_ret.index)
    s = stock_ret.loc[common]
    m = index_ret.loc[common]
    cov = s.rolling(window).cov(m)
    var = m.rolling(window).var()
    return (cov / var.replace(0, pd.NA)).dropna()


def get_top_flop_performers(returns: pd.Series, n: int = 5) -> dict:
    """Top / Flop n performers à partir d'une série de rendements."""
    clean = returns.dropna().sort_values(ascending=False)
    return {
        "top": clean.head(n),
        "flop": clean.tail(n).sort_values(),
    }


def format_fundamental_value(key, value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    pct_keys = {
        "profitMargins", "operatingMargins", "grossMargins", "ebitdaMargins",
        "returnOnAssets", "returnOnEquity", "revenueGrowth", "earningsGrowth",
        "earningsQuarterlyGrowth", "dividendYield", "payoutRatio",
        "fiveYearAvgDividendYield", "52WeekChange",
    }
    big_money_keys = {
        "marketCap", "enterpriseValue", "totalCash", "totalDebt", "totalRevenue",
        "ebitda", "netIncomeToCommon", "freeCashflow", "operatingCashflow",
        "sharesOutstanding", "floatShares", "averageVolume",
    }
    try:
        if key in pct_keys:
            return f"{float(value) * 100:.2f}%"
        if key in big_money_keys:
            v = float(value)
            for unit, div in [("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)]:
                if abs(v) >= div:
                    return f"{v / div:.2f} {unit}"
            return f"{v:.0f}"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)
    except (TypeError, ValueError):
        return str(value)


def get_market_caps(tickers: list[str]) -> dict[str, float]:
    """Retourne la capitalisation boursière de chaque ticker."""
    caps = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info or {}
            mc = info.get("marketCap")
            if mc and mc > 0:
                caps[t] = float(mc)
        except Exception:
            pass
    return caps
