"""
Page Accueil - Dashboard du marché, Top/Flop, Carte sectorielle
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_handler import (
    SECTOR_TICKERS,
    fetch_multiple_tickers,
    calculate_returns_for_period,
    get_top_flop_performers,
    get_market_caps,
)

st.set_page_config(page_title="Accueil - FinanceMatrix", page_icon="🏠", layout="wide")

# CSS
_css = Path(__file__).parents[1] / "assets" / "style.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

st.title("🏠 Accueil — Tableau de bord du marché")

# ── Couleurs FinanceMatrix ──
COLOR_PRIMARY = "#01467A"
COLOR_GREEN = "#10B981"
COLOR_RED = "#EF4444"
COLOR_MUTED = "#64748B"

# ── Indices pour le bandeau ──
INDEX_TICKERS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow Jones": "^DJI",
                 "Russell 2000": "^RUT", "CAC 40": "^FCHI", "DAX": "^GDAXI"}


@st.cache_data(ttl=300, show_spinner="Chargement des indices…")
def _fetch_indices():
    return fetch_multiple_tickers(list(INDEX_TICKERS.values()), period="1mo")


@st.cache_data(ttl=300, show_spinner="Chargement du secteur…")
def _fetch_sector(tickers: tuple, period: str):
    return fetch_multiple_tickers(list(tickers), period=period)


@st.cache_data(ttl=600, show_spinner="Chargement des capitalisations…")
def _fetch_market_caps(tickers: tuple):
    return get_market_caps(list(tickers))


def _signed(v):
    if pd.isna(v):
        return "<span style='font-size:1.3rem;font-weight:700;'>—</span>"
    cls = COLOR_GREEN if v >= 0 else COLOR_RED
    return f"<span style='font-size:1.3rem;font-weight:700;color:{cls};'>{v:+.2f}%</span>"


def _sparkline(series: pd.Series, color: str) -> go.Figure:
    s = series.dropna().tail(20)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(s))), y=s.values, mode="lines",
        line=dict(color=color, width=2), hoverinfo="skip", showlegend=False,
    ))
    fig.update_layout(
        height=45, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def _format_cap(v):
    if v >= 1e12:
        return f"${v / 1e12:.1f}T"
    if v >= 1e9:
        return f"${v / 1e9:.1f}B"
    if v >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v:,.0f}"


# ═════════════════════ Bandeau marché ═════════════════════
try:
    idx_prices = _fetch_indices()
    if not idx_prices.empty:
        items_html = ""
        for label, ticker in INDEX_TICKERS.items():
            if ticker in idx_prices.columns:
                s = idx_prices[ticker].dropna()
                if len(s) >= 2:
                    last = float(s.iloc[-1])
                    var_day = (s.iloc[-1] / s.iloc[-2] - 1) * 100
                    items_html += f"""
                    <div class="mb-item">
                        <span class="mb-label">{label}</span>
                        <span class="mb-value">{last:,.2f}</span>
                        {_signed(var_day)}
                    </div>"""
        if items_html:
            st.markdown(f'<div class="market-band">{items_html}</div>', unsafe_allow_html=True)
except Exception:
    st.warning("Impossible de charger les indices. Vérifiez votre connexion.")

st.markdown("")

# ═════════════════════ Filtres ═════════════════════
col_sector, col_period = st.columns([1, 1])
with col_sector:
    sector_names = ["Tous"] + list(SECTOR_TICKERS.keys())
    selected_sector = st.selectbox("🏭 Secteur", sector_names, index=0)

with col_period:
    period_labels = {
        "1D": "1 Jour", "1W": "1 Semaine", "1M": "1 Mois",
        "3M": "3 Mois", "6M": "6 Mois", "1Y": "1 An",
    }
    selected_period = st.selectbox(
        "📅 Période",
        list(period_labels.keys()),
        format_func=lambda x: period_labels[x],
        index=2,
    )

# ═════════════════════ Données secteur ═════════════════════
if selected_sector == "Tous":
    all_tickers = []
    sector_of = {}
    for sec, tk_list in SECTOR_TICKERS.items():
        for t in tk_list[:8]:
            all_tickers.append(t)
            sector_of[t] = sec
    tickers = all_tickers
    display_sector = "Tous les secteurs"
else:
    tickers = SECTOR_TICKERS[selected_sector]
    sector_of = {t: selected_sector for t in tickers}
    display_sector = selected_sector

period_map = {"1D": "5d", "1W": "1mo", "1M": "3mo", "3M": "6mo", "6M": "1y", "1Y": "2y"}
dl_period = period_map.get(selected_period, "3mo")

with st.spinner(f"Téléchargement de {len(tickers)} tickers ({display_sector})…"):
    prices = _fetch_sector(tuple(tickers), dl_period)

if prices.empty:
    st.error("Aucune donnée récupérée. Vérifiez votre connexion Internet.")
    st.stop()

returns = calculate_returns_for_period(prices, selected_period)
performers = get_top_flop_performers(returns, n=5)

st.caption(f"📊 {len(returns.dropna())} actions éligibles · {period_labels[selected_period]}")

# ═════════════════════ Top / Flop ═════════════════════
col_top, col_flop = st.columns(2)


def _render_performer(symbol: str, rank: int, ret: float, kind: str):
    cls = "top" if kind == "top" else "flop"
    ret_cls = "pos" if ret >= 0 else "neg"
    sparkline_color = COLOR_GREEN if kind == "top" else COLOR_RED
    col_head, col_spark = st.columns([3, 1])
    with col_head:
        st.markdown(f"""
        <div class="perf-card {cls}">
            <div class="perf-rank">#{rank}</div>
            <div>
                <div class="perf-name">{symbol}</div>
            </div>
            <div class="perf-return {ret_cls}">{ret:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col_spark:
        if symbol in prices.columns:
            st.plotly_chart(
                _sparkline(prices[symbol], sparkline_color),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"spark_{kind}_{symbol}_{rank}",
            )


with col_top:
    st.markdown("### 🚀 Top 5 performers")
    st.caption(f"Meilleures performances · {period_labels[selected_period]}")
    for i, (symbol, ret) in enumerate(performers["top"].items(), 1):
        _render_performer(symbol, i, ret, "top")

with col_flop:
    st.markdown("### 📉 Flop 5 performers")
    st.caption(f"Pires performances · {period_labels[selected_period]}")
    for i, (symbol, ret) in enumerate(performers["flop"].items(), 1):
        _render_performer(symbol, i, ret, "flop")

st.markdown("---")

# ═════════════════════ Carte sectorielle (treemap) ═════════════════════
st.markdown("### 🗺️ Carte sectorielle")
st.caption("Taille = capitalisation boursière · Couleur = rendement sur la période")

tm_tickers = list(returns.dropna().index)
if tm_tickers:
    with st.spinner("Chargement des capitalisations boursières…"):
        caps = _fetch_market_caps(tuple(tm_tickers))

    tm_rows = []
    for sym in tm_tickers:
        ret_val = float(returns[sym])
        cap_val = caps.get(sym, 1.0)
        sec = sector_of.get(sym, "Autre")
        tm_rows.append({
            "Symbol": sym,
            "Secteur": sec,
            "Rendement": ret_val,
            "MarketCap": cap_val,
            "Cap_Label": _format_cap(cap_val) if cap_val > 1 else "",
        })

    tm_df = pd.DataFrame(tm_rows)

    if not tm_df.empty:
        path_levels = ([px.Constant(display_sector), "Secteur", "Symbol"]
                       if selected_sector == "Tous"
                       else [px.Constant(display_sector), "Symbol"])
        fig_tm = px.treemap(
            tm_df,
            path=path_levels,
            values="MarketCap",
            color="Rendement",
            color_continuous_scale=[(0.0, COLOR_RED), (0.5, "#F5F5F5"), (1.0, COLOR_GREEN)],
            color_continuous_midpoint=0,
            hover_data={"Rendement": ":.2f", "MarketCap": ":,.0f"},
            custom_data=["Rendement", "Cap_Label"],
        )
        fig_tm.update_traces(
            hovertemplate="<b>%{label}</b><br>Rendement: %{customdata[0]:+.2f}%<br>"
                          "Cap: %{customdata[1]}<extra></extra>",
            root_color="rgba(0,0,0,0)",
            textinfo="label+percent parent",
        )
        fig_tm.update_layout(
            height=550,
            margin=dict(l=8, r=8, t=10, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar=dict(title=f"Rend. ({period_labels[selected_period]})",
                                    tickformat=".1f"),
            font=dict(color=COLOR_PRIMARY),
        )
        st.plotly_chart(fig_tm, use_container_width=True)
    else:
        st.info("Pas assez de données pour la carte sectorielle.")
else:
    st.info("Pas assez de données pour la carte sectorielle.")

# ═════════════════════ Tableau complet ═════════════════════
with st.expander("📊 Voir tous les rendements", expanded=False):
    ret_df = pd.DataFrame({
        "Symbole": returns.index,
        "Secteur": [sector_of.get(s, "") for s in returns.index],
        f"Rendement {period_labels[selected_period]} (%)": returns.values,
    }).dropna().sort_values(
        f"Rendement {period_labels[selected_period]} (%)", ascending=False
    ).reset_index(drop=True)
    st.dataframe(
        ret_df.style.format({f"Rendement {period_labels[selected_period]} (%)": "{:+.2f}%"}),
        use_container_width=True, height=400,
    )
    st.download_button(
        "⬇️ Exporter en CSV",
        data=ret_df.to_csv(index=False).encode("utf-8"),
        file_name=f"rendements_{selected_sector}_{selected_period}.csv",
        mime="text/csv",
    )

st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.75rem;margin-top:2rem;'>"
    "FinanceMatrix · Données fournies par Yahoo Finance</p>",
    unsafe_allow_html=True,
)
