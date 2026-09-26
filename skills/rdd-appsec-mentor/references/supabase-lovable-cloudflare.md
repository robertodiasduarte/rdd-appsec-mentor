# Referência técnica: Supabase, Lovable, Cloudflare e OWASP

Revisado em 2026-09-26. Quando houver internet disponível, preferir a documentação oficial atual.

## Supabase

### Security Advisor: por onde começar

Fonte oficial:
- https://supabase.com/docs/guides/database/database-linter

Com dezenas de tabelas e Edge Functions, a triagem começa pelo que a plataforma aponta de graça (Dashboard → Advisors → Security). Cada lint mapeia numa classe de achado desta skill:

| Lint do Advisor | Classe | Onde corrigir e provar |
|---|---|---|
| `security_definer_view` | View sem `security_invoker` — vazamento vivo, não cosmético | [remediacao-supabase.md §2](remediacao-supabase.md) |
| `rls_disabled_in_public` | Tabela exposta sem RLS | playbook 3.1 + [§3](remediacao-supabase.md) |
| `policy_exists_rls_disabled` | Policy escrita, RLS desligada (a policy não vale) | [§3](remediacao-supabase.md) |
| `rls_enabled_no_policy` | RLS ligada sem policy (nega tudo, inclusive o app) | [§3](remediacao-supabase.md) |
| `function_search_path_mutable` | Função sem `search_path` fixo — combinar com a revisão de `EXECUTE` | [§1](remediacao-supabase.md) |
| `auth_users_exposed` | View/tabela em `public` expõe `auth.users` | [§2](remediacao-supabase.md) / [§3](remediacao-supabase.md) |
| (sem lint) | Bucket público / listagem aberta / função `SECURITY DEFINER` chamável por `anon` | [§4](remediacao-supabase.md) / [§1](remediacao-supabase.md) |

O Advisor não vê Storage nem quem pode executar funções: as queries de [remediacao-supabase.md](remediacao-supabase.md) cobrem o que ele não cobre.

### RLS e Data API

Fonte oficial:
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/docs/guides/api/securing-your-api

Pontos operacionais:

- Em schemas expostos, avaliar RLS **e** grants.
- Policies determinam linhas; grants determinam se o papel alcança o objeto.
- Uma policy não substitui uma revisão de privilégios — e uma policy sem `GRANT` de tabela é inerte (o Postgres checa o privilégio antes do RLS).
- Policies são `PERMISSIVE` por default e somam por OR: uma `USING (true)` anula as demais.
- Testar comportamento real com conta/chave de baixo privilégio e dados sintéticos; sem staging, contar sem transferir (`HEAD` com `Prefer: count=exact`).

### Chaves

Fonte oficial:
- https://supabase.com/docs/guides/getting-started/api-keys
- https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys

Suportar os dois vocabulários durante a transição:

| Cliente | Backend privilegiado |
|---|---|
| `publishable` | `secret` |
| legado `anon` | legado `service_role` |

Nunca pedir ou armazenar a chave privilegiada no relatório.

Rotação: as chaves legadas (`anon`/`service_role`, formato JWT) são assinadas pelo JWT secret do projeto — rotacionar o secret invalida as duas juntas e desloga todos. As novas (`sb_publishable_`/`sb_secret_`) rotacionam uma a uma: criar → migrar consumidores → conferir uso da antiga → revogar. Ordem completa em [remediacao-supabase.md §5](remediacao-supabase.md).

### Funções SQL

Fonte oficial:
- https://supabase.com/docs/guides/database/functions
- https://www.postgresql.org/docs/current/sql-grant.html (o Postgres concede `EXECUTE` a `PUBLIC` por default; o Supabase acrescenta grants diretos a `anon` e `authenticated` via default privileges)

`SECURITY DEFINER` define sob que privilégio a função roda, não quem pode chamá-la. Revogar de `PUBLIC`, `anon` **e** `authenticated`; provar com `has_function_privilege`; recriar só com `CREATE OR REPLACE`. Bloco completo em [remediacao-supabase.md §1](remediacao-supabase.md).

Revisar:

- `security invoker` por padrão quando suficiente;
- necessidade real de `security definer`;
- `search_path`;
- privilégios `EXECUTE`;
- default privileges de novas funções;
- checagem de autorização no corpo quando aplicável.

### Edge Functions

Fonte oficial:
- https://supabase.com/docs/guides/functions/auth

Distinguir:

- autenticar o chamador;
- autorizar o chamador para o objeto/tenant;
- executar ação privilegiada.

Não presumir que usar uma Edge Function torna a operação segura por si só.

`verify_jwt = true` (o default) rejeita o `OPTIONS` do preflight CORS antes do código — edge chamada pelo navegador com autenticação manual usa `verify_jwt = false` no `config.toml` **e** `getUser()` no servidor. Inventário e smoke em [remediacao-supabase.md §6](remediacao-supabase.md).

### Storage

Fonte oficial:
- https://supabase.com/docs/guides/storage/security/access-control

Revisar policies de `storage.objects`, bucket público/privado e necessidade de URLs assinadas. A listagem (`/storage/v1/object/list/`) exige o header `Authorization` mesmo para o visitante; documento de cliente nunca fica em bucket público. Queries, curl e migração de `getPublicUrl` em [remediacao-supabase.md §4](remediacao-supabase.md).

## Lovable

Fontes oficiais:
- https://docs.lovable.dev/tips-tricks/security-best-practices
- https://docs.lovable.dev/features/security

Checklist:

- segredos fora do frontend;
- controles de autorização no backend/banco, não só na UI;
- revisar RLS de tabelas sensíveis;
- revisar Security view/scan antes de publicar;
- tratar correção automática como proposta que precisa de teste.

## Cloudflare

Fontes oficiais:
- https://developers.cloudflare.com/rules/transform/response-header-modification/
- https://developers.cloudflare.com/waf/rate-limiting-rules/
- https://developers.cloudflare.com/ssl/edge-certificates/additional-options/http-strict-transport-security/

Revisar:

- regra de **response header** versus request header;
- efeito de `Set` versus `Add`;
- compatibilidade de cabeçalhos com fluxos legítimos;
- rate limiting calibrado;
- HSTS somente com entendimento do impacto de `max-age`, subdomínios e preload.

## OWASP

Fonte oficial:
- https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/

Usar OWASP como taxonomia complementar. Para apps Supabase, BOLA/IDOR deve ser investigada tanto na rota/Edge Function quanto no acesso direto a dados e RPCs.

## Regra de atualização

Se a documentação atual divergir deste arquivo, seguir a documentação oficial atual e registrar no relatório que houve mudança de plataforma.
