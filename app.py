import json
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st

st.set_page_config(page_title="Foot IA", page_icon="⚽", layout="centered")

st.title("⚽ Foot IA")
st.caption("Tableau de bord football connecté à football-data.org")

competitions = {
    "Ligue 1 — France": "FL1",
    "Premier League — Angleterre": "PL",
    "Liga — Espagne": "PD",
    "Bundesliga — Allemagne": "BL1",
    "Serie A — Italie": "SA",
}

competition_name = st.selectbox(
    "Choisis une compétition",
    list(competitions.keys()),
)
status_options = {
    "Tous les matchs": "",
    "En cours": "IN_PLAY",
    "À venir": "SCHEDULED",
    "Terminés": "FINISHED",
}
status_label = st.selectbox(
    "Filtrer par statut",
    list(status_options.keys()),
)
if st.button("🔄 Charger les matchs", use_container_width=True):
    st.session_state["load_matches"] = True

if st.session_state.get("load_matches", False):
    token = st.secrets.get("FOOTBALL_DATA_TOKEN", "")

    if not token:
        st.error(
            "Token introuvable. Vérifie les Secrets dans "
            "les paramètres de ton application Streamlit."
        )
    else:
        today = datetime.now(timezone.utc).date()
        end_date = today + timedelta(days=7)

        code = competitions[competition_name]
        filters = {
    "dateFrom": today.isoformat(),
    "dateTo": end_date.isoformat(),
}

selected_status = status_options[status_label]

if selected_status:
    filters["status"] = selected_status

params = urlencode(filters)
        url = (
            f"https://api.football-data.org/v4/competitions/"
            f"{code}/matches?{params}"
        )

        request = Request(
            url,
            headers={"X-Auth-Token": token},
        )

        try:
            with st.spinner("Récupération des matchs..."):
                with urlopen(request, timeout=20) as response:
                    data = json.loads(response.read().decode("utf-8"))

            matches = data.get("matches", [])

            if not matches:
                st.info(
                    "Aucun match retourné pour cette compétition "
                    "sur cette période. Essaie une autre compétition."
                )
            else:
                st.success(f"{len(matches)} match(s) récupéré(s)")

                status_labels = {
                    "SCHEDULED": "À venir",
                    "TIMED": "Programmé",
                    "IN_PLAY": "En cours",
                    "LIVE": "En direct",
                    "PAUSED": "En pause",
                    "FINISHED": "Terminé",
                    "POSTPONED": "Reporté",
                    "SUSPENDED": "Suspendu",
                    "CANCELLED": "Annulé",
                }

                for match in matches:
                    home = match.get("homeTeam", {}).get("name") or "Domicile"
                    away = match.get("awayTeam", {}).get("name") or "Extérieur"
                    score = match.get("score", {}).get("fullTime", {})
                    home_goals = score.get("home")
                    away_goals = score.get("away")

                    if home_goals is None or away_goals is None:
                        score_text = "Pas encore de score"
                    else:
                        score_text = f"{home_goals} – {away_goals}"

                    date_text = match.get("utcDate", "")
                    try:
                        date_text = (
                            datetime.fromisoformat(
                                date_text.replace("Z", "+00:00")
                            )
                            .astimezone()
                            .strftime("%d/%m/%Y à %H:%M")
                        )
                    except (ValueError, TypeError):
                        date_text = "Date indisponible"

                    status = status_labels.get(
                        match.get("status", ""),
                        match.get("status", "Inconnu"),
                    )

                    with st.container(border=True):
                        st.caption(date_text)
                        st.subheader(f"{home}  —  {away}")
                        st.write(f"**Score :** {score_text}")
                        st.write(f"**Statut :** {status}")

        except HTTPError as error:
            if error.code == 403:
                st.error(
                    "Accès refusé par l'API. Vérifie que ton offre "
                    "autorise cette compétition."
                )
            elif error.code == 429:
                st.error(
                    "Limite de requêtes atteinte. Attends un peu "
                    "avant de réessayer."
                )
            elif error.code == 400:
                st.error(
                    "La requête a été refusée. Vérifie la compétition "
                    "choisie et réessaie."
                )
            else:
                st.error(
                    f"L'API a renvoyé une erreur HTTP {error.code}."
                )
        except URLError:
            st.error(
                "Connexion à l'API impossible. Réessaie dans quelques "
                "instants."
            )
        except (ValueError, KeyError, TypeError):
            st.error(
                "La réponse de l'API n'a pas pu être lue correctement."
            )

st.divider()
st.caption(
    "Source : football-data.org. Les compétitions et données "
    "disponibles dépendent de ton offre API. Les scores et statuts "
    "ne garantissent pas une couverture en temps réel."
)
