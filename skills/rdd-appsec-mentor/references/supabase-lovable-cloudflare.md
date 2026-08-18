# Referência técnica: Supabase, Lovable, Cloudflare e OWASP

Revisado em 2026-08-18. Quando houver internet disponível, preferir a documentação oficial atual.

## Supabase

### RLS e Data API

Fonte oficial:
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/docs/guides/api/securing-your-api

Pontos operacionais:

- Em schemas expostos, avaliar RLS **e** grants.
- Policies determinam linhas; grants determinam se o papel alcança o objeto.
- Uma policy não substitui uma revisão de privilégios.
- Testar comportamento real com conta/chave de baixo privilégio e dados sintéticos.

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

### Funções SQL

Fonte oficial:
- https://supabase.com/docs/guides/database/functions

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

### Storage

Fonte oficial:
- https://supabase.com/docs/guides/storage/security/access-control

Revisar policies de `storage.objects`, bucket público/privado e necessidade de URLs assinadas.

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
