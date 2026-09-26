# Changelog

Todas as mudanças relevantes desta skill ficam registradas aqui. O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); as versões seguem o [SemVer](https://semver.org/lang/pt-BR/).

## [1.3.0] — 2026-09-26

Da detecção à correção provada. Motivada pelo uso real da skill num portal em produção (5 achados, 2 P0): o método acertou, mas a skill ficava muda na hora do `REVOKE`.

### Adicionado

- `references/remediacao-supabase.md`: para cada classe de achado — função `SECURITY DEFINER`, view sem `security_invoker`, policy permissiva/inerte, bucket público, segredo exposto, Edge Function/`verify_jwt` — o contrato **detectar → mapa de chamadores → corrigir → provar → tripwire e rollback**, com SQL/curl executável e a saída esperada ao lado.
- Prova mínima sem PII (`HEAD` com `Prefer: count=exact`) e smoke pelo vetor real, antes e depois da correção.
- `SKILL.md`: a etapa 10 vira **Correção e verificação** (10.1 mapa de chamadores · 10.2 corrigir · 10.3 provar · 10.4 tripwire); a etapa 4 começa pelo Security Advisor; o gate de abertura aceita "project ref + repositório local" quando não há URL pública.
- `references/supabase-lovable-cloudflare.md`: tabela lint do Advisor → classe de achado; fontes novas (linter, `functions/auth`, `GRANT` do Postgres).
- `assets/findings-template.json`: campos `component`, `repro_path`, `callers_confirmed`, `fix_sql_or_steps`, `retest` e `status` (`aberto` → `corrigido` → `verificado` → `aceito`).
- `assets/diagnostic-report-template.md`: coluna **Reteste** na matriz GUT, "Chamadores confirmados" e "Prova pós-correção" por achado; verificação pós-correção em tabela por achado.
- Testes dos três scripts (`tests/`, `unittest` da biblioteca padrão), executados no CI e na Release.

### Alterado

- `references/rdd-security-playbook.md`: a query de RLS passa a cobrir tabelas particionadas (`relkind IN ('r','p')`); Storage ganha query e `curl`; o Teste E cobre `/.env*`, `/.git/HEAD`, `config.toml` e source maps; placeholders unificados (`SEUPROJETO`, `<ANON_KEY>`).
- `scripts/gut_rank.py`: coluna `status` na saída Markdown/CSV.
- `scripts/report_lint.py`: cruza cada `F-nnn` da matriz com a sua seção; exige "Prova" em achado `Confirmado` e "Chamadores confirmados" em correção com `REVOKE`/`public = false`.
- `scripts/redact_secrets.py`: redige senha de `postgres://`, chaves `sk-`/`sk-proj-`, `sk_live_`/`sk_test_`/`whsec_`, `re_`, `SUPABASE_DB_URL` e tokens hex longos em linha de chave; nunca redige `sb_publishable_` (é pública).
- README: 10 etapas (eram 9 no texto), tabela de conteúdo atualizada.

## [1.2.0] — 2026-09-20

### Alterado

- CI e Release fixam as GitHub Actions por SHA.
- A Release publica `SHA256SUMS.txt` ao lado do `.zip`.

## [1.1.0] — 2026-08-20

### Alterado

- README: instalação por motor (Claude.ai, ChatGPT, Claude Code, Codex, Cursor e outros) com a pasta real em que cada instalador grava.

## [1.0.0] — 2026-08-18

### Adicionado

- Primeira publicação: `SKILL.md` com o método (gate de autorização, diagnóstico em etapas, matriz GUT, níveis de confiança), quatro referências, três scripts (`gut_rank.py`, `redact_secrets.py`, `report_lint.py`) e os templates de relatório e de achados.

[1.3.0]: https://github.com/robertodiasduarte/rdd-appsec-mentor/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/robertodiasduarte/rdd-appsec-mentor/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/robertodiasduarte/rdd-appsec-mentor/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/robertodiasduarte/rdd-appsec-mentor/releases/tag/v1.0.0
