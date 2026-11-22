"""Petite couche d'accès à l'API REST de GLPI (session, en-têtes)."""
import requests

import config

if not config.VERIFY_TLS:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def open_session():
    """Renvoie un jeton de session GLPI, ou None si l'authentification échoue."""
    headers = {
        "Content-Type": "application/json",
        "App-Token": config.GLPI_APP_TOKEN,
        "Authorization": f"user_token {config.GLPI_USER_TOKEN}",
    }
    try:
        resp = requests.get(f"{config.GLPI_URL}initSession", headers=headers,
                            verify=config.VERIFY_TLS, timeout=config.TIMEOUT)
    except requests.RequestException as e:
        print(f"Erreur de connexion au serveur GLPI : {e}")
        return None
    if resp.status_code != 200:
        print(f"Erreur d'authentification GLPI (statut {resp.status_code}).")
        return None
    return resp.json().get("session_token")


def headers(session_token):
    return {
        "Content-Type": "application/json",
        "Session-Token": session_token,
        "App-Token": config.GLPI_APP_TOKEN,
    }


def get(session_token, path):
    return requests.get(f"{config.GLPI_URL}{path}", headers=headers(session_token),
                        verify=config.VERIFY_TLS, timeout=config.TIMEOUT)


def post(session_token, path, payload):
    return requests.post(f"{config.GLPI_URL}{path}", headers=headers(session_token),
                         json=payload, verify=config.VERIFY_TLS, timeout=config.TIMEOUT)


def close_session(session_token):
    try:
        get(session_token, "killSession")
    except requests.RequestException:
        pass
