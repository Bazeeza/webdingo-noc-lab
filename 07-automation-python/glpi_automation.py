#!/usr/bin/env python3
"""Zabbix -> GLPI : création automatique de tickets d'incident.

Lancé par une action Zabbix quand un déclencheur atteint la sévérité « High »
ou « Disaster ». Reçoit les données de l'alerte en arguments, s'authentifie à
l'API GLPI, calcule la priorité, crée le ticket assigné au groupe « Admins »
et ajoute une liste de tâches de diagnostic pour guider les techniciens.

Usage : glpi_automation.py <hôte> <déclencheur> <valeur> <sévérité>
"""
import sys
from datetime import datetime

import glpi_client as glpi

# Identifiants numériques dans le GLPI du laboratoire
DEFAULT_GROUP_ID = 1003      # groupe « Admins » : notifie toute l'équipe
ROUTER_INVENTORY_ID = 7      # équipement réseau « Routeur 1 » dans l'inventaire
DEFAULT_ENTITY_ID = 0        # entité racine

SEVERITY_TO_PRIORITY = {"Information": 1, "Warning": 2, "Average": 3, "High": 4, "Disaster": 5}


def determine_priority(severity):
    return SEVERITY_TO_PRIORITY.get(severity, 3)


def create_tasks(token, ticket_id, priority):
    if priority >= 4:
        tasks = [
            f"Vérifier les logs du routeur Cisco (inventaire n° {ROUTER_INVENTORY_ID}).",
            "Confirmer le statut des interfaces Gi0/1 (WAN) et Gi0/0 (trunk).",
            "Escalader l'incident à l'équipe de direction.",
        ]
    elif priority == 3:
        tasks = ["Analyser les tendances CPU / mémoire.", "Vérifier le taux de perte de paquets."]
    else:
        tasks = []
    for content in tasks:
        glpi.post(token, "TicketTask", {"input": {"tickets_id": ticket_id, "content": content, "tasktype": 1}})


def create_ticket(token, subject, body, severity):
    priority = determine_priority(severity)
    resp = glpi.post(token, "Ticket", {"input": {
        "name": subject,
        "content": body,
        "status": 1,            # Nouveau
        "priority": priority,
        "type": 1,              # Incident
        "entities_id": DEFAULT_ENTITY_ID,
        "_items_id_common": ROUTER_INVENTORY_ID,
        "itemtype": "NetworkEquipment",
        "groups_id_assign": DEFAULT_GROUP_ID,
    }})
    if resp.status_code != 201:
        print(f"ÉCHEC de création du ticket (statut {resp.status_code}) : {resp.text}")
        return None
    ticket_id = resp.json().get("id")
    print(f"SUCCÈS : ticket GLPI n° {ticket_id} créé (groupe {DEFAULT_GROUP_ID}).")
    create_tasks(token, ticket_id, priority)
    return ticket_id


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 1
    hostname, trigger_name, item_value, severity = argv[1:5]
    subject = f"ALERTE RÉSEAU : {hostname} - {trigger_name}"
    body = (f"Alerte Zabbix.\n\nSujet : {trigger_name}\nValeur : {item_value}\n"
            f"Sévérité : {severity}\nDate : {datetime.now():%Y-%m-%d %H:%M:%S}")

    token = glpi.open_session()
    if not token:
        return 1
    try:
        return 0 if create_ticket(token, subject, body, severity) else 1
    finally:
        glpi.close_session(token)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
