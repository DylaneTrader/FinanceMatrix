"""
Page Analyse Technique — Indicateurs complets avec signaux
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
    calculate_indicators,
    get_ticker_info,
    get_fundamentals,
    format_fundamental_value,
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


@st.cache_data(ttl=300, show_spinner="Chargement des données…")
def _fetch(ticker, period):
    df = fetch_data(ticker, period=period)
    if df is not None:
        df = calculate_indicators(df)
    return df


@st.cache_data(ttl=600)
def _info(ticker):
    return get_ticker_info(ticker)


@st.cache_data(ttl=600)
def _funds(ticker):
    return get_fundamentals(ticker)


df = _fetch(selected_ticker, selected_period)
if df is None or df.empty:
    st.error(f"Aucune donnée pour {selected_ticker}. Essayez un autre ticker.")
    st.stop()

info = _info(selected_ticker)
st.markdown(f"**{info.get('longName') or info.get('shortName') or selected_ticker}** — "
            f"{info.get('sector', '')} · {info.get('industry', '')}")

st.markdown("---")


# ═══════════════ HELPERS ═══════════════
def _safe(col, idx=-1):
    """Get last (or idx) value of a column safely."""
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
sma20_v = _safe("SMA_20")
sma50_v = _safe("SMA_50")
adx_val = _safe("ADX")
cci_val = _safe("CCI")
close_last = float(df["Close"].iloc[-1])

# RSI card
if np.isnan(rsi_val):
    rsi_card = _signal_card("RSI (14)", "—", "Indisponible", C_MUTED)
elif rsi_val > 70:
    rsi_card = _signal_card("RSI (14)", f"{rsi_val:.1f}", "🔴 Suracheté", C_RED)
elif rsi_val < 30:
    rsi_card = _signal_card("RSI (14)", f"{rsi_val:.1f}", "🟢 Survendu", C_GREEN)
else:
    rsi_card = _signal_card("RSI (14)", f"{rsi_val:.1f}", "⚪ Neutre", C_MUTED)

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
    if adx_val > 25:
        adx_card = _signal_card("ADX", f"{adx_val:.1f}", "🟢 Tendance forte", C_GREEN)
    else:
        adx_card = _signal_card("ADX", f"{adx_val:.1f}", "⚪ Pas de tendance", C_MUTED)
else:
    adx_card = _signal_card("ADX", "—", "Indisponible", C_MUTED)

# Prix vs SMA 50
if not np.isnan(sma50_v):
    px_diff = (close_last / sma50_v - 1) * 100
    if px_diff > 0:
        px_card = _signal_card("Prix vs SMA 50", f"{px_diff:+.1f}%", "🟢 Au-dessus", C_GREEN)
    else:
        px_card = _signal_card("Prix vs SMA 50", f"{px_diff:+.1f}%", "🔴 En-dessous", C_RED)
else:
    px_card = _signal_card("Prix vs SMA 50", "—", "Indisponible", C_MUTED)

# CCI card
if not np.isnan(cci_val):
    if cci_val > 100:
        cci_card = _signal_card("CCI (20)", f"{cci_val:.0f}", "🔴 Suracheté", C_RED)
    elif cci_val < -100:
        cci_card = _signal_card("CCI (20)", f"{cci_val:.0f}", "🟢 Survendu", C_GREEN)
    else:
        cci_card = _signal_card("CCI (20)", f"{cci_val:.0f}", "⚪ Neutre", C_MUTED)
else:
    cci_card = _signal_card("CCI (20)", "—", "Indisponible", C_MUTED)

# Stochastic card
stoch_k = _safe("Stoch_K")
if not np.isnan(stoch_k):
    if stoch_k > 80:
        stoch_card = _signal_card("Stochastic %K", f"{stoch_k:.1f}", "🔴 Suracheté", C_RED)
    elif stoch_k < 20:
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
    st.subheader("RSI — Relative Strength Index")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.6, 0.4], subplot_titles=("Prix", "RSI (14)"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_LINE, width=2)), row=1, col=1)
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI",
                                 line=dict(color=C_PRIMARY, width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=C_RED, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=C_GREEN, row=2, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(16,185,129,0.08)", line_width=0, row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    _chart_layout(fig, 580)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Stochastic RSI subplot
    if "StochRSI_K" in df.columns:
        st.markdown("##### Stochastic RSI")
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
        lbl = "🔴 Suracheté" if rsi_val > 70 else ("🟢 Survendu" if rsi_val < 30 else "⚪ Neutre")
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
    # VWAP
    if "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP",
                                 line=dict(color="#F59E0B", width=1.2, dash="dot")))
    # Parabolic SAR
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
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.6, 0.4], subplot_titles=("Prix", "MACD"))
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
            st.metric("ATR (14)", f"{_safe('ATR'):.2f}" if not np.isnan(_safe("ATR")) else "—")

# ──────────────── Stochastic ────────────────
with tab_stoch:
    st.subheader("Oscillateur Stochastique")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.6, 0.4], subplot_titles=("Prix", "Stochastic (14,3)"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_LINE, width=2)), row=1, col=1)
    if "Stoch_K" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_K"], mode="lines", name="%K",
                                 line=dict(color=C_PRIMARY, width=1.5)), row=2, col=1)
    if "Stoch_D" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_D"], mode="lines", name="%D",
                                 line=dict(color=C_RED, width=1.2, dash="dash")), row=2, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color=C_RED, row=2, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color=C_GREEN, row=2, col=1)
    fig.add_hrect(y0=80, y1=100, fillcolor="rgba(239,68,68,0.08)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=0, y1=20, fillcolor="rgba(16,185,129,0.08)", line_width=0, row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    _chart_layout(fig, 550)
    st.plotly_chart(fig, use_container_width=True)

    # Williams %R
    st.markdown("##### Williams %R")
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
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.55, 0.45], subplot_titles=("Prix", "ADX / +DI / -DI"))
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
    fig.add_hline(y=25, line_dash="dash", line_color=C_MUTED, opacity=0.5, row=2, col=1)
    _chart_layout(fig, 580)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "<div style='background:white;padding:14px;border-radius:10px;border-left:4px solid #0C64CF;'>"
        "<strong>Interprétation ADX :</strong><br>"
        "• <b>ADX &gt; 25</b> : tendance forte<br>"
        "• <b>ADX &lt; 20</b> : marché sans tendance (range)<br>"
        "• <b>+DI &gt; -DI</b> : tendance haussière · <b>-DI &gt; +DI</b> : tendance baissière"
        "</div>", unsafe_allow_html=True)

    # Aroon
    st.markdown("##### Aroon Oscillator")
    if "Aroon_Up" in df.columns:
        fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                             row_heights=[0.5, 0.5], subplot_titles=("Aroon Up / Down", "Aroon Oscillator"))
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
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_PRIMARY, width=2)))
    if "Ichimoku_Tenkan" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_Tenkan"], name="Tenkan-sen (9)",
                                 line=dict(color="#3B82F6", width=1.2)))
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_Kijun"], name="Kijun-sen (26)",
                                 line=dict(color=C_RED, width=1.2)))
    if "Ichimoku_SpanA" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_SpanA"], name="Senkou Span A",
                                 line=dict(color=C_GREEN, width=0.8)))
    if "Ichimoku_SpanB" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_SpanB"], name="Senkou Span B",
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

    # OBV
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        row_heights=[0.4, 0.3, 0.3],
                        subplot_titles=("Prix + Volume", "OBV (On-Balance Volume)", "CMF / MFI"))
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
        st.markdown("##### MFI — Money Flow Index")
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
        st.markdown("##### Force Index (13)")
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

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Prix",
                             line=dict(color=C_PRIMARY, width=2)))

    if channel_type == "Keltner" and "Keltner_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Keltner_Upper"], name="Keltner Haut",
                                 line=dict(color=C_RED, width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["Keltner_Lower"], name="Keltner Bas",
                                 line=dict(color=C_GREEN, width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(12,100,207,0.06)"))
        fig.add_trace(go.Scatter(x=df.index, y=df["Keltner_Mid"], name="EMA 20",
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

    mc1, mc2 = st.columns(2)

    with mc1:
        # CCI
        st.markdown("##### CCI — Commodity Channel Index")
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
        st.markdown("##### ROC — Rate of Change")
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
        st.markdown("##### TRIX")
        if "TRIX" in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["TRIX"], mode="lines", name="TRIX",
                                     line=dict(color=C_PRIMARY, width=1.5)))
            fig.add_hline(y=0, line_dash="dash", line_color=C_MUTED)
            _chart_layout(fig, 300)
            st.plotly_chart(fig, use_container_width=True)

        # Ulcer Index
        st.markdown("##### Ulcer Index")
        if "Ulcer_Index" in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["Ulcer_Index"], mode="lines",
                                     name="Ulcer Index", line=dict(color=C_ACCENT, width=1.5),
                                     fill="tozeroy", fillcolor="rgba(217,31,22,0.08)"))
            _chart_layout(fig, 300)
            st.plotly_chart(fig, use_container_width=True)

    # DPO
    st.markdown("##### DPO — Detrended Price Oscillator")
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
