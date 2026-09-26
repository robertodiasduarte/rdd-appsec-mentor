"""Tests for scripts/report_lint.py — the template passes; each negative names its finding."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "skills" / "rdd-appsec-mentor" / "scripts"))
import report_lint as rl  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_MD = REPO / "skills" / "rdd-appsec-mentor" / "assets" / "diagnostic-report-template.md"

SKELETON = """# Relatório

## 1. Resumo executivo
texto

## 2. Escopo, evidências e limitações
texto

## 4. Matriz GUT

| ID | Achado | Confiança | G | U | T | GUT | Prioridade | Status | Reteste |
|---|---|---|---:|---:|---:|---:|---|---|---|
{gut_rows}

## 5. Achados detalhados

{sections}

## 6. Plano de ação ordenado
1. ação

## 7. Verificação pós-correção
| ID | Reteste |
|---|---|
{verif_rows}

## 8. Risco residual e pendências
texto
"""


def report(gut_rows, sections, verif_rows=""):
    return SKELETON.format(gut_rows=gut_rows, sections=sections, verif_rows=verif_rows)


def row(fid, conf="Provável"):
    return f"| {fid} | Título | {conf} | 5 | 5 | 4 | 100 | P0 | aberto | pendente |"


def section(fid, conf="Provável", body=""):
    return f"### {fid} — Título\n\n**Confiança:** {conf}\n\n{body}\n"


class TemplatePasses(unittest.TestCase):
    def test_template_do_repo_passa(self):
        self.assertEqual(rl.lint_text(TEMPLATE_MD.read_text(encoding="utf-8")), [])

    def test_relatorio_minimo_passa(self):
        text = report(row("F-001"), section("F-001", body="#### Como corrigir\n1. passo"))
        self.assertEqual(rl.lint_text(text), [])


class CrossCheck(unittest.TestCase):
    def test_fnnn_orfao(self):
        # F-002 na matriz sem seção; F-003 com seção sem linha na matriz
        text = report(
            row("F-001") + "\n" + row("F-002"),
            section("F-001") + section("F-003"),
        )
        failures = rl.lint_text(text)
        self.assertIn("F-002: na matriz GUT sem seção ### F-002", failures)
        self.assertIn("F-003: seção ### F-003 sem linha na matriz GUT", failures)
        self.assertFalse(any(f.startswith("F-001") for f in failures))

    def test_linhas_da_secao_7_nao_contam_como_matriz(self):
        # F-009 só aparece na tabela de verificação (seção 7), não na matriz GUT → não exige seção
        text = report(row("F-001"), section("F-001"), verif_rows="| F-009 | pendente |")
        self.assertEqual(rl.lint_text(text), [])


class Confirmado(unittest.TestCase):
    def test_confirmado_sem_prova(self):
        text = report(row("F-001", "Confirmado"), section("F-001", "Confirmado", body="**Evidência:** x"))
        self.assertIn('F-001: achado Confirmado sem "Prova"/"Antes"', rl.lint_text(text))

    def test_confirmado_com_antes_passa(self):
        text = report(row("F-001", "Confirmado"), section("F-001", "Confirmado", body="**Antes:** curl → 200"))
        self.assertEqual(rl.lint_text(text), [])

    def test_provavel_nao_exige_prova(self):
        text = report(row("F-001"), section("F-001", body="**Evidência:** x"))
        self.assertEqual(rl.lint_text(text), [])


class Chamadores(unittest.TestCase):
    def test_revoke_sem_chamadores_nomeia_so_o_ofensor(self):
        ok = section("F-001", body="#### Chamadores confirmados\n| x | y |\n\n#### Como corrigir\nREVOKE EXECUTE ON FUNCTION public.f(uuid) FROM anon;")
        bad = section("F-002", body="#### Como corrigir\nREVOKE EXECUTE ON FUNCTION public.g(uuid) FROM anon;")
        text = report(row("F-001") + "\n" + row("F-002"), ok + bad)
        failures = rl.lint_text(text)
        self.assertEqual(failures, ['F-002: correção com REVOKE/public = false sem "Chamadores confirmados"'])

    def test_public_false_sem_chamadores(self):
        bad = section("F-001", body="#### Como corrigir\nUPDATE storage.buckets SET public = false WHERE id = 'b';")
        self.assertIn(
            'F-001: correção com REVOKE/public = false sem "Chamadores confirmados"',
            rl.lint_text(report(row("F-001"), bad)),
        )


class Cli(unittest.TestCase):
    def _run(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(text)
        old = sys.argv
        sys.argv = ["report_lint.py", fh.name]
        try:
            return rl.main()
        finally:
            sys.argv = old
            pathlib.Path(fh.name).unlink()

    def test_main_exit_0_no_template(self):
        self.assertEqual(self._run(TEMPLATE_MD.read_text(encoding="utf-8")), 0)

    def test_main_exit_1_com_falha(self):
        self.assertEqual(self._run(report(row("F-001"), "")), 1)


if __name__ == "__main__":
    unittest.main()
