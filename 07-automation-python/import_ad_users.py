#!/usr/bin/env python3
"""Importation Active Directory -> GLPI.

Se connecte au contrôleur de domaine en LDAP, lit les utilisateurs et leur
unité d'organisation (OU), puis crée dans GLPI les comptes et les groupes
correspondants. Évite la saisie manuelle de centaines de comptes.
"""
import re

from ldap3 import ALL, SIMPLE, Connection, Server
from unidecode import unidecode

import config
import glpi_client as glpi

GROUPS_CACHE = {}


def load_existing_groups(token):
    resp = glpi.get(token, "Group?range=0-500")
    if resp.status_code in (200, 206):
        for grp in resp.json():
            GROUPS_CACHE[grp["name"]] = grp["id"]
    print(f" [INFO] {len(GROUPS_CACHE)} groupes existants chargés en cache.")


def get_group_id(token, group_name):
    if group_name in GROUPS_CACHE:
        return GROUPS_CACHE[group_name]
    print(f"   + Nouveau groupe détecté : création de '{group_name}'...")
    resp = glpi.post(token, "Group", {"input": {"name": group_name}})
    if resp.status_code == 201:
        GROUPS_CACHE[group_name] = resp.json()["id"]
        return GROUPS_CACHE[group_name]
    return None


def get_or_create_user(token, user):
    search = ("search/User?criteria[0][field]=1&criteria[0][searchtype]=equals"
              f"&criteria[0][value]={user['name']}")
    resp = glpi.get(token, search)
    if resp.status_code == 200 and resp.json().get("totalcount", 0) > 0:
        return resp.json()["data"][0]["1"]

    print(f"   + Création utilisateur : {user['name']}")
    resp = glpi.post(token, "User", {"input": {
        "name": user["name"],
        "realname": user["lastname"],
        "firstname": user["firstname"],
        "is_active": 1,
    }})
    if resp.status_code != 201:
        return None
    user_id = resp.json()["id"]
    glpi.post(token, "UserEmail", {"input": {"users_id": user_id, "email": user["email"], "is_default": 1}})
    return user_id


def main():
    config.require_ad()
    print("--- Importation AD -> GLPI ---")
    try:
        conn = Connection(Server(config.AD_SERVER_IP, get_info=ALL), user=config.AD_USER,
                          password=config.AD_PASSWORD, authentication=SIMPLE, auto_bind=True)
    except Exception as e:
        print(f"ERREUR AD : {e}")
        return

    token = glpi.open_session()
    if not token:
        return
    load_existing_groups(token)

    conn.search(config.AD_BASE_DN, "(&(objectClass=user)(objectCategory=person)(sn=*))",
                attributes=["sAMAccountName", "sn", "givenName", "distinguishedName"])
    count = 0
    for entry in conn.entries:
        login = str(entry.sAMAccountName)
        if login.endswith("$") or login in config.SKIP_ACCOUNTS:
            continue
        lastname = str(entry.sn)
        firstname = str(entry.givenName) if entry.givenName else ""

        # Courriel au format prenom.nom@domaine, sans accents ni espaces
        first = unidecode(firstname.lower().replace(" ", ""))
        last = unidecode(lastname.lower().replace(" ", ""))
        email = f"{first}.{last}@{config.AD_DOMAIN}"

        group_name = "Utilisateurs AD"
        match = re.search(r"OU=([^,]+)", str(entry.distinguishedName))
        if match:
            group_name = match.group(1)
            if group_name in config.SKIP_OUS:
                continue

        group_id = get_group_id(token, group_name)
        user_id = get_or_create_user(token, {"name": login, "lastname": lastname,
                                             "firstname": firstname, "email": email})
        if user_id and group_id:
            glpi.post(token, "Group_User", {"input": {"users_id": user_id, "groups_id": group_id}})
            count += 1

    glpi.close_session(token)
    print(f"\n--- Terminé ! {count} utilisateurs traités. ---")


if __name__ == "__main__":
    main()
