"""
Page Simulation Portefeuille — Portefeuille virtuel avec suivi de performance
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_handler import SECTOR_TICKERS, fetch_multiple_tickers

st.set_page_config(page_title="Simulation - FinanceMatrix", page_icon="💼", layout="wide")

_css = Path(__file__).parents[1] / "assets" / "style.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

C_PRIMARY = "#01467A"
C_GREEN = "#10B981"
C_RED = "#EF4444"
C_LINE = "#0C64CF"

st.title("💼 Simulation Portefeuille")

# ── Fichier de persistance ──
PORTFOLIO_FILE = Path(__file__).parents[1] / "data" / "portfolio.json"
PORTFOLIO_FILE.parent.mkdir(exist_ok=True)


def _load_portfolio() -> dict:
    if PORTFOLIO_FILE.exists():
        return json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    return {"cash": 100_000.0, "positions": [], "history": []}


def _save_portfolio(pf: dict):
    PORTFOLIO_FILE.write_text(json.dumps(pf, indent=2, default=str), encoding="utf-8")


# Charger en session
if "portfolio" not in st.session_state:
    st.session_state.portfolio = _load_portfolio()

pf = st.session_state.portfolio

# ═══════════════ ACTIONS ═══════════════
st.markdown("---")

tab_trade, tab_positions, tab_perf = st.tabs(["🛒 Passer un ordre", "📋 Positions", "📈 Performance"])

# ── Passer un ordre ──
with tab_trade:
    st.subheader("🛒 Passer un ordre")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    all_tickers = sorted(set(t for tl in SECTOR_TICKERS.values() for t in tl))
    with c1:
        order_ticker = st.selectbox("Ticker", all_tickers, key="order_ticker")
    with c2:
        order_side = st.radio("Type", ["Achat", "Vente"], horizontal=True, key="order_side")
    with c3:
        order_qty = st.number_input("Quantité", min_value=1, value=10, step=1, key="order_qty")
    with c4:
        st.metric("💵 Cash disponible", f"${pf['cash']:,.2f}")

    # Prix actuel
    @st.cache_data(ttl=60)
    def _get_last_price(ticker):
        data = fetch_multiple_tickers([ticker], period="5d")
        if data.empty or ticker not in data.columns:
            return None
        return float(data[ticker].dropna().iloc[-1])

    current_price = _get_last_price(order_ticker)
    if current_price:
        total = current_price * order_qty
        st.info(f"Prix actuel de **{order_ticker}** : **${current_price:,.2f}** · "
                f"Total : **${total:,.2f}**")

        if st.button("✅ Exécuter l'ordre", type="primary"):
            if order_side == "Achat":
                if total > pf["cash"]:
                    st.error("Cash insuffisant !")
                else:
                    pf["cash"] -= total
                    # Vérifier si position existante
                    existing = [p for p in pf["positions"] if p["ticker"] == order_ticker]
                    if existing:
                        pos = existing[0]
                        old_total = pos["avg_price"] * pos["qty"]
                        pos["qty"] += order_qty
                        pos["avg_price"] = (old_total + total) / pos["qty"]
                    else:
                        pf["positions"].append({
                            "ticker": order_ticker,
                            "qty": order_qty,
                            "avg_price": current_price,
                            "date": datetime.now().isoformat(),
                        })
                    pf["history"].append({
                        "date": datetime.now().isoformat(),
                        "ticker": order_ticker,
                        "side": "BUY",
                        "qty": order_qty,
                        "price": current_price,
                    })
                    _save_portfolio(pf)
                    st.success(f"✅ Achat de {order_qty} × {order_ticker} à ${current_price:,.2f}")
                    st.rerun()
            else:  # Vente
                existing = [p for p in pf["positions"] if p["ticker"] == order_ticker]
                if not existing or existing[0]["qty"] < order_qty:
                    st.error("Position insuffisante pour vendre !")
                else:
                    pos = existing[0]
                    pf["cash"] += total
                    pos["qty"] -= order_qty
                    if pos["qty"] == 0:
                        pf["positions"].remove(pos)
                    pf["history"].append({
                        "date": datetime.now().isoformat(),
                        "ticker": order_ticker,
                        "side": "SELL",
                        "qty": order_qty,
                        "price": current_price,
                    })
                    _save_portfolio(pf)
                    st.success(f"✅ Vente de {order_qty} × {order_ticker} à ${current_price:,.2f}")
                    st.rerun()
    else:
        st.warning(f"Impossible de récupérer le prix de {order_ticker}.")

# ── Positions ──
with tab_positions:
    st.subheader("📋 Positions actuelles")

    if not pf["positions"]:
        st.info("Aucune position. Passez un ordre pour commencer.")
    else:
        pos_data = []
        total_market_value = 0
        total_cost = 0

        for pos in pf["positions"]:
            cp = _get_last_price(pos["ticker"])
            if cp is None:
                cp = pos["avg_price"]
            mv = cp * pos["qty"]
            cost = pos["avg_price"] * pos["qty"]
            pnl = mv - cost
            pnl_pct = (pnl / cost) * 100 if cost != 0 else 0
            total_market_value += mv
            total_cost += cost
            pos_data.append({
                "Ticker": pos["ticker"],
                "Qté": pos["qty"],
                "PRU": f"${pos['avg_price']:,.2f}",
                "Prix actuel": f"${cp:,.2f}",
                "Valeur": f"${mv:,.2f}",
                "P&L": f"${pnl:,.2f}",
                "P&L %": f"{pnl_pct:+.2f}%",
            })

        st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)

        # Résumé
        total_pnl = total_market_value - total_cost
        portfolio_value = pf["cash"] + total_market_value
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            st.metric("💵 Cash", f"${pf['cash']:,.2f}")
        with rc2:
            st.metric("📊 Valeur marché", f"${total_market_value:,.2f}")
        with rc3:
            st.metric("💰 Valeur totale", f"${portfolio_value:,.2f}")
        with rc4:
            color = C_GREEN if total_pnl >= 0 else C_RED
            st.metric("📈 P&L total", f"${total_pnl:,.2f}",
                      delta=f"{(total_pnl / total_cost * 100):+.2f}%" if total_cost else "0%")

        # Répartition par position
        st.markdown("##### 🥧 Répartition du portefeuille")
        import plotly.express as px
        alloc_data = [{"Actif": p["Ticker"], "Valeur": float(p["Valeur"].replace("$", "").replace(",", ""))}
                      for p in pos_data]
        alloc_data.append({"Actif": "Cash", "Valeur": pf["cash"]})
        alloc_df = pd.DataFrame(alloc_data)
        fig_pie = px.pie(alloc_df, values="Valeur", names="Actif",
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color=C_PRIMARY), height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Reset
    st.markdown("---")
    if st.button("🔄 Réinitialiser le portefeuille", type="secondary"):
        st.session_state.portfolio = {"cash": 100_000.0, "positions": [], "history": []}
        _save_portfolio(st.session_state.portfolio)
        st.success("Portefeuille réinitialisé à $100,000.")
        st.rerun()

# ── Historique ──
with tab_perf:
    st.subheader("📈 Historique des transactions")
    if not pf["history"]:
        st.info("Aucune transaction enregistrée.")
    else:
        hist_df = pd.DataFrame(pf["history"])
        hist_df["total"] = hist_df["price"] * hist_df["qty"]
        hist_df.columns = ["Date", "Ticker", "Type", "Qté", "Prix", "Total"]
        hist_df = hist_df.sort_values("Date", ascending=False)
        st.dataframe(
            hist_df.style.format({"Prix": "${:,.2f}", "Total": "${:,.2f}"}),
            use_container_width=True, hide_index=True,
        )
