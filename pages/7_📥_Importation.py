"""
Page Importation — Téléchargement et mise à jour des données locales
"""

import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_handler import SECTOR_TICKERS, has_local_data, _DATA_DIR, _ACTIONS_DIR, _INDICES_DIR, _SOCIETE_DIR

st.set_page_config(page_title="Importation - FinanceMatrix", page_icon="📥", layout="wide")

_css = Path(__file__).parents[1] / "assets" / "style.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

C_PRIMARY = "#01467A"
C_GREEN = "#10B981"
C_RED = "#EF4444"
C_MUTED = "#64748B"

st.title("📥 Importation des données")

st.markdown("""
Cette page permet de **télécharger** et **mettre à jour** les données historiques
depuis Yahoo Finance. Les données sont stockées localement dans le dossier `data/` :

```
data/
├── actions/     # CSV historique par action
├── indices/     # CSV historique par indice/FX/crypto
└── societes/    # JSON info société par ticker
```

En **production**, un workflow **GitHub Actions** met à jour automatiquement chaque jour.
""")

st.markdown("---")


# ═══ ÉTAT DES DONNÉES LOCALES ═══
st.markdown("### 📊 État des données locales")

if has_local_data():
    action_files = list(_ACTIONS_DIR.glob("*_historique.csv")) if _ACTIONS_DIR.exists() else []
    indice_files = list(_INDICES_DIR.glob("*_historique.csv")) if _INDICES_DIR.exists() else []
    info_files = list(_SOCIETE_DIR.glob("*_info.json")) if _SOCIETE_DIR.exists() else []

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("📈 Actions", len(action_files))
    with sc2:
        st.metric("📊 Indices/FX/Crypto", len(indice_files))
    with sc3:
        st.metric("📋 Fiches société", len(info_files))
    with sc4:
        total_tickers = sum(len(v) for v in SECTOR_TICKERS.values())
        done = len(action_files) + len(indice_files)
        pct = int(done / total_tickers * 100) if total_tickers else 0
        st.metric("📦 Couverture", f"{pct}%")

    # Résumé du scraping
    resume_path = _DATA_DIR / "resume_scraping.csv"
    if resume_path.exists():
        with st.expander("📋 Résumé détaillé", expanded=False):
            resume = pd.read_csv(resume_path, sep=";", decimal=",")
            st.dataframe(resume, use_container_width=True, hide_index=True)

    # Dernière mise à jour
    all_csvs = action_files + indice_files
    if all_csvs:
        latest = max(f.stat().st_mtime for f in all_csvs)
        latest_dt = datetime.fromtimestamp(latest)
        age = datetime.now() - latest_dt
        if age.days == 0:
            age_str = "Aujourd'hui"
            age_color = C_GREEN
        elif age.days == 1:
            age_str = "Hier"
            age_color = C_GREEN
        elif age.days <= 3:
            age_str = f"Il y a {age.days} jours"
            age_color = "#F59E0B"
        else:
            age_str = f"Il y a {age.days} jours"
            age_color = C_RED
        st.markdown(
            f"<div style='background:white;padding:12px 16px;border-radius:10px;"
            f"border-left:4px solid {age_color};margin:10px 0;'>"
            f"🕐 Dernière mise à jour : <b>{latest_dt.strftime('%d/%m/%Y %H:%M')}</b> — "
            f"<span style='color:{age_color};font-weight:600;'>{age_str}</span></div>",
            unsafe_allow_html=True,
        )
else:
    st.warning("⚠️ Aucune donnée locale. Lancez un premier téléchargement ci-dessous.")

st.markdown("---")

# ═══ CONFIGURATION DU TÉLÉCHARGEMENT ═══
st.markdown("### ⚙️ Téléchargement")

col1, col2 = st.columns(2)

with col1:
    sector_names = ["Tous"] + list(SECTOR_TICKERS.keys())
    import_sector = st.selectbox("🏭 Secteur", sector_names, index=0, key="imp_sector")

    if import_sector == "Tous":
        import_tickers = []
        seen = set()
        for t_list in SECTOR_TICKERS.values():
            for t in t_list:
                if t not in seen:
                    import_tickers.append(t)
                    seen.add(t)
    else:
        import_tickers = SECTOR_TICKERS[import_sector]

with col2:
    mode = st.radio(
        "Mode", ["🔄 Mise à jour incrémentale", "📥 Téléchargement complet"],
        key="imp_mode", horizontal=True,
    )
    incremental = mode.startswith("🔄")

st.markdown(f"**{len(import_tickers)} tickers** sélectionnés · "
            f"Mode : **{'Incrémental' if incremental else 'Complet'}**")

# ═══ BOUTON DE LANCEMENT ═══
if st.button("🚀 Lancer le téléchargement", type="primary", use_container_width=True):
    import yfinance as yf

    progress_bar = st.progress(0, text="Initialisation…")
    log_area = st.empty()
    status_container = st.container()

    total = len(import_tickers)
    success_count = 0
    error_count = 0
    uptodate_count = 0
    error_tickers = []
    logs = []

    for i, ticker in enumerate(import_tickers):
        progress_bar.progress(
            (i + 1) / total,
            text=f"[{i + 1}/{total}] {ticker}…",
        )

        safe = ticker.replace(".", "_").replace("^", "IDX_").replace("=", "_").replace("-", "_")
        is_index = ticker.startswith("^") or ticker.endswith("=X") or ticker.endswith("=F") or ticker.endswith("-USD")
        output_dir = _INDICES_DIR if is_index else _ACTIONS_DIR
        filepath = output_dir / f"{safe}_historique.csv"

        # Charger existant
        existing_df = pd.DataFrame()
        since = None
        if filepath.exists():
            try:
                existing_df = pd.read_csv(filepath, sep=";", decimal=",", parse_dates=["Date"])
                if incremental and not existing_df.empty:
                    since = existing_df["Date"].max() + timedelta(days=1)
                    if since.date() >= datetime.now().date():
                        uptodate_count += 1
                        logs.append(f"✅ {ticker} — déjà à jour")
                        continue
            except Exception:
                existing_df = pd.DataFrame()

        # Télécharger
        try:
            if since and incremental:
                data = yf.download(ticker, start=since.strftime("%Y-%m-%d"),
                                   interval="1d", progress=False, auto_adjust=True)
            else:
                data = yf.download(ticker, period="max", interval="1d",
                                   progress=False, auto_adjust=True)

            if data is None or data.empty:
                if incremental and not existing_df.empty:
                    uptodate_count += 1
                    logs.append(f"✅ {ticker} — pas de nouvelles données")
                    continue
                error_count += 1
                error_tickers.append(ticker)
                logs.append(f"❌ {ticker} — aucune donnée")
                continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            new_df = pd.DataFrame({
                "Date": data.index,
                "Ouverture": data["Open"].values,
                "Plus_Haut": data["High"].values,
                "Plus_Bas": data["Low"].values,
                "Cloture": data["Close"].values,
                "Volume_Titres": data.get("Volume", pd.Series(0, index=data.index)).values,
            }).reset_index(drop=True)

            # Fusionner
            if not existing_df.empty:
                cols_b = ["Date", "Ouverture", "Plus_Haut", "Plus_Bas", "Cloture", "Volume_Titres"]
                existing_clean = existing_df[[c for c in cols_b if c in existing_df.columns]].copy()
                combined = pd.concat([existing_clean, new_df], ignore_index=True)
            else:
                combined = new_df

            combined["Date"] = pd.to_datetime(combined["Date"])
            combined = combined.sort_values("Date").drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)
            combined["Variation_Pct"] = (combined["Cloture"].pct_change() * 100).round(2)

            # Sauvegarder historique
            output_dir.mkdir(parents=True, exist_ok=True)
            combined.to_csv(filepath, index=False, encoding="utf-8-sig", sep=";", decimal=",")

            # Info société (actions uniquement)
            if not is_index:
                try:
                    info_raw = yf.Ticker(ticker).info or {}
                    if info_raw:
                        info_out = {"ticker": ticker}
                        keys_map = {
                            "longName": "Nom", "shortName": "Nom_Court", "sector": "Secteur",
                            "industry": "Industrie", "country": "Pays", "website": "Site_Web",
                            "currency": "Devise", "exchange": "Bourse",
                            "marketCap": "Capitalisation", "trailingPE": "PER_Trailing",
                            "dividendYield": "Rendement_Dividende", "beta": "Beta",
                            "recommendationKey": "Recommandation",
                            "longBusinessSummary": "Description",
                        }
                        for yk, lk in keys_map.items():
                            v = info_raw.get(yk)
                            if v is not None:
                                info_out[lk] = v
                        _SOCIETE_DIR.mkdir(parents=True, exist_ok=True)
                        info_path = _SOCIETE_DIR / f"{safe}_info.json"
                        with open(info_path, "w", encoding="utf-8") as f:
                            json.dump(info_out, f, ensure_ascii=False, indent=2, default=str)
                except Exception:
                    pass

            success_count += 1
            logs.append(f"✅ {ticker} — {len(combined)} lignes")

        except Exception as e:
            error_count += 1
            error_tickers.append(ticker)
            logs.append(f"❌ {ticker} — {e}")

        time.sleep(0.2)

    progress_bar.progress(1.0, text="Terminé !")

    # ── Résumé final ──
    with status_container:
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("✅ Mis à jour", success_count)
        with sc2:
            st.metric("📦 Déjà à jour", uptodate_count)
        with sc3:
            st.metric("❌ Erreurs", error_count)
        with sc4:
            st.metric("📊 Total", total)

        if error_tickers:
            st.warning(f"Tickers en erreur : {', '.join(error_tickers)}")

        with st.expander("📜 Journal détaillé", expanded=False):
            st.text("\n".join(logs))

    st.success("🎉 Téléchargement terminé ! Rechargez les autres pages pour utiliser les données locales.")

else:
    st.info("Cliquez sur le bouton pour lancer le téléchargement.")

st.markdown("---")

# ═══ SECTION CLI ═══
st.markdown("### 💻 Utilisation en ligne de commande")
st.code("""
# Mise à jour incrémentale (recommandé)
python scraper_yfinance.py update

# Téléchargement complet (initial)
python scraper_yfinance.py full

# Test sur un seul ticker
python scraper_yfinance.py test AAPL
""", language="bash")

st.markdown("### 🤖 GitHub Actions (production)")
st.markdown("""
En production, le workflow `.github/workflows/update_data.yml` s'exécute
automatiquement chaque jour pour mettre à jour les données.

**📅 Planification :** Tous les jours de bourse à **22h UTC** (après fermeture US)

Le workflow :
1. Clone le dépôt
2. Installe les dépendances (`yfinance`, `pandas`)
3. Lance `python scraper_yfinance.py update`
4. Commit et push les fichiers CSV/JSON mis à jour
""")

# Lien vers GitHub Actions
REPO_OWNER = "DylaneTrader"
REPO_NAME = "FinanceMatrix"
workflow_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/actions/workflows/update_data.yml"

col_link1, col_link2 = st.columns(2)
with col_link1:
    st.link_button(
        "▶️ Lancer le workflow manuellement",
        workflow_url,
        use_container_width=True,
    )
with col_link2:
    st.link_button(
        "📊 Voir l'historique des exécutions",
        f"https://github.com/{REPO_OWNER}/{REPO_NAME}/actions",
        use_container_width=True,
    )
