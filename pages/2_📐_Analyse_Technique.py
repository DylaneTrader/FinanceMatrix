"""
Page Analyse Technique — Indicateurs complets avec signaux et paramètres configurables
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_handler import (
    SECTOR_TICKERS,
    fetch_data,
    get_ticker_info,
    get_fundamentals,
    format_fundamental_value,
    _parabolic_sar,
)

st.set_page_config(page_title="Analyse Technique - FinanceMatrix", page_icon="📐", layout="wide")

_css = Path(__file__).parents[1] / "assets" / "style.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Couleurs
C_PRIMARY = "#01467A"
C_ACCENT = "#D91F16"
C_GREEN = "#10B981"
C_RED = "#EF4444"
C_MUTED = "#64748B"
C_LINE = "#0C64CF"

PERIOD_OPTIONS = {
    "5d": "5 Jours", "1mo": "1 Mois", "3mo": "3 Mois",
    "6mo": "6 Mois", "1y": "1 An", "2y": "2 Ans", "5y": "5 Ans",
}

st.title("📐 Analyse Technique")

# ═══ Sidebar sélection ═══
sector_names = list(SECTOR_TICKERS.keys())
selected_sector = st.sidebar.selectbox("🏭 Secteur", sector_names, index=0)
tickers = SECTOR_TICKERS[selected_sector]
selected_ticker = st.sidebar.selectbox("📈 Ticker", tickers, index=0)
selected_period = st.sidebar.selectbox(
    "📅 Période", list(PERIOD_OPTIONS.keys()),
    format_func=lambda x: PERIOD_OPTIONS[x], index=4,
)

# ═══ Paramètres des indicateurs (sidebar) ═══
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Paramètres indicateurs")

with st.sidebar.expander("📊 RSI", expanded=False):
    p_rsi = st.number_input("Période RSI", 2, 50, 14, key="p_rsi")
    p_rsi_ob = st.number_input("Seuil suracheté", 50, 100, 70, key="p_rsi_ob")
    p_rsi_os = st.number_input("Seuil survendu", 0, 50, 30, key="p_rsi_os")
    p_stochrsi_period = st.number_input("Stoch RSI période", 2, 50, 14, key="p_stochrsi_p")
    p_stochrsi_k = st.number_input("Stoch RSI %K lissage", 1, 20, 3, key="p_stochrsi_k")
    p_stochrsi_d = st.number_input("Stoch RSI %D lissage", 1, 20, 3, key="p_stochrsi_d")

with st.sidebar.expander("📉 MACD", expanded=False):
    p_macd_fast = st.number_input("EMA rapide", 2, 50, 12, key="p_macd_fast")
    p_macd_slow = st.number_input("EMA lente", 10, 100, 26, key="p_macd_slow")
    p_macd_signal = st.number_input("Signal", 2, 50, 9, key="p_macd_signal")

with st.sidebar.expander("🔄 Stochastic", expanded=False):
    p_stoch_k = st.number_input("Période %K", 2, 50, 14, key="p_stoch_k")
    p_stoch_d = st.number_input("Lissage %D", 1, 20, 3, key="p_stoch_d")
    p_stoch_ob = st.number_input("Seuil suracheté", 50, 100, 80, key="p_stoch_ob")
    p_stoch_os = st.number_input("Seuil survendu", 0, 50, 20, key="p_stoch_os")
    p_williams = st.number_input("Williams %R période", 2, 50, 14, key="p_williams")

with st.sidebar.expander("📏 ADX / Aroon", expanded=False):
    p_adx = st.number_input("Période ADX", 2, 50, 14, key="p_adx")
    p_adx_threshold = st.number_input("Seuil tendance", 10, 50, 25, key="p_adx_th")
    p_aroon = st.number_input("Période Aroon", 5, 100, 25, key="p_aroon")

with st.sidebar.expander("☁️ Ichimoku", expanded=False):
    p_ichi_tenkan = st.number_input("Tenkan-sen", 2, 50, 9, key="p_ichi_t")
    p_ichi_kijun = st.number_input("Kijun-sen", 5, 100, 26, key="p_ichi_k")
    p_ichi_spanb = st.number_input("Senkou Span B", 10, 200, 52, key="p_ichi_sb")
    p_ichi_disp = st.number_input("Décalage", 5, 100, 26, key="p_ichi_d")

with st.sidebar.expander("📦 Volume", expanded=False):
    p_cmf = st.number_input("CMF période", 5, 50, 20, key="p_cmf")
    p_mfi = st.number_input("MFI période", 2, 50, 14, key="p_mfi")
    p_force_ema = st.number_input("Force Index EMA", 2, 50, 13, key="p_force")

with st.sidebar.expander("📐 Canaux", expanded=False):
    p_kelt_ema = st.number_input("Keltner EMA", 5, 100, 20, key="p_kelt_ema")
    p_kelt_mult = st.number_input("Keltner multiplicateur ATR", 0.5, 5.0, 2.0, step=0.5, key="p_kelt_m")
    p_donch = st.number_input("Donchian période", 5, 100, 20, key="p_donch")

with st.sidebar.expander("🧮 Autres", expanded=False):
    p_cci = st.number_input("CCI période", 5, 50, 20, key="p_cci")
    p_roc = st.number_input("ROC période", 1, 50, 12, key="p_roc")
    p_trix = st.number_input("TRIX EMA", 5, 50, 15, key="p_trix")
    p_dpo = st.number_input("DPO période", 5, 50, 20, key="p_dpo")
    p_ulcer = st.number_input("Ulcer Index période", 5, 50, 14, key="p_ulcer")
    p_atr = st.number_input("ATR période", 2, 50, 14, key="p_atr")


# ═══ Fetch data ═══
@st.cache_data(ttl=300, show_spinner="Chargement des données…")
def _fetch(ticker, period):
    return fetch_data(ticker, period=period)


@st.cache_data(ttl=600)
def _info(ticker):
    return get_ticker_info(ticker)


@st.cache_data(ttl=600)
def _funds(ticker):
    return get_fundamentals(ticker)


raw_df = _fetch(selected_ticker, selected_period)
if raw_df is None or raw_df.empty:
    st.error(f"Aucune donnée pour {selected_ticker}. Essayez un autre ticker.")
    st.stop()

df = raw_df.copy()
close = df["Close"]
high = df["High"]
low = df["Low"]
volume = df.get("Volume", pd.Series(0, index=df.index))
tp = (high + low + close) / 3

# ═══ Calcul dynamique de TOUS les indicateurs avec paramètres utilisateur ═══

# ATR
high_low = high - low
high_close = (high - close.shift()).abs()
low_close = (low - close.shift()).abs()
tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
df["TR"] = tr
df["ATR"] = tr.rolling(p_atr).mean()

# RSI
delta = close.diff()
gain = delta.where(delta > 0, 0).rolling(p_rsi).mean()
loss = (-delta.where(delta < 0, 0)).rolling(p_rsi).mean()
rs = gain / loss.replace(0, 1e-9)
df["RSI"] = 100 - (100 / (1 + rs))

# Stochastic RSI
rsi_s = df["RSI"]
rsi_min = rsi_s.rolling(p_stochrsi_period).min()
rsi_max = rsi_s.rolling(p_stochrsi_period).max()
stoch_rsi = (rsi_s - rsi_min) / (rsi_max - rsi_min).replace(0, 1e-9)
df["StochRSI_K"] = stoch_rsi.rolling(p_stochrsi_k).mean() * 100
df["StochRSI_D"] = df["StochRSI_K"].rolling(p_stochrsi_d).mean()

# MACD
ema_fast = close.ewm(span=p_macd_fast, adjust=False).mean()
ema_slow = close.ewm(span=p_macd_slow, adjust=False).mean()
df["MACD"] = ema_fast - ema_slow
df["MACD_Signal"] = df["MACD"].ewm(span=p_macd_signal, adjust=False).mean()
df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

# ADX
plus_dm = high.diff()
minus_dm = -low.diff()
plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
atr_adx = df["ATR"].replace(0, 1e-9)
plus_di = 100 * plus_dm.rolling(p_adx).mean() / atr_adx
minus_di = 100 * minus_dm.rolling(p_adx).mean() / atr_adx
df["Plus_DI"] = plus_di
df["Minus_DI"] = minus_di
dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9) * 100
df["ADX"] = dx.rolling(p_adx).mean()

# CCI
sma_tp = tp.rolling(p_cci).mean()
mad = tp.rolling(p_cci).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
df["CCI"] = (tp - sma_tp) / (0.015 * mad.replace(0, 1e-9))

# Stochastic
h_stoch = high.rolling(p_stoch_k).max()
l_stoch = low.rolling(p_stoch_k).min()
df["Stoch_K"] = 100 * (close - l_stoch) / (h_stoch - l_stoch).replace(0, 1e-9)
df["Stoch_D"] = df["Stoch_K"].rolling(p_stoch_d).mean()

# Williams %R
h_wr = high.rolling(p_williams).max()
l_wr = low.rolling(p_williams).min()
df["Williams_R"] = -100 * (h_wr - close) / (h_wr - l_wr).replace(0, 1e-9)

# OBV
obv_sign = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
df["OBV"] = (obv_sign * volume).cumsum()

# VWAP
cum_vol = volume.cumsum()
cum_tp_vol = (tp * volume).cumsum()
df["VWAP"] = cum_tp_vol / cum_vol.replace(0, 1e-9)

# Ichimoku
h_t = high.rolling(p_ichi_tenkan).max()
l_t = low.rolling(p_ichi_tenkan).min()
df["Ichimoku_Tenkan"] = (h_t + l_t) / 2
h_k = high.rolling(p_ichi_kijun).max()
l_k = low.rolling(p_ichi_kijun).min()
df["Ichimoku_Kijun"] = (h_k + l_k) / 2
df["Ichimoku_SpanA"] = ((df["Ichimoku_Tenkan"] + df["Ichimoku_Kijun"]) / 2).shift(p_ichi_disp)
h_sb = high.rolling(p_ichi_spanb).max()
l_sb = low.rolling(p_ichi_spanb).min()
df["Ichimoku_SpanB"] = ((h_sb + l_sb) / 2).shift(p_ichi_disp)
df["Ichimoku_Chikou"] = close.shift(-p_ichi_disp)

# Parabolic SAR
df["PSAR"] = _parabolic_sar(high, low, close)

# CMF
mfv = ((close - low) - (high - close)) / (high - low).replace(0, 1e-9) * volume
df["CMF"] = mfv.rolling(p_cmf).sum() / volume.rolling(p_cmf).sum().replace(0, 1e-9)

# MFI
raw_mf = tp * volume
pos_mf = raw_mf.where(tp > tp.shift(), 0).rolling(p_mfi).sum()
neg_mf = raw_mf.where(tp < tp.shift(), 0).rolling(p_mfi).sum()
mf_ratio = pos_mf / neg_mf.replace(0, 1e-9)
df["MFI"] = 100 - (100 / (1 + mf_ratio))

# ROC
df["ROC"] = (close / close.shift(p_roc) - 1) * 100

# TRIX
ema1_t = close.ewm(span=p_trix, adjust=False).mean()
ema2_t = ema1_t.ewm(span=p_trix, adjust=False).mean()
ema3_t = ema2_t.ewm(span=p_trix, adjust=False).mean()
df["TRIX"] = ema3_t.pct_change() * 100

# DPO
df["DPO"] = close.shift(p_dpo // 2 + 1) - close.rolling(p_dpo).mean()

# Keltner
ema_kc = close.ewm(span=p_kelt_ema, adjust=False).mean()
df["Keltner_Upper"] = ema_kc + p_kelt_mult * df["ATR"]
df["Keltner_Mid"] = ema_kc
df["Keltner_Lower"] = ema_kc - p_kelt_mult * df["ATR"]

# Donchian
df["Donchian_Upper"] = high.rolling(p_donch).max()
df["Donchian_Lower"] = low.rolling(p_donch).min()
df["Donchian_Mid"] = (df["Donchian_Upper"] + df["Donchian_Lower"]) / 2

# Ulcer Index
rolling_max_u = close.rolling(p_ulcer).max()
pct_dd = (close - rolling_max_u) / rolling_max_u * 100
df["Ulcer_Index"] = (pct_dd.pow(2).rolling(p_ulcer).mean()).pow(0.5)

# Force Index
df["Force_Index"] = close.diff() * volume
df["Force_Index_13"] = df["Force_Index"].ewm(span=p_force_ema, adjust=False).mean()

# Aroon
df["Aroon_Up"] = high.rolling(p_aroon + 1).apply(
    lambda x: x.argmax() / p_aroon * 100, raw=True)
df["Aroon_Down"] = low.rolling(p_aroon + 1).apply(
    lambda x: x.argmin() / p_aroon * 100, raw=True)
df["Aroon_Osc"] = df["Aroon_Up"] - df["Aroon_Down"]

# Return
df["Return"] = close.pct_change()

# ═══ Info ticker ═══
info = _info(selected_ticker)
st.markdown(f"**{info.get('longName') or info.get('shortName') or selected_ticker}** — "
            f"{info.get('sector', '')} · {info.get('industry', '')}")

st.markdown("---")


# ═══════════════ HELPERS ═══════════════
def _safe(col, idx=-1):
    if col not in df.columns:
        return np.nan
    s = df[col].dropna()
    return float(s.iloc[idx]) if len(s) > abs(idx) else np.nan


def _signal_card(title: str, value: str, status: str, color: str) -> str:
    return (
        f"<div style='background:white;border-radius:12px;padding:14px 16px;"
        f"border-left:5px solid {color};box-shadow:0 1px 3px rgba(0,0,0,0.06);'>"
        f"<div style='font-size:0.78rem;color:{C_MUTED};text-transform:uppercase;"
        f"letter-spacing:0.05em;margin-bottom:4px;'>{title}</div>"
        f"<div style='font-size:1.45rem;font-weight:700;color:{C_PRIMARY};'>{value}</div>"
        f"<div style='font-size:0.82rem;color:{color};font-weight:600;margin-top:2px;'>{status}</div>"
        f"</div>"
    )


def _chart_layout(fig, h=550):
    fig.update_layout(
        height=h, hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C_PRIMARY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="#E2E8F0")
    fig.update_yaxes(gridcolor="#E2E8F0")


# ═══════════════ TABLEAU DE BORD DES SIGNAUX ═══════════════
rsi_val = _safe("RSI")
macd_val = _safe("MACD")
macd_sig = _safe("MACD_Signal")
adx_val = _safe("ADX")
cci_val = _safe("CCI")
close_last = float(df["Close"].iloc[-1])

# RSI card
if np.isnan(rsi_val):
    rsi_card = _signal_card(f"RSI ({p_rsi})", "—", "Indisponible", C_MUTED)
elif rsi_val > p_rsi_ob:
    rsi_card = _signal_card(f"RSI ({p_rsi})", f"{rsi_val:.1f}", "🔴 Suracheté", C_RED)
elif rsi_val < p_rsi_os:
    rsi_card = _signal_card(f"RSI ({p_rsi})", f"{rsi_val:.1f}", "🟢 Survendu", C_GREEN)
else:
    rsi_card = _signal_card(f"RSI ({p_rsi})", f"{rsi_val:.1f}", "⚪ Neutre", C_MUTED)

# MACD card
macd_prev = _safe("MACD", -2)
sig_prev = _safe("MACD_Signal", -2)
if not np.isnan(macd_val) and not np.isnan(macd_sig):
    if macd_val > macd_sig and macd_prev <= sig_prev:
        macd_card = _signal_card("MACD", f"{macd_val:.3f}", "🟢 Croisement haussier", C_GREEN)
    elif macd_val < macd_sig and macd_prev >= sig_prev:
        macd_card = _signal_card("MACD", f"{macd_val:.3f}", "🔴 Croisement baissier", C_RED)
    elif macd_val > macd_sig:
        macd_card = _signal_card("MACD", f"{macd_val:.3f}", "🟢 Haussier", C_GREEN)
    else:
        macd_card = _signal_card("MACD", f"{macd_val:.3f}", "🔴 Baissier", C_RED)
else:
    macd_card = _signal_card("MACD", "—", "Indisponible", C_MUTED)

# ADX card
if not np.isnan(adx_val):
    if adx_val > p_adx_threshold:
        adx_card = _signal_card(f"ADX ({p_adx})", f"{adx_val:.1f}", "🟢 Tendance forte", C_GREEN)
    else:
        adx_card = _signal_card(f"ADX ({p_adx})", f"{adx_val:.1f}", "⚪ Pas de tendance", C_MUTED)
else:
    adx_card = _signal_card("ADX", "—", "Indisponible", C_MUTED)

# Prix vs SMA 50
sma50_v = df["Close"].rolling(50).mean().dropna()
if not sma50_v.empty:
    sma50_last = float(sma50_v.iloc[-1])
    px_diff = (close_last / sma50_last - 1) * 100
    if px_diff > 0:
        px_card = _signal_card("Prix vs SMA 50", f"{px_diff:+.1f}%", "🟢 Au-dessus", C_GREEN)
    else:
        px_card = _signal_card("Prix vs SMA 50", f"{px_diff:+.1f}%", "🔴 En-dessous", C_RED)
else:
    px_card = _signal_card("Prix vs SMA 50", "—", "Indisponible", C_MUTED)

# CCI card
if not np.isnan(cci_val):
    if cci_val > 100:
        cci_card = _signal_card(f"CCI ({p_cci})", f"{cci_val:.0f}", "🔴 Suracheté", C_RED)
    elif cci_val < -100:
        cci_card = _signal_card(f"CCI ({p_cci})", f"{cci_val:.0f}", "🟢 Survendu", C_GREEN)
    else:
        cci_card = _signal_card(f"CCI ({p_cci})", f"{cci_val:.0f}", "⚪ Neutre", C_MUTED)
else:
    cci_card = _signal_card("CCI", "—", "Indisponible", C_MUTED)

# Stochastic card
stoch_k = _safe("Stoch_K")
if not np.isnan(stoch_k):
    if stoch_k > p_stoch_ob:
        stoch_card = _signal_card("Stochastic %K", f"{stoch_k:.1f}", "🔴 Suracheté", C_RED)
    elif stoch_k < p_stoch_os:
        stoch_card = _signal_card("Stochastic %K", f"{stoch_k:.1f}", "🟢 Survendu", C_GREEN)
    else:
        stoch_card = _signal_card("Stochastic %K", f"{stoch_k:.1f}", "⚪ Neutre", C_MUTED)
else:
    stoch_card = _signal_card("Stochastic %K", "—", "Indisponible", C_MUTED)

st.markdown("##### 🎯 Tableau de bord des signaux")
r1c1, r1c2, r1c3 = st.columns(3)
r2c1, r2c2, r2c3 = st.columns(3)
with r1c1:
    st.markdown(rsi_card, unsafe_allow_html=True)
with r1c2:
    st.markdown(macd_card, unsafe_allow_html=True)
with r1c3:
    st.markdown(adx_card, unsafe_allow_html=True)
with r2c1:
    st.markdown(px_card, unsafe_allow_html=True)
with r2c2:
    st.markdown(cci_card, unsafe_allow_html=True)
with r2c3:
    st.markdown(stoch_card, unsafe_allow_html=True)

st.markdown("")

# ═══════════════ TABS INDICATEURS ═══════════════
(tab_rsi, tab_ma, tab_macd, tab_bb, tab_stoch, tab_adx,
 tab_ichimoku, tab_vol, tab_channels, tab_misc) = st.tabs([
    "📊 RSI", "📈 Moyennes Mobiles", "📉 MACD", "🎯 Bollinger",
    "🔄 Stochastic", "📏 ADX", "☁️ Ichimoku", "📦 Volume",
    "📐 Canaux", "🧮 Autres",
])

# ──────────────── RSI ────────────────
with tab_rsi:
    st.subheader(f"RSI — Relative Strength Index ({p_rsi})")
    st.caption(f"Paramètres : période={p_rsi}, suracheté={p_rsi_ob}, survendu={p_rsi_os}")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.6, 0.4], subplot_titles=("Prix", f"RSI ({p_rsi})"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_LINE, width=2)), row=1, col=1)
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI",
                                 line=dict(color=C_PRIMARY, width=1.5)), row=2, col=1)
    fig.add_hline(y=p_rsi_ob, line_dash="dash", line_color=C_RED, row=2, col=1)
    fig.add_hline(y=p_rsi_os, line_dash="dash", line_color=C_GREEN, row=2, col=1)
    fig.add_hrect(y0=p_rsi_ob, y1=100, fillcolor="rgba(239,68,68,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=0, y1=p_rsi_os, fillcolor="rgba(16,185,129,0.08)", line_width=0, row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    _chart_layout(fig, 580)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Stochastic RSI subplot
    if "StochRSI_K" in df.columns:
        st.markdown(f"##### Stochastic RSI (période={p_stochrsi_period}, K={p_stochrsi_k}, D={p_stochrsi_d})")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df.index, y=df["StochRSI_K"], mode="lines",
                                  name="Stoch RSI %K", line=dict(color=C_LINE, width=1.5)))
        fig2.add_trace(go.Scatter(x=df.index, y=df["StochRSI_D"], mode="lines",
                                  name="Stoch RSI %D", line=dict(color=C_RED, width=1.2, dash="dash")))
        fig2.add_hline(y=80, line_dash="dash", line_color=C_RED, opacity=0.5)
        fig2.add_hline(y=20, line_dash="dash", line_color=C_GREEN, opacity=0.5)
        _chart_layout(fig2, 300)
        fig2.update_yaxes(range=[0, 100])
        st.plotly_chart(fig2, use_container_width=True)

    if not np.isnan(rsi_val):
        lbl = ("🔴 Suracheté" if rsi_val > p_rsi_ob
               else ("🟢 Survendu" if rsi_val < p_rsi_os else "⚪ Neutre"))
        st.info(f"**RSI actuel : {rsi_val:.2f}** — {lbl}")

# ──────────────── Moyennes Mobiles ────────────────
with tab_ma:
    st.subheader("Prix avec Moyennes Mobiles")
    c1, c2 = st.columns(2)
    with c1:
        sma1 = st.slider("SMA courte", 5, 50, 20, key="sma1")
        sma2 = st.slider("SMA longue", 20, 200, 50, key="sma2")
    with c2:
        ema1 = st.slider("EMA courte", 5, 50, 12, key="ema1")
        ema2 = st.slider("EMA longue", 20, 200, 26, key="ema2")

    sma_short = df["Close"].rolling(sma1).mean()
    sma_long = df["Close"].rolling(sma2).mean()
    ema_short = df["Close"].ewm(span=ema1, adjust=False).mean()
    ema_long = df["Close"].ewm(span=ema2, adjust=False).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_PRIMARY, width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=sma_short, name=f"SMA {sma1}",
                             line=dict(color="#3B82F6", width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=sma_long, name=f"SMA {sma2}",
                             line=dict(color="#1D4ED8", width=1.5, dash="dash")))
    fig.add_trace(go.Scatter(x=df.index, y=ema_short, name=f"EMA {ema1}",
                             line=dict(color=C_GREEN, width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=ema_long, name=f"EMA {ema2}",
                             line=dict(color="#059669", width=1.5, dash="dash")))
    if "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP",
                                 line=dict(color="#F59E0B", width=1.2, dash="dot")))
    if "PSAR" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["PSAR"], mode="markers", name="SAR",
                                 marker=dict(color="#8B5CF6", size=3)))
    _chart_layout(fig, 520)
    st.plotly_chart(fig, use_container_width=True)

    cs1, cs2 = st.columns(2)
    with cs1:
        if len(sma_short.dropna()) >= 2 and len(sma_long.dropna()) >= 2:
            if sma_short.iloc[-1] > sma_long.iloc[-1]:
                st.success(f"🟢 SMA {sma1} > SMA {sma2} — Tendance haussière")
            else:
                st.error(f"🔴 SMA {sma1} < SMA {sma2} — Tendance baissière")
    with cs2:
        if len(ema_short.dropna()) >= 2 and len(ema_long.dropna()) >= 2:
            if ema_short.iloc[-1] > ema_long.iloc[-1]:
                st.success(f"🟢 EMA {ema1} > EMA {ema2} — Tendance haussière")
            else:
                st.error(f"🔴 EMA {ema1} < EMA {ema2} — Tendance baissière")

# ──────────────── MACD ────────────────
with tab_macd:
    st.subheader("MACD — Moving Average Convergence Divergence")
    st.caption(f"Paramètres : rapide={p_macd_fast}, lente={p_macd_slow}, signal={p_macd_signal}")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.6, 0.4],
                        subplot_titles=("Prix", f"MACD ({p_macd_fast},{p_macd_slow},{p_macd_signal})"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_LINE, width=2)), row=1, col=1)
    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD",
                                 line=dict(color="#3B82F6", width=1.5)), row=2, col=1)
    if "MACD_Signal" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], mode="lines", name="Signal",
                                 line=dict(color=C_RED, width=1.5)), row=2, col=1)
    if "MACD_Hist" in df.columns:
        colors_hist = [C_GREEN if v >= 0 else C_RED for v in df["MACD_Hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histogramme",
                             marker_color=colors_hist, opacity=0.7), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color=C_MUTED, opacity=0.5, row=2, col=1)
    _chart_layout(fig, 580)
    st.plotly_chart(fig, use_container_width=True)

    if "MACD" in df.columns:
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric("MACD", f"{df['MACD'].iloc[-1]:.4f}")
        with mc2:
            st.metric("Signal", f"{df['MACD_Signal'].iloc[-1]:.4f}")
        with mc3:
            hist_v = df["MACD_Hist"].iloc[-1]
            st.metric("Histogramme", f"{hist_v:.4f}", delta="Positif" if hist_v > 0 else "Négatif")

# ──────────────── Bollinger ────────────────
with tab_bb:
    st.subheader("Bandes de Bollinger")
    cb1, cb2 = st.columns([1, 2])
    with cb1:
        bb_period = st.slider("Période (SMA)", 10, 50, 20, key="bb_period")
        bb_k = st.slider("Écarts-types (k)", 1.0, 3.0, 2.0, step=0.5, key="bb_k")
    with cb2:
        st.markdown(
            "<div style='background:white;padding:14px;border-radius:10px;border-left:4px solid #0C64CF;'>"
            "<strong>Interprétation :</strong><br>"
            "• Prix touche la bande haute → zone de <b style='color:#EF4444'>surachat</b><br>"
            "• Prix touche la bande basse → zone de <b style='color:#10B981'>survente</b><br>"
            "• Bandwidth faible → faible volatilité (expansion imminente)<br>"
            "• %B &gt; 1 ou &lt; 0 → excès statistique"
            "</div>", unsafe_allow_html=True)

    sma_bb = df["Close"].rolling(bb_period).mean()
    std_bb = df["Close"].rolling(bb_period).std()
    upper = sma_bb + bb_k * std_bb
    lower = sma_bb - bb_k * std_bb
    bandwidth = (upper - lower) / sma_bb * 100
    percent_b = (df["Close"] - lower) / (upper - lower)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.7, 0.3],
                        subplot_titles=(f"Prix & Bollinger ({bb_period}, k={bb_k})", "Bandwidth (%)"))
    fig.add_trace(go.Scatter(x=upper.index, y=upper, mode="lines", name="Bande haute",
                             line=dict(color=C_RED, width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=lower.index, y=lower, mode="lines", name="Bande basse",
                             line=dict(color=C_GREEN, width=1, dash="dot"),
                             fill="tonexty", fillcolor="rgba(12,100,207,0.06)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=sma_bb.index, y=sma_bb, mode="lines", name=f"SMA {bb_period}",
                             line=dict(color=C_MUTED, width=1.2, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_PRIMARY, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=bandwidth.index, y=bandwidth, mode="lines", name="Bandwidth",
                             line=dict(color=C_LINE, width=1.5),
                             fill="tozeroy", fillcolor="rgba(12,100,207,0.10)",
                             showlegend=False), row=2, col=1)
    _chart_layout(fig, 620)
    st.plotly_chart(fig, use_container_width=True)

    if not percent_b.dropna().empty:
        val_pb = float(percent_b.dropna().iloc[-1])
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            tag = ("🔴 Au-dessus" if val_pb > 1 else "🟢 Sous" if val_pb < 0
                   else "🟠 Proche haute" if val_pb > 0.8
                   else "🔵 Proche basse" if val_pb < 0.2 else "⚪ Neutre")
            st.metric("%B actuel", f"{val_pb:.2f}", delta=tag)
        with bc2:
            st.metric("Bandwidth", f"{bandwidth.dropna().iloc[-1]:.1f}%")
        with bc3:
            atr_v = _safe("ATR")
            st.metric(f"ATR ({p_atr})", f"{atr_v:.2f}" if not np.isnan(atr_v) else "—")

# ──────────────── Stochastic ────────────────
with tab_stoch:
    st.subheader("Oscillateur Stochastique")
    st.caption(f"Paramètres : %K={p_stoch_k}, %D lissage={p_stoch_d}, suracheté={p_stoch_ob}, survendu={p_stoch_os}")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.6, 0.4],
                        subplot_titles=("Prix", f"Stochastic ({p_stoch_k},{p_stoch_d})"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_LINE, width=2)), row=1, col=1)
    if "Stoch_K" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_K"], mode="lines", name="%K",
                                 line=dict(color=C_PRIMARY, width=1.5)), row=2, col=1)
    if "Stoch_D" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_D"], mode="lines", name="%D",
                                 line=dict(color=C_RED, width=1.2, dash="dash")), row=2, col=1)
    fig.add_hline(y=p_stoch_ob, line_dash="dash", line_color=C_RED, row=2, col=1)
    fig.add_hline(y=p_stoch_os, line_dash="dash", line_color=C_GREEN, row=2, col=1)
    fig.add_hrect(y0=p_stoch_ob, y1=100, fillcolor="rgba(239,68,68,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=0, y1=p_stoch_os, fillcolor="rgba(16,185,129,0.08)", line_width=0, row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    _chart_layout(fig, 550)
    st.plotly_chart(fig, use_container_width=True)

    # Williams %R
    st.markdown(f"##### Williams %R (période={p_williams})")
    if "Williams_R" in df.columns:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df.index, y=df["Williams_R"], mode="lines",
                                  name="Williams %R", line=dict(color=C_PRIMARY, width=1.5)))
        fig2.add_hline(y=-20, line_dash="dash", line_color=C_RED)
        fig2.add_hline(y=-80, line_dash="dash", line_color=C_GREEN)
        _chart_layout(fig2, 280)
        fig2.update_yaxes(range=[-100, 0])
        st.plotly_chart(fig2, use_container_width=True)
        wr = _safe("Williams_R")
        if not np.isnan(wr):
            lbl = "🔴 Suracheté" if wr > -20 else ("🟢 Survendu" if wr < -80 else "⚪ Neutre")
            st.info(f"**Williams %R : {wr:.1f}** — {lbl}")

# ──────────────── ADX ────────────────
with tab_adx:
    st.subheader("ADX — Average Directional Index")
    st.caption(f"Paramètres : période={p_adx}, seuil tendance={p_adx_threshold}")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.55, 0.45],
                        subplot_titles=("Prix", f"ADX / +DI / -DI ({p_adx})"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_LINE, width=2)), row=1, col=1)
    if "ADX" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ADX"], mode="lines", name="ADX",
                                 line=dict(color=C_PRIMARY, width=2)), row=2, col=1)
    if "Plus_DI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Plus_DI"], mode="lines", name="+DI",
                                 line=dict(color=C_GREEN, width=1.2)), row=2, col=1)
    if "Minus_DI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Minus_DI"], mode="lines", name="-DI",
                                 line=dict(color=C_RED, width=1.2)), row=2, col=1)
    fig.add_hline(y=p_adx_threshold, line_dash="dash", line_color=C_MUTED, opacity=0.5, row=2, col=1)
    _chart_layout(fig, 580)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"<div style='background:white;padding:14px;border-radius:10px;border-left:4px solid #0C64CF;'>"
        f"<strong>Interprétation ADX :</strong><br>"
        f"• <b>ADX &gt; {p_adx_threshold}</b> : tendance forte<br>"
        f"• <b>ADX &lt; {p_adx_threshold}</b> : marché sans tendance (range)<br>"
        f"• <b>+DI &gt; -DI</b> : tendance haussière · <b>-DI &gt; +DI</b> : tendance baissière"
        f"</div>", unsafe_allow_html=True)

    # Aroon
    st.markdown(f"##### Aroon Oscillator (période={p_aroon})")
    if "Aroon_Up" in df.columns:
        fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                             row_heights=[0.5, 0.5],
                             subplot_titles=("Aroon Up / Down", "Aroon Oscillator"))
        fig2.add_trace(go.Scatter(x=df.index, y=df["Aroon_Up"], mode="lines", name="Aroon Up",
                                  line=dict(color=C_GREEN, width=1.5)), row=1, col=1)
        fig2.add_trace(go.Scatter(x=df.index, y=df["Aroon_Down"], mode="lines", name="Aroon Down",
                                  line=dict(color=C_RED, width=1.5)), row=1, col=1)
        fig2.add_trace(go.Scatter(x=df.index, y=df["Aroon_Osc"], mode="lines", name="Oscillator",
                                  line=dict(color=C_PRIMARY, width=1.5)), row=2, col=1)
        fig2.add_hline(y=0, line_dash="dash", line_color=C_MUTED, row=2, col=1)
        _chart_layout(fig2, 420)
        st.plotly_chart(fig2, use_container_width=True)

# ──────────────── Ichimoku ────────────────
with tab_ichimoku:
    st.subheader("Ichimoku Cloud")
    st.caption(f"Paramètres : Tenkan={p_ichi_tenkan}, Kijun={p_ichi_kijun}, "
               f"Span B={p_ichi_spanb}, décalage={p_ichi_disp}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_PRIMARY, width=2)))
    if "Ichimoku_Tenkan" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_Tenkan"],
                                 name=f"Tenkan-sen ({p_ichi_tenkan})",
                                 line=dict(color="#3B82F6", width=1.2)))
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_Kijun"],
                                 name=f"Kijun-sen ({p_ichi_kijun})",
                                 line=dict(color=C_RED, width=1.2)))
    if "Ichimoku_SpanA" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_SpanA"], name="Senkou Span A",
                                 line=dict(color=C_GREEN, width=0.8)))
    if "Ichimoku_SpanB" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_SpanB"],
                                 name=f"Senkou Span B ({p_ichi_spanb})",
                                 line=dict(color=C_RED, width=0.8),
                                 fill="tonexty", fillcolor="rgba(16,185,129,0.08)"))
    if "Ichimoku_Chikou" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_Chikou"], name="Chikou Span",
                                 line=dict(color="#8B5CF6", width=1, dash="dot")))
    _chart_layout(fig, 600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "<div style='background:white;padding:14px;border-radius:10px;border-left:4px solid #0C64CF;'>"
        "<strong>Interprétation Ichimoku :</strong><br>"
        "• Prix au-dessus du nuage → tendance haussière<br>"
        "• Prix en-dessous du nuage → tendance baissière<br>"
        "• Tenkan croise Kijun vers le haut → signal d'achat<br>"
        "• Chikou Span au-dessus du prix passé → confirmation haussière"
        "</div>", unsafe_allow_html=True)

# ──────────────── Volume ────────────────
with tab_vol:
    st.subheader("Indicateurs de Volume")
    st.caption(f"Paramètres : CMF={p_cmf}, MFI={p_mfi}, Force Index EMA={p_force_ema}")

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        row_heights=[0.4, 0.3, 0.3],
                        subplot_titles=("Prix + Volume", "OBV (On-Balance Volume)",
                                        f"CMF ({p_cmf})"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_LINE, width=2)), row=1, col=1)
    if "Volume" in df.columns:
        vol_colors = [C_GREEN if df["Close"].iloc[i] >= df["Close"].iloc[max(0, i - 1)]
                      else C_RED for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
                             marker_color=vol_colors, opacity=0.6), row=1, col=1)
    if "OBV" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["OBV"], mode="lines", name="OBV",
                                 line=dict(color=C_PRIMARY, width=1.5)), row=2, col=1)
    if "CMF" in df.columns:
        cmf_colors = [C_GREEN if v >= 0 else C_RED for v in df["CMF"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["CMF"], name="CMF",
                             marker_color=cmf_colors, opacity=0.7), row=3, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color=C_MUTED, opacity=0.5, row=3, col=1)
    _chart_layout(fig, 700)
    st.plotly_chart(fig, use_container_width=True)

    # MFI
    if "MFI" in df.columns:
        st.markdown(f"##### MFI — Money Flow Index ({p_mfi})")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df.index, y=df["MFI"], mode="lines", name="MFI",
                                  line=dict(color=C_PRIMARY, width=1.5)))
        fig2.add_hline(y=80, line_dash="dash", line_color=C_RED)
        fig2.add_hline(y=20, line_dash="dash", line_color=C_GREEN)
        _chart_layout(fig2, 280)
        fig2.update_yaxes(range=[0, 100])
        st.plotly_chart(fig2, use_container_width=True)

    # Force Index
    if "Force_Index_13" in df.columns:
        st.markdown(f"##### Force Index (EMA {p_force_ema})")
        fig3 = go.Figure()
        fi_colors = [C_GREEN if v >= 0 else C_RED for v in df["Force_Index_13"].fillna(0)]
        fig3.add_trace(go.Bar(x=df.index, y=df["Force_Index_13"], name="Force Index",
                              marker_color=fi_colors, opacity=0.7))
        fig3.add_hline(y=0, line_dash="dash", line_color=C_MUTED)
        _chart_layout(fig3, 280)
        st.plotly_chart(fig3, use_container_width=True)

# ──────────────── Canaux ────────────────
with tab_channels:
    st.subheader("Canaux de prix")
    channel_type = st.radio("Type de canal", ["Keltner", "Donchian"], horizontal=True, key="ch_type")

    if channel_type == "Keltner":
        st.caption(f"Paramètres : EMA={p_kelt_ema}, multiplicateur ATR={p_kelt_mult}")
    else:
        st.caption(f"Paramètres : période={p_donch}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_PRIMARY, width=2)))

    if channel_type == "Keltner" and "Keltner_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Keltner_Upper"], name="Keltner Haut",
                                 line=dict(color=C_RED, width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["Keltner_Lower"], name="Keltner Bas",
                                 line=dict(color=C_GREEN, width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(12,100,207,0.06)"))
        fig.add_trace(go.Scatter(x=df.index, y=df["Keltner_Mid"], name=f"EMA {p_kelt_ema}",
                                 line=dict(color=C_MUTED, width=1, dash="dash")))
    elif channel_type == "Donchian" and "Donchian_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Donchian_Upper"], name="Donchian Haut",
                                 line=dict(color=C_RED, width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["Donchian_Lower"], name="Donchian Bas",
                                 line=dict(color=C_GREEN, width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(12,100,207,0.06)"))
        fig.add_trace(go.Scatter(x=df.index, y=df["Donchian_Mid"], name="Médian",
                                 line=dict(color=C_MUTED, width=1, dash="dash")))
    _chart_layout(fig, 500)
    st.plotly_chart(fig, use_container_width=True)

# ──────────────── Autres ────────────────
with tab_misc:
    st.subheader("Indicateurs supplémentaires")
    st.caption(f"CCI={p_cci} · ROC={p_roc} · TRIX={p_trix} · DPO={p_dpo} · Ulcer={p_ulcer}")

    mc1, mc2 = st.columns(2)

    with mc1:
        # CCI
        st.markdown(f"##### CCI — Commodity Channel Index ({p_cci})")
        if "CCI" in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["CCI"], mode="lines", name="CCI",
                                     line=dict(color=C_PRIMARY, width=1.5)))
            fig.add_hline(y=100, line_dash="dash", line_color=C_RED)
            fig.add_hline(y=-100, line_dash="dash", line_color=C_GREEN)
            fig.add_hline(y=0, line_dash="dash", line_color=C_MUTED, opacity=0.3)
            _chart_layout(fig, 300)
            st.plotly_chart(fig, use_container_width=True)

        # ROC
        st.markdown(f"##### ROC — Rate of Change ({p_roc})")
        if "ROC" in df.columns:
            fig = go.Figure()
            roc_colors = [C_GREEN if v >= 0 else C_RED for v in df["ROC"].fillna(0)]
            fig.add_trace(go.Bar(x=df.index, y=df["ROC"], name="ROC",
                                 marker_color=roc_colors, opacity=0.7))
            fig.add_hline(y=0, line_dash="dash", line_color=C_MUTED)
            _chart_layout(fig, 300)
            st.plotly_chart(fig, use_container_width=True)

    with mc2:
        # TRIX
        st.markdown(f"##### TRIX (EMA {p_trix})")
        if "TRIX" in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["TRIX"], mode="lines", name="TRIX",
                                     line=dict(color=C_PRIMARY, width=1.5)))
            fig.add_hline(y=0, line_dash="dash", line_color=C_MUTED)
            _chart_layout(fig, 300)
            st.plotly_chart(fig, use_container_width=True)

        # Ulcer Index
        st.markdown(f"##### Ulcer Index ({p_ulcer})")
        if "Ulcer_Index" in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["Ulcer_Index"], mode="lines",
                                     name="Ulcer Index", line=dict(color=C_ACCENT, width=1.5),
                                     fill="tozeroy", fillcolor="rgba(217,31,22,0.08)"))
            _chart_layout(fig, 300)
            st.plotly_chart(fig, use_container_width=True)

    # DPO
    st.markdown(f"##### DPO — Detrended Price Oscillator ({p_dpo})")
    if "DPO" in df.columns:
        fig = go.Figure()
        dpo_colors = [C_GREEN if v >= 0 else C_RED for v in df["DPO"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["DPO"], name="DPO",
                             marker_color=dpo_colors, opacity=0.7))
        fig.add_hline(y=0, line_dash="dash", line_color=C_MUTED)
        _chart_layout(fig, 300)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ═══════════════ INFOS FONDAMENTALES ═══════════════
with st.expander("📋 Données fondamentales", expanded=False):
    fund = _funds(selected_ticker)
    FUND_GROUPS = {
        "Valorisation": ["marketCap", "enterpriseValue", "trailingPE", "forwardPE",
                         "pegRatio", "priceToBook", "priceToSalesTrailing12Months"],
        "Rentabilité": ["profitMargins", "operatingMargins", "grossMargins",
                        "returnOnAssets", "returnOnEquity"],
        "Croissance": ["revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth"],
        "Bilan": ["totalCash", "totalDebt", "debtToEquity", "currentRatio", "quickRatio"],
        "Dividendes": ["dividendRate", "dividendYield", "payoutRatio"],
        "Analystes": ["recommendationKey", "targetMeanPrice", "targetHighPrice",
                      "targetLowPrice", "numberOfAnalystOpinions"],
    }
    for group_name, keys in FUND_GROUPS.items():
        st.markdown(f"**{group_name}**")
        rows = []
        for k in keys:
            v = fund.get(k)
            if v is not None:
                rows.append({"Indicateur": k, "Valeur": format_fundamental_value(k, v)})
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("Aucune donnée disponible.")
