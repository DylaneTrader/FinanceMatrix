"""
Page Corrélations & Bêta — Matrices de corrélation et analyse du bêta
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
    calculate_correlation_matrix,
    calculate_beta,
    calculate_rolling_beta,
)

st.set_page_config(page_title="Corrélations & Bêta - FinanceMatrix", page_icon="🔗", layout="wide")

_css = Path(__file__).parents[1] / "assets" / "style.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

C_PRIMARY = "#01467A"
C_GREEN = "#10B981"
C_RED = "#EF4444"
C_LINE = "#0C64CF"
C_MUTED = "#64748B"

st.title("🔗 Corrélations & Bêta")

# ── Sélection ──
sector_names = list(SECTOR_TICKERS.keys())
selected_sector = st.sidebar.selectbox("🏭 Secteur", sector_names, index=0)
tickers = SECTOR_TICKERS[selected_sector]


@st.cache_data(ttl=300, show_spinner="Chargement…")
def _fetch(tickers_tuple, period):
    return fetch_multiple_tickers(list(tickers_tuple), period=period)


prices = _fetch(tuple(tickers), "1y")
if prices.empty:
    st.error("Aucune donnée.")
    st.stop()

st.markdown("---")

tab_corr, tab_beta = st.tabs(["📊 Corrélations", "📉 Analyse Bêta"])

# ══════════ CORRÉLATIONS ══════════
with tab_corr:
    st.subheader("Matrice de Corrélation")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        corr_method = st.selectbox("📐 Méthode", ["pearson", "spearman"],
                                   format_func=lambda x: "Pearson" if x == "pearson" else "Spearman")
    with c2:
        max_assets = st.slider("Nombre max d'actifs", 5, 50, min(20, len(prices.columns)))
    with c3:
        try:
            from scipy.cluster.hierarchy import linkage, leaves_list
            from scipy.spatial.distance import squareform
            _HAS_SCIPY = True
        except ImportError:
            _HAS_SCIPY = False
        cluster = st.checkbox("🧬 Clustering hiérarchique", value=_HAS_SCIPY, disabled=not _HAS_SCIPY)

    display_prices = prices.iloc[:, :max_assets] if len(prices.columns) > max_assets else prices
    corr_matrix = calculate_correlation_matrix(display_prices, method=corr_method)

    if cluster and _HAS_SCIPY and len(corr_matrix) > 2:
        try:
            dist = 1 - corr_matrix.fillna(0).abs()
            np.fill_diagonal(dist.values, 0)
            condensed = squareform(dist.values, checks=False)
            Z = linkage(condensed, method="average")
            order = leaves_list(Z)
            ordered = corr_matrix.columns[order]
            corr_matrix = corr_matrix.loc[ordered, ordered]
        except Exception:
            pass

    fig = px.imshow(
        corr_matrix, labels=dict(color="Corrélation"),
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="equal",
    )
    fig.update_layout(
        title=f"Corrélation ({corr_method.capitalize()}) — {selected_sector}",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C_PRIMARY), height=700,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Stats
    st.markdown("##### 📊 Statistiques")
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    vals = corr_matrix.where(mask).stack()
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("Moyenne", f"{vals.mean():.3f}")
    with mc2:
        st.metric("Médiane", f"{vals.median():.3f}")
    with mc3:
        st.metric("Max", f"{vals.max():.3f}")
    with mc4:
        st.metric("Min", f"{vals.min():.3f}")

    # Top paires
    with st.expander("🔝 Top 10 paires les plus corrélées"):
        pairs = []
        cols_list = corr_matrix.columns.tolist()
        for i in range(len(cols_list)):
            for j in range(i + 1, len(cols_list)):
                pairs.append({"Action 1": cols_list[i], "Action 2": cols_list[j],
                               "Corrélation": corr_matrix.iloc[i, j]})
        pairs_df = pd.DataFrame(pairs).sort_values("Corrélation", ascending=False).head(10)
        st.dataframe(pairs_df.style.format({"Corrélation": "{:.3f}"}),
                     use_container_width=True, hide_index=True)

    with st.expander("📉 Top 10 paires les moins corrélées"):
        pairs_low = pd.DataFrame(pairs).sort_values("Corrélation").head(10)
        st.dataframe(pairs_low.style.format({"Corrélation": "{:.3f}"}),
                     use_container_width=True, hide_index=True)

# ══════════ ANALYSE BÊTA ══════════
with tab_beta:
    st.subheader("📉 Analyse du Bêta")

    st.markdown(
        "<div style='background:white;padding:18px;border-radius:12px;"
        "border-left:5px solid #0C64CF;margin-bottom:1rem;'>"
        "<h4 style='margin:0 0 8px;'>📚 Qu'est-ce que le Bêta ?</h4>"
        "<p style='margin:0;'>Le <b>bêta (β)</b> mesure la sensibilité d'une action aux mouvements du marché.</p>"
        "<ul style='margin:8px 0 0;'>"
        "<li><b>β = 1</b> : évolue comme le marché</li>"
        "<li><b>β &gt; 1</b> : plus volatile (amplifie)</li>"
        "<li><b>β &lt; 1</b> : moins volatile (atténue)</li>"
        "<li><b>β &lt; 0</b> : direction inverse (rare)</li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )

    cb1, cb2, cb3 = st.columns(3)
    with cb1:
        selected_action = st.selectbox("📈 Action", sorted(prices.columns.tolist()),
                                       key="beta_action")
    with cb2:
        bench_options = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow Jones": "^DJI",
                         "Russell 2000": "^RUT"}
        bench_label = st.selectbox("📊 Benchmark", list(bench_options.keys()), key="beta_bench")
        bench_ticker = bench_options[bench_label]
    with cb3:
        beta_periods = {"Toute la période": None, "3 mois": 65, "6 mois": 130,
                        "1 an": 252, "2 ans": 504}
        beta_period_label = st.selectbox("📅 Période", list(beta_periods.keys()), index=3,
                                         key="beta_period")
        beta_period_days = beta_periods[beta_period_label]

    # Fetch benchmark
    @st.cache_data(ttl=300)
    def _fetch_bench(ticker):
        return fetch_multiple_tickers([ticker], period="2y")

    bench_prices = _fetch_bench(bench_ticker)

    if selected_action and not bench_prices.empty and bench_ticker in bench_prices.columns:
        stock_series = prices[selected_action]
        index_series = bench_prices[bench_ticker]

        beta_val = calculate_beta(stock_series, index_series, beta_period_days)

        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            if not np.isnan(beta_val):
                tag = "Agressif" if beta_val > 1.1 else ("Défensif" if beta_val < 0.9 else "Neutre")
                st.metric("Bêta", f"{beta_val:.3f}", delta=tag)
            else:
                st.metric("Bêta", "N/A")
        with rc2:
            stock_ret = stock_series.pct_change().dropna()
            if beta_period_days:
                stock_ret = stock_ret.tail(beta_period_days)
            st.metric("Vol. Action", f"{stock_ret.std() * np.sqrt(252) * 100:.1f}%")
        with rc3:
            idx_ret = index_series.pct_change().dropna()
            if beta_period_days:
                idx_ret = idx_ret.tail(beta_period_days)
            st.metric(f"Vol. {bench_label}", f"{idx_ret.std() * np.sqrt(252) * 100:.1f}%")
        with rc4:
            common = stock_ret.index.intersection(idx_ret.index)
            corr_val = stock_ret.loc[common].corr(idx_ret.loc[common]) if len(common) > 10 else np.nan
            st.metric("Corrélation", f"{corr_val:.3f}" if not np.isnan(corr_val) else "N/A")

        # Bêta glissant
        st.markdown("##### 📈 Bêta glissant (60 jours)")
        rolling_b = calculate_rolling_beta(stock_series, index_series, window=60)
        if not rolling_b.empty:
            fig_rb = go.Figure()
            fig_rb.add_trace(go.Scatter(x=rolling_b.index, y=rolling_b.values, mode="lines",
                                        name="Bêta glissant", line=dict(color=C_LINE, width=2)))
            fig_rb.add_hline(y=1, line_dash="dash", line_color=C_MUTED, opacity=0.5)
            fig_rb.update_layout(
                height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=C_PRIMARY), hovermode="x unified",
                yaxis_title="Bêta",
            )
            fig_rb.update_xaxes(gridcolor="#E2E8F0")
            fig_rb.update_yaxes(gridcolor="#E2E8F0")
            st.plotly_chart(fig_rb, use_container_width=True)

        # Scatter rendements
        st.markdown("##### 🔍 Nuage de points des rendements")
        common = stock_series.pct_change().dropna().index.intersection(
            index_series.pct_change().dropna().index
        )
        s_ret = stock_series.pct_change().loc[common] * 100
        i_ret = index_series.pct_change().loc[common] * 100
        if beta_period_days:
            s_ret = s_ret.tail(beta_period_days)
            i_ret = i_ret.tail(beta_period_days)
        scatter_df = pd.DataFrame({bench_label: i_ret, selected_action: s_ret}).dropna()
        if not scatter_df.empty:
            fig_sc = px.scatter(scatter_df, x=bench_label, y=selected_action,
                                trendline="ols", opacity=0.5,
                                labels={bench_label: f"Rendement {bench_label} (%)",
                                        selected_action: f"Rendement {selected_action} (%)"},
                                color_discrete_sequence=[C_LINE])
            fig_sc.update_layout(
                height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=C_PRIMARY),
            )
            fig_sc.update_xaxes(gridcolor="#E2E8F0")
            fig_sc.update_yaxes(gridcolor="#E2E8F0")
            st.plotly_chart(fig_sc, use_container_width=True)
    else:
        st.warning("Données insuffisantes pour l'analyse du bêta.")
