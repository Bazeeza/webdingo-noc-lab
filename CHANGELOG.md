# Journal des modifications

## 1.0.0 (2026-11-22)

Première publication du projet intégrateur.

- Réseau Cisco redondant : deux routeurs HSRP avec suivi du lien Internet, VLAN, NAT, SNMP restreint.
- Services : Active Directory, DNS, DHCP, messagerie Zimbra, GLPI.
- Supervision : Zabbix en haute disponibilité, métriques et seuils justifiés, tableaux de bord Grafana.
- Automatisation : tickets GLPI créés par Zabbix, synchronisation AD vers GLPI.
- Runbooks d'incident et plan de tests de bascule HSRP.
- CI : compilation Python, détection de secrets, liens Markdown.

Différences avec le rendu d'origine : secrets retirés, relais DHCP et passerelle HSRP corrigés,
adresses harmonisées avec les captures, scripts restructurés.
