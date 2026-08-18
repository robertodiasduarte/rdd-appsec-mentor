#!/usr/bin/env python3
"""Rank AppSec findings using the GUT matrix (G x U x T).

Input: JSON array of findings with gravity, urgency and trend in [1, 5].
Output: markdown, JSON or CSV sorted by score, then G, U and T.
No network access and no third-party dependencies.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any


def priority(score: int) -> str:
    if score >= 80:
        return "P0"
    if score >= 45:
        return "P1"
    if score >= 20:
        return "P2"
    return "P3"


def validate_score(name: str, value: Any, finding_id: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{finding_id}: {name} deve ser inteiro de 1 a 5")
    if not 1 <= value <= 5:
        raise ValueError(f"{finding_id}: {name} fora da faixa 1..5")
    return value


def load_findings(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("o JSON deve ser uma lista não vazia de achados")

    ranked = []
    seen = set()
    for idx, item in enumerate(data, 1):
        if not isinstance(item, dict):
            raise ValueError(f"item {idx}: esperado objeto JSON")
        fid = str(item.get("id") or f"F-{idx:03d}")
        if fid in seen:
            raise ValueError(f"id duplicado: {fid}")
        seen.add(fid)
        title = str(item.get("title") or "").strip()
        if not title:
            raise ValueError(f"{fid}: title é obrigatório")

        g = validate_score("gravity", item.get("gravity"), fid)
        u = validate_score("urgency", item.get("urgency"), fid)
        t = validate_score("trend", item.get("trend"), fid)
        score = g * u * t

        out = dict(item)
        out.update({"id": fid, "gravity": g, "urgency": u, "trend": t,
                    "gut_score": score, "priority": priority(score)})
        ranked.append(out)

    ranked.sort(
        key=lambda x: (
            -x["gut_score"],
            -x["gravity"],
            -x["urgency"],
            -x["trend"],
            x["id"],
        )
    )
    return ranked


def as_markdown(items: list[dict[str, Any]]) -> str:
    lines = [
        "| ID | Achado | Confiança | G | U | T | GUT | Prioridade |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for x in items:
        title = str(x["title"]).replace("|", r"\|").replace("\n", " ")
        confidence = str(x.get("confidence", "")).replace("|", r"\|").replace("\n", " ")
        lines.append(
            f"| {x['id']} | {title} | {confidence} | {x['gravity']} | "
            f"{x['urgency']} | {x['trend']} | {x['gut_score']} | {x['priority']} |"
        )
    return "\n".join(lines)


def as_csv(items: list[dict[str, Any]]) -> str:
    fields = ["id", "title", "confidence", "gravity", "urgency", "trend", "gut_score", "priority"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(items)
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSON com achados")
    parser.add_argument("--format", choices=["markdown", "json", "csv"], default="markdown")
    args = parser.parse_args()

    try:
        items = load_findings(args.input)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    if args.format == "markdown":
        print(as_markdown(items))
    elif args.format == "csv":
        print(as_csv(items), end="")
    else:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
