#!/usr/bin/env python3
"""Redact common secrets from text evidence.

Conservative helper for reports/log snippets. It does not guarantee complete
secret detection; rotate any credential that may have been exposed.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    (re.compile(r"\bsb_secret_[A-Za-z0-9._-]{12,}\b"), "<SUPABASE_SECRET_REDACTED>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "<JWT_REDACTED>"),
    (re.compile(r"(?im)\b([A-Z0-9_]*(?:SERVICE_ROLE|SECRET_KEY|API_KEY|PASSWORD|PASSWD)[A-Z0-9_]*)\b\s*=\s*([^\s#]{8,})"),
     lambda m: f"{m.group(1)}=<REDACTED>"),
    (re.compile(r"(?i)\b(service[_-]?role|secret[_-]?key|api[_-]?key|password|passwd)\b\s*[:=]\s*([\"']?)[^\s,\"']{8,}\2"),
     lambda m: f"{m.group(1)}=<REDACTED>"),
    (re.compile(r"(?i)\bAuthorization:\s*Bearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Authorization: Bearer <REDACTED>"),
]

def redact(text: str) -> str:
    out = text
    for pattern, replacement in PATTERNS:
        out = pattern.sub(replacement, out)
    return out

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
