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
                    if home_goals is not None and away_goals is not None:
                        total_goals = home_goals + away_goals

                        st.metric("Total de buts", total_goals)

                        if home_goals > away_goals:
                            st.write("📊 Lecture du score : avantage domicile")
                        elif away_goals > home_goals:
                            st.write("📊 Lecture du score : avantage extérieur")
                        else:
                            st.write("📊 Lecture du score : égalité")

                    else:
                        st.info(
                            "Analyse limitée : le score complet "
                            "n'est pas encore disponible."
                        )
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
st.divider()
st.header("📊 Analyse historique des buts")

st.write(
    "Calcule les moyennes à partir des matchs terminés "
    "de la compétition sélectionnée."
)

if st.button("Calculer les moyennes historiques"):
    token = st.secrets.get("FOOTBALL_DATA_TOKEN", "")

    if not token:
        st.error("Token API introuvable dans les Secrets.")
    else:
        today = datetime.now(timezone.utc).date()
        date_from = today - timedelta(days=90)
        date_to = today + timedelta(days=1)

        code = competitions[competition_name]

        params = urlencode({
            "status": "FINISHED",
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
        })

        url = (
            f"https://api.football-data.org/v4/competitions/"
            f"{code}/matches?{params}"
        )

        request = Request(
            url,
            headers={"X-Auth-Token": token},
        )

        try:
            with st.spinner("Analyse des matchs terminés..."):
                with urlopen(request, timeout=20) as response:
                    data = json.loads(
                        response.read().decode("utf-8")
                    )

            matches = data.get("matches", [])

            finished_scores = []

            for match in matches:
                if match.get("status") != "FINISHED":
                    continue

                score = match.get("score", {}).get("fullTime", {})
                home = score.get("home")
                away = score.get("away")

                if (
                    isinstance(home, int)
                    and isinstance(away, int)
                ):
                    finished_scores.append((home, away))

            if not finished_scores:
                st.warning(
                    "Aucun score final exploitable trouvé "
                    "sur cette période."
                )
            else:
                count = len(finished_scores)

                home_avg = sum(
                    home for home, away in finished_scores
                ) / count

                away_avg = sum(
                    away for home, away in finished_scores
                ) / count

                total_avg = home_avg + away_avg

                st.success(
                    f"Analyse basée sur {count} matchs terminés"
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Buts par match",
                    f"{total_avg:.2f}",
                )

                col2.metric(
                    "Buts domicile",
                    f"{home_avg:.2f}",
                )

                col3.metric(
                    "Buts extérieur",
                    f"{away_avg:.2f}",
                )

                st.caption(
                    "Période : 90 derniers jours environ. "
                    "Ces moyennes décrivent les résultats passés ; "
                    "elles ne prédisent pas à elles seules le prochain match."
                )

        except HTTPError as error:
            st.error(
                f"Erreur API HTTP {error.code}. "
                "Vérifie les droits d'accès et réessaie."
            )
        except URLError:
            st.error("Connexion à l'API impossible. Réessaie plus tard.")
        except (ValueError, KeyError, TypeError):
            st.error("Impossible de lire les données reçues.")
st.divider()
st.header("🧠 Analyse individuelle des équipes")

st.write(
    "Compare les performances de chaque équipe à domicile "
    "et à l'extérieur à partir des matchs terminés."
)

if st.button("Analyser les équipes", use_container_width=True):
    token = st.secrets.get("FOOTBALL_DATA_TOKEN", "")

    if not token:
        st.error("Token API introuvable dans les Secrets.")
    else:
        today = datetime.now(timezone.utc).date()
        date_from = today - timedelta(days=90)
        date_to = today + timedelta(days=1)
        code = competitions[competition_name]

        params = urlencode({
            "status": "FINISHED",
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
        })

        url = (
            f"https://api.football-data.org/v4/competitions/"
            f"{code}/matches?{params}"
        )

        request = Request(
            url,
            headers={"X-Auth-Token": token},
        )

        try:
            with st.spinner("Analyse des équipes..."):
                with urlopen(request, timeout=20) as response:
                    data = json.loads(
                        response.read().decode("utf-8")
                    )

            teams = {}
            valid_matches = 0

            for match in data.get("matches", []):
                if match.get("status") != "FINISHED":
                    continue

                home_team = match.get("homeTeam", {}).get("name")
                away_team = match.get("awayTeam", {}).get("name")
                score = match.get("score", {}).get("fullTime", {})
                home_goals = score.get("home")
                away_goals = score.get("away")

                if not home_team or not away_team:
                    continue

                if not isinstance(home_goals, int):
                    continue

                if not isinstance(away_goals, int):
                    continue

                valid_matches += 1

                if home_team not in teams:
                    teams[home_team] = {
                        "matches": 0,
                        "scored": 0,
                        "conceded": 0,
                        "home_matches": 0,
                        "home_scored": 0,
                        "home_conceded": 0,
                        "away_matches": 0,
                        "away_scored": 0,
                        "away_conceded": 0,
                    }

                if away_team not in teams:
                    teams[away_team] = {
                        "matches": 0,
                        "scored": 0,
                        "conceded": 0,
                        "home_matches": 0,
                        "home_scored": 0,
                        "home_conceded": 0,
                        "away_matches": 0,
                        "away_scored": 0,
                        "away_conceded": 0,
                    }

                home = teams[home_team]
                away = teams[away_team]

                home["matches"] += 1
                home["scored"] += home_goals
                home["conceded"] += away_goals
                home["home_matches"] += 1
                home["home_scored"] += home_goals
                home["home_conceded"] += away_goals

                away["matches"] += 1
                away["scored"] += away_goals
                away["conceded"] += home_goals
                away["away_matches"] += 1
                away["away_scored"] += away_goals
                away["away_conceded"] += home_goals

            if not teams:
                st.warning(
                    "Aucune donnée exploitable sur cette période."
                )
            else:
                st.success(
                    f"{valid_matches} matchs terminés analysés."
                )

                team_name = st.selectbox(
                    "Choisis une équipe",
                    sorted(teams.keys()),
                    key="team_analysis_select",
                )

                stats = teams[team_name]
                count = stats["matches"]

                avg_scored = stats["scored"] / count
                avg_conceded = stats["conceded"] / count

                st.subheader(team_name)
                st.caption(
                    f"{count} match(s) dans l'échantillon "
                    f"des 90 derniers jours environ."
                )

                col1, col2 = st.columns(2)
                col1.metric(
                    "Buts marqués / match",
                    f"{avg_scored:.2f}",
                )
                col2.metric(
                    "Buts encaissés / match",
                    f"{avg_conceded:.2f}",
                )

                st.markdown("#### 🏠 À domicile")
                if stats["home_matches"] > 0:
                    n = stats["home_matches"]
                    c1, c2 = st.columns(2)
                    c1.metric(
                        "Buts marqués",
                        f"{stats['home_scored'] / n:.2f}",
                    )
                    c2.metric(
                        "Buts encaissés",
                        f"{stats['home_conceded'] / n:.2f}",
                    )
                    st.caption(f"Basé sur {n} match(s) à domicile.")
                else:
                    st.info("Aucun match à domicile dans l'échantillon.")

                st.markdown("#### ✈️ À l'extérieur")
                if stats["away_matches"] > 0:
                    n = stats["away_matches"]
                    c1, c2 = st.columns(2)
                    c1.metric(
                        "Buts marqués",
                        f"{stats['away_scored'] / n:.2f}",
                    )
                    c2.metric(
                        "Buts encaissés",
                        f"{stats['away_conceded'] / n:.2f}",
                    )
                    st.caption(f"Basé sur {n} match(s) à l'extérieur.")
                else:
                    st.info(
                        "Aucun match à l'extérieur dans l'échantillon."
                    )

                st.markdown("#### 📋 Lecture statistique")

                if count < 5:
                    st.warning(
                        "Échantillon très limité : moins de 5 matchs. "
                        "Les moyennes sont peu stables."
                    )
                elif count < 10:
                    st.info(
                        "Échantillon encore limité. "
                        "Interprète les moyennes avec prudence."
                    )
                else:
                    st.write(
                        "L'échantillon est plus fourni, mais "
                        "les moyennes restent descriptives et "
                        "ne garantissent pas les performances futures."
                    )

                st.caption(
                    "Source : football-data.org. Les chiffres décrivent "
                    "les matchs retournés par l'API pour la compétition "
                    "choisie et la période sélectionnée. Ils ne constituent "
                    "pas à eux seuls une prédiction."
                )

        except HTTPError as error:
            st.error(
                f"Erreur API HTTP {error.code}. "
                "Vérifie les droits d'accès et réessaie."
            )
        except URLError:
            st.error("Connexion à l'API impossible. Réessaie plus tard.")
        except (ValueError, KeyError, TypeError):
            st.error("Impossible de lire les données reçues.")
