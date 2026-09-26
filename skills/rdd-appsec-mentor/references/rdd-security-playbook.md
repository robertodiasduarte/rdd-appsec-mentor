# Roteiro RDD de verificação de segurança

Este arquivo adapta o roteiro fornecido pelos mentores para uso didático e seguro. O foco é orientar alunos que constroem aplicações com Lovable/vibe coding, Supabase e, quando houver, Cloudflare.

## Sumário

1. Auditoria orientada por evidências
2. Seis testes no navegador
3. Supabase
4. Cloudflare
5. Pós-correção

## 1. Auditoria orientada por evidências

Quando houver acesso ao repositório, revisar o projeto inteiro em vez de analisar trechos isolados. Procurar:

- identificadores controlados pelo cliente;
- decisões de autorização feitas só no frontend;
- Edge Functions como único gate para dados também acessíveis pela Data API;
- funções SQL privilegiadas;
- RLS ausente ou permissiva;
- rotas `debug`, `test`, `dev`, `admin`, `status`, `info`;
- autenticação e sessão;
- segredos no frontend;
- Storage público.

Todo achado de código precisa de `arquivo:linha` quando essa informação estiver disponível. Código antigo ou migrations históricas podem produzir falso positivo; confirmar o estado real.

### Revisão adversarial depois da correção

Perguntar:

1. A correção fecha o problema ou só muda o caminho?
2. Existe caminho alternativo até o mesmo dado?
3. O fluxo legítimo quebrou?
4. Uma alteração futura pode desfazer a proteção silenciosamente?
5. Qual teste executável prova o antes e o depois?

## 2. Seis testes no navegador

Sempre com duas contas próprias/sintéticas.

### Teste A — BOLA/IDOR

Logar como Ana, abrir um objeto sintético da Ana e trocar somente o identificador por um objeto sintético do Beto.

**Passa:** acesso negado, vazio seguro ou erro apropriado.  
**Falha:** Ana consegue ler ou alterar o objeto do Beto.

UUID não substitui autorização.

### Teste B — rota administrativa direta

Como usuário comum, digitar diretamente uma rota administrativa conhecida do próprio app.

**Passa:** bloqueia no servidor/edge/backend.  
**Falha:** conteúdo/ação administrativa fica acessível apenas porque o menu foi escondido.

### Teste C — logout

Abrir duas sessões/abas de teste. Fazer logout em uma e verificar o comportamento autorizado esperado na outra conforme a política de sessão do app.

Registrar a política desejada; nem todo produto exige logout global em todos os dispositivos, mas a aplicação deve comportar-se conforme a decisão de segurança documentada.

### Teste D — segredo/senha em URL

Submeter o login e verificar se senha/token aparece em URL, histórico ou logs visíveis.

Falha se credencial sensível for transportada em query string.

### Teste E — debug/teste em produção

Verificar somente caminhos conhecidos do próprio projeto e candidatos mínimos aprovados no escopo, como `/debug`, `/test`, `/status` e `/info` — e os arquivos que costumam ser esquecidos na pasta pública: `/.env`, `/.env.production`, `/.env.local`, `/.git/HEAD`, `/.git/config`, `/supabase/config.toml`, `/config.json` e source maps (`*.js.map`) referenciados pelos bundles.

Falha quando configuração, segredo, dado ou operação sensível está exposta sem necessidade. `.env` na pasta pública quase sempre está também no histórico do git (`git log --all -- .env`); rotação e ordem em [remediacao-supabase.md §5](remediacao-supabase.md).

### Teste F — primeiro acesso previsível

Verificar se senha inicial é derivada de CPF, telefone, nome, aniversário ou outro dado previsível.

Preferir convite/link de uso único ou segredo aleatório com expiração e troca obrigatória.

## 3. Supabase

### 3.1 RLS

Listar tabelas do schema exposto sem RLS:

```sql
SELECT c.relname AS tabela_sem_rls
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind IN ('r', 'p')
  AND NOT c.relrowsecurity
ORDER BY 1;
-- esperado: 0 linhas. `relkind IN ('r','p')` cobre tabelas comuns e particionadas.
```

Interpretar junto com grants, exposição da Data API e políticas. Uma tabela no schema exposto sem RLS deve ser tratada como alta prioridade até provar que não está acessível aos papéis clientes.

Esta query **não enxerga views** (`relkind = 'v'`): uma view sem `security_invoker` fura a RLS das tabelas-base e nasce legível por `anon`. Detecção e correção em [remediacao-supabase.md §2](remediacao-supabase.md). Policies conflitantes, permissivas ou inertes: [§3](remediacao-supabase.md).

### 3.2 Acesso direto pela Data API

Quando autorizado, testar tabela sintética com chave publishable/legada anon e sem token de usuário. Não usar tabela com dados reais para prova.

Exemplo conceitual:

```bash
curl "https://SEUPROJETO.supabase.co/rest/v1/TABELA_SINTETICA?select=*&limit=5" \
  -H "apikey: <ANON_KEY>"
# esperado: nenhum registro não público e nenhuma operação além do desenho de acesso previsto.
```

Em produção, sem tabela sintética, conte sem transferir nenhuma linha:

```bash
curl -sI "https://SEUPROJETO.supabase.co/rest/v1/TABELA?select=id" \
  -H "apikey: <ANON_KEY>" -H "Prefer: count=exact"
# esperado (fechada): HTTP 401/403 ou content-range: */0
# achado Confirmado: content-range: 0-16/17 → o número após a barra é quantas linhas o visitante vê, sem login e sem PII no relatório
```

Detalhe em [remediacao-supabase.md §0.1](remediacao-supabase.md).

### 3.3 Funções privilegiadas

Localizar funções `SECURITY DEFINER` e revisar privilégios:

```sql
SELECT p.proname AS funcao,
       pg_get_function_identity_arguments(p.oid) AS argumentos,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS logado_pode_executar,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS visitante_pode_executar
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.prosecdef
ORDER BY 1;
```

Para cada função:

- por que ela precisa ser `SECURITY DEFINER`?
- `search_path` está seguro?
- quem pode executar?
- a identidade vem de sessão/token validado ou de parâmetro?
- existe checagem de objeto/tenant?
- ela é usada em policy RLS?
- o chamador usa privilégio de backend que bypassa RLS?

Esta query já resolve herança de `PUBLIC` e grants diretos — ela está certa. O que vem **depois** dela (alvo por assinatura, `REVOKE` dos três, prova por privilégio e por vetor real, tripwire) está em [remediacao-supabase.md §1](remediacao-supabase.md). Antes de revogar, o mapa de chamadores (etapa 10.1 do SKILL.md) é obrigatório: uma policy `TO public` que chama a função derruba o `SELECT` da tabela inteira.

### 3.4 Edge Functions

Verificar:

- autenticação do token **no servidor** (`getUser()`), nunca decodificando o JWT — e `verify_jwt = false` no `config.toml` quando a edge é chamada pelo navegador (com `true`, o gateway derruba o preflight CORS antes do código; ver [remediacao-supabase.md §6](remediacao-supabase.md));
- autorização por objeto/tenant;
- ordem da autorização antes de operação com privilégio elevado;
- segredos só no lado servidor;
- respostas e logs sem dados sensíveis.

### 3.5 Storage

```sql
SELECT id, name, public, file_size_limit, allowed_mime_types FROM storage.buckets ORDER BY public DESC, name;
-- esperado: public = true só em bucket de asset de site (logo, ícone). Documento de cliente em bucket público é achado.
SELECT policyname, roles, cmd, qual, with_check FROM pg_policies WHERE schemaname = 'storage' AND tablename = 'objects';
-- esperado: nenhuma policy SELECT/INSERT com roles = '{public}' ou qual = 'true' em bucket de documentos.
```

```bash
curl -s -w '\nhttp=%{http_code}\n' -X POST "https://SEUPROJETO.supabase.co/storage/v1/object/list/meu-bucket" \
  -H "apikey: <ANON_KEY>" -H "Authorization: Bearer <ANON_KEY>" -H "Content-Type: application/json" -d '{"prefix":"","limit":1}'
# esperado (fechado): []  http=200 · achado: itens listados sem login. Sem o header Authorization vem 400 e não prova nada.
```

Para cada bucket:

- público ou privado?
- o conteúdo é realmente público?
- existe listagem desnecessária?
- políticas limitam usuário/tenant?
- URLs assinadas têm escopo/expiração adequados?

Fechar bucket e migrar os chamadores de `getPublicUrl`/`/object/public/`: [remediacao-supabase.md §4](remediacao-supabase.md).

### 3.6 Chaves

- chave publishable/legada anon pode existir no cliente;
- chave secret/legada service_role deve permanecer em backend confiável;
- suspeita de vazamento de segredo privilegiado => rotacionar **na ordem certa** (criar nova → migrar consumidores → conferir logs → revogar a antiga; o JWT secret invalida `anon` e `service_role` juntas) e revisar logs — [remediacao-supabase.md §5](remediacao-supabase.md);
- não copiar segredo para relatório.

## 4. Cloudflare / HTTP

Revisar cabeçalhos e aplicar configurações uma por vez.

Cabeçalhos comuns a avaliar:

- `X-Frame-Options` ou política equivalente via CSP;
- `X-Content-Type-Options`;
- `Referrer-Policy`;
- `Permissions-Policy`;
- `Strict-Transport-Security` quando a operação HTTPS está madura.

Não aplicar política que quebre iframe, player, câmera, microfone, geolocalização ou integrações legítimas.

Usar rate limiting no login/API sensível de acordo com tráfego legítimo; não escolher valores cegamente.

## 5. Depois de corrigir

Procedimento completo na etapa 10 do SKILL.md (10.1 mapa de chamadores → 10.2 corrigir → 10.3 provar pelo privilégio **e** pelo vetor real → 10.4 tripwire). Por classe de achado: [remediacao-supabase.md](remediacao-supabase.md).

- guardar evidência do "antes";
- repetir o mesmo caminho depois;
- validar que o uso legítimo continua funcionando;
- testar caminho alternativo;
- criar regressão automatizada quando possível;
- preservar logs antes de mudanças em caso de possível incidente.
