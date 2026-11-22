# Tests de bascule HSRP

Une redondance qui n'a jamais été testée n'est pas une redondance. Cette page décrit comment
prouver que le réseau survit à la perte du lien Internet principal, puis à la perte complète
du routeur principal, et ce qu'on doit observer à chaque étape.

## Préparation

- Un poste dans le VLAN 2 (USERS) et un serveur dans le VLAN 1.
- Une session console sur chaque routeur.
- Un ping continu depuis le poste vers Internet, pour mesurer la coupure :
  ```
  ping -t 8.8.8.8
  ```
- Zabbix ouvert sur *Monitoring > Problems*.

## Test 1 : état normal

Sur Routeur1 :

```
Routeur1# show standby brief
                     P indicates configured to preempt.
                     |
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Gi0/0.1     1    110 P Active  local           192.168.5.2     192.168.5.254
Gi0/0.2     2    110 P Active  local           192.168.6.2     192.168.6.254
```

**Attendu** : Routeur1 est *Active* (priorité 110) sur les deux groupes, Routeur2 est *Standby*.
Sur le poste, `tracert 8.8.8.8` passe par la passerelle `192.168.6.254`.

## Test 2 : perte du lien Internet principal

Simuler la panne du fournisseur principal sur Routeur1 :

```
Routeur1(config)# interface GigabitEthernet0/1
Routeur1(config-if)# shutdown
```

**Attendu** :

- `show track 1` : l'état passe à *Down* ;
- la priorité de Routeur1 tombe à 90 (110 - 20), sous celle de Routeur2 (100) ;
- Routeur2 devient *Active* (préemption) ; `show standby brief` sur Routeur2 le confirme ;
- le ping continu perd au plus quelques paquets, puis repart par le lien de secours ;
- Zabbix lève l'alerte de statut de l'interface Gi0/1 de Routeur1.

> Les connexions déjà ouvertes (téléchargement, session SSH) sont coupées : le NAT de Routeur2
> utilise une autre adresse publique. Les nouvelles connexions fonctionnent tout de suite.

## Test 3 : retour du lien principal

```
Routeur1(config-if)# no shutdown
```

**Attendu** : le suivi repasse à *Up*, Routeur1 retrouve la priorité 110 et reprend le rôle
*Active* tout seul grâce à `preempt`. L'alerte Zabbix se ferme automatiquement.

## Test 4 : panne complète du routeur principal

Débrancher l'alimentation de Routeur1.

**Attendu** :

- Routeur2 ne reçoit plus les messages *hello* de Routeur1 et devient *Active* après le délai
  *hold* (10 secondes par défaut) ;
- le ping continu perd quelques secondes de paquets, puis repart ;
- Zabbix signale Routeur1 injoignable (SNMP et ping).

Au rallumage de Routeur1 : il reprend le rôle *Active* (préemption), et l'alerte
« redémarrage récent du routeur » (uptime inférieur à 1 heure) apparaît dans Zabbix.

## Grille de résultats

| Test | Attendu | Paquets perdus | Résultat |
|---|---|---|---|
| 1. État normal | Routeur1 *Active* | 0 | ☐ |
| 2. Lien principal coupé | Routeur2 *Active*, Internet maintenu | quelques-uns | ☐ |
| 3. Lien rétabli | Routeur1 reprend *Active* | 0 à 1 | ☐ |
| 4. Routeur1 éteint | Routeur2 *Active* après ~10 s | quelques secondes | ☐ |

## Pour réduire le temps de bascule

Les minuteurs HSRP par défaut (hello 3 s, hold 10 s) peuvent être réduits sur les deux routeurs :

```
standby 1 timers msec 250 msec 750
standby 2 timers msec 250 msec 750
```

La bascule après une panne complète passe alors sous la seconde, au prix d'un peu plus de
trafic de contrôle.
