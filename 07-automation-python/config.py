"""Paramètres communs des scripts WebDingo.

Tous les secrets viennent de variables d'environnement (voir .env.example),
jamais du code. Copier .env.example en .env, le remplir, puis le charger avant
de lancer un script, par exemple :  set -a; . ./.env; set +a
"""
import os
import sys


def _get(name, default=None):
    value = os.environ.get(name, default)
    if value is None or value == "":
        sys.exit(f"Variable d'environnement manquante : {name} (voir .env.example)")
    return value


GLPI_URL = _get("GLPI_URL", "http://192.168.5.14/glpi/apirest.php/")
GLPI_APP_TOKEN = _get("GLPI_APP_TOKEN")
GLPI_USER_TOKEN = _get("GLPI_USER_TOKEN")

AD_SERVER_IP = _get("AD_SERVER_IP", "192.168.5.50")
AD_DOMAIN = _get("AD_DOMAIN", "webdingo.ca")
AD_USER = os.environ.get("AD_USER", "")          # requis seulement par les scripts AD
AD_PASSWORD = os.environ.get("AD_PASSWORD", "")
AD_BASE_DN = _get("AD_BASE_DN", "DC=webdingo,DC=ca")

# Le laboratoire utilisait des certificats autosignés. Mettre GLPI_VERIFY_TLS=1 avec un vrai certificat.
VERIFY_TLS = os.environ.get("GLPI_VERIFY_TLS", "0") == "1"
TIMEOUT = 15  # secondes : un script ne reste jamais bloqué

# Comptes à ne jamais importer ni modifier
SKIP_ACCOUNTS = {"krbtgt", "Invité", "Guest", "Administrateur", "Administrator"}
SKIP_OUS = {"Domain Controllers", "Managed Service Accounts"}


def require_ad():
    if not AD_USER or not AD_PASSWORD:
        sys.exit("AD_USER et AD_PASSWORD sont requis pour ce script (voir .env.example)")
