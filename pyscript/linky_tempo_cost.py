"""
Script Python pour calculer le coût Linky avec tarification Tempo
Installation : Utiliser l'intégration pyscript (HACS)
Emplacement : config/pyscript/linky_tempo_cost.py

Ce script calcule le coût de la consommation Linky en appliquant
les tarifs Tempo (Bleu/Blanc/Rouge × HP/HC) sur les données horaires.
"""

import sqlite3
from datetime import datetime, timedelta
import logging

_LOGGER = logging.getLogger(__name__)

# ID du statistic Linky (à adapter)
LINKY_STATISTIC_ID = "linky:xxx"

# Entités RTE Tempo
TEMPO_COULEUR_ENTITY = "sensor.rte_tempo_couleur_actuelle"
TEMPO_HC_ENTITY = "binary_sensor.rte_tempo_heures_creuses"

# Tarifs Tempo (entités input_number)
TARIFS = {
    "bleu_hp": "input_number.tempo_bleu_hp",
    "bleu_hc": "input_number.tempo_bleu_hc",
    "blanc_hp": "input_number.tempo_blanc_hp",
    "blanc_hc": "input_number.tempo_blanc_hc",
    "rouge_hp": "input_number.tempo_rouge_hp",
    "rouge_hc": "input_number.tempo_rouge_hc",
}

# Sensors de sortie
COUT_TOTAL_ENTITY = "input_number.linky_cout_total"
COUT_HIER_ENTITY = "input_number.linky_cout_hier"


def get_tarif(couleur, is_hc):
    """Récupère le tarif selon la couleur et HP/HC."""
    couleur_lower = couleur.lower() if couleur else "bleu"
    periode = "hc" if is_hc else "hp"
    tarif_key = f"{couleur_lower}_{periode}"

    try:
        tarif = float(state.get(TARIFS[tarif_key]))
        return tarif
    except (ValueError, KeyError, TypeError):
        _LOGGER.error(f"Impossible de récupérer le tarif {tarif_key}")
        return 0.15  # Tarif par défaut


def is_heure_creuse(hour):
    """
    Détermine si une heure est en heures creuses.
    À ADAPTER selon votre contrat !
    Exemple : HC de 22h à 6h
    """
    return hour >= 22 or hour < 6


def get_couleur_tempo_for_date(date, hass):
    """
    Récupère la couleur Tempo pour une date donnée.
    ATTENTION : Cette fonction doit être adaptée selon vos données.

    Options :
    1. Interroger l'historique de sensor.rte_tempo_couleur_actuelle
    2. Utiliser une API RTE
    3. Stocker les couleurs dans un helper

    Pour l'instant, retourne la couleur actuelle (approximation).
    """
    try:
        # Tentative de récupération depuis l'historique
        # Cette partie nécessite d'interroger la base de données
        couleur = hass.states.get(TEMPO_COULEUR_ENTITY)
        return couleur if couleur else "BLEU"
    except Exception as e:
        _LOGGER.error(f"Erreur récupération couleur Tempo: {e}")
        return "BLEU"


@service
def calcul_cout_tempo_journee():
    """
    Service principal : calcule le coût de la dernière journée Tempo.
    Appel : service: pyscript.calcul_cout_tempo_journee
    """

    _LOGGER.info("Début du calcul du coût Tempo")

    try:
        # Connexion à la base de données HA
        db_path = "/config/home-assistant_v2.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Récupération des tarifs actuels
        tarifs = {}
        for key, entity in TARIFS.items():
            tarifs[key] = float(state.get(entity) or 0.15)

        # Calcul de la période : journée civile COMPLÈTE de J-1 00h à J 00h
        # À 7h00 du jour J, on a les données de J-1 complètes (0h-23h59)
        # On calcule une journée civile : J-1 00h00 à J 00h00
        now = datetime.now()
        # Hier (J-1) à 00h00
        debut_journee = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        # Aujourd'hui (J) à 00h00
        fin_journee = now.replace(hour=0, minute=0, second=0, microsecond=0)

        start_ts = int(debut_journee.timestamp())
        end_ts = int(fin_journee.timestamp())

        _LOGGER.info(f"📅 Période : {debut_journee} à {fin_journee}")
        _LOGGER.info(f"   (Journée civile COMPLÈTE : 24h de données)")

        # Requête SQL pour récupérer les données horaires
        query = """
            SELECT s.start_ts, s.state, s.sum
            FROM statistics s
            JOIN statistics_meta m ON m.id = s.metadata_id
            WHERE m.statistic_id = ?
              AND s.start_ts >= ?
              AND s.start_ts < ?
            ORDER BY s.start_ts ASC
        """

        cursor.execute(query, (LINKY_STATISTIC_ID, start_ts, end_ts))
        rows = cursor.fetchall()

        _LOGGER.info(f"Nombre de lignes récupérées : {len(rows)}")

        # Récupération des couleurs Tempo depuis les sensors
        # Couleur J-2 : pour les heures de 00h à 06h (fin de la journée Tempo de J-2)
        # Couleur J-1 : pour les heures de 06h à 00h (journée Tempo de J-1)
        couleur_j2 = state.get("sensor.tempo_couleur_avant_hier") or "BLEU"
        couleur_j1 = state.get("sensor.tempo_couleur_hier") or "BLEU"

        _LOGGER.info(f"🎨 Couleurs Tempo utilisées :")
        _LOGGER.info(f"   - J-2 (pour 00h-06h) : {couleur_j2}")
        _LOGGER.info(f"   - J-1 (pour 06h-00h) : {couleur_j1}")

        # Calcul du coût
        cout_total = 0.0
        details = []

        for start_ts, state_wh, sum_wh in rows:
            # Conversion du timestamp en datetime
            dt = datetime.fromtimestamp(start_ts)
            hour = dt.hour

            # Détermination de la couleur Tempo selon l'heure
            # 00h à 06h : couleur de J-2 (fin de la journée Tempo de J-2)
            # 06h à 24h : couleur de J-1 (journée Tempo de J-1)
            if hour < 6:
                couleur = couleur_j2
            else:
                couleur = couleur_j1

            # Détermination HP/HC
            is_hc = is_heure_creuse(hour)

            # Récupération du tarif
            tarif = get_tarif(couleur, is_hc)

            # Calcul du coût pour cette heure
            energie_kwh = state_wh / 1000.0
            cout_heure = energie_kwh * tarif
            cout_total += cout_heure

            details.append(
                f"{dt.strftime('%H:%M')} - {couleur} {'HC' if is_hc else 'HP'} : "
                f"{energie_kwh:.3f} kWh × {tarif:.4f} €/kWh = {cout_heure:.2f} €"
            )

        # Affichage des détails dans les logs
        _LOGGER.info("Détail du calcul :")
        for detail in details:
            _LOGGER.info(detail)

        _LOGGER.info(f"✅ Coût total de la journée : {cout_total:.2f} €")
        _LOGGER.info(f"   (Du {debut_journee.strftime('%d/%m/%Y 00h')} au {fin_journee.strftime('%d/%m/%Y 00h')})")
        _LOGGER.info(f"   (Couleurs : {couleur_j2} pour 00h-06h, {couleur_j1} pour 06h-00h)")

        # Mise à jour du sensor de coût du jour
        input_number.set_value(entity_id=COUT_HIER_ENTITY, value=round(cout_total, 2))

        # Mise à jour du coût total cumulé
        # On ajoute le coût du jour au total existant
        cout_total_actuel = float(state.get(COUT_TOTAL_ENTITY) or 0)
        nouveau_cout_total = cout_total_actuel + cout_total
        input_number.set_value(entity_id=COUT_TOTAL_ENTITY, value=round(nouveau_cout_total, 2))

        _LOGGER.info(f"💶 Coût total cumulé : {nouveau_cout_total:.2f} €")

        # ============================================================
        # BACKDATING : Écriture dans statistics avec timestamp de J-1
        # ============================================================
        # On écrit le coût à 23h59:59 de J-1 pour que le Tableau Énergie
        # affiche le coût sur le bon jour (J-1 au lieu de J)

        # Timestamp de fin de journée J-1 (23h59:59)
        end_of_yesterday = fin_journee - timedelta(seconds=1)  # J 00h00 - 1 seconde = J-1 23h59:59
        backdate_ts = int(end_of_yesterday.timestamp())

        # Écriture dans la table statistics
        try:
            insert_query = """
                INSERT INTO statistics (metadata_id, start_ts, state, sum)
                SELECT m.id, ?, ?, ?
                FROM statistics_meta m
                WHERE m.statistic_id = 'sensor.linky_cout_total_cumule'
                ON CONFLICT(metadata_id, start_ts) DO UPDATE SET
                    state = excluded.state,
                    sum = excluded.sum
            """
            cursor.execute(insert_query, (backdate_ts, round(cout_total, 2), round(nouveau_cout_total, 2)))
            conn.commit()
            _LOGGER.info(f"✅ Statistique backdatée écrite à {end_of_yesterday.strftime('%d/%m/%Y %H:%M:%S')}")
        except Exception as e:
            _LOGGER.warning(f"Impossible d'écrire la statistique backdatée : {e}")
            _LOGGER.info("Les input_number ont quand même été mis à jour")

        # Fermeture de la connexion
        conn.close()

        # Notification de succès avec informations détaillées
        persistent_notification.create(
            title="✅ Calcul Coût Linky Tempo",
            message=f"Journée du {debut_journee.strftime('%d/%m 00h')} au {fin_journee.strftime('%d/%m 00h')}\n" \
                    f"Couleurs : {couleur_j2} (00h-06h) + {couleur_j1} (06h-00h)\n" \
                    f"Coût de la journée : {cout_total:.2f} €\n" \
                    f"Coût total cumulé : {nouveau_cout_total:.2f} €\n" \
                    f"Nombre d'heures : {len(rows)}",
            notification_id="linky_tempo_calcul"
        )

    except Exception as e:
        _LOGGER.error(f"Erreur lors du calcul du coût Tempo : {e}")
        persistent_notification.create(
            title="Erreur Calcul Linky Tempo",
            message=f"Erreur : {str(e)}",
            notification_id="linky_tempo_error"
        )


@service
def reset_cout_total():
    """
    Service pour réinitialiser le coût total.
    Appel : service: pyscript.reset_cout_total
    """
    input_number.set_value(entity_id=COUT_TOTAL_ENTITY, value=0)
    _LOGGER.info("Coût total réinitialisé")


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

@service
def get_couleur_tempo_historique(date_str):
    """
    Service pour récupérer la couleur Tempo d'une date passée.
    Appel : service: pyscript.get_couleur_tempo_historique
            data:
              date_str: "2024-01-15"

    Cette fonction interroge l'historique de sensor.rte_tempo_couleur_actuelle
    """
    try:
        db_path = "/config/home-assistant_v2.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Conversion de la date en timestamps (journée Tempo : 06h à 06h)
        date = datetime.strptime(date_str, "%Y-%m-%d")
        start_dt = date.replace(hour=6, minute=0, second=0)
        end_dt = (date + timedelta(days=1)).replace(hour=6, minute=0, second=0)

        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())

        # Requête pour récupérer la couleur Tempo
        query = """
            SELECT state
            FROM states
            WHERE entity_id = ?
              AND last_updated_ts >= ?
              AND last_updated_ts < ?
            ORDER BY last_updated_ts ASC
            LIMIT 1
        """

        cursor.execute(query, (TEMPO_COULEUR_ENTITY, start_ts, end_ts))
        result = cursor.fetchone()

        conn.close()

        if result:
            couleur = result[0]
            _LOGGER.info(f"Couleur Tempo pour {date_str} : {couleur}")
            return couleur
        else:
            _LOGGER.warning(f"Aucune couleur trouvée pour {date_str}")
            return "BLEU"  # Valeur par défaut

    except Exception as e:
        _LOGGER.error(f"Erreur récupération couleur Tempo historique : {e}")
        return "BLEU"
