"""
Page À propos — Documentation complète des indicateurs et formules
"""

import streamlit as st
from pathlib import Path
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="À propos - FinanceMatrix", page_icon="ℹ️", layout="wide")

_css = Path(__file__).parents[1] / "assets" / "style.css"
if _css.exists():
    st.markdown(f"<style>{_css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

st.title("ℹ️ À propos — FinanceMatrix")

st.markdown("""
**FinanceMatrix** est une plateforme d'analyse des marchés financiers mondiaux,
construite avec [Streamlit](https://streamlit.io) et [Plotly](https://plotly.com).
Les données sont fournies en temps réel par [Yahoo Finance](https://finance.yahoo.com) via la librairie `yfinance`.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
st.markdown("### 📐 Indicateurs de Tendance")
# ═══════════════════════════════════════════════════════════

with st.expander("**SMA — Simple Moving Average**"):
    st.markdown(r"""
Moyenne arithmétique des prix de clôture sur $n$ périodes.

$$SMA_n = \frac{1}{n} \sum_{i=0}^{n-1} P_{t-i}$$

Périodes disponibles : **10, 20, 50, 100, 200**.

**Signaux :**
- **Golden Cross** : SMA courte croise au-dessus de la SMA longue → signal haussier
- **Death Cross** : SMA courte croise en-dessous de la SMA longue → signal baissier
""")

with st.expander("**EMA — Exponential Moving Average**"):
    st.markdown(r"""
Moyenne pondérée exponentiellement, plus réactive aux prix récents.

$$EMA_t = P_t \times k + EMA_{t-1} \times (1 - k) \quad \text{où } k = \frac{2}{n + 1}$$

Périodes disponibles : **9, 12, 20, 26, 50, 200**.
""")

with st.expander("**VWAP — Volume Weighted Average Price**"):
    st.markdown(r"""
Prix moyen pondéré par le volume, indicateur intraday de référence.

$$VWAP = \frac{\sum (P_{typical} \times V)}{\sum V} \quad \text{où } P_{typical} = \frac{H + L + C}{3}$$

- Prix > VWAP → le titre surperforme par rapport au volume moyen
- Prix < VWAP → le titre sous-performe
""")

with st.expander("**Parabolic SAR — Stop and Reverse**"):
    st.markdown(r"""
Indicateur de tendance et de stop-loss dynamique développé par J. Welles Wilder.

$$SAR_{t+1} = SAR_t + AF \times (EP - SAR_t)$$

- $AF$ : facteur d'accélération (commence à 0.02, incrémenté de 0.02 jusqu'à max 0.20)
- $EP$ : point extrême (plus haut en tendance haussière, plus bas en baissière)

Le SAR est placé **sous** le prix en tendance haussière et **au-dessus** en tendance baissière.
Un retournement se produit quand le prix croise le SAR.
""")

with st.expander("**ADX — Average Directional Index**"):
    st.markdown(r"""
Mesure la **force** de la tendance (sans indiquer la direction).

$$DM^+ = H_t - H_{t-1} \quad (si > 0 \text{ et } > DM^-)$$
$$DM^- = L_{t-1} - L_t \quad (si > 0 \text{ et } > DM^+)$$
$$+DI = \frac{EMA_{14}(DM^+)}{ATR_{14}} \times 100 \qquad -DI = \frac{EMA_{14}(DM^-)}{ATR_{14}} \times 100$$
$$DX = \frac{|{+DI} - {-DI}|}{+DI + {-DI}} \times 100 \qquad ADX = EMA_{14}(DX)$$

**Interprétation :**
- **ADX > 25** : tendance forte
- **ADX < 20** : marché sans tendance (range)
- **+DI > -DI** : tendance haussière · **-DI > +DI** : tendance baissière
""")

with st.expander("**Aroon — Indicateur de tendance**"):
    st.markdown(r"""
Mesure le temps écoulé depuis le dernier plus haut / plus bas sur 25 périodes.

$$Aroon\ Up = \frac{25 - \text{périodes depuis le plus haut}}{25} \times 100$$
$$Aroon\ Down = \frac{25 - \text{périodes depuis le plus bas}}{25} \times 100$$
$$Aroon\ Oscillator = Aroon\ Up - Aroon\ Down$$

- **Aroon Up > 70 et Aroon Down < 30** → tendance haussière forte
- **Aroon Up < 30 et Aroon Down > 70** → tendance baissière forte
- **Oscillator > 0** → tendance haussière · **< 0** → tendance baissière
""")

with st.expander("**Ichimoku Cloud — Nuage d'Ichimoku**"):
    st.markdown(r"""
Système complet d'analyse tendancielle japonais composé de 5 lignes :

$$Tenkan\text{-}sen\ (9) = \frac{H_9 + L_9}{2}$$
$$Kijun\text{-}sen\ (26) = \frac{H_{26} + L_{26}}{2}$$
$$Senkou\ Span\ A = \frac{Tenkan + Kijun}{2} \quad (\text{projeté 26 périodes en avant})$$
$$Senkou\ Span\ B = \frac{H_{52} + L_{52}}{2} \quad (\text{projeté 26 périodes en avant})$$
$$Chikou\ Span = C_t \quad (\text{décalé 26 périodes en arrière})$$

**Interprétation :**
- Prix au-dessus du nuage → tendance haussière
- Prix en-dessous du nuage → tendance baissière
- Tenkan croise Kijun vers le haut → signal d'achat
- Chikou Span au-dessus du prix passé → confirmation haussière
""")

with st.expander("**DPO — Detrended Price Oscillator**"):
    st.markdown(r"""
Élimine la tendance pour identifier les cycles de prix.

$$DPO = C_t - SMA_{20}\left(t - \frac{20}{2} - 1\right)$$

Oscille autour de zéro. Valeurs positives = prix au-dessus de la tendance, négatives = en-dessous.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
st.markdown("### 📊 Oscillateurs")
# ═══════════════════════════════════════════════════════════

with st.expander("**RSI — Relative Strength Index**", expanded=True):
    st.markdown(r"""
Mesure la vitesse et l'amplitude des variations de prix (période 14).

$$RSI = 100 - \frac{100}{1 + RS} \quad \text{où } RS = \frac{\text{Moyenne des hausses}}{\text{Moyenne des baisses}}$$

- **RSI > 70** → zone de surachat
- **RSI < 30** → zone de survente
- **30 ≤ RSI ≤ 70** → zone neutre
""")

with st.expander("**Stochastic RSI**"):
    st.markdown(r"""
Applique l'oscillateur stochastique au RSI pour plus de sensibilité.

$$StochRSI = \frac{RSI - RSI_{min,14}}{RSI_{max,14} - RSI_{min,14}}$$
$$\%K = SMA_3(StochRSI) \times 100 \qquad \%D = SMA_3(\%K)$$

Même interprétation que le stochastique classique (80/20).
""")

with st.expander("**MACD — Moving Average Convergence Divergence**"):
    st.markdown(r"""
Mesure la convergence/divergence entre deux EMA.

$$MACD = EMA_{12} - EMA_{26}$$
$$Signal = EMA_9(MACD)$$
$$Histogramme = MACD - Signal$$

- MACD croise au-dessus du Signal → signal d'achat
- MACD croise en-dessous du Signal → signal de vente
- Histogramme positif croissant → momentum haussier
""")

with st.expander("**Stochastic Oscillator (%K, %D)**"):
    st.markdown(r"""
Mesure la position du prix par rapport à sa fourchette haute/basse sur $n$ périodes.

$$\%K = \frac{C_t - L_{14}}{H_{14} - L_{14}} \times 100 \qquad \%D = SMA_3(\%K)$$

- **%K > 80** → zone de surachat
- **%K < 20** → zone de survente
- Croisement %K au-dessus de %D → signal d'achat
""")

with st.expander("**Williams %R**"):
    st.markdown(r"""
Oscillateur similaire au stochastique, inversé (varie de 0 à -100).

$$\%R = \frac{H_{14} - C_t}{H_{14} - L_{14}} \times (-100)$$

- **%R > -20** → surachat
- **%R < -80** → survente
""")

with st.expander("**CCI — Commodity Channel Index**"):
    st.markdown(r"""
Mesure l'écart du prix par rapport à sa moyenne statistique.

$$CCI = \frac{TP - SMA_{20}(TP)}{0.015 \times \text{Écart moyen absolu}} \quad \text{où } TP = \frac{H + L + C}{3}$$

- **CCI > +100** → surachat / tendance haussière forte
- **CCI < -100** → survente / tendance baissière forte
""")

with st.expander("**ROC — Rate of Change**"):
    st.markdown(r"""
Variation en pourcentage du prix sur $n$ périodes.

$$ROC = \frac{C_t - C_{t-12}}{C_{t-12}} \times 100$$

Oscille autour de zéro. Momentum positif quand ROC > 0.
""")

with st.expander("**TRIX — Triple Exponential Average**"):
    st.markdown(r"""
Taux de variation d'une triple EMA lissée, filtre le bruit.

$$TRIX = \frac{EMA_3(EMA_3(EMA_3(C)))_t - EMA_3(EMA_3(EMA_3(C)))_{t-1}}{EMA_3(EMA_3(EMA_3(C)))_{t-1}} \times 100$$

Croisement de zéro utilisé comme signal. Période par défaut : 15.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
st.markdown("### 📏 Volatilité & Canaux")
# ═══════════════════════════════════════════════════════════

with st.expander("**Bandes de Bollinger**"):
    st.markdown(r"""
Enveloppe autour de la SMA basée sur l'écart-type.

$$Bande\ haute = SMA_{20} + k \times \sigma_{20} \qquad Bande\ basse = SMA_{20} - k \times \sigma_{20}$$

- **%B** : position du prix dans les bandes ($\%B = \frac{C - Bande\ basse}{Bande\ haute - Bande\ basse}$)
- **Bandwidth** : largeur relative ($\frac{Bande\ haute - Bande\ basse}{SMA} \times 100$)
- Bandwidth faible → faible volatilité (expansion imminente)
""")

with st.expander("**ATR — Average True Range**"):
    st.markdown(r"""
Mesure de la volatilité basée sur le True Range (Wilder, 1978).

$$TR = \max(H_t - L_t,\ |H_t - C_{t-1}|,\ |L_t - C_{t-1}|)$$
$$ATR_{14} = \text{Moyenne mobile de } TR \text{ sur 14 jours}$$

Un ATR élevé indique une forte volatilité. Utilisé pour dimensionner les stops.
""")

with st.expander("**Keltner Channel**"):
    st.markdown(r"""
Canal basé sur l'EMA et l'ATR (plus lisse que Bollinger).

$$Keltner\ Mid = EMA_{20}$$
$$Keltner\ Upper = EMA_{20} + 2 \times ATR_{10}$$
$$Keltner\ Lower = EMA_{20} - 2 \times ATR_{10}$$

Breakout au-dessus/en-dessous du canal → signal de tendance forte.
""")

with st.expander("**Donchian Channel**"):
    st.markdown(r"""
Canal basé sur les plus hauts et plus bas sur $n$ périodes.

$$Donchian\ Upper = \max(H_{20}) \qquad Donchian\ Lower = \min(L_{20})$$
$$Donchian\ Mid = \frac{Upper + Lower}{2}$$

Utilisé dans les systèmes de suivi de tendance (Turtle Trading).
""")

with st.expander("**Ulcer Index**"):
    st.markdown(r"""
Mesure de la volatilité baissière (drawdown).

$$\%DD_i = \frac{C_i - \max(C_{i-13}, \ldots, C_i)}{\max(C_{i-13}, \ldots, C_i)} \times 100$$
$$UI = \sqrt{\frac{\sum \%DD_i^2}{14}}$$

Un Ulcer Index élevé indique un risque de pertes important.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
st.markdown("### 📦 Indicateurs de Volume")
# ═══════════════════════════════════════════════════════════

with st.expander("**OBV — On-Balance Volume**"):
    st.markdown(r"""
Cumul du volume en fonction de la direction du prix.

$$OBV_t = OBV_{t-1} + \begin{cases} V_t & \text{si } C_t > C_{t-1} \\ -V_t & \text{si } C_t < C_{t-1} \\ 0 & \text{sinon} \end{cases}$$

L'OBV croissant confirme la tendance haussière. Divergence OBV/Prix → signal de retournement.
""")

with st.expander("**CMF — Chaikin Money Flow**"):
    st.markdown(r"""
Mesure la pression achat/vente sur 20 périodes.

$$CLV = \frac{(C - L) - (H - C)}{H - L} \qquad CMF = \frac{\sum_{i=1}^{20} CLV_i \times V_i}{\sum_{i=1}^{20} V_i}$$

- **CMF > 0** → pression acheteuse
- **CMF < 0** → pression vendeuse
""")

with st.expander("**MFI — Money Flow Index**"):
    st.markdown(r"""
RSI pondéré par le volume ("Volume-weighted RSI").

$$TP = \frac{H + L + C}{3} \qquad MF = TP \times V$$
$$MFI = 100 - \frac{100}{1 + \frac{\sum MF^+}{\sum MF^-}}$$

- **MFI > 80** → surachat
- **MFI < 20** → survente
""")

with st.expander("**Force Index**"):
    st.markdown(r"""
Combine prix, direction et volume pour mesurer la force des mouvements.

$$FI = (C_t - C_{t-1}) \times V_t$$
$$FI_{13} = EMA_{13}(FI)$$

Force Index positif → pression acheteuse · négatif → pression vendeuse.
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
st.markdown("### 🔗 Corrélation & Bêta")
# ═══════════════════════════════════════════════════════════

with st.expander("**Corrélation de Pearson**"):
    st.markdown(r"""
$$\rho_{X,Y} = \frac{Cov(X,Y)}{\sigma_X \cdot \sigma_Y}$$

- $\rho = 1$ : corrélation positive parfaite
- $\rho = 0$ : aucune corrélation
- $\rho = -1$ : corrélation négative parfaite
""")

with st.expander("**Bêta (β)**"):
    st.markdown(r"""
$$\beta = \frac{Cov(R_{action}, R_{marché})}{Var(R_{marché})}$$

- $\beta = 1$ → évolue comme le marché
- $\beta > 1$ → plus volatile · $\beta < 1$ → moins volatile · $\beta < 0$ → direction inverse
""")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
st.markdown("### 📈 Performances")
# ═══════════════════════════════════════════════════════════

with st.expander("**Performances Calendaires**"):
    st.markdown("""
- **WTD** (Week-to-Date) : depuis le début de la semaine (lundi)
- **MTD** (Month-to-Date) : depuis le 1er du mois
- **QTD** (Quarter-to-Date) : depuis le début du trimestre
- **STD** (Semester-to-Date) : depuis le début du semestre
- **YTD** (Year-to-Date) : depuis le 1er janvier
""")

with st.expander("**Performances Glissantes**"):
    st.markdown("""
Calculées sur un nombre fixe de séances de bourse :
- **1 Semaine** : 5 séances
- **1 Mois** : 22 séances
- **3 Mois** : 65 séances
- **6 Mois** : 130 séances
- **1 An** : 252 séances
""")

st.markdown("---")

st.markdown("### 📊 Univers couvert")
st.markdown(f"""
L'application couvre **{sum(len(v) for v in __import__('data_handler', fromlist=['SECTOR_TICKERS']).SECTOR_TICKERS.values())}
tickers** répartis dans **{len(__import__('data_handler', fromlist=['SECTOR_TICKERS']).SECTOR_TICKERS)}
secteurs** : Technology, Financial Services, Healthcare, Consumer Cyclical,
Consumer Defensive, Communication Services, Energy, Industrials, Basic Materials,
Real Estate, Utilities, Crypto & ETF, Indices & FX.
""")

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:0.8rem;'>"
    "FinanceMatrix · Données fournies par Yahoo Finance · "
    "Construit avec Streamlit & Plotly</p>",
    unsafe_allow_html=True,
)
