#!/usr/bin/env python3
"""Liaison utilisateurs / groupes AD -> GLPI.

Une fois les utilisateurs et les groupes créés, parcourt l'Active Directory et
force l'association de chaque employé au groupe de son OU (ex. OU=Ventes),
pour que chacun soit rattaché au bon département dans GLPI.
"""
import re

from ldap3 import ALL, SIMPLE, Connection, Server

import config
import glpi_client as glpi

USERS = {}
GROUPS = {}


def load_glpi_data(token):
    resp = glpi.get(token, "Group?range=0-1000")
    if resp.status_code in (200, 206):
        GROUPS.update({g["name"]: g["id"] for g in resp.json()})
    resp = glpi.get(token, "User?range=0-2000")
    if resp.status_code in (200, 206):
        USERS.update({u["name"]: u["id"] for u in resp.json()})


def main():
    config.require_ad()
    conn = Connection(Server(config.AD_SERVER_IP, get_info=ALL), user=config.AD_USER,
                      password=config.AD_PASSWORD, authentication=SIMPLE, auto_bind=True)
    token = glpi.open_session()
    if not token:
        return
    load_glpi_data(token)

    conn.search(config.AD_BASE_DN, "(&(objectClass=user)(objectCategory=person)(sn=*))",
                attributes=["sAMAccountName", "distinguishedName"])
    for entry in conn.entries:
        login = str(entry.sAMAccountName)
        match = re.search(r"OU=([^,]+)", str(entry.distinguishedName))
        group_name = match.group(1) if match else None
        if not group_name or group_name in config.SKIP_OUS:
            continue

        uid, gid = USERS.get(login), GROUPS.get(group_name)
        if uid and gid:
            print(f"Liaison {login} -> {group_name}")
            glpi.post(token, "Group_User", {"input": {"users_id": uid, "groups_id": gid}})

    glpi.close_session(token)


if __name__ == "__main__":
    main()
