#!/usr/bin/env python3
"""Structural lint for RDD AppSec diagnostic reports.

Checks the minimum sections, the GUT table, and — per finding — that every
F-nnn in the GUT matrix has its own `### F-nnn` section (and vice versa), that a
`Confirmado` finding carries a proof ("Prova" / "Antes"), and that a fix with
`REVOKE` or `public = false` carries "Chamadores confirmados". Each failure names
the offending finding.
"""
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

FINDING_ID = r"F-\d{3}"
SECTION_HEADING = re.compile(rf"^###\s+({FINDING_ID})\b", re.M)
TABLE_ROW = re.compile(rf"^\|\s*({FINDING_ID})\s*\|", re.M)
GUT_HEADING = re.compile(r"^##\s+.*Matriz GUT", re.M | re.I)
NEXT_H2 = re.compile(r"^##\s", re.M)
FINDING_BOUNDARY = re.compile(rf"^(###\s+{FINDING_ID}\b|##\s)", re.M)
REVOKE_OR_PUBLIC_FALSE = re.compile(r"\bREVOKE\b|\bpublic\s*=\s*false\b", re.I)
CONFIRMADO = re.compile(r"\*\*Confian[çc]a:\*\*\s*\[?\s*Confirmado\b", re.I)
PROVA = re.compile(r"\bProva\b|\*\*Antes:\*\*", re.I)
CHAMADORES = re.compile(r"Chamadores confirmados", re.I)


def gut_table_ids(text: str) -> list[str]:
    """IDs listed in the GUT matrix block (from the 'Matriz GUT' heading to the next H2)."""
    heading = GUT_HEADING.search(text)
    if not heading:
        return []
    block_start = heading.end()
    nxt = NEXT_H2.search(text, block_start)
    block = text[block_start:nxt.start() if nxt else len(text)]
    seen: list[str] = []
    for m in TABLE_ROW.finditer(block):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def finding_sections(text: str) -> dict[str, str]:
    """Map F-nnn -> body of its `### F-nnn` section (up to the next finding or H2)."""
    sections: dict[str, str] = {}
    for m in SECTION_HEADING.finditer(text):
        fid = m.group(1)
        nxt = FINDING_BOUNDARY.search(text, m.end())
        sections[fid] = text[m.end():nxt.start() if nxt else len(text)]
    return sections


def lint_text(text: str) -> list[str]:
    failures: list[str] = []
    lowered = text.lower()
    for heading in REQUIRED:
        if heading.lower() not in lowered:
            failures.append(f"seção ausente: {heading}")

    if not re.search(r"\|\s*ID\s*\|.*\bG\b.*\bU\b.*\bT\b.*GUT.*Prioridade", text, re.I):
        failures.append("tabela GUT não encontrada")

    if "Confiança" not in text and "confidence" not in lowered:
        failures.append("campo de confiança não encontrado")

    if not re.search(r"\bP[0-3]\b", text):
        failures.append("nenhuma prioridade P0..P3 encontrada")

    table_ids = gut_table_ids(text)
    sections = finding_sections(text)
    for fid in table_ids:
        if fid not in sections:
            failures.append(f"{fid}: na matriz GUT sem seção ### {fid}")
    for fid in sections:
        if fid not in table_ids:
            failures.append(f"{fid}: seção ### {fid} sem linha na matriz GUT")

    for fid, body in sections.items():
        if CONFIRMADO.search(body) and not PROVA.search(body):
            failures.append(f'{fid}: achado Confirmado sem "Prova"/"Antes"')
        if REVOKE_OR_PUBLIC_FALSE.search(body) and not CHAMADORES.search(body):
            failures.append(f'{fid}: correção com REVOKE/public = false sem "Chamadores confirmados"')

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    try:
        text = args.report.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"FAIL: {exc}")
        return 2

    failures = lint_text(text)
    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS: estrutura mínima do relatório encontrada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
