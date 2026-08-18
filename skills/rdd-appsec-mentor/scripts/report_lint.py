#!/usr/bin/env python3
"""Minimal structural lint for RDD AppSec diagnostic reports."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED = [
    "Resumo executivo",
    "Escopo",
    "Matriz GUT",
    "Achados detalhados",
    "Plano de ação",
    "Verificação pós-correção",
    "Risco residual",
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    try:
        text = args.report.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"FAIL: {exc}")
        return 2

    failures = []
    for heading in REQUIRED:
        if heading.lower() not in text.lower():
            failures.append(f"seção ausente: {heading}")

    if not re.search(r"\|\s*ID\s*\|.*\bG\b.*\bU\b.*\bT\b.*GUT.*Prioridade", text, re.I):
        failures.append("tabela GUT não encontrada")

    if "Confiança" not in text and "confidence" not in text.lower():
        failures.append("campo de confiança não encontrado")

    if not re.search(r"\bP[0-3]\b", text):
        failures.append("nenhuma prioridade P0..P3 encontrada")

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS: estrutura mínima do relatório encontrada")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
