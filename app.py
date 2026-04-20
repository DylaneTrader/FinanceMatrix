"""
FinanceMatrix - Multi-page Streamlit App
Analyse globale des marchés financiers
"""

import streamlit as st
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────
st.set_page_config(
    page_title="FinanceMatrix",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS injection ───────────────────────────────────────────
_css_path = Path(__file__).parent / "assets" / "style.css"
if _css_path.exists():
    st.markdown(f"<style>{_css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ─── Sidebar branding ───────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='text-align:center;color:#F5F5F5;margin-bottom:0;'>📊 FinanceMatrix</h2>"
        "<p style='text-align:center;color:#94A3B8;font-size:0.82rem;margin-top:4px;'>"
        "Global Market Analytics</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

# ─── Landing page ────────────────────────────────────────────
st.markdown(
    "<h1 style='text-align:center;'>📊 FinanceMatrix</h1>"
    "<p style='text-align:center;color:#64748B;font-size:1.1rem;margin-bottom:2rem;'>"
    "Plateforme d'analyse des marchés financiers mondiaux</p>",
    unsafe_allow_html=True,
)

cols = st.columns(3)

cards = [
    ("🏠", "Accueil", "Dashboard du marché, Top/Flop performers, carte sectorielle"),
    ("📐", "Analyse Technique", "RSI, MACD, Bollinger, SMA/EMA avec signaux"),
    ("📈", "Performances", "Performances calendaires, glissantes et comparatives"),
    ("🔗", "Corrélations & Bêta", "Matrices de corrélation et analyse du bêta"),
    ("💼", "Simulation", "Portefeuille virtuel avec suivi de performance"),
    ("ℹ️", "À propos", "Documentation des indicateurs et formules"),
]

for i, (icon, title, desc) in enumerate(cards):
    with cols[i % 3]:
        st.markdown(
            f"""<div style="background:white;border-radius:14px;padding:22px 18px;
            margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.06);
            border-left:5px solid #0C64CF;min-height:140px;">
            <div style="font-size:2rem;margin-bottom:8px;">{icon}</div>
            <div style="font-weight:700;color:#01467A;font-size:1.05rem;">{title}</div>
            <div style="color:#64748B;font-size:0.85rem;margin-top:6px;">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.8rem;'>"
    "Sélectionnez une page dans la barre latérale pour commencer l'analyse."
    "</p>",
    unsafe_allow_html=True,
)
