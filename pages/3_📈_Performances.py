"""
Page Performances — Calendaires, Glissantes et Comparatives
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
from pathlib import Path
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_handler import (
    SECTOR_TICKERS,
    fetch_data,
    fetch_multiple_tickers,
    calculate_returns_for_period,
    calculate_calendar_performance,
    calculate_cumulative_returns,
)

st.set_page_config(page_title="Performances - FinanceMatrix", page_icon="📈", layout="wide")

_css = Path(__file__).parents[1] / "assets" / "style.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

C_PRIMARY = "#01467A"
C_GREEN = "#10B981"
C_RED = "#EF4444"
C_MUTED = "#64748B"

st.title("📈 Performances — Calendaires & Glissantes")


def _style_perf(val):
    if pd.isna(val):
        return ""
    color = C_GREEN if val >= 0 else C_RED
    return f"color: {color}; font-weight: bold"


# ═══ SIDEBAR FILTRES ═══
st.sidebar.markdown("### 🔧 Filtres")

# Filtre sectoriel avec option "Tous"
sector_names = ["Tous"] + list(SECTOR_TICKERS.keys())
selected_sector = st.sidebar.selectbox("🏭 Secteur", sector_names, index=0)

if selected_sector == "Tous":
    tickers = []
    for s_tickers in SECTOR_TICKERS.values():
        tickers.extend(s_tickers[:5])  # Top 5 per sector for performance
else:
    tickers = SECTOR_TICKERS[selected_sector]

# Filtre temporel
TIME_PERIODS = {
    "6mo": "6 Mois",
    "1y": "1 An",
    "2y": "2 Ans",
    "5y": "5 Ans",
}
data_period = st.sidebar.selectbox(
    "📅 Horizon de données", list(TIME_PERIODS.keys()),
    format_func=lambda x: TIME_PERIODS[x], index=1,
)

# Indices de référence
BENCHMARK_TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Dow Jones": "^DJI",
    "CAC 40": "^FCHI",
    "MSCI World": "URTH",
    "Euro Stoxx 50": "^STOXX50E",
}


@st.cache_data(ttl=300, show_spinner="Chargement des données…")
def _fetch(tickers_tuple, period):
    return fetch_multiple_tickers(list(tickers_tuple), period=period)


@st.cache_data(ttl=300, show_spinner="Chargement de l'indice…")
def _fetch_bench(ticker, period):
    df = fetch_data(ticker, period=period)
    if df is not None and "Close" in df.columns:
        return df["Close"].rename(ticker)
    return pd.Series(dtype=float)


prices = _fetch(tuple(tickers), data_period)
if prices.empty:
    st.error("Aucune donnée. Vérifiez votre connexion.")
    st.stop()

st.markdown("---")

# ══════════ Tabs ══════════
perf_tab1, perf_tab2, perf_tab3 = st.tabs(
    ["📅 Performances Calendaires", "🔄 Performances Glissantes", "📊 Graphique Comparatif"]
)

# ──────────────── Calendaires ────────────────
with perf_tab1:
    st.markdown("##### Performances Calendaires")
    st.caption("Depuis le début de chaque période calendaire")

    calendar_perfs = {}
    for pt in ["WTD", "MTD", "QTD", "STD", "YTD"]:
        calendar_perfs[pt] = calculate_calendar_performance(prices, pt)

    perf_df = pd.DataFrame(calendar_perfs)
    perf_cols = [c for c in ["WTD", "MTD", "QTD", "STD", "YTD"] if c in perf_df.columns]

    # Heatmap
    st.markdown("###### 🗺️ Heatmap des performances")
    display_df = perf_df.dropna(how="all")
    if not display_df.empty and perf_cols:
        fig_hm = px.imshow(
            display_df[perf_cols].values,
            x=perf_cols,
            y=display_df.index.tolist(),
            color_continuous_scale=[(0.0, C_RED), (0.5, "#F5F5F5"), (1.0, C_GREEN)],
            color_continuous_midpoint=0,
            text_auto=".1f",
            aspect="auto",
            labels=dict(color="Perf. (%)"),
        )
        fig_hm.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=max(250, 30 * len(display_df) + 80),
            margin=dict(l=10, r=10, t=20, b=30),
            font=dict(color=C_PRIMARY),
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    st.markdown("###### 📋 Détail par action")
    if perf_cols and not perf_df.empty:
        # Add sector column if "Tous"
        if selected_sector == "Tous":
            sector_of = {}
            for sec, t_list in SECTOR_TICKERS.items():
                for t in t_list:
                    sector_of[t] = sec
            perf_df.insert(0, "Secteur", perf_df.index.map(lambda t: sector_of.get(t, "")))

        st.dataframe(
            perf_df.style.map(_style_perf, subset=perf_cols).format(
                {c: "{:+.2f}%" for c in perf_cols}
            ),
            use_container_width=True, height=500,
        )
        st.download_button(
            "⬇️ Exporter (CSV)", data=perf_df.to_csv().encode("utf-8"),
            file_name=f"perf_calendaires_{selected_sector}.csv", mime="text/csv",
            key="dl_cal",
        )

# ──────────────── Glissantes ────────────────
with perf_tab2:
    st.markdown("##### Performances Glissantes")
    periods_map = {"1W": "1 Sem", "1M": "1 Mois", "3M": "3 Mois",
                   "6M": "6 Mois", "1Y": "1 An"}
    rolling_perfs = {}
    for period, label in periods_map.items():
        rolling_perfs[label] = calculate_returns_for_period(prices, period)

    rolling_df = pd.DataFrame(rolling_perfs)
    roll_cols = list(periods_map.values())

    if selected_sector == "Tous":
        sector_of = {}
        for sec, t_list in SECTOR_TICKERS.items():
            for t in t_list:
                sector_of[t] = sec
        rolling_df.insert(0, "Secteur", rolling_df.index.map(lambda t: sector_of.get(t, "")))

    st.dataframe(
        rolling_df.style.map(_style_perf, subset=roll_cols).format(
            {c: "{:+.2f}%" for c in roll_cols}
        ),
        use_container_width=True, height=500,
    )
    st.download_button(
        "⬇️ Exporter (CSV)", data=rolling_df.to_csv().encode("utf-8"),
        file_name=f"perf_glissantes_{selected_sector}.csv", mime="text/csv",
        key="dl_roll",
    )

# ──────────────── Graphique comparatif ────────────────
with perf_tab3:
    st.markdown("##### Graphique Comparatif d'Évolution")
    c_sel, c_per = st.columns([2, 1])
    with c_sel:
        available = sorted(prices.columns.tolist())
        default = available[:3] if len(available) >= 3 else available
        selected = st.multiselect("📊 Actions à comparer", available, default=default,
                                  max_selections=10, key="compare_sel")
    with c_per:
        chart_periods = {"1M": "1 Mois", "3M": "3 Mois", "6M": "6 Mois",
                         "1Y": "1 An", "MAX": "Maximum"}
        chart_period = st.selectbox("📅 Période", list(chart_periods.keys()),
                                    format_func=lambda x: chart_periods[x], index=3, key="chart_p")
        chart_mode = st.radio("Mode", ["Base 100", "Drawdown (%)", "Rendement quotidien (%)"],
                              key="chart_mode", horizontal=False)

    # Benchmark comparison
    use_benchmark = st.checkbox("📏 Comparer à un indice de référence", key="use_bench")
    bench_series_list = []
    if use_benchmark:
        bench_names = st.multiselect(
            "Sélectionner les indices", list(BENCHMARK_TICKERS.keys()),
            default=["S&P 500"], key="bench_sel",
        )
        for bn in bench_names:
            bs = _fetch_bench(BENCHMARK_TICKERS[bn], data_period)
            if not bs.empty:
                bench_series_list.append(bs.rename(bn))

    if selected:
        chart_data = prices[selected].copy()

        # Merge benchmark data if any
        for bs in bench_series_list:
            chart_data = chart_data.join(bs, how="outer")

        if chart_period != "MAX":
            days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
            start = prices.index[-1] - timedelta(days=days_map[chart_period])
            chart_data = chart_data.loc[chart_data.index >= pd.Timestamp(start)]

        chart_data = chart_data.dropna(how="all")

        if chart_mode == "Base 100":
            plot_df = calculate_cumulative_returns(chart_data)
            y_title, ref = "Valeur (base 100)", 100
        elif chart_mode == "Drawdown (%)":
            cum = calculate_cumulative_returns(chart_data)
            plot_df = (cum / cum.cummax() - 1) * 100
            y_title, ref = "Drawdown (%)", 0
        else:
            plot_df = chart_data.pct_change() * 100
            y_title, ref = "Rendement quotidien (%)", 0

        fig = go.Figure()
        colors = px.colors.qualitative.Set2
        bench_name_list = [bs.name for bs in bench_series_list]
        for i, col in enumerate(plot_df.columns):
            is_bench = col in bench_name_list
            kw = {}
            if chart_mode == "Drawdown (%)":
                kw = dict(fill="tozeroy", fillcolor="rgba(239,68,68,0.08)")
            line_style = dict(
                color=colors[i % len(colors)],
                width=3 if is_bench else 2,
                dash="dash" if is_bench else "solid",
            )
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df[col], mode="lines",
                name=f"📏 {col}" if is_bench else col,
                line=line_style, **kw,
            ))
        fig.add_hline(y=ref, line_dash="dash", line_color="#94A3B8", opacity=0.5)
        fig.update_layout(
            title=f"{chart_mode} · {chart_periods[chart_period]}",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Date", yaxis_title=y_title,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(color=C_PRIMARY), hovermode="x unified", height=520,
        )
        fig.update_xaxes(gridcolor="#E2E8F0")
        fig.update_yaxes(gridcolor="#E2E8F0")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sélectionnez au moins une action.")
