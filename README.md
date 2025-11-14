# 🎯 Linky + Tempo pour Home Assistant

Calcule automatiquement le coût de votre consommation Linky selon les tarifs Tempo.

**Architecture simple** : Trigger-based sensors + script Python

**Durée d'installation : 15 minutes**

---

## 📊 Table des matières

- [Ce que vous obtenez](#-ce-que-vous-obtenez)
- [Architecture](#%EF%B8%8F-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
  - [Étape 1 : Trouver votre ID Linky](#étape-1--trouver-votre-id-linky)
  - [Étape 2 : Connaître vos heures creuses](#étape-2--connaître-vos-heures-creuses)
  - [Étape 3 : Copier les fichiers](#étape-3--copier-les-fichiers)
  - [Étape 4 : Script Python](#étape-4--script-python)
  - [Étape 5 : Configuration](#étape-5--modifier-configurationyaml)
  - [Étape 6 : Redémarrer](#étape-6--redémarrer)
  - [Étape 7 : Vérifier](#étape-7--vérifier)
  - [Étape 8 : Tableau Énergie](#étape-8--tableau-énergie)
- [Dépannage](#-dépannage)

---

## ✅ Ce que vous obtenez

- ⚡ **Calcul automatique** du coût chaque matin à 7h00
- 📅 **24h de données complètes** (journée civile : 00h → 00h)
- 🎨 **Tarifs Tempo correctement appliqués** (Bleu/Blanc/Rouge × HP/HC)
- 🎯 **2 couleurs selon tranches horaires** :
  - 00h-06h : Couleur de J-2 (avant-hier)
  - 06h-00h : Couleur de J-1 (hier)
- 📊 **Intégration au Tableau Énergie** avec affichage sur le bon jour
- 🏗️ **Architecture simple** : trigger-based sensors (pas de SQL compliqué)

---

## 🏗️ Architecture

```
sensor.rte_tempo_couleur_actuelle (RTE Tempo)
         ↓
    Change de couleur à 6h00
         ↓
    Trigger-based sensors se mettent à jour
         ↓
  sensor.tempo_couleur_hier (J-1)
  sensor.tempo_couleur_avant_hier (J-2)
         ↓
    Script Python calcule le coût à 7h00
         ↓
    Écrit dans statistics avec timestamp backdaté (J-1 23h59)
         ↓
    Tableau Énergie affiche le coût sur le BON jour ✅
```

**Tout automatique ! 🎉**

---

## 🔍 Prérequis

- [ ] Home Assistant installé et fonctionnel
- [ ] Intégration **ha-linky** installée et fonctionnelle
- [ ] Intégration **RTE Tempo** installée et fonctionnelle
- [ ] **pyscript** installé via HACS

### Si vous n'avez pas ces intégrations :

**ha-linky** : [tuto youtube](https://youtu.be/j_PNaZmhXcU?si=cuBwK3gPe6a-Upq9)

**RTE Tempo** : HACS > Intégrations > "RTE Tempo" > Installer > Redémarrer > Ajouter intégration

** SQLite Web**: Paramètres > Modules complémentaires > Boutique de Modules complémentaires > "sqlite" > installer

**pyscript** : [tuto youtube](https://youtu.be/IkoLVc2z9dA?si=OsD-P1yje1jso95B) HACS > Intégrations > "pyscript" > Installer > Redémarrer

---

## 🚀 INSTALLATION

## Étape 1 : Trouver votre ID Linky

Ouvrez un SQLite web :

```bash
SELECT statistic_id FROM statistics_meta WHERE statistic_id LIKE '%linky%';
```

Vous obtiendrez : `linky:xxx`

**⚠️ NOTEZ CE NUMÉRO !**

---

## Étape 2 : Connaître vos heures creuses

Vérifiez votre contrat EDF.

**Exemples courants :**
- HC nuit : 22h → 6h
- HC nuit + midi : 22h → 6h + 12h → 14h

**⚠️ NOTEZ VOS HEURES CREUSES !**

---

## Étape 3 : Copier les fichiers

### 📄 Fichier 1 : Tarifs Tempo

Créez `/config/linky_tempo_pricing.yaml` :

```yaml
input_number:
  tempo_bleu_hp:
    name: "Tempo Bleu - Heures Pleines"
    min: 0
    max: 1
    step: 0.0001
    initial: 0.1494  # ⚠️ MODIFIEZ
    unit_of_measurement: "€/kWh"
    icon: mdi:currency-eur

  tempo_bleu_hc:
    name: "Tempo Bleu - Heures Creuses"
    min: 0
    max: 1
    step: 0.0001
    initial: 0.1232  # ⚠️ MODIFIEZ
    unit_of_measurement: "€/kWh"
    icon: mdi:currency-eur

  tempo_blanc_hp:
    name: "Tempo Blanc - Heures Pleines"
    min: 0
    max: 1
    step: 0.0001
    initial: 0.1730  # ⚠️ MODIFIEZ
    unit_of_measurement: "€/kWh"
    icon: mdi:currency-eur

  tempo_blanc_hc:
    name: "Tempo Blanc - Heures Creuses"
    min: 0
    max: 1
    step: 0.0001
    initial: 0.1391  # ⚠️ MODIFIEZ
    unit_of_measurement: "€/kWh"
    icon: mdi:currency-eur

  tempo_rouge_hp:
    name: "Tempo Rouge - Heures Pleines"
    min: 0
    max: 1
    step: 0.0001
    initial: 0.6468  # ⚠️ MODIFIEZ
    unit_of_measurement: "€/kWh"
    icon: mdi:currency-eur

  tempo_rouge_hc:
    name: "Tempo Rouge - Heures Creuses"
    min: 0
    max: 1
    step: 0.0001
    initial: 0.1460  # ⚠️ MODIFIEZ
    unit_of_measurement: "€/kWh"
    icon: mdi:currency-eur

  tempo_abonnement:
    name: "Abonnement Tempo mensuel"
    min: 0
    max: 50
    step: 0.01
    initial: 12.86
    unit_of_measurement: "€/mois"
    icon: mdi:currency-eur
```

### 📄 Fichier 2 : Helpers coûts

Créez `/config/linky_tempo_helpers.yaml` :

```yaml
input_number:
  linky_cout_total:
    name: "Linky Coût Total"
    min: 0
    max: 100000
    step: 0.01
    unit_of_measurement: "€"
    icon: mdi:currency-eur
    mode: box

  linky_cout_hier:
    name: "Linky Coût Hier"
    min: 0
    max: 1000
    step: 0.01
    unit_of_measurement: "€"
    icon: mdi:currency-eur
    mode: box
```

### 📄 Fichier 3 : Sensors SQL Linky

Créez des entités dasn apparails > nouvel appareil > SQL :

**⚠️ REMPLACEZ `linky:xxx` par VOTRE ID !**

```yaml
sql:
  - name: "Linky Énergie Totale"
    unique_id: linky_energie_totale
    query: >
      SELECT ROUND(s.sum / 1000.0, 3)
      FROM statistics s
      JOIN statistics_meta m ON m.id = s.metadata_id
      WHERE m.statistic_id = 'linky:xxx'
      ORDER BY s.start_ts DESC
      LIMIT 1;
    column: "kwh"
    unit_of_measurement: "kWh"
    device_class: energy
    state_class: total_increasing

  - name: "Linky Consommation Hier"
    unique_id: linky_conso_hier
    query: >
      SELECT ROUND(SUM(s.state) / 1000.0, 3)
      FROM statistics s
      JOIN statistics_meta m ON m.id = s.metadata_id
      WHERE m.statistic_id = 'linky:xxx'
        AND s.start_ts >= CAST(strftime('%s', datetime('now', '-1 day', 'start of day')) AS INTEGER)
        AND s.start_ts < CAST(strftime('%s', datetime('now', 'start of day')) AS INTEGER)
    column: "kwh"
    unit_of_measurement: "kWh"
    device_class: energy
    state_class: total
```

### 📄 Fichier 4 : Sensors historique Tempo

Créez `/config/linky_tempo_sensors_historique.yaml` :

```yaml
template:
  # Sensors déclenchés par l'heure (pas par changement d'état)
  - trigger:
      # 1) Juste avant le basculement de journée (on capture "hier")
      - id: roll_hier
        platform: time
        at: "05:59:59"

      # 2) Juste après le basculement (on décale "avant-hier")
      - id: roll_avant_hier
        platform: time
        at: "06:00:01"

      # 3) Au démarrage de Home Assistant (restauration)
      - id: startup
        platform: homeassistant
        event: start

    sensor:
      - name: "Tempo Couleur Hier"
        unique_id: tempo_couleur_hier_trigger
        state: >
          {% if trigger.platform == 'state' %}
            {{ states('sensor.tempo_couleur_avant_hier') }}
          {% else %}
            {{ states('sensor.tempo_couleur_hier') if states('sensor.tempo_couleur_hier') != 'unknown' else 'BLEU' }}
          {% endif %}
        icon: mdi:calendar-minus

      - name: "Tempo Couleur Avant-hier"
        unique_id: tempo_couleur_avant_hier_trigger
        state: >
          {% if trigger.platform == 'state' and trigger.from_state is not none %}
            {{ trigger.from_state.state }}
          {% else %}
            {{ states('sensor.tempo_couleur_avant_hier') if states('sensor.tempo_couleur_avant_hier') != 'unknown' else 'BLEU' }}
          {% endif %}
        icon: mdi:calendar-minus-outline

  - sensor:
      - name: "Tempo Historique 3 Jours"
        unique_id: tempo_historique_3_jours
        state: >
          Aujourd'hui: {{ states('sensor.rte_tempo_couleur_actuelle') }} |
          Hier: {{ states('sensor.tempo_couleur_hier') }} |
          Avant-hier: {{ states('sensor.tempo_couleur_avant_hier') }}
        icon: mdi:calendar-range
        attributes:
          aujourd_hui: "{{ states('sensor.rte_tempo_couleur_actuelle') }}"
          hier: "{{ states('sensor.tempo_couleur_hier') }}"
          avant_hier: "{{ states('sensor.tempo_couleur_avant_hier') }}"
```

### 📄 Fichier 5 : Templates

Créez `/config/linky_tempo_templates.yaml` :

```yaml
template:
  - sensor:
      # Tarif actuel en temps réel
      - name: "Linky Tarif Actuel"
        unique_id: linky_tarif_actuel
        unit_of_measurement: "€/kWh"
        device_class: monetary
        state: >
          {% set couleur = states('sensor.rte_tempo_couleur_actuelle')|lower %}
          {% set hc = is_state('binary_sensor.rte_tempo_heures_creuses', 'on') %}
          {% if couleur == 'bleu' %}
            {% if hc %}{{ states('input_number.tempo_bleu_hc')|float(0.1232) }}
            {% else %}{{ states('input_number.tempo_bleu_hp')|float(0.1494) }}{% endif %}
          {% elif couleur == 'blanc' %}
            {% if hc %}{{ states('input_number.tempo_blanc_hc')|float(0.1391) }}
            {% else %}{{ states('input_number.tempo_blanc_hp')|float(0.1730) }}{% endif %}
          {% elif couleur == 'rouge' %}
            {% if hc %}{{ states('input_number.tempo_rouge_hc')|float(0.1460) }}
            {% else %}{{ states('input_number.tempo_rouge_hp')|float(0.6468) }}{% endif %}
          {% else %}
            0.15
          {% endif %}
        attributes:
          couleur: "{{ states('sensor.rte_tempo_couleur_actuelle') }}"
          type_heure: "{{ 'HC' if is_state('binary_sensor.rte_tempo_heures_creuses', 'on') else 'HP' }}"
        icon: mdi:cash

      # Sensor pour le Tableau Énergie (IMPORTANT!)
      - name: "Linky Coût Total Cumulé"
        unique_id: linky_cout_total_cumule
        unit_of_measurement: "€"
        device_class: monetary
        state_class: total_increasing
        state: "{{ states('input_number.linky_cout_total')|float(0) }}"
        icon: mdi:cash-multiple

      # Statistiques additionnelles
      - name: "Linky Prix Moyen kWh"
        unique_id: linky_prix_moyen_kwh
        unit_of_measurement: "€/kWh"
        state: >
          {% set energie = states('sensor.linky_energie_totale')|float(0) %}
          {% set cout = states('input_number.linky_cout_total')|float(0) %}
          {% if energie > 0 %}
            {{ (cout / energie)|round(4) }}
          {% else %}
            0
          {% endif %}
        icon: mdi:calculator
```

### 📄 Fichier 6 : Automation

Créez `/config/linky_tempo_automation.yaml` :

```yaml
automation:
  - id: linky_calcul_cout_tempo
    alias: "Linky - Calcul Coût Tempo Quotidien"
    description: "Calcule le coût de la consommation de la veille selon les tarifs Tempo"
    trigger:
      - platform: time
        at: "07:00:00"
    condition: []
    action:
      - delay:
          minutes: 2
      - service: pyscript.calcul_cout_tempo_journee
        data: {}
    mode: single
```

---

## Étape 4 : Script Python

### Créer le dossier

```bash
mkdir -p /config/pyscript
```

### Copier le script

Copiez le fichier `pyscript/linky_tempo_cost.py` fourni dans `/config/pyscript/`

**⚠️ MODIFICATIONS OBLIGATOIRES :**

1. **Ligne 17** : Remplacez par votre ID Linky
   ```python
   LINKY_STATISTIC_ID = "linky:VOTRE_ID_ICI"
   ```

2. **Lignes 52-58** : Configurez VOS heures creuses
   ```python
   def is_heure_creuse(hour):
       return hour >= 22 or hour < 6  # Modifiez selon votre contrat
   ```

---

## Étape 5 : Modifier configuration.yaml

Ajoutez dans `/config/configuration.yaml` :

```yaml
# Configuration Linky + Tempo
pyscript:

input_number:
  - !include linky_tempo_pricing.yaml
  - !include linky_tempo_helpers.yaml

sql:
  - !include linky_tempo_sql.yaml

template:
  - !include linky_tempo_sensors_historique.yaml
  - !include linky_tempo_templates.yaml

automation: !include linky_tempo_automation.yaml
```

**Note :** Adaptez si vous avez déjà ces sections (fusionnez le contenu).

---

## Étape 6 : Redémarrer

**Paramètres** > **Système** > **Redémarrer**

Attendez 2-3 minutes.

---

## Étape 7 : Vérifier

### Vérifier les sensors

**Outils de développement** > **États**

Recherchez :
- `sensor.tempo_couleur_hier` ✅
- `sensor.tempo_couleur_avant_hier` ✅
- `sensor.linky_energie_totale` ✅
- `sensor.linky_tarif_actuel` ✅
- `sensor.linky_cout_total_cumule` ✅

**Note :** Les sensors de couleurs peuvent être "unknown" les premiers jours (attendez 2-3 jours).

### Tester le calcul

**Outils de développement** > **Services**

```yaml
service: pyscript.calcul_cout_tempo_journee
```

Vérifiez les logs (**Paramètres** > **Système** > **Journaux**) :

```
📅 Période : [date] à [date]
🎨 Couleurs Tempo utilisées :
   - J-2 (pour 00h-06h) : BLEU
   - J-1 (pour 06h-00h) : BLANC
📊 Nombre de lignes récupérées : 24
✅ Coût total de la journée : XX.XX €
✅ Statistique backdatée écrite à [date] 23:59:59  ← Affichage sur le bon jour!
```

---

## Étape 8 : Tableau Énergie

1. **Énergie** (barre latérale) > **CONFIGURER**
2. **Réseau électrique** :
   - **Consommation** : `sensor.linky_energie_totale`
   - **Suivi des coûts** : ✅ Cocher
   - **Coût total** : `sensor.linky_cout_total_cumule` ⚠️ Pas l'input_number!
3. **ENREGISTRER**

Attendez 2-3 heures pour voir les données.

---

## 🐛 Dépannage

### Les sensors sont "unknown"

**Cause :** Pas assez d'historique.

**Solution :** Attendez 2-3 jours que l'historique RTE Tempo se remplisse.

### Erreur "LINKY_STATISTIC_ID not found"

**Cause :** ID Linky incorrect.

**Solution :**
1. Vérifiez votre ID (Étape 1)
2. Remplacez dans `linky_tempo_sql.yaml` (2 fois)
3. Remplacez dans `pyscript/linky_tempo_cost.py` (ligne 17)
4. Redémarrez

### Le calcul ne fonctionne pas

**Vérifiez :**
- pyscript est installé
- Le fichier Python est dans `/config/pyscript/`
- Les logs pour voir l'erreur exacte

### Les heures creuses ne correspondent pas

**Solution :** Modifiez la fonction `is_heure_creuse()` dans le script Python (lignes 52-58).

### Le coût s'affiche sur le mauvais jour

**Vérifiez les logs** : Vous devez voir "Statistique backdatée écrite à ..."

Si ce message n'apparaît pas, c'est qu'il y a eu une erreur d'écriture dans statistics.

---

## 📊 Entités créées

### Sensors

- `sensor.tempo_couleur_hier` - Couleur J-1
- `sensor.tempo_couleur_avant_hier` - Couleur J-2
- `sensor.linky_energie_totale` - Énergie totale (kWh)
- `sensor.linky_tarif_actuel` - Tarif actuel (€/kWh)
- `sensor.linky_cout_total_cumule` - **Pour le Tableau Énergie** (€)
- `sensor.linky_prix_moyen_kwh` - Prix moyen (€/kWh)

### Helpers (input_number)

- `input_number.linky_cout_total` - Coût total cumulé (€)
- `input_number.linky_cout_hier` - Coût hier (€)
- `input_number.tempo_bleu/blanc/rouge_hp/hc` - 6 tarifs Tempo

---

## ⏱️ Timeline quotidienne

```
06h00 → Couleur Tempo change
        Trigger-based sensors se mettent à jour

06h30 → Linky importe les données de J-1

07h00 → Automation déclenche pyscript
        ↓
        Calcul du coût (24h, 2 couleurs)
        ↓
        Écriture dans statistics avec timestamp J-1 23h59
        ↓
        Mise à jour input_number
        ↓
        Notification
```

**Le Tableau Énergie affiche le coût sur le BON jour (J-1) ! 🎉**

---

## 🎓 Pourquoi 2 couleurs ?

Les journées Tempo vont de **6h à 6h** (pas minuit à minuit).

Dans une journée civile (lundi 00h → mardi 00h) :

```
Lundi 00h ────── 06h ──────────────────────── Mardi 00h
     │            │                              │
     │   Tempo    │      Tempo du lundi          │
     │  dimanche  │                              │
     └────────────┴──────────────────────────────┘
       6 heures          18 heures
```

On utilise :
- Couleur du **dimanche** pour 00h-06h
- Couleur du **lundi** pour 06h-00h

---

## 📝 Points importants

### ✅ À FAIRE :

- Remplacer votre ID Linky dans 2 fichiers
- Configurer vos heures creuses dans le script Python
- Ajuster vos tarifs Tempo
- Attendre 2-3 jours que l'historique se remplisse

### ✅ Architecture utilisée :

- **Trigger-based sensors** (pas de SQL pour les couleurs)
- **Script Python pyscript** (calcul + backdating)
- **Aucun input_text**
- **Aucune automation de sauvegarde**

---

## 🎊 Version

**Version : 1.0 - Trigger-based avec Backdating**

- Date : 13 novembre 2024
- Architecture : Trigger-based template sensors
- Calcul : Journée civile complète (24h)
- Couleurs : 2 couleurs Tempo par journée
- Backdating : Affichage sur le bon jour dans le Tableau Énergie ✅

---

## 📚 Autres fichiers

- **README_LINKY_TEMPO.md** - Documentation de référence complète
- **RECAP_NETTOYAGE.md** - Résumé du nettoyage effectué
- **configuration_example.yaml** - Exemple de configuration
- **lovelace_card_example.yaml** - Exemples de cartes
- **diagnostic_linky_tempo.sh** - Script de diagnostic

---

**Bon monitoring ! 📊⚡💶**
