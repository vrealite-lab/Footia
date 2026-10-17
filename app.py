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
st.divider()
st.header("⚔️ Comparateur avant-match")

st.write(
    "Compare une équipe à domicile et une équipe à l'extérieur "
    "à partir des résultats historiques de la compétition."
)

if st.button("🔄 Charger les données de comparaison"):
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
            with st.spinner("Préparation des statistiques..."):
                with urlopen(request, timeout=20) as response:
                    data = json.loads(
                        response.read().decode("utf-8")
                    )

            teams = {}

            for match in data.get("matches", []):
                if match.get("status") != "FINISHED":
                    continue

                home_name = match.get("homeTeam", {}).get("name")
                away_name = match.get("awayTeam", {}).get("name")
                score = match.get("score", {}).get("fullTime", {})
                hg = score.get("home")
                ag = score.get("away")

                if not home_name or not away_name:
                    continue
                if not isinstance(hg, int) or not isinstance(ag, int):
                    continue

                if home_name not in teams:
                    teams[home_name] = {
                        "home_n": 0, "home_for": 0, "home_against": 0,
                        "away_n": 0, "away_for": 0, "away_against": 0,
                        "all_n": 0, "all_for": 0, "all_against": 0,
                    }

                if away_name not in teams:
                    teams[away_name] = {
                        "home_n": 0, "home_for": 0, "home_against": 0,
                        "away_n": 0, "away_for": 0, "away_against": 0,
                        "all_n": 0, "all_for": 0, "all_against": 0,
                    }

                h = teams[home_name]
                a = teams[away_name]

                h["home_n"] += 1
                h["home_for"] += hg
                h["home_against"] += ag

                a["away_n"] += 1
                a["away_for"] += ag
                a["away_against"] += hg

                h["all_n"] += 1
                h["all_for"] += hg
                h["all_against"] += ag

                a["all_n"] += 1
                a["all_for"] += ag
                a["all_against"] += hg

            st.session_state["comparison_data"] = {
                "competition": competition_name,
                "teams": teams,
            }

            if teams:
                st.success(
                    f"Données chargées pour {len(teams)} équipes."
                )
            else:
                st.warning("Aucun résultat historique exploitable.")

        except HTTPError as error:
            st.error(f"Erreur API HTTP {error.code}.")
        except URLError:
            st.error("Connexion à l'API impossible. Réessaie plus tard.")
        except (ValueError, KeyError, TypeError):
            st.error("Impossible de lire les données reçues.")

comparison = st.session_state.get("comparison_data")

if comparison:
    if comparison["competition"] != competition_name:
        st.warning(
            "Tu as changé de compétition. Recharge les données "
            "pour comparer les équipes de la nouvelle compétition."
        )
    else:
        teams = comparison["teams"]
        names = sorted(teams.keys())

        if len(names) >= 2:
            home_name = st.selectbox(
                "Équipe à domicile",
                names,
                key="compare_home",
            )

            away_names = [name for name in names if name != home_name]

            away_name = st.selectbox(
                "Équipe à l'extérieur",
                away_names,
                key="compare_away",
            )

            if st.button("📊 Comparer les équipes"):
                home = teams[home_name]
                away = teams[away_name]

                st.subheader(f"{home_name} vs {away_name}")

                c1, c2 = st.columns(2)

                c1.metric(
                    f"{home_name} — buts marqués à domicile",
                    f"{home['home_for'] / home['home_n']:.2f}"
                    if home["home_n"] else "Données insuffisantes",
                )

                c2.metric(
                    f"{away_name} — buts marqués à l'extérieur",
                    f"{away['away_for'] / away['away_n']:.2f}"
                    if away["away_n"] else "Données insuffisantes",
                )

                c1, c2 = st.columns(2)

                c1.metric(
                    f"{home_name} — buts encaissés à domicile",
                    f"{home['home_against'] / home['home_n']:.2f}"
                    if home["home_n"] else "Données insuffisantes",
                )

                c2.metric(
                    f"{away_name} — buts encaissés à l'extérieur",
                    f"{away['away_against'] / away['away_n']:.2f}"
                    if away["away_n"] else "Données insuffisantes",
                )

                if home["home_n"] and away["away_n"]:
                    expected_home = (
                        home["home_for"] / home["home_n"]
                        + away["away_against"] / away["away_n"]
                    ) / 2

                    expected_away = (
                        away["away_for"] / away["away_n"]
                        + home["home_against"] / home["home_n"]
                    ) / 2

                    st.markdown("### ⚽ Indication expérimentale")

                    c1, c2 = st.columns(2)

                    c1.metric(
                        "Buts indicatifs — domicile",
                        f"{expected_home:.2f}",
                    )

                    c2.metric(
                        "Buts indicatifs — extérieur",
                        f"{expected_away:.2f}",
                    )

                    st.write(
                        f"Total indicatif : "
                        f"{expected_home + expected_away:.2f} buts."
                    )

                    st.caption(
                        "Calcul exploratoire : moyenne entre l'attaque "
                        "d'une équipe dans ce contexte et les buts "
                        "encaissés par son adversaire dans le contexte "
                        "opposé. Ce n'est pas un modèle prédictif validé."
                    )

                    if home["home_n"] < 5 or away["away_n"] < 5:
                        st.warning(
                            "Au moins une équipe a moins de 5 matchs "
                            "dans son contexte. Les moyennes sont fragiles."
                        )
                else:
                    st.warning(
                        "Il manque des matchs à domicile ou à l'extérieur "
                        "pour calculer les indications."
                    )
        else:
            st.info("Il faut au moins deux équipes avec des données.")

# ============================================================
# BACKTESTING HISTORIQUE - PREMIER LEAGUE
# Bloc indépendant : ne remplace aucune section existante
# ============================================================

import math

st.divider()
st.header("🧪 Backtesting historique")

st.write(
    "Le modèle estime les buts et les probabilités de résultat "
    "en utilisant uniquement les matchs antérieurs à chaque rencontre testée."
)

if st.button("▶️ Lancer le backtesting Premier League", key="run_backtest_pl"):

    token = st.secrets.get("FOOTBALL_DATA_TOKEN", "")

    if not token:
        st.error("Token API introuvable dans les Secrets.")

    else:
        today = datetime.now(timezone.utc).date()
        date_from = today - timedelta(days=90)

        params = urlencode({
            "dateFrom": date_from.isoformat(),
            "dateTo": (today + timedelta(days=1)).isoformat(),
            "status": "FINISHED",
        })

        url = (
            "https://api.football-data.org/v4/"
            f"competitions/PL/matches?{params}"
        )

        request = Request(
            url,
            headers={"X-Auth-Token": token},
        )

        try:
            with st.spinner("Récupération et test des matchs..."):
                with urlopen(request, timeout=30) as response:
                    data = json.loads(
                        response.read().decode("utf-8")
                    )

            matches = []

            for match in data.get("matches", []):
                score = match.get("score", {}).get("fullTime", {})
                hg = score.get("home")
                ag = score.get("away")

                if (
                    match.get("status") == "FINISHED"
                    and isinstance(hg, int)
                    and isinstance(ag, int)
                    and match.get("utcDate")
                    and match.get("homeTeam", {}).get("name")
                    and match.get("awayTeam", {}).get("name")
                ):
                    matches.append({
                        "date": match["utcDate"],
                        "home": match["homeTeam"]["name"],
                        "away": match["awayTeam"]["name"],
                        "hg": hg,
                        "ag": ag,
                    })

            matches.sort(key=lambda m: m["date"])

            # Statistiques cumulées uniquement des matchs déjà joués.
            history = []
            predictions = []

            def poisson_probs(lam, max_goals=10):
                lam = max(0.05, min(float(lam), 8.0))
                probs = []
                for goals in range(max_goals + 1):
                    probs.append(
                        math.exp(-lam) * lam ** goals
                        / math.factorial(goals)
                    )

                total = sum(probs)
                return [p / total for p in probs]

            def estimate_goals(team, venue, prior, league_avg):
                # venue = "home" ou "away"
                scored = 0
                conceded = 0
                count = 0

                for old in prior:
                    if venue == "home" and old["home"] == team:
                        scored += old["hg"]
                        conceded += old["ag"]
                        count += 1

                    elif venue == "away" and old["away"] == team:
                        scored += old["ag"]
                        conceded += old["hg"]
                        count += 1

                # Lissage : équivalent à 3 matchs moyens ajoutés.
                smoothed_scored = (
                    scored + 3 * league_avg
                ) / (count + 3)

                smoothed_conceded = (
                    conceded + 3 * league_avg
                ) / (count + 3)

                return smoothed_scored, smoothed_conceded, count

            for match in matches:

                # On attend d'avoir une base historique minimale.
                if len(history) < 10:
                    history.append(match)
                    continue

                home_avg = sum(m["hg"] for m in history) / len(history)
                away_avg = sum(m["ag"] for m in history) / len(history)

                if home_avg <= 0 or away_avg <= 0:
                    history.append(match)
                    continue

                home_scored, home_conceded, home_n = estimate_goals(
                    match["home"], "home", history, home_avg
                )

                away_scored, away_conceded, away_n = estimate_goals(
                    match["away"], "away", history, away_avg
                )

                # Forces relatives à la moyenne de la compétition.
                home_attack = home_scored / home_avg
                away_defence = away_conceded / home_avg

                away_attack = away_scored / away_avg
                home_defence = home_conceded / away_avg

                expected_home = home_avg * home_attack * away_defence
                expected_away = away_avg * away_attack * home_defence

                ph = poisson_probs(expected_home)
                pa = poisson_probs(expected_away)

                p_home = 0.0
                p_draw = 0.0
                p_away = 0.0

                for i, pi in enumerate(ph):
                    for j, pj in enumerate(pa):
                        probability = pi * pj

                        if i > j:
                            p_home += probability
                        elif i == j:
                            p_draw += probability
                        else:
                            p_away += probability

                probabilities = [p_home, p_draw, p_away]
                labels = ["Domicile", "Nul", "Extérieur"]
                predicted_result = labels[
                    probabilities.index(max(probabilities))
                ]

                actual_result = (
                    "Domicile" if match["hg"] > match["ag"]
                    else "Extérieur" if match["hg"] < match["ag"]
                    else "Nul"
                )

                predictions.append({
                    "Date": match["date"][:10],
                    "Domicile": match["home"],
                    "Extérieur": match["away"],
                    "Buts domicile estimés": round(expected_home, 2),
                    "Buts extérieur estimés": round(expected_away, 2),
                    "Score réel": f'{match["hg"]}-{match["ag"]}',
                    "Résultat prédit": predicted_result,
                    "Résultat réel": actual_result,
                    "P victoire domicile (%)": round(p_home * 100, 1),
                    "P nul (%)": round(p_draw * 100, 1),
                    "P victoire extérieur (%)": round(p_away * 100, 1),
                    "_eh": expected_home,
                    "_ea": expected_away,
                    "_probs": probabilities,
                    "_home_goals": match["hg"],
                    "_away_goals": match["ag"],
                    "_actual_class": (
                        0 if actual_result == "Domicile"
                        else 1 if actual_result == "Nul"
                        else 2
                    ),
                    "_home_n": home_n,
                    "_away_n": away_n,
                })

                # IMPORTANT : le match entre dans l'historique
                # seulement après la création de sa prédiction.
                history.append(match)

            st.session_state["backtest_pl_results"] = predictions

            if predictions:
                st.success(
                    f"Test terminé : {len(predictions)} matchs évalués."
                )
            else:
                st.warning(
                    "Pas assez de matchs historiques exploitables "
                    "pour lancer le test."
                )

        except HTTPError as error:
            st.error(f"Erreur API HTTP {error.code}.")
        except URLError:
            st.error("Connexion à l'API impossible. Réessaie plus tard.")
        except (ValueError, KeyError, TypeError, ZeroDivisionError):
            st.error(
                "Les données reçues n'ont pas pu être analysées."
            )

results = st.session_state.get("backtest_pl_results", [])

if results:
    st.subheader("📈 Résultats du test")

    n = len(results)

    mae = sum(
        abs(r["_eh"] - r["_home_goals"])
        + abs(r["_ea"] - r["_away_goals"])
        for r in results
    ) / (2 * n)

    rmse = math.sqrt(
        sum(
            (r["_eh"] - r["_home_goals"]) ** 2
            + (r["_ea"] - r["_away_goals"]) ** 2
            for r in results
        ) / (2 * n)
    )

    correct = sum(
        r["Résultat prédit"] == r["Résultat réel"]
        for r in results
    )

    brier = sum(
        sum(
            (r["_probs"][i] - (1 if i == r["_actual_class"] else 0)) ** 2
            for i in range(3)
        )
        for r in results
    ) / n

    c1, c2 = st.columns(2)
    c1.metric("Matchs testés", n)
    c2.metric("Résultat exact prédit", f"{correct / n * 100:.1f}%")

    c1, c2 = st.columns(2)
    c1.metric("MAE des buts", f"{mae:.2f}")
    c2.metric("RMSE des buts", f"{rmse:.2f}")

    st.metric("Brier victoire/nul/défaite", f"{brier:.3f}")

    st.caption(
        "MAE et RMSE : erreurs moyennes sur les buts de chaque équipe. "
        "Brier : qualité des trois probabilités, plus bas est préférable. "
        "Ces résultats ne garantissent pas les performances futures."
    )

    # Présenter les colonnes utiles, sans les variables techniques.
    display_results = [
        {
            key: value
            for key, value in row.items()
            if not key.startswith("_")
        }
        for row in results
    ]

    st.dataframe(display_results, use_container_width=True)
