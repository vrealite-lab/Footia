import math
import streamlit as st

st.set_page_config(page_title="Foot IA — Prototype", page_icon="⚽", layout="centered")

st.title("⚽ Foot IA — Analyseur de match")
st.caption("Prototype gratuit • Mode démonstration — aucune donnée en direct")

st.warning(
    "Les valeurs ci-dessous sont des exemples modifiables, pas des statistiques réelles. "
    "Ce prototype ne fournit pas de conseil de pari ni de garantie de résultat."
)

st.subheader("1. Renseigne les données du match")
col1, col2 = st.columns(2)
with col1:
    home = st.text_input("Équipe à domicile", "Équipe A")
    home_goals = st.number_input("Buts domicile", min_value=0, max_value=20, value=1, step=1)
    home_shots = st.slider("Tirs domicile (exemple)", 0, 30, 7)
    home_sot = st.slider("Tirs cadrés domicile (exemple)", 0, 15, 3)
with col2:
    away = st.text_input("Équipe à l'extérieur", "Équipe B")
    away_goals = st.number_input("Buts extérieur", min_value=0, max_value=20, value=0, step=1)
    away_shots = st.slider("Tirs extérieur (exemple)", 0, 30, 4)
    away_sot = st.slider("Tirs cadrés extérieur (exemple)", 0, 15, 1)

minute = st.slider("Minute du match", 1, 90, 35)
st.caption("Pour ce premier prototype, les probabilités reposent sur des hypothèses simplifiées et des paramètres que tu saisis.")

st.subheader("2. Estimation simplifiée des buts restants")
st.write(
    "Le calcul ci-dessous utilise un modèle de Poisson très simplifié. "
    "Il sert à apprendre et à tester l'interface, pas à prédire fiablement un vrai match."
)

remaining = max(0, 90 - minute) / 90
# Example baseline rates, adjusted slightly by shots on target; deliberately transparent.
home_rate = remaining * (0.85 + min(home_sot, 8) * 0.10)
away_rate = remaining * (0.70 + min(away_sot, 8) * 0.10)

def poisson_prob(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def prob_at_least_one(lam):
    return 1 - math.exp(-lam)

p_home_goal = prob_at_least_one(home_rate)
p_away_goal = prob_at_least_one(away_rate)
p_any_goal = 1 - math.exp(-(home_rate + away_rate))

m1, m2, m3 = st.columns(3)
m1.metric("Score saisi", f"{home_goals} – {away_goals}")
m2.metric("Au moins 1 but supplémentaire*", f"{p_any_goal:.0%}")
m3.metric("But domicile supplémentaire*", f"{p_home_goal:.0%}")

st.caption("*Estimations illustratives issues d'hypothèses de démonstration, non calibrées sur des données historiques.")

st.subheader("3. Lecture descriptive des chiffres saisis")
if home_sot + away_sot == 0:
    st.info("Aucun tir cadré saisi. Il y a trop peu d'information pour interpréter la pression offensive.")
elif home_sot > away_sot:
    st.write(f"Dans les valeurs saisies, {home} a davantage de tirs cadrés ({home_sot} contre {away_sot}). Cela ne garantit pas un but.")
elif away_sot > home_sot:
    st.write(f"Dans les valeurs saisies, {away} a davantage de tirs cadrés ({away_sot} contre {home_sot}). Cela ne garantit pas un but.")
else:
    st.write("Les deux équipes ont le même nombre de tirs cadrés dans les valeurs saisies.")

st.subheader("4. Prochaine amélioration")
st.markdown(
    "- Connecter une source de données football autorisée.\n"
    "- Afficher la date et l'heure de la dernière mise à jour.\n"
    "- Tester les estimations sur des matchs historiques avant de les utiliser.\n"
    "- Comparer les probabilités aux cotes seulement lorsque des données fiables sont disponibles."
)
st.caption("Utilise ce prototype à des fins éducatives. Les paris comportent un risque de perte.")
