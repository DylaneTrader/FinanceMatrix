#!/usr/bin/env python3
# Copyright (c) FinanceMatrix.
# SPDX-License-Identifier: MIT
"""
Scraper FinanceMatrix — Yahoo Finance (yfinance)
=================================================
Télécharge les données historiques OHLCV et les infos société
pour tous les tickers de l'univers FinanceMatrix.

Structure de sortie :
    data/
    ├── actions/          # CSV historique par ticker (ex: AAPL_historique.csv)
    ├── indices/          # CSV historique par indice/FX/crypto
    └── societes/         # JSON info société par ticker

Modes :
    python scraper_yfinance.py full           - Scraping complet (initial ou incrémental)
    python scraper_yfinance.py test [TICKER]  - Test sur un seul ticker
    python scraper_yfinance.py update         - Mise à jour incrémentale uniquement
"""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

ROOT_DIR = Path(__file__).parent
OUTPUT_DIR = ROOT_DIR / "data"
ACTIONS_DIR = OUTPUT_DIR / "actions"
INDICES_DIR = OUTPUT_DIR / "indices"
SOCIETE_DIR = OUTPUT_DIR / "societes"

# Historique max par défaut
DEFAULT_PERIOD = "max"

# Pause entre requêtes info (secondes)
REQUEST_DELAY = 0.3

# ---------------------------------------------------------------------------
# Tickers — importés depuis data_handler
# ---------------------------------------------------------------------------

# Tickers classés comme "indices" (pas d'info société disponible)
INDEX_LIKE_PREFIXES = ("^", "=X", "=F")


def _is_index(ticker: str) -> bool:
    return any(ticker.endswith(sfx) or ticker.startswith(sfx) for sfx in INDEX_LIKE_PREFIXES) or ticker.endswith("-USD")


def _load_tickers() -> dict[str, list[str]]:
    """Charge SECTOR_TICKERS depuis data_handler."""
    sys.path.insert(0, str(ROOT_DIR))
    from data_handler import SECTOR_TICKERS
    return SECTOR_TICKERS


def _safe_name(ticker: str) -> str:
    """Nom de fichier safe pour un ticker."""
    return ticker.replace(".", "_").replace("^", "IDX_").replace("=", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(ROOT_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Données existantes
# ---------------------------------------------------------------------------


def load_existing_data(ticker: str) -> pd.DataFrame:
    """Charge le CSV existant d'un ticker s'il existe."""
    output_dir = INDICES_DIR if _is_index(ticker) else ACTIONS_DIR
    filepath = output_dir / f"{_safe_name(ticker)}_historique.csv"
    if not filepath.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath, sep=";", decimal=",", parse_dates=["Date"])
        log.info(f"  Existant : {len(df)} lignes -> {df['Date'].max().strftime('%Y-%m-%d')}")
        return df
    except Exception as e:
        log.warning(f"  Lecture échouée {filepath}: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Scraping historique
# ---------------------------------------------------------------------------


def scrape_history(ticker: str, since: datetime | None = None) -> pd.DataFrame:
    """Télécharge l'historique OHLCV via yfinance.

    Si `since` est fourni, ne télécharge que les données après cette date (incrémental).
    """
    try:
        if since:
            start_str = since.strftime("%Y-%m-%d")
            data = yf.download(
                ticker, start=start_str, interval="1d",
                progress=False, auto_adjust=True,
            )
        else:
            data = yf.download(
                ticker, period=DEFAULT_PERIOD, interval="1d",
                progress=False, auto_adjust=True,
            )
    except Exception as e:
        log.error(f"  Erreur yfinance {ticker}: {e}")
        return pd.DataFrame()

    if data is None or data.empty:
        log.warning(f"  Aucune donnée pour {ticker}")
        return pd.DataFrame()

    # Aplatir MultiIndex si nécessaire
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    df = pd.DataFrame()
    df["Date"] = data.index
    df["Ouverture"] = data["Open"].values
    df["Plus_Haut"] = data["High"].values
    df["Plus_Bas"] = data["Low"].values
    df["Cloture"] = data["Close"].values
    if "Volume" in data.columns:
        df["Volume_Titres"] = data["Volume"].values
    else:
        df["Volume_Titres"] = 0

    df = df.reset_index(drop=True)
    log.info(f"  Téléchargé : {len(df)} lignes "
             f"({df['Date'].min().strftime('%Y-%m-%d')} -> {df['Date'].max().strftime('%Y-%m-%d')})")
    return df


def merge_and_finalize(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """Fusionne anciennes et nouvelles données, recalcule les colonnes dérivées."""
    if existing_df.empty and new_df.empty:
        return pd.DataFrame()

    if existing_df.empty:
        combined = new_df
    elif new_df.empty:
        combined = existing_df
    else:
        cols_brutes = ["Date", "Ouverture", "Plus_Haut", "Plus_Bas", "Cloture", "Volume_Titres"]
        existing_clean = existing_df[[c for c in cols_brutes if c in existing_df.columns]].copy()
        new_clean = new_df[[c for c in cols_brutes if c in new_df.columns]].copy()
        combined = pd.concat([existing_clean, new_clean], ignore_index=True)

    combined["Date"] = pd.to_datetime(combined["Date"])
    combined = (
        combined.sort_values("Date")
        .drop_duplicates(subset=["Date"], keep="last")
        .reset_index(drop=True)
    )

    # Colonnes dérivées
    if "Volume_Titres" in combined.columns:
        combined["Volume_FCFA"] = (
            combined["Volume_Titres"]
            * (combined["Plus_Haut"] + combined["Plus_Bas"]) / 2
        ).round(0)

    combined["Variation_Pct"] = combined["Cloture"].pct_change() * 100
    combined["Variation_Pct"] = combined["Variation_Pct"].round(2)

    return combined


# ---------------------------------------------------------------------------
# Info société
# ---------------------------------------------------------------------------


def scrape_info(ticker: str) -> dict:
    """Récupère les informations fondamentales via yfinance."""
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as e:
        log.warning(f"  Erreur info {ticker}: {e}")
        return {}

    if not info:
        return {}

    result = {"ticker": ticker}
    keys_map = {
        "longName": "Nom",
        "shortName": "Nom_Court",
        "sector": "Secteur",
        "industry": "Industrie",
        "country": "Pays",
        "city": "Ville",
        "website": "Site_Web",
        "currency": "Devise",
        "exchange": "Bourse",
        "fullTimeEmployees": "Employes",
        "longBusinessSummary": "Description",
        "marketCap": "Capitalisation",
        "enterpriseValue": "Valeur_Entreprise",
        "trailingPE": "PER_Trailing",
        "forwardPE": "PER_Forward",
        "dividendYield": "Rendement_Dividende",
        "profitMargins": "Marge_Nette",
        "returnOnEquity": "ROE",
        "debtToEquity": "Dette_Capitaux",
        "beta": "Beta",
        "recommendationKey": "Recommandation",
        "targetMeanPrice": "Objectif_Moyen",
    }
    for yf_key, local_key in keys_map.items():
        val = info.get(yf_key)
        if val is not None:
            result[local_key] = val

    return result


# ---------------------------------------------------------------------------
# Sauvegarde
# ---------------------------------------------------------------------------


def save_history(df: pd.DataFrame, ticker: str) -> Path | None:
    """Sauvegarde l'historique en CSV."""
    if df.empty:
        return None
    output_dir = INDICES_DIR if _is_index(ticker) else ACTIONS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{_safe_name(ticker)}_historique.csv"
    df.to_csv(filepath, index=False, encoding="utf-8-sig", sep=";", decimal=",")
    log.info(f"  -> {filepath} ({len(df)} lignes)")
    return filepath


def save_info(info: dict, ticker: str) -> Path | None:
    """Sauvegarde les infos société en JSON."""
    if not info or len(info) <= 1:
        return None
    SOCIETE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SOCIETE_DIR / f"{_safe_name(ticker)}_info.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2, default=str)
    log.info(f"  -> {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Résumé
# ---------------------------------------------------------------------------


def build_summary() -> pd.DataFrame:
    """Crée un fichier résumé avec les stats de chaque ticker."""
    summary = []
    for subdir, label in [(ACTIONS_DIR, "Action"), (INDICES_DIR, "Indice")]:
        if not subdir.exists():
            continue
        for csv_file in sorted(subdir.glob("*_historique.csv")):
            try:
                df = pd.read_csv(csv_file, sep=";", decimal=",", parse_dates=["Date"])
                ticker_raw = csv_file.stem.replace("_historique", "")
                summary.append({
                    "Ticker": ticker_raw,
                    "Type": label,
                    "Nb_Lignes": len(df),
                    "Date_Min": df["Date"].min().strftime("%Y-%m-%d"),
                    "Date_Max": df["Date"].max().strftime("%Y-%m-%d"),
                    "Dernier_Cours": df.loc[df["Date"].idxmax(), "Cloture"],
                })
            except Exception:
                continue

    if summary:
        df_summary = pd.DataFrame(summary)
        filepath = OUTPUT_DIR / "resume_scraping.csv"
        df_summary.to_csv(filepath, index=False, encoding="utf-8-sig", sep=";", decimal=",")
        log.info(f"\nRésumé : {filepath}")
        return df_summary
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def scrape_ticker(ticker: str, incremental: bool = True) -> dict:
    """Scrape un ticker (historique + info). Retourne un dict de statut."""
    result = {"ticker": ticker, "status": "ok", "rows": 0}

    existing_df = load_existing_data(ticker)
    since = None
    if incremental and not existing_df.empty:
        since = existing_df["Date"].max() + timedelta(days=1)
        if since.date() >= datetime.now().date():
            result["status"] = "up-to-date"
            result["rows"] = len(existing_df)
            return result

    new_df = scrape_history(ticker, since=since)
    final_df = merge_and_finalize(existing_df, new_df)
    save_history(final_df, ticker)
    result["rows"] = len(final_df)

    if not _is_index(ticker):
        info = scrape_info(ticker)
        save_info(info, ticker)
        time.sleep(REQUEST_DELAY)

    return result


def run_full_scrape(incremental: bool = True) -> int:
    """Scrape complet de tous les tickers."""
    sector_tickers = _load_tickers()
    start_time = time.time()
    all_tickers = []
    for t_list in sector_tickers.values():
        for t in t_list:
            if t not in all_tickers:
                all_tickers.append(t)

    total = len(all_tickers)
    success = 0
    errors = 0
    up_to_date = 0

    mode = "INCRÉMENTAL" if incremental else "COMPLET"
    log.info(f"{'=' * 60}")
    log.info(f"SCRAPING {mode} — {total} TICKERS")
    log.info(f"{'=' * 60}")

    for i, ticker in enumerate(all_tickers, 1):
        log.info(f"\n[{i}/{total}] {ticker}")
        try:
            r = scrape_ticker(ticker, incremental=incremental)
            if r["status"] == "up-to-date":
                up_to_date += 1
                log.info(f"  Déjà à jour")
            else:
                success += 1
        except Exception as e:
            log.error(f"  ERREUR {ticker}: {e}")
            errors += 1

    elapsed = time.time() - start_time
    log.info(f"\n{'=' * 60}")
    log.info(f"TERMINÉ en {elapsed / 60:.1f} min — {success} mis à jour, "
             f"{up_to_date} déjà à jour, {errors} erreurs")
    log.info(f"{'=' * 60}")

    build_summary()
    return EXIT_SUCCESS if errors == 0 else EXIT_FAILURE


def run_test(ticker: str = "AAPL") -> int:
    """Test rapide sur un seul ticker."""
    log.info(f"=== TEST : {ticker} ===")
    r = scrape_ticker(ticker, incremental=False)
    log.info(f"Statut : {r}")

    output_dir = INDICES_DIR if _is_index(ticker) else ACTIONS_DIR
    filepath = output_dir / f"{_safe_name(ticker)}_historique.csv"
    if filepath.exists():
        df = pd.read_csv(filepath, sep=";", decimal=",")
        print(f"\nAperçu ({len(df)} lignes):")
        print(df.head(5).to_string(index=False))
        print("...")
        print(df.tail(5).to_string(index=False))

    info_path = SOCIETE_DIR / f"{_safe_name(ticker)}_info.json"
    if info_path.exists():
        with open(info_path, encoding="utf-8") as f:
            info = json.load(f)
        print(f"\nInfo société : {json.dumps(info, ensure_ascii=False, indent=2)[:600]}")

    return EXIT_SUCCESS


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "test":
            ticker = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
            return run_test(ticker)
        elif cmd == "full":
            return run_full_scrape(incremental=False)
        elif cmd == "update":
            return run_full_scrape(incremental=True)
        else:
            print("Usage:")
            print("  python scraper_yfinance.py full            - Scraping complet")
            print("  python scraper_yfinance.py update          - Mise à jour incrémentale")
            print("  python scraper_yfinance.py test [TICKER]   - Test sur un ticker")
            return EXIT_SUCCESS
    else:
        return run_full_scrape(incremental=True)


if __name__ == "__main__":
    sys.exit(main())
