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

Verificar somente caminhos conhecidos do próprio projeto e candidatos mínimos aprovados no escopo, como `/debug`, `/test`, `/status` e `/info`.

Falha quando configuração, segredo, dado ou operação sensível está exposta sem necessidade.

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
  AND c.relkind = 'r'
  AND NOT c.relrowsecurity
ORDER BY 1;
```

Interpretar junto com grants, exposição da Data API e políticas. Uma tabela no schema exposto sem RLS deve ser tratada como alta prioridade até provar que não está acessível aos papéis clientes.

### 3.2 Acesso direto pela Data API

Quando autorizado, testar tabela sintética com chave publishable/legada anon e sem token de usuário. Não usar tabela com dados reais para prova.

Exemplo conceitual:

```bash
curl "https://SEUPROJETO.supabase.co/rest/v1/TABELA_SINTETICA?select=*&limit=5" \
  -H "apikey: CHAVE_PUBLICAVEL_OU_ANON"
```

Esperado: nenhum registro não público e nenhuma operação além do desenho de acesso previsto.

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

Antes de revogar, mapear dependências e testar. Preferir mudanças específicas e reversíveis.

### 3.4 Edge Functions

Verificar:

- autenticação do token;
- autorização por objeto/tenant;
- ordem da autorização antes de operação com privilégio elevado;
- segredos só no lado servidor;
- respostas e logs sem dados sensíveis.

### 3.5 Storage

Para cada bucket:

- público ou privado?
- o conteúdo é realmente público?
- existe listagem desnecessária?
- políticas limitam usuário/tenant?
- URLs assinadas têm escopo/expiração adequados?

### 3.6 Chaves

- chave publishable/legada anon pode existir no cliente;
- chave secret/legada service_role deve permanecer em backend confiável;
- suspeita de vazamento de segredo privilegiado => rotacionar/revogar e revisar logs;
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

- guardar evidência do "antes";
- repetir o mesmo caminho depois;
- validar que o uso legítimo continua funcionando;
- testar caminho alternativo;
- criar regressão automatizada quando possível;
- preservar logs antes de mudanças em caso de possível incidente.
