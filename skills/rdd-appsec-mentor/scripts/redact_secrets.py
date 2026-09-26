#!/usr/bin/env python3
"""Redact common secrets from text evidence.

Conservative helper for reports/log snippets. It does not guarantee complete
secret detection; rotate any credential that may have been exposed.

Covered: Supabase secret keys, JWTs, `*_KEY=`/`PASSWORD=` style assignments,
`Authorization: Bearer`, database URLs (`postgres://user:senha@host`), OpenAI
(`sk-`, `sk-proj-`), Stripe (`sk_live_`, `sk_test_`, `whsec_`), Resend (`re_`),
and long hex tokens on lines that carry a key-like label. Public identifiers such
as `sb_publishable_…` and placeholders in angle brackets (`<ANON_KEY>`) are left untouched.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    # Whole-value assignments of connection strings (before the URL rule, which keeps the host).
    (re.compile(r"(?im)\b(SUPABASE_DB_URL|DATABASE_URL|DB_URL|POSTGRES_URL)\b\s*=\s*\S+"),
     lambda m: f"{m.group(1)}=<REDACTED>"),
    # Database URL: only the password is redacted, host/db stay readable for the report.
    (re.compile(r"(?i)\b(postgres(?:ql)?://[^:/\s@]+:)([^@\s]+)(@)"),
     lambda m: f"{m.group(1)}<REDACTED>{m.group(3)}"),
    (re.compile(r"\bsb_secret_[A-Za-z0-9._-]{12,}\b"), "<SUPABASE_SECRET_REDACTED>"),
    (re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b"), "<OPENAI_KEY_REDACTED>"),
    (re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{8,}\b"), "<STRIPE_KEY_REDACTED>"),
    (re.compile(r"\bwhsec_[A-Za-z0-9]{8,}\b"), "<STRIPE_WEBHOOK_SECRET_REDACTED>"),
    (re.compile(r"\bre_[A-Za-z0-9]{6,}_[A-Za-z0-9]{8,}\b"), "<RESEND_KEY_REDACTED>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "<JWT_REDACTED>"),
    (re.compile(r"(?im)\b([A-Z0-9_]*(?:SERVICE_ROLE|SECRET_KEY|API_KEY|PASSWORD|PASSWD)[A-Z0-9_]*)\b\s*=\s*([^\s#<][^\s#]{7,})"),
     lambda m: f"{m.group(1)}=<REDACTED>"),
    (re.compile(r"(?i)\b(service[_-]?role|secret[_-]?key|api[_-]?key|password|passwd)\b\s*[:=]\s*([\"']?)[^\s,\"'<][^\s,\"']{7,}\2"),
     lambda m: f"{m.group(1)}=<REDACTED>"),
    (re.compile(r"(?i)\bAuthorization:\s*Bearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Authorization: Bearer <REDACTED>"),
]

# Long hex tokens are only redacted on lines that look like they carry a credential —
# a bare commit SHA or a SHA256 checksum in evidence stays readable.
KEY_LABEL = re.compile(r"(?i)(?:^|[^a-z])(token|secret|key|api|password|passwd|senha|credential)(?:[^a-z]|$)")  # `_` conta como fronteira: ACCESS_TOKEN=, api_key:
HEX_TOKEN = re.compile(r"\b[0-9a-fA-F]{32,}\b")


def _redact_hex_on_key_lines(text: str) -> str:
    out = []
    for line in text.splitlines(keepends=True):
        if KEY_LABEL.search(line):
            line = HEX_TOKEN.sub("<HEX_TOKEN_REDACTED>", line)
        out.append(line)
    return "".join(out)


def redact(text: str) -> str:
    out = text
    for pattern, replacement in PATTERNS:
        out = pattern.sub(replacement, out)
    return _redact_hex_on_key_lines(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, help="arquivo; se omitido, usa stdin")
    args = parser.parse_args()
    try:
        text = args.input.read_text(encoding="utf-8", errors="replace") if args.input else sys.stdin.read()
    except OSError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(redact(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
