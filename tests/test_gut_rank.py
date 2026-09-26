"""Tests for scripts/gut_rank.py — golden outputs, boundaries and error paths."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "skills" / "rdd-appsec-mentor" / "scripts"))
import gut_rank as gr  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_JSON = REPO / "skills" / "rdd-appsec-mentor" / "assets" / "findings-template.json"


def finding(fid, g, u, t, **extra):
    base = {"id": fid, "title": f"Achado {fid}", "gravity": g, "urgency": u, "trend": t}
    base.update(extra)
    return base


class PriorityBoundaries(unittest.TestCase):
    def test_faixas_na_fronteira_exata(self):
        self.assertEqual(gr.priority(80), "P0")
        self.assertEqual(gr.priority(79), "P1")
        self.assertEqual(gr.priority(45), "P1")
        self.assertEqual(gr.priority(44), "P2")
        self.assertEqual(gr.priority(20), "P2")
        self.assertEqual(gr.priority(19), "P3")


class Ranking(unittest.TestCase):
    def test_ordena_por_score_depois_g_u_t_depois_id(self):
        items = gr.rank_findings([
            finding("F-003", 2, 2, 2),   # 8
            finding("F-001", 5, 5, 4),   # 100
            finding("F-002", 4, 5, 5),   # 100 — G menor que F-001, fica depois
        ])
        self.assertEqual([x["id"] for x in items], ["F-001", "F-002", "F-003"])
        self.assertEqual([x["priority"] for x in items], ["P0", "P0", "P3"])

    def test_campos_extras_sao_preservados(self):
        items = gr.rank_findings([finding("F-001", 3, 3, 3, callers_confirmed=["edge-x (service_role)"], retest="curl …")])
        self.assertEqual(items[0]["callers_confirmed"], ["edge-x (service_role)"])
        self.assertEqual(items[0]["retest"], "curl …")

    def test_markdown_tem_coluna_status(self):
        items = gr.rank_findings([finding("F-001", 5, 5, 4, confidence="Confirmado", status="verificado")])
        md = gr.as_markdown(items)
        self.assertEqual(
            md.splitlines()[0],
            "| ID | Achado | Confiança | G | U | T | GUT | Prioridade | Status |",
        )
        self.assertEqual(
            md.splitlines()[2],
            "| F-001 | Achado F-001 | Confirmado | 5 | 5 | 4 | 100 | P0 | verificado |",
        )

    def test_csv_tem_coluna_status(self):
        items = gr.rank_findings([finding("F-001", 1, 1, 1, status="aberto")])
        lines = gr.as_csv(items).splitlines()
        self.assertEqual(lines[0], "id,title,confidence,gravity,urgency,trend,gut_score,priority,status")
        self.assertEqual(lines[1], "F-001,Achado F-001,,1,1,1,1,P3,aberto")

    def test_status_ausente_vira_vazio(self):
        items = gr.rank_findings([finding("F-001", 1, 1, 1)])
        self.assertEqual(items[0]["status"], "")

    def test_template_do_repo_e_valido(self):
        items = gr.load_findings(TEMPLATE_JSON)
        self.assertEqual(items[0]["id"], "F-001")
        self.assertEqual(items[0]["status"], "aberto")
        for campo in ("component", "repro_path", "callers_confirmed", "fix_sql_or_steps", "retest", "status"):
            self.assertIn(campo, items[0])


class Errors(unittest.TestCase):
    def test_score_fora_da_faixa(self):
        with self.assertRaisesRegex(ValueError, "F-001: gravity fora da faixa 1..5"):
            gr.rank_findings([finding("F-001", 6, 1, 1)])

    def test_score_booleano_e_rejeitado(self):
        with self.assertRaisesRegex(ValueError, "urgency deve ser inteiro"):
            gr.rank_findings([finding("F-001", 1, True, 1)])

    def test_id_duplicado(self):
        with self.assertRaisesRegex(ValueError, "id duplicado: F-001"):
            gr.rank_findings([finding("F-001", 1, 1, 1), finding("F-001", 2, 2, 2)])

    def test_status_invalido(self):
        with self.assertRaisesRegex(ValueError, "F-001: status deve ser um de aberto, corrigido, verificado, aceito"):
            gr.rank_findings([finding("F-001", 1, 1, 1, status="fechado")])

    def test_lista_vazia(self):
        with self.assertRaises(ValueError):
            gr.rank_findings([])

    def test_main_devolve_2_em_json_invalido(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write('{"nao": "lista"}')
        old = sys.argv
        sys.argv = ["gut_rank.py", fh.name]
        try:
            self.assertEqual(gr.main(), 2)
        finally:
            sys.argv = old
            pathlib.Path(fh.name).unlink()


if __name__ == "__main__":
    unittest.main()
