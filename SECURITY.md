# Sécurité

Ce dépôt documente un **laboratoire** : adresses privées, domaine fictif (`webdingo.ca`),
aucun service exposé sur Internet.

- Aucun secret n'est publié. Les configurations utilisent des valeurs `<À_REMPLACER>` et les
  scripts lisent leurs secrets dans des variables d'environnement (voir `.env.example`).
- À chaque push, la CI vérifie qu'aucun mot de passe, jeton, communauté SNMP ou clé privée
  n'a été commité.

## Signaler un problème

Si vous trouvez une information sensible ou une faille dans ce dépôt, merci de la signaler en
privé, pas dans une issue publique :

- [Signaler une vulnérabilité](https://github.com/Bazeeza/webdingo-noc-lab/security/advisories/new) (avis de sécurité privé GitHub)
- Courriel : info@bazeeza.ca
