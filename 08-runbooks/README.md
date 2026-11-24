# Runbooks d'incident

[![Français](https://img.shields.io/badge/Langue-Français-3fe0a0?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-2b9dff?style=for-the-badge)](README.en.md)

Que faire quand une alerte sonne. Chaque fiche suit le même ordre : **ce que ça veut dire,
l'impact, vérifier, agir, escalader**. Le ticket GLPI est créé automatiquement pour les
alertes *High* ; le technicien y note chaque étape, puis le ferme avec la cause trouvée.

| Alerte Zabbix | Sévérité | Fiche |
|---|---|---|
| Statut de l'interface Gi0/1 : DOWN | High | [1. Lien Internet principal tombé](#1-lien-internet-principal-tombé) |
| Bande passante entrante > 60 % / > 85 % | Warning / High | [2. Saturation du lien](#2-saturation-du-lien) |
| Erreurs ou paquets rejetés sur Gi0/1 | Warning / High | [3. Erreurs d'interface](#3-erreurs-dinterface) |
| Perte de paquets ICMP, latence | Warning / High | [4. Lien dégradé](#4-lien-dégradé) |
| Uptime < 1 h / < 5 min | Warning / High | [5. Redémarrage du routeur](#5-redémarrage-du-routeur) |
| Connexions TCP établies > 100 / > 200 | Warning / High | [6. Connexions TCP anormales](#6-connexions-tcp-anormales) |
| CPU ou mémoire du routeur élevés | Warning / High | [7. Routeur surchargé](#7-routeur-surchargé) |
| Espace disque < 20 % / < 10 % | Warning / High | [8. Disque d'un serveur presque plein](#8-disque-dun-serveur-presque-plein) |

---

## 1. Lien Internet principal tombé

**Ce que ça veut dire** : l'interface WAN de Routeur1 est hors service.
**Impact attendu** : aucun pour les utilisateurs si HSRP a basculé ; les connexions ouvertes
avant la panne sont coupées.

**Vérifier**

```
Routeur1# show ip interface brief
Routeur1# show interfaces GigabitEthernet0/1
Routeur1# show track 1
Routeur2# show standby brief
```

- Routeur2 doit être *Active* sur les deux groupes. Sinon, passer directement à l'escalade.
- `administratively down` : quelqu'un a fait `shutdown` ; `down/down` : câble, port ou fournisseur.

**Agir**

1. Vérifier le câble et les voyants du port Gi0/1, puis l'équipement du fournisseur.
2. Si l'interface est montée mais sans adresse : `show dhcp lease`, puis `shutdown` / `no shutdown`.
3. Au retour du lien, confirmer que Routeur1 reprend le rôle *Active* (préemption).

**Escalader** : au fournisseur Internet si le lien reste coupé plus de 15 minutes ; en urgence
si Routeur2 n'a pas pris le relais (Internet coupé pour tous).

## 2. Saturation du lien

**Ce que ça veut dire** : le trafic entrant sur Gi0/1 dépasse 60 % (Warning) ou 85 % (High)
de la capacité pendant 5 minutes.
**Impact attendu** : navigation lente, appels VoIP hachés, applications web qui expirent.

**Vérifier**

```
Routeur1# show interfaces GigabitEthernet0/1 | include rate
Routeur1# show ip nat translations
Routeur1# show ip nat statistics
```

- Dans Grafana, regarder si la hausse est brutale (transfert ponctuel) ou progressive (besoin réel).
- Dans les traductions NAT, repérer l'adresse interne qui a le plus de sessions.

**Agir**

1. Identifier le poste ou le serveur en cause et son usage (mise à jour, sauvegarde, téléchargement).
2. Trafic légitime mais mal placé (sauvegarde en journée) : le reprogrammer hors des heures.
3. Trafic anormal : isoler le poste (port du switch en `shutdown`) et traiter comme un incident de sécurité.

**Escalader** : si la saturation revient chaque jour, proposer une augmentation de capacité
ou de la qualité de service (QoS) ; si le trafic est suspect, à l'équipe sécurité.

## 3. Erreurs d'interface

**Ce que ça veut dire** : des paquets arrivent ou partent corrompus, ou sont rejetés.
Une interface saine reste à 0.
**Impact attendu** : retransmissions, lenteurs, perte de paquets.

**Vérifier**

```
Routeur1# show interfaces GigabitEthernet0/1 | include errors|CRC|drops|duplex
```

- Erreurs CRC ou *input errors* : presque toujours physique (câble, connecteur, port).
- Discards sans erreurs : congestion (voir la fiche 2).
- Mauvaise négociation : vérifier que la vitesse et le duplex sont identiques des deux côtés.

**Agir**

1. Remettre les compteurs à zéro pour mesurer proprement : `clear counters GigabitEthernet0/1`.
2. Changer le câble, puis le port si les erreurs reviennent.
3. Corriger le duplex si les deux côtés ne correspondent pas.

**Escalader** : au fournisseur si les erreurs persistent avec un câble et un port neufs.

## 4. Lien dégradé

**Ce que ça veut dire** : le lien répond mais perd des paquets (> 10 % ou > 50 %) ou la latence
dépasse 100 ms.
**Impact attendu** : VoIP robotique, VPN instables, pages qui se rechargent.

**Vérifier**

```
Routeur1# ping 8.8.8.8 repeat 100
Routeur1# traceroute 8.8.8.8
```

- La perte commence-t-elle au premier saut (réseau interne), au routeur, ou chez le fournisseur ?
- Comparer avec Routeur2 : si son lien est sain, basculer volontairement sur lui.

**Agir**

1. Problème interne : voir les fiches 3 et 7.
2. Problème chez le fournisseur : basculer le trafic sur le lien de secours en baissant la
   priorité HSRP de Routeur1 (`standby 1 priority 90`, `standby 2 priority 90`), puis la
   remettre à 110 une fois le problème réglé.

**Escalader** : au fournisseur, avec les résultats du ping et du traceroute.

## 5. Redémarrage du routeur

**Ce que ça veut dire** : l'uptime est inférieur à 1 heure (Warning) ou à 5 minutes (High).
**Impact attendu** : une coupure brève pendant le redémarrage si c'était le routeur actif.

**Vérifier**

```
Routeur1# show version | include uptime|returned
Routeur1# show logging
```

- *returned to ROM by reload* : redémarrage manuel. Était-il planifié ?
- *power-on* : coupure de courant. Vérifier l'onduleur et l'alimentation.
- *crash* ou message d'erreur : sauvegarder le journal et le fichier de crash.

**Agir**

1. Confirmer que la configuration est complète : `show running-config` comparé à la configuration de référence.
2. Vérifier que HSRP est revenu à l'état normal (`show standby brief`).

**Escalader** : au fabricant si le routeur redémarre plusieurs fois ou après un crash.

## 6. Connexions TCP anormales

**Ce que ça veut dire** : le routeur a plus de 100 (Warning) ou 200 (High) connexions TCP
établies. Ce sont des connexions **vers le routeur lui-même** : sessions de gestion ou attaque.
**Impact attendu** : CPU élevé, gestion du routeur lente, risque de déni de service.

**Vérifier**

```
Routeur1# show tcp brief all
Routeur1# show users
Routeur1# show processes cpu sorted
```

- Repérer les adresses sources : postes internes connus, ou adresses inconnues ?

**Agir**

1. Sessions de gestion oubliées : `clear line` pour les fermer.
2. Sources inconnues : bloquer avec une liste d'accès et limiter la gestion aux adresses
   d'administration (`access-class` sur les lignes VTY).
3. Conserver les preuves (sorties des commandes, heure) dans le ticket.

**Escalader** : à l'équipe sécurité dès qu'une source inconnue est en cause.

## 7. Routeur surchargé

**Ce que ça veut dire** : CPU au-dessus de 60 % / 90 %, ou mémoire au-dessus de 70 % / 90 %.
**Impact attendu** : latence, routage et NAT ralentis, risque de plantage.

**Vérifier**

```
Routeur1# show processes cpu sorted
Routeur1# show processes cpu history
Routeur1# show memory statistics
```

**Agir**

1. Identifier le processus en cause (NAT, SNMP trop fréquent, attaque : voir la fiche 6).
2. Si c'est la charge normale : planifier un équipement plus puissant.

**Escalader** : au fabricant si un processus fuit la mémoire.

## 8. Disque d'un serveur presque plein

**Ce que ça veut dire** : moins de 20 % (Warning) ou de 10 % (High) libre sur `/`.
**Impact attendu** : base de données Zabbix ou GLPI arrêtée, journaux perdus.

**Vérifier**

```
df -h /
sudo du -xh / --max-depth=2 2>/dev/null | sort -h | tail -15
sudo journalctl --disk-usage
```

**Agir**

1. Réduire les journaux système : `sudo journalctl --vacuum-time=14d`.
2. Supprimer les paquets en cache : `sudo apt-get clean`.
3. Sur Zabbix : vérifier la durée de conservation de l'historique (31 jours) et des tendances (365 jours).
4. Si l'espace manque encore : agrandir le disque virtuel.

**Escalader** : à l'équipe système si la croissance continue malgré le nettoyage.

---

## Clôture d'un incident

1. Confirmer que l'alerte Zabbix est revenue à l'état *Resolved*.
2. Dans le ticket GLPI : cause, actions faites, durée de l'impact.
3. Si la cause peut revenir : créer une tâche de prévention (changement de câble, QoS, capacité).
