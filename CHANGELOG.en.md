# Changelog

[![Français](https://img.shields.io/badge/Langue-Français-3fe0a0?style=for-the-badge)](CHANGELOG.md)
[![English](https://img.shields.io/badge/Language-English-2b9dff?style=for-the-badge)](CHANGELOG.en.md)

## 1.0.0 (2026-11-22)

First release of the capstone project.

- Redundant Cisco network: two HSRP routers with Internet link tracking, VLANs, NAT, restricted SNMP.
- Services: Active Directory, DNS, DHCP, Zimbra email, GLPI.
- Monitoring: high-availability Zabbix, justified metrics and thresholds, Grafana dashboards.
- Automation: GLPI tickets created by Zabbix, AD to GLPI synchronization.
- Incident runbooks and HSRP failover test plan.
- CI: Python compilation, secret detection, Markdown links.

Differences with the original submission: secrets removed, DHCP relay and HSRP gateway fixed,
addresses aligned with the screenshots, scripts restructured.
