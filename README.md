# FinanceMatrix // Analyse Quantitative

Application multi-page d'analyse des marchés financiers mondiaux, construite avec
**Streamlit**, **Plotly** et **yfinance**.

## Style
Interface professionnelle "finance" : palette Royal Navy Blue / Snake Fruit accent,
typographie sérif (Cambria), composants responsives.

## Pages

| # | Page | Description |
|---|------|-------------|
| 🏠 | **Accueil** | Bandeau indices, Top/Flop performers, carte sectorielle (treemap) |
| 📐 | **Analyse Technique** | Tableau de bord des signaux + onglets RSI, SMA/EMA, MACD, Bollinger |
| 📈 | **Performances** | Performances calendaires (WTD→YTD), glissantes, graphique comparatif |
| 🔗 | **Corrélations & Bêta** | Matrice de corrélation (Pearson/Spearman), clustering, analyse bêta |
| 💼 | **Simulation Portefeuille** | Portefeuille virtuel $100k, ordres achat/vente, suivi P&L |
| ℹ️ | **À propos** | Documentation des indicateurs et formules (LaTeX) |

## Fonctionnalités
- Données de marché en temps réel via `yfinance` (250+ tickers, 13 secteurs).
- Analyse technique avec tableau de bord des signaux (RSI, MACD, SMA, Bollinger, ATR).
- Performances calendaires et glissantes avec heatmap et graphique comparatif.
- Matrice de corrélation avec clustering hiérarchique et analyse du bêta glissant.
- Simulation de portefeuille avec persistance JSON.
- Données fondamentales (valorisation, rentabilité, croissance, dividendes, analystes).

## Installation et lancement

1. **Prérequis** : Python 3.11+
2. **Installation** :
   ```bash
   pip install streamlit plotly pandas yfinance
   ```
3. **Lancement** :
   ```bash
   streamlit run app.py
   ```
4. **Accès** : ouvrez votre navigateur à `http://localhost:8501`.

## Structure
- `app.py` — application Streamlit.
- `data_handler.py` — récupération et traitement des données financières.
- `assets/style.css` — thème visuel.
