# Security

[![Français](https://img.shields.io/badge/Langue-Français-3fe0a0?style=for-the-badge)](SECURITY.md)
[![English](https://img.shields.io/badge/Language-English-2b9dff?style=for-the-badge)](SECURITY.en.md)

This repository documents a **lab**: private addresses, fictional domain (`webdingo.ca`),
no service exposed to the Internet.

- No secret is published. The configurations use `<À_REMPLACER>` (to replace) values and the
  scripts read their secrets from environment variables (see `.env.example`).
- On every push, the CI checks that no password, token, SNMP community or private key
  has been committed.

## Reporting a problem

If you find sensitive information or a vulnerability in this repository, please report it
privately, not in a public issue:

- [Report a vulnerability](https://github.com/Bazeeza/webdingo-noc-lab/security/advisories/new) (private GitHub security advisory)
- Email: info@bazeeza.ca
