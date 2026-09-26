"""Tests for scripts/redact_secrets.py.

Every secret-looking fixture is built at runtime by concatenation: the repository's
publish-check scans tests/ too, and a literal key-shaped string would block the release.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "skills" / "rdd-appsec-mentor" / "scripts"))
import redact_secrets as rs  # noqa: E402


class Providers(unittest.TestCase):
    def test_openai_key(self):
        chave = "sk-" + "a" * 24
        self.assertEqual(rs.redact(f"OPENAI={chave}"), "OPENAI=<OPENAI_KEY_REDACTED>")

    def test_openai_project_key(self):
        chave = "sk-proj-" + "b" * 30
        self.assertEqual(rs.redact(chave), "<OPENAI_KEY_REDACTED>")

    def test_stripe_live_test_e_webhook(self):
        live = "sk_" + "live_" + "c" * 20
        test = "sk_" + "test_" + "d" * 20
        wh = "whsec_" + "e" * 24
        out = rs.redact(f"{live} {test} {wh}")
        self.assertEqual(out, "<STRIPE_KEY_REDACTED> <STRIPE_KEY_REDACTED> <STRIPE_WEBHOOK_SECRET_REDACTED>")

    def test_resend_key(self):
        chave = "re_" + "AbCdEf12" + "_" + "g" * 20
        self.assertEqual(rs.redact(f"RESEND={chave}"), "RESEND=<RESEND_KEY_REDACTED>")

    def test_supabase_secret(self):
        chave = "sb_" + "secret_" + "h" * 20
        self.assertEqual(rs.redact(chave), "<SUPABASE_SECRET_REDACTED>")

    def test_jwt(self):
        jwt = "eyJ" + "i" * 20 + "." + "j" * 20 + "." + "k" * 20
        self.assertEqual(rs.redact(f"token {jwt}"), "token <JWT_REDACTED>")


class DatabaseUrls(unittest.TestCase):
    def test_postgres_url_redige_so_a_senha(self):
        url = "postgres://app:" + "s3nh4" * 3 + "@db.example.internal:5432/app"
        self.assertEqual(rs.redact(url), "postgres://app:<REDACTED>@db.example.internal:5432/app")

    def test_postgresql_scheme(self):
        url = "postgresql://app:" + "x" * 12 + "@host/db"
        self.assertEqual(rs.redact(url), "postgresql://app:<REDACTED>@host/db")

    def test_supabase_db_url_inteira(self):
        linha = "SUPABASE_DB_URL=postgres://postgres:" + "y" * 12 + "@db.host:5432/postgres"
        self.assertEqual(rs.redact(linha), "SUPABASE_DB_URL=<REDACTED>")


class HexTokens(unittest.TestCase):
    def test_hex_fronteira_exata(self):
        self.assertNotIn("REDACTED", rs.redact("token=" + "a" * 31))   # 31: fica
        self.assertIn("<HEX_TOKEN_REDACTED>", rs.redact("token=" + "a" * 32))   # 32: redige

    def test_hex_com_rotulo_composto_por_underscore(self):
        # ACCESS_TOKEN= — o `_` não é fronteira `\b`, mas tem de contar como rótulo de chave (review pós-build R3)
        self.assertEqual(rs.redact("ACCESS_TOKEN=" + "c" * 64), "ACCESS_TOKEN=<HEX_TOKEN_REDACTED>")
        self.assertEqual(rs.redact("x_api_secret: " + "d" * 40), "x_api_secret: <HEX_TOKEN_REDACTED>")

    def test_hex_sem_rotulo_de_chave_fica(self):
        sha = "0123456789abcdef" * 4   # SHA256 em evidência: linha sem rótulo de chave
        self.assertEqual(rs.redact(f"{sha}  rdd-appsec-mentor.zip"), f"{sha}  rdd-appsec-mentor.zip")

    def test_commit_sha_em_linha_neutra_fica(self):
        sha = "f" * 40
        self.assertEqual(rs.redact(f"commit {sha}"), f"commit {sha}")


class Untouched(unittest.TestCase):
    def test_publishable_nao_redige(self):
        s = "sb_" + "publishable_" + "x" * 20
        self.assertEqual(rs.redact(s), s)

    def test_texto_comum_intacto(self):
        s = "REVOKE EXECUTE ON FUNCTION public.minha_fn(uuid) FROM anon; -- esperado: false"
        self.assertEqual(rs.redact(s), s)

    def test_apikey_placeholder_intacto(self):
        s = '-H "apikey: <ANON_KEY>"'
        self.assertEqual(rs.redact(s), s)


class Legacy(unittest.TestCase):
    def test_assignment_service_role(self):
        self.assertEqual(rs.redact("SUPABASE_SERVICE_ROLE_KEY=" + "z" * 20), "SUPABASE_SERVICE_ROLE_KEY=<REDACTED>")

    def test_bearer(self):
        self.assertEqual(rs.redact("Authorization: Bearer " + "w" * 20), "Authorization: Bearer <REDACTED>")


if __name__ == "__main__":
    unittest.main()
