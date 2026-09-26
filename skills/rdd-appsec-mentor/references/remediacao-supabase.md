# Remediação e prova no Supabase — o que fazer depois do achado

Revisado em 2026-09-26. Este arquivo cobre o trecho em que a maioria das correções falha: **entre o achado e a prova de que ele fechou**. Cada classe de achado tem o mesmo contrato, nesta ordem:

1. **Detectar** — a query ou o `curl` que mostra o estado real (não o código, não a migration).
2. **Mapa de chamadores** — quem usa o objeto hoje, por role. Nada é revogado antes disto.
3. **Corrigir** — um bloco idempotente, uma mudança por vez, com alvo exato.
4. **Provar** — pelo **privilégio** (`has_function_privilege`, `has_table_privilege`) **e** pelo **vetor real** (HTTP), com a saída esperada escrita ao lado.
5. **Tripwire e rollback** — a query que deve voltar 0 linhas a cada deploy, e o bloco que desfaz a correção se um chamador legítimo quebrar.

Placeholders usados em todo o arquivo: `SEUPROJETO` (ref do projeto), `<ANON_KEY>` (chave `anon`/`publishable`, que já está no JavaScript do site), `<JWT_DO_USUARIO>` (token de uma conta sintética), `public.minha_fn(uuid)`, `public.minha_view`, `minha_tabela`, `meu-bucket`. Substitua todos antes de executar.

Todo bloco termina com `-- esperado:` ou `# esperado:`. Se o que você vê é diferente do esperado, o achado **não** está fechado — volte ao bloco anterior.

---

## §0 Como provar sem tocar dado real

### 0.1 Quantas linhas o visitante vê, sem transferir nenhuma

Sem staging, a skill antiga mandava parar na revisão estática — e o achado ficava `Provável` para sempre. O PostgREST responde à contagem **sem corpo**:

```bash
curl -sI "https://SEUPROJETO.supabase.co/rest/v1/minha_tabela?select=id" \
  -H "apikey: <ANON_KEY>" -H "Prefer: count=exact"
# esperado (tabela fechada):  content-range: */0   ou HTTP 401/403 com "permission denied"
# achado Confirmado:          content-range: 0-16/17  → o número depois da barra é quantas linhas o anon vê
# sem o header Prefer vem `0-16/*` — o `*` significa que você esqueceu o count=exact
```

Zero registros transferidos, zero PII no relatório. Se o cliente não faz `HEAD`, o `GET` com `Range: 0-0` transfere **um** registro (HTTP 206) — use só em tabela sintética.

### 0.2 A prova é o privilégio, não a chamada

Função com efeito colateral (apaga, mescla, envia) **nunca** é confirmada invocando. O que decide é o privilégio efetivo:

```sql
SELECT has_function_privilege('anon',          'public.minha_fn(uuid)', 'EXECUTE') AS anon_exec,
       has_function_privilege('authenticated', 'public.minha_fn(uuid)', 'EXECUTE') AS auth_exec;
-- esperado (função só do backend): false | false
-- esperado (função chamada pelo front logado): false | true
```

`has_function_privilege` resolve herança de `PUBLIC` e grants diretos — é o único sinal que não engana. O `success: true` de uma migration **não** é prova de nada.

### 0.3 Smoke pelo vetor real, ANTES e DEPOIS

`SET LOCAL ROLE anon` só vale dentro de `BEGIN … ROLLBACK` (solto no SQL editor, cada linha roda como `postgres` e o teste "passa" sem testar nada) e, mesmo certo, prova a ACL — não prova que o **endpoint** fechou. O vetor real é HTTP:

```bash
# ANTES da correção — guarde esta saída: ela some para sempre depois do fix
curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/rest/v1/rpc/minha_fn" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <ANON_KEY>" \
  -H "Content-Type: application/json" -d '{"p": "<uuid-sintetico>"}'
# esperado ANTES (achado): http=200 com resposta da função
# esperado DEPOIS:         {"code":"42501","message":"permission denied for function minha_fn",...}  http=403
# Só o status não prova nada: 403 também vem de WAF ou proxy. O que prova é o code 42501 no corpo.
```

Função com **efeito colateral**: não rode o ANTES — registre o privilégio (0.2) como baseline.

Duas armadilhas medidas:

- **Overload ambíguo não é testável por chamada.** Com duas assinaturas (`(uuid)` e `(uuid, text)`) o PostgREST devolve `300 PGRST203` **sem executar** — o status não diz nada sobre permissão. Prove por `oid::regprocedure` + `has_function_privilege`.
- **Feche olhando os logs do Postgres**: os únicos `42501` do período devem ser os do seu smoke. Qualquer outro é um usuário real que a correção quebrou.

### 0.4 Estados do achado

| Confiança / status | Significa | Próxima ação |
|---|---|---|
| `Hipótese` | Só leitura de código ou migration antiga | Query de estado real (Detectar) |
| `Provável` | Query confirma a configuração, sem vetor | Prova mínima sem PII (0.1) ou privilégio (0.2) |
| `Confirmado` · `aberto` | Vetor real devolve dado / 200 | Mapa de chamadores → Corrigir |
| `corrigido` | Bloco aplicado | Provar (privilégio **e** vetor) |
| `verificado` | `false/false` **e** `42501` registrados | Tripwire + relatório |
| `aceito` | Dono aceitou o risco, com motivo escrito | Seção "Risco residual" |

---

## §1 Função `SECURITY DEFINER` executável por quem não deveria

> `SECURITY DEFINER` define **sob que privilégio** a função roda, não **quem pode chamá-la**. Quem pode chamar é o `EXECUTE` — e, num projeto Supabase de fábrica, toda função nova em `public` nasce com `EXECUTE` concedido a `anon` e `authenticated` (default privileges do projeto). Uma função que apaga vinte tabelas e nasce assim é chamável por qualquer visitante via `/rest/v1/rpc/`.

### Detectar

```sql
SELECT p.oid::regprocedure AS funcao,
       has_function_privilege('anon',          p.oid, 'EXECUTE') AS anon_exec,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS auth_exec,
       array_to_string(p.proacl, ', ')                          AS acl
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.prosecdef
  AND (has_function_privilege('anon', p.oid, 'EXECUTE')
    OR has_function_privilege('authenticated', p.oid, 'EXECUTE'))
ORDER BY anon_exec DESC, 1;
-- esperado: 0 linhas com anon_exec = true — cada uma é ACHADO.
-- Linhas só com auth_exec = true são CANDIDATAS: viram achado se o front logado NÃO chama a função
-- ou se o corpo não checa auth.uid()/tenant antes de agir.
-- No acl, uma entrada `=X/postgres` (nada à esquerda do `=`) significa que PUBLIC tem EXECUTE.
```

O seu projeto ainda concede por default a quem cria função nova?

```sql
SELECT array_to_string(defaclacl, ', ') AS default_acl_funcoes
FROM pg_default_acl
WHERE defaclnamespace = 'public'::regnamespace AND defaclobjtype = 'f';
-- esperado: sem `anon=` nem `authenticated=`. Se aparecerem, toda função nova nasce aberta (ver Tripwire).
```

Confira **overloads** antes de escrever qualquer `REVOKE` — o alvo é sempre a assinatura completa, nunca só o nome:

```sql
SELECT p.oid::regprocedure FROM pg_proc p
WHERE p.pronamespace = 'public'::regnamespace AND p.proname = 'minha_fn';
-- esperado: a lista completa de assinaturas; o REVOKE abaixo vai para cada uma que for achado.
```

### Mapa de chamadores

Antes de revogar de `anon`, descubra se uma **policy** chama a função. Se uma policy aplicável a anon (`TO public` ou `TO anon`) invoca `minha_fn`, o `REVOKE` derruba o `SELECT` da tabela inteira com `42501` — e não é a função que quebra, é a tabela:

```sql
SELECT c.relname AS tabela, pol.polname AS policy,
       CASE WHEN pol.polroles = '{0}'::oid[] THEN 'PUBLIC (perigo)'
            ELSE array_to_string(ARRAY(SELECT rolname FROM pg_roles WHERE oid = ANY(pol.polroles)), ',') END AS roles,
       has_table_privilege('anon', c.oid, 'SELECT') AS anon_le_tabela
FROM pg_policy pol JOIN pg_class c ON c.oid = pol.polrelid
WHERE pg_get_expr(pol.polqual, pol.polrelid)      ILIKE '%minha_fn%'
   OR pg_get_expr(pol.polwithcheck, pol.polrelid) ILIKE '%minha_fn%';
-- esperado: 0 linhas, ou só policies `TO authenticated` (anon nunca as avalia).
-- Linha com PUBLIC/anon E anon_le_tabela = true → NÃO revogue de anon ainda; troque a policy antes.
```

Complete o mapa com as outras fontes (procedimento 10.1 do SKILL.md): grep no repositório pelo nome (front, Edge Functions, scripts), Edge Functions que usam `SUPABASE_SERVICE_ROLE_KEY` (não quebram com o REVOKE — são o caminho legítimo a preservar), `cron.job` e triggers, funções que chamam esta (`pg_proc.prosrc ~* 'minha_fn'`), e quem de fato executou por role:

```sql
SELECT r.rolname, s.calls, left(s.query, 80) AS query
FROM pg_stat_statements s JOIN pg_roles r ON r.oid = s.userid
WHERE s.query ILIKE '%minha_fn%' ORDER BY s.calls DESC LIMIT 20;
-- esperado: só service_role/postgres (e o seu próprio curl de teste). anon/authenticated com calls > 0 = chamador vivo.
```

Saída do mapa: uma tabela `objeto × chamador × role × ação (manter / migrar / quebra aceita)` no relatório.

### Corrigir

Revogue dos **três**. `REVOKE … FROM anon, authenticated` sem `PUBLIC` deixa a herança de `PUBLIC`; `REVOKE … FROM PUBLIC` sozinho (o padrão clássico do Postgres) deixa os grants **diretos** que o default privilege concedeu a `anon` e `authenticated`. Os dois erros deixam a função aberta com cara de fechada.

```sql
-- Alvo EXATO (a assinatura, por causa dos overloads). Se precisar reemitir o corpo, use CREATE OR REPLACE —
-- DROP + CREATE zera a ACL e o default privilege reconcede EXECUTE em silêncio.
REVOKE ALL     ON FUNCTION public.minha_fn(uuid) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.minha_fn(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.minha_fn(uuid) FROM authenticated;
GRANT  EXECUTE ON FUNCTION public.minha_fn(uuid) TO service_role;   -- ou TO authenticated, se o front logado chama
-- esperado: 4 comandos sem erro. O "sem erro" ainda não é prova — vá para Provar.
```

Variantes que mordem:

- **A ACL só tem PUBLIC** (`=X/postgres`, sem `authenticated=`) e o front logado usa a função: faça `GRANT EXECUTE … TO authenticated` **antes** do `REVOKE … FROM PUBLIC`, senão o revoke tira o acesso do usuário logado junto.
- **A função aparece numa policy PUBLIC/anon** (mapa acima): antes do REVOKE, rode o dry-run definitivo — se der `42501`, a quebra é real:

```sql
BEGIN;
REVOKE EXECUTE ON FUNCTION public.minha_fn(uuid) FROM anon;
SET LOCAL ROLE anon;
SELECT count(*) FROM minha_tabela;
ROLLBACK;
-- esperado: um número (a policy não depende da função para anon). `permission denied for function` = quebra real, não revogue ainda.
```

- **Gate dentro do corpo**: dentro de uma `SECURITY DEFINER`, `current_user` é o **definer** (`postgres`), não quem chamou — `pg_has_role(current_user, …)` vira uma porta aberta para todos. Quem chamou é `auth.uid()`; o papel que chamou é `current_setting('role', true)`. E `auth.uid() IS NULL` não prova "é o backend": um JWT sem `sub` também dá NULL.

### Provar

```sql
SELECT has_function_privilege('anon',          'public.minha_fn(uuid)', 'EXECUTE') AS anon_exec,
       has_function_privilege('authenticated', 'public.minha_fn(uuid)', 'EXECUTE') AS auth_exec,
       has_function_privilege('service_role',  'public.minha_fn(uuid)', 'EXECUTE') AS svc_exec;
-- esperado: false | false | true   (ou false | true | true na variante authenticated)
```

```bash
curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/rest/v1/rpc/minha_fn" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <ANON_KEY>" \
  -H "Content-Type: application/json" -d '{"p": "<uuid-sintetico>"}'
# esperado DEPOIS: {"code":"42501","message":"permission denied for function minha_fn",...}  http=403
# Função com efeito colateral: não rode este curl — a prova é a query acima.
```

Se `anon_exec` continua `true` depois do bloco, a tabela abaixo diz onde procurar:

| Sintoma | Causa | O que fazer |
|---|---|---|
| `anon_exec = true` e `acl` tem `=X/postgres` | Faltou `REVOKE … FROM PUBLIC` | Rode a linha do PUBLIC |
| `auth_exec = true` e `acl` tem `authenticated=X` | Faltou o REVOKE direto | Rode a linha do authenticated |
| Voltou a `true` numa migration seguinte | Alguém fez `DROP` + `CREATE` | Reemitir com `CREATE OR REPLACE`; ver Tripwire |
| `true` só em uma assinatura | Overload não coberto | Repita o bloco para cada `regprocedure` |

### Tripwire e rollback

A prova mede o **instante**; a tripwire mede o **estado**. Rode a cada deploy (CI, cron ou checklist):

```sql
SELECT p.oid::regprocedure
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.prosecdef
  AND has_function_privilege('anon', p.oid, 'EXECUTE');
-- esperado: 0 linhas. Qualquer linha = regressão (alguém recriou a função ou criou uma nova aberta).
```

Impeça que a **próxima** função nasça aberta:

```sql
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;
-- esperado: a query de pg_default_acl (Detectar) passa a mostrar só postgres/service_role.
-- Atenção: isto vale para funções criadas pelo MESMO role que rodou o comando (normalmente postgres).
```

Rollback, só se um chamador legítimo quebrou e o mapa de chamadores estava incompleto:

```sql
GRANT EXECUTE ON FUNCTION public.minha_fn(uuid) TO authenticated;   -- devolve ao front logado
-- esperado: has_function_privilege('authenticated', …) = true; refaça o mapa antes de tentar de novo.
```

---

## §2 View sem `security_invoker` (o lint `security_definer_view`)

> Uma view em `public`, dona `postgres`, com `security_invoker` desligado, roda com o privilégio do dono e **fura toda a RLS das tabelas-base**. Como o default privilege de tabelas concede `SELECT` a `anon`, a view nasce legível em `GET /rest/v1/minha_view` para qualquer visitante — é vazamento vivo, não aviso cosmético. A query de "tabelas sem RLS" do playbook não a enxerga: view é `relkind = 'v'`, não `'r'`.

### Detectar

```sql
SELECT c.relname AS view, c.relkind,
       has_table_privilege('anon',          c.oid, 'SELECT') AS anon_le,
       has_table_privilege('authenticated', c.oid, 'SELECT') AS auth_le,
       array_to_string(c.reloptions, ',')                    AS reloptions
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('v', 'm')
  AND NOT coalesce('security_invoker=on' = ANY(c.reloptions)
                OR 'security_invoker=true' = ANY(c.reloptions), false)
ORDER BY anon_le DESC, 1;
-- esperado: 0 linhas com anon_le = true. Linha com anon_le = true = ACHADO (leitura anônima furando a RLS das bases).
-- Linhas com anon_le = false mas sem invoker ainda merecem o fix (o lint continua acusando e a próxima GRANT reabre).
```

```bash
curl -sI "https://SEUPROJETO.supabase.co/rest/v1/minha_view?select=*" \
  -H "apikey: <ANON_KEY>" -H "Prefer: count=exact"
# esperado (fechada): HTTP 401/403 ou content-range: */0
# achado Confirmado:  content-range: 0-N/N com N > 0 — sem login
```

### Mapa de chamadores

```sql
-- quem de fato leu a view, por role
SELECT r.rolname, s.calls, left(s.query, 80) AS query
FROM pg_stat_statements s JOIN pg_roles r ON r.oid = s.userid
WHERE s.query ILIKE '%minha_view%' ORDER BY s.calls DESC LIMIT 20;
-- esperado: só service_role/postgres (e o seu curl). anon com forma `SELECT * … LIMIT/OFFSET` sem filtro costuma ser scanner, não app.

-- dependências: outra view ou função que lê esta
SELECT DISTINCT d.refobjid::regclass AS depende_de, c.relname AS view_aninhada
FROM pg_depend d JOIN pg_rewrite rw ON rw.oid = d.objid JOIN pg_class c ON c.oid = rw.ev_class
WHERE d.refobjid = 'public.minha_view'::regclass AND c.relname <> 'minha_view';
SELECT p.oid::regprocedure FROM pg_proc p WHERE p.prosrc ~* 'minha_view';
-- esperado: vazio = sem quebra em cascata.
```

Mais o grep no front e nas Edge Functions por `from('minha_view')`.

### Corrigir

```sql
ALTER VIEW public.minha_view SET (security_invoker = on);   -- a view passa a respeitar a RLS de quem consulta
REVOKE ALL ON public.minha_view FROM anon, authenticated;   -- fecha a leitura direta; service_role ignora RLS/invoker e não quebra
-- esperado: 2 comandos sem erro. Idempotente: pode rodar de novo.
-- Se o front LOGADO precisa da view: mantenha `GRANT SELECT ON public.minha_view TO authenticated` — com invoker ligado,
-- a RLS das tabelas-base decide as linhas.
```

### Provar

```sql
SELECT has_table_privilege('anon',          'public.minha_view', 'SELECT') AS anon_le,
       has_table_privilege('authenticated', 'public.minha_view', 'SELECT') AS auth_le,
       array_to_string(reloptions, ',') AS reloptions
FROM pg_class WHERE oid = 'public.minha_view'::regclass;
-- esperado: false | false | security_invoker=on   (ou false | true | … se o front logado usa)
```

```bash
curl -s -w '\nhttp=%{http_code}\n' "https://SEUPROJETO.supabase.co/rest/v1/minha_view?select=*&limit=1" \
  -H "apikey: <ANON_KEY>"
# esperado DEPOIS: {"code":"42501","message":"permission denied for view minha_view",...}  http=403
```

### Tripwire e rollback

```sql
SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('v','m')
  AND has_table_privilege('anon', c.oid, 'SELECT')
  AND NOT coalesce('security_invoker=on' = ANY(c.reloptions) OR 'security_invoker=true' = ANY(c.reloptions), false);
-- esperado: 0 linhas a cada deploy.
```

```sql
-- rollback (só se um consumidor legítimo quebrou)
ALTER VIEW public.minha_view SET (security_invoker = off);
GRANT SELECT ON public.minha_view TO anon, authenticated;
-- esperado: volta ao estado anterior; refaça o mapa de chamadores.
```

---

## §3 Policies RLS conflitantes, permissivas ou inertes

> Policies são **PERMISSIVE por default e somam por OR**: basta uma `USING (true)` para anular todas as outras da mesma tabela. O inverso também morde na correção: **policy sem `GRANT` de tabela é inerte** — o Postgres checa o privilégio da tabela **antes** de avaliar qualquer policy, e o PostgREST devolve `403 permission denied for table` sem a policy nunca rodar. E RLS ligada **sem nenhuma policy** nega tudo — inclusive para o próprio app.

### Detectar

```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd,
       qual AS using_expr, with_check
FROM pg_policies
WHERE schemaname IN ('public', 'storage')
ORDER BY tablename, policyname;
-- esperado: nenhuma linha com qual = 'true' em tabela com dado de cliente; nenhuma com cmd = 'ALL' e with_check = 'true'.
-- Red flags: qual = 'true' · roles = '{public}' (vale para anon) · with_check = 'true' em INSERT/UPDATE (qualquer um escreve qualquer linha).
```

```sql
-- policy inerte: existe policy para authenticated, mas o role não alcança a tabela
SELECT t.tablename,
       EXISTS (SELECT 1 FROM information_schema.role_table_grants g
               WHERE g.table_schema = 'public' AND g.table_name = t.tablename
                 AND g.grantee = 'authenticated' AND g.privilege_type = 'SELECT') AS auth_tem_grant
FROM pg_policies t WHERE t.schemaname = 'public' AND 'authenticated' = ANY(t.roles)
GROUP BY 1, 2 HAVING NOT bool_or(EXISTS (SELECT 1 FROM information_schema.role_table_grants g
               WHERE g.table_schema = 'public' AND g.table_name = t.tablename
                 AND g.grantee = 'authenticated' AND g.privilege_type = 'SELECT'));
-- esperado: 0 linhas. Cada linha é uma policy que nunca roda (403 antes do RLS).

-- RLS ligada sem policy (nega tudo, inclusive o app)
SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r','p') AND c.relrowsecurity
  AND NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid);
-- esperado: só tabelas que são de fato só do backend (service_role ignora RLS).
```

Vocabulário que decide a leitura da tabela acima:

| Termo | Significa |
|---|---|
| `roles = '{public}'` / `polroles = '{0}'` | A policy vale para **todos**, inclusive `anon` |
| `TO authenticated` | Anon nunca avalia esta policy |
| `permissive = PERMISSIVE` | Soma por OR com as outras; `RESTRICTIVE` soma por AND |
| `FORCE ROW LEVEL SECURITY` | RLS vale até para o **dono** da tabela (o backend com `postgres` também é filtrado) |

### Mapa de chamadores

Policy não tem "chamador" — tem **leitor**. Antes de trocar uma `USING (true)`, meça quem lê hoje e com que forma (0.1 para anon; `pg_stat_statements` × `pg_roles` para os demais). Quem precisa continuar lendo entra na nova policy pela coluna de dono/tenant, nunca por `true`.

### Corrigir

```sql
-- 1) trocar a policy aberta por uma ancorada no dono (uma tabela por vez)
DROP POLICY IF EXISTS "policy_aberta" ON public.minha_tabela;
CREATE POLICY minha_tabela_le_proprio ON public.minha_tabela
  FOR SELECT TO authenticated
  USING (dono_user_id = auth.uid());
-- 2) garantir que o role alcança a tabela (sem isto a policy é inerte)
GRANT SELECT ON public.minha_tabela TO authenticated;
-- 3) anon não deve nem alcançar tabela com dado de cliente
REVOKE ALL ON public.minha_tabela FROM anon;
-- esperado: 4 comandos sem erro. Dar GRANT SELECT a authenticated é seguro: a RLS filtra as linhas — quem não casa recebe [] e não erro.
```

Escrita: `FOR INSERT … WITH CHECK (dono_user_id = auth.uid())` e `FOR UPDATE … USING (…) WITH CHECK (…)` — `with_check = 'true'` deixa qualquer conta escrever em qualquer linha. Cuidado com `auth.uid() IS NULL` em `OR`: NULL em três valores não é `false`, e um JWT sem `sub` passa por ele.

### Provar

```bash
# anon: não alcança
curl -sI "https://SEUPROJETO.supabase.co/rest/v1/minha_tabela?select=id" -H "apikey: <ANON_KEY>" -H "Prefer: count=exact"
# esperado: HTTP 401/403 (permission denied) — ou content-range: */0 se você preferiu manter o GRANT e fechar só por policy

# Ana logada: vê só o dela; Beto logado: vê só o dele (contas sintéticas)
curl -sI "https://SEUPROJETO.supabase.co/rest/v1/minha_tabela?select=id" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <JWT_DO_USUARIO>" -H "Prefer: count=exact"
# esperado: content-range: 0-(n-1)/n com n = quantas linhas são da conta — e n muda quando o JWT muda
```

```sql
SELECT policyname, roles, cmd, qual FROM pg_policies WHERE tablename = 'minha_tabela';
-- esperado: nenhuma linha com qual = 'true'; a nova policy presente; grant de authenticated confirmado em role_table_grants.
```

### Tripwire e rollback

```sql
SELECT tablename, policyname FROM pg_policies
WHERE schemaname = 'public' AND (qual = 'true' OR with_check = 'true');
-- esperado: só a lista curta de tabelas realmente públicas (catálogo, configuração pública) — qualquer outra é regressão.
```

```sql
-- rollback (o app parou de ler): devolve o estado anterior enquanto o mapa de leitores é refeito
DROP POLICY IF EXISTS minha_tabela_le_proprio ON public.minha_tabela;
CREATE POLICY "policy_aberta" ON public.minha_tabela FOR SELECT TO authenticated USING (true);
```

---

## §4 Bucket de Storage público ou com listagem aberta

> Bucket **público** serve qualquer objeto por URL sem login (`/storage/v1/object/public/meu-bucket/arquivo`). Bucket **privado** com policy de `SELECT` em `storage.objects` para `anon` permite **listar** sem login. Documento de cliente (contrato, certidão, guia, admissão) nunca fica em bucket público — bucket público é para logo, ícone, asset de site.

### Detectar

```sql
SELECT id, name, public, file_size_limit, allowed_mime_types, created_at
FROM storage.buckets ORDER BY public DESC, name;
-- esperado: public = true só em buckets de asset de site. Qualquer bucket com documento de cliente e public = true é ACHADO.

SELECT policyname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname = 'storage' AND tablename = 'objects'
ORDER BY policyname;
-- esperado: nenhuma policy SELECT/INSERT com roles = '{public}' ou qual = 'true' em bucket de documentos.
```

```bash
# listagem sem login (a API de Storage exige o header Authorization; com a anon key você é o visitante)
curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/storage/v1/object/list/meu-bucket" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <ANON_KEY>" \
  -H "Content-Type: application/json" -d '{"prefix":"","limit":1}'
# esperado (fechado): []  http=200   (sem policy de SELECT para anon não há itens)
# achado Confirmado:  [{"name":"...","id":"..."}]  → listagem aberta sem login
# sem o header Authorization vem 400 "headers must have required property 'authorization'" — não é prova de nada

# download público
curl -s -o /dev/null -w 'http=%{http_code}\n' "https://SEUPROJETO.supabase.co/storage/v1/object/public/meu-bucket/caminho/arquivo.pdf"
# esperado (privado): http=400   ·   achado: http=200 em documento de cliente
```

### Mapa de chamadores

O que quebra ao fechar um bucket é quem usa **URL pública**:

```bash
grep -rn "object/public/meu-bucket\|getPublicUrl(" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.html' .
# esperado: a lista de telas/edges que precisam migrar para URL assinada (createSignedUrl) ou download via Edge Function
```

Mais: e-mails/WhatsApp enviados com link público (continuam funcionando até o bucket fechar — avise os destinatários), integrações que baixam por URL, e o próprio Lovable, que costuma gerar `getPublicUrl` por padrão.

### Corrigir

```sql
UPDATE storage.buckets SET public = false WHERE id = 'meu-bucket';
-- esperado: UPDATE 1

-- policies em storage.objects ancoradas no dono ou no prefixo do tenant (uma por operação)
DROP POLICY IF EXISTS "leitura aberta" ON storage.objects;
CREATE POLICY meu_bucket_le_proprio ON storage.objects
  FOR SELECT TO authenticated
  USING (bucket_id = 'meu-bucket' AND (storage.foldername(name))[1] = auth.uid()::text);
CREATE POLICY meu_bucket_sobe_proprio ON storage.objects
  FOR INSERT TO authenticated
  WITH CHECK (bucket_id = 'meu-bucket' AND (storage.foldername(name))[1] = auth.uid()::text);
-- esperado: objetos organizados por pasta = id do usuário (`<uuid>/arquivo.pdf`); ajuste o predicado à sua convenção de pastas.
```

No código: trocar `getPublicUrl(caminho)` por `createSignedUrl(caminho, 60)` (segundos) ou por download via Edge Function que autoriza antes de servir. Migre os chamadores do mapa **antes** do `UPDATE`, ou no mesmo deploy.

### Provar

```bash
curl -s -o /dev/null -w 'http=%{http_code}\n' "https://SEUPROJETO.supabase.co/storage/v1/object/public/meu-bucket/caminho/arquivo.pdf"
# esperado DEPOIS: http=400 (bucket privado não serve por /public/)

curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/storage/v1/object/list/meu-bucket" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <ANON_KEY>" -H "Content-Type: application/json" -d '{"prefix":"","limit":1}'
# esperado DEPOIS: []  http=200

# Ana logada lista só a pasta dela; a pasta do Beto volta []
curl -s -X POST "https://SEUPROJETO.supabase.co/storage/v1/object/list/meu-bucket" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <JWT_DO_USUARIO>" -H "Content-Type: application/json" \
  -d '{"prefix":"<uuid-do-beto>/","limit":1}'
# esperado: []
```

### Tripwire e rollback

```sql
SELECT id FROM storage.buckets WHERE public AND id NOT IN ('assets-do-site');   -- sua allowlist
-- esperado: 0 linhas a cada deploy.
```

```sql
-- rollback (um link público legítimo quebrou e não dá para migrar agora)
UPDATE storage.buckets SET public = true WHERE id = 'meu-bucket';
-- esperado: UPDATE 1 — e o achado volta a `aberto` no relatório, com prazo.
```

---

## §5 Segredo exposto: `.env` na pasta pública, `service_role` no bundle, histórico do git

> Segredo exposto está **comprometido enquanto não for revogado** — não importa se "ninguém viu". A ordem da rotação decide se o app fica de pé.

### Detectar

Enumeração mínima no próprio site (dentro da ética da skill: só caminhos do seu app):

```bash
for p in /.env /.env.production /.env.local /.git/HEAD /.git/config /supabase/config.toml /config.json; do
  printf '%-24s ' "$p"; curl -s -o /dev/null -w '%{http_code}\n' "https://SEUAPP.exemplo/$p"
done
# esperado: 404 (ou 403) em todos. 200 em /.env* ou /.git/HEAD = ACHADO P0.
```

```bash
# source maps referenciados pelos bundles expõem o código original (e às vezes o .env embutido)
curl -s "https://SEUAPP.exemplo/" | grep -o 'src="[^"]*\.js"' | head
curl -s "https://SEUAPP.exemplo/assets/index.js" | grep -o 'sourceMappingURL=[^ ]*'
# esperado: nenhum .map servido em produção

# a service_role (ou sb_secret_) nunca pode estar no bundle do front
curl -s "https://SEUAPP.exemplo/assets/index.js" | grep -c -E 'service_role|sb_secret_'
# esperado: 0
```

Se o `.env` está na pasta pública, **provavelmente está no histórico do git** também:

```bash
git log --all --oneline -- .env .env.production .env.local
# esperado: vazio. Qualquer commit = o segredo está no histórico (e no GitHub, se o repo é público ou foi clonado).
```

### Mapa de chamadores

Quem usa a chave que vai ser rotacionada: Edge Functions (`SUPABASE_SERVICE_ROLE_KEY` nos secrets), crons, webhooks, servidores próprios, automações (n8n, Zapier, Make), scripts de importação, o CI. Cada um precisa receber a chave nova **antes** de a antiga morrer.

### Corrigir

Rotação **sem derrubar o app**. **Chaves legadas (`anon` e `service_role` no formato JWT)** são assinadas pelo **JWT secret do projeto**. Rotacionar esse secret invalida as **duas** juntas e desloga todos os usuários — é o botão de pânico, não a rotina.

**Chaves novas (`sb_publishable_…` e `sb_secret_…`)** rotacionam **uma a uma**:

1. Criar uma `sb_secret_` nova no painel (API Keys).
2. Migrar **todos** os consumidores do mapa para a nova (secrets das Edge Functions, servidor, crons, automações, CI).
3. Confirmar nos logs que a chave antiga parou de ser usada (painel → API → uso por chave).
4. Revogar a antiga.
5. Quando todos os consumidores já usam `sb_*`, desabilitar as chaves legadas JWT no painel.

Depois, sempre: tirar o arquivo da pasta pública, adicionar ao `.gitignore`, e — se estava no histórico — reescrever o histórico ou tratar o repositório como exposto (a chave já foi rotacionada; o histórico limpo é higiene, não segurança). Revisar os logs de acesso do período em que a chave ficou exposta.

### Provar

```bash
curl -s -w '\nhttp=%{http_code}\n' "https://SEUPROJETO.supabase.co/rest/v1/" -H "apikey: <CHAVE_ANTIGA>"
# esperado DEPOIS da revogação: {"message":"Invalid API key",...}  http=401

curl -s -o /dev/null -w 'http=%{http_code}\n' "https://SEUAPP.exemplo/.env"
# esperado: 404
```

### Tripwire e rollback

- Tripwire no CI: um `grep -rE 'service_role|sb_secret_|eyJ[A-Za-z0-9_-]{30,}\.' dist/` que falha o build se encontrar algo (o mesmo princípio do `scripts/redact_secrets.py`).
- `.env*` no `.gitignore`; pasta pública sem arquivos que não sejam servidos de propósito.
- Rollback não existe para exposição: uma chave vista é uma chave rotacionada. O que se reverte é só o consumidor que ficou sem a chave nova — reaponte-o e siga.

---

## §6 Edge Functions: autorização antes de agir e a armadilha do `verify_jwt`

> Uma Edge Function que usa `service_role` ignora a RLS. Se ela não autoriza **antes** de agir, ela é uma porta de backend aberta para qualquer chamador. E a correção mais comum — "ligue a validação de token" — quebra toda edge chamada pelo **navegador**: com `verify_jwt = true` (o default) o gateway rejeita o `OPTIONS` do preflight CORS **antes** do seu código rodar, porque o preflight não carrega `Authorization` por especificação do browser.

### Detectar

```bash
# inventário: quais edges usam service_role e qual o verify_jwt de cada uma
grep -rl "SUPABASE_SERVICE_ROLE_KEY" supabase/functions/*/index.ts
grep -n -A1 "^\[functions\." supabase/config.toml
# esperado: toda edge com service_role tem (a) bloco [functions.<nome>] explícito e (b) autorização no código antes de qualquer escrita.
# Edge SEM bloco no config.toml guarda o verify_jwt só em prod — o repositório não diz o que vale.
```

```bash
# preflight: a edge é alcançável pelo browser?
curl -s -o /dev/null -w 'options=%{http_code}\n' -X OPTIONS "https://SEUPROJETO.supabase.co/functions/v1/minha-edge" \
  -H "Origin: https://SEUAPP.exemplo" -H "Access-Control-Request-Method: POST"
# esperado: options=204. 401 = verify_jwt=true numa edge chamada pelo browser — ela está morta para o front.

# sem token: a edge nega antes de tocar o banco?
curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/functions/v1/minha-edge" -H "apikey: <ANON_KEY>" -d '{}'
# esperado: http=401 sem efeito colateral. 200 = ACHADO (a edge age sem saber quem chama).
```

### Mapa de chamadores

Browser (front logado) · outro servidor (webhook, cron, automação) · nenhum (edge órfã). A resposta decide a forma: edge chamada pelo browser com auth manual = `verify_jwt = false` **e** `getUser()` no código; edge chamada só por servidor com segredo compartilhado = pode ficar `true` ou validar o segredo no header.

### Corrigir

```toml
# supabase/config.toml — edge chamada pelo browser, autenticação manual no código
[functions.minha-edge]
verify_jwt = false
```

```ts
// dentro da edge: CORS por allowlist → token → getUser() no servidor → papel/tenant → só então service_role
const jwt = req.headers.get("Authorization")?.replace(/^Bearer\s+/i, "");
if (!jwt) return json({ error: "unauthorized" }, 401);
const { data: { user }, error } = await createClient(url, anonKey).auth.getUser(jwt);
if (error || !user) return json({ error: "unauthorized" }, 401);
// autorizar para o OBJETO/tenant (nunca confiar em id vindo do body):
// const podeVer = await checaDono(user.id, params.id); if (!podeVer) return json({ error: "forbidden" }, 403);
// só depois: const admin = createClient(url, serviceRoleKey); ...
```

Nunca decodificar o JWT no cliente ou na edge para ler `sub` (`atob`): a validação é `getUser()` no servidor. `verify_jwt = false` **não** afrouxa nada quando o `getUser()` existe — o vetor perigoso é `false` **sem** `getUser()`.

### Provar

```bash
curl -s -o /dev/null -w 'options=%{http_code}\n' -X OPTIONS "https://SEUPROJETO.supabase.co/functions/v1/minha-edge" \
  -H "Origin: https://SEUAPP.exemplo" -H "Access-Control-Request-Method: POST"
# esperado: options=204

curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/functions/v1/minha-edge" -H "apikey: <ANON_KEY>" -d '{}'
# esperado: http=401

# Ana pedindo o objeto do Beto (contas sintéticas)
curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/functions/v1/minha-edge" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <JWT_DO_USUARIO>" -H "Content-Type: application/json" \
  -d '{"id": "<id-do-objeto-do-beto>"}'
# esperado: http=403 (ou 404) — nunca o objeto
```

### Tripwire e rollback

- Tripwire no CI: para cada `index.ts` com `SUPABASE_SERVICE_ROLE_KEY`, exigir `getUser(` no mesmo arquivo (ou o helper de autorização da casa) — `grep -L` lista as que faltam; a lista deve ser vazia.
- Smoke do preflight (`OPTIONS` → 204) a cada deploy das edges chamadas pelo browser.
- Rollback: reverter o `config.toml` da edge e redeployar; a autorização no código fica — ela nunca quebra o preflight.

---

## Regra de atualização

Se a documentação oficial atual divergir deste arquivo, siga a documentação e registre no relatório que houve mudança de plataforma. Fontes: Postgres `GRANT` (default de `EXECUTE` para `PUBLIC`), Supabase `database/postgres/row-level-security`, `database/database-linter`, `storage/security/access-control`, `getting-started/api-keys`, `getting-started/migrating-to-new-api-keys`, `functions/auth`.
