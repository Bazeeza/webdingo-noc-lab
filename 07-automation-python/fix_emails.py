#!/usr/bin/env python3
"""Normalisation des courriels GLPI.

Réconcilie le nom d'ouverture de session AD et le courriel enregistré dans
GLPI : force le format login_AD@webdingo.ca pour tous les utilisateurs, pour
qu'aucune alerte ne soit rejetée par Zimbra pour cause d'adresse inconnue.
"""
from ldap3 import ALL, SIMPLE, Connection, Server

import config
import glpi_client as glpi

USERS = {}


def load_all_glpi_users(token):
    print("--- Chargement du cache GLPI ---")
    resp = glpi.get(token, "User?range=0-5000&expand_dropdowns=false")
    if resp.status_code in (200, 206):
        USERS.update({u["name"]: u["id"] for u in resp.json()})
    print(f" > {len(USERS)} utilisateurs en mémoire.")


def main():
    config.require_ad()
    conn = Connection(Server(config.AD_SERVER_IP, get_info=ALL), user=config.AD_USER,
                      password=config.AD_PASSWORD, authentication=SIMPLE, auto_bind=True)
    token = glpi.open_session()
    if not token:
        return
    load_all_glpi_users(token)

    conn.search(config.AD_BASE_DN, "(&(objectClass=user)(objectCategory=person)(sn=*))",
                attributes=["sAMAccountName"])
    updated = 0
    for entry in conn.entries:
        login = str(entry.sAMAccountName)
        if login.endswith("$") or login in config.SKIP_ACCOUNTS:
            continue
        target = f"{login}@{config.AD_DOMAIN}"
        glpi_id = USERS.get(login) or USERS.get(target)  # login simple ou UPN
        if glpi_id:
            print(f"Utilisateur {login:<15} -> OK")
            glpi.post(token, "UserEmail", {"input": {"users_id": glpi_id, "email": target, "is_default": 1}})
            updated += 1
        else:
            print(f"Utilisateur {login:<15} -> [!] introuvable dans GLPI")

    glpi.close_session(token)
    print(f"\n--- Terminé ! {updated} courriels vérifiés. ---")


if __name__ == "__main__":
    main()
