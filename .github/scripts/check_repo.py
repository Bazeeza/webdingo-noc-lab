#!/usr/bin/env python3
"""Repository checks run by CI (and locally: python3 -I .github/scripts/check_repo.py).

1. Every Python script compiles.
2. No secret is committed: API tokens, Cisco passwords and SNMP communities
   must stay <PLACEHOLDERS>, secrets in .env.example must stay empty.
3. Every relative Markdown link points to a file that exists.
"""
import pathlib
import py_compile
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".venv", "__pycache__"}
TEXT_EXT = {".py", ".md", ".cfg", ".txt", ".yml", ".yaml", ".example", ""}

# (description, regex). A match is a finding unless the value is a <PLACEHOLDER>.
SECRET_RULES = [
    ("Cisco password or secret", re.compile(r"^\s*(?:enable\s+)?(?:password|secret)\s+(?!<)(\S+)", re.M)),
    ("Cisco username with password", re.compile(r"^\s*username\s+\S+\s+(?:password|secret)\s+(?:\d\s+)?(?!<)(\S+)", re.M)),
    ("SNMP community", re.compile(r"snmp-server\s+(?:community|host\s+\S+\s+version\s+2c)\s+(?!<)(\S+)")),
    ("Zimbra LDAP bind password", re.compile(r"BindPassword\s+\"(?!<)([^\"]+)\"")),
    ("hard-coded token or password in code", re.compile(r"(?i)(?:token|password|passwd|secret)\w*\s*=\s*[\"']([^\"'<\s]{8,})[\"']")),
    ("long random token", re.compile(r"(?<![A-Za-z0-9/@])([A-Za-z0-9]{40})(?![A-Za-z0-9])")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----()")),
]
ENV_SECRETS = ("GLPI_APP_TOKEN", "GLPI_USER_TOKEN", "AD_PASSWORD")


def files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not SKIP_DIRS & set(p.relative_to(ROOT).parts):
            yield p


def main():
    problems = []

    for p in files():
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix == ".py":
            try:
                py_compile.compile(str(p), doraise=True, cfile=None)
            except py_compile.PyCompileError as e:
                problems.append(f"{rel}: does not compile: {e.msg}")
        if p.suffix not in TEXT_EXT or rel.startswith(".github/scripts/"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for name, rule in SECRET_RULES:
            for m in rule.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{rel}:{line}: possible {name}")
        if p.name == ".env.example":
            for key in ENV_SECRETS:
                m = re.search(rf"^{key}=(.*)$", text, re.M)
                if m and m.group(1).strip():
                    problems.append(f"{rel}: {key} must stay empty in the example file")
        if p.suffix == ".md":
            for target in re.findall(r"\]\(([^)#\s]+)", text):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (p.parent / target).exists():
                    problems.append(f"{rel}: broken link -> {target}")

    for line in problems:
        print("::error::" + line)
    print(f"{len(problems)} problem(s) found")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
