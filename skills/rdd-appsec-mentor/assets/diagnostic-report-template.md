# Relatório de Diagnóstico de Segurança — [Nome da aplicação]

**URL:** [https://...]  
**Data:** [AAAA-MM-DD]  
**Ambiente:** [produção/staging/dev]  
**Autorização confirmada:** [sim/não + observação]  
**Escopo:** [componentes avaliados]

## 1. Resumo executivo

[Explique em linguagem simples o estado encontrado, principais riscos e o que deve ser feito primeiro.]

## 2. Escopo, evidências e limitações

**Avaliamos**
- [item]

**Não avaliamos**
- [item]

**Evidências recebidas**
- [item]

**Limitações**
- [item]

## 3. Visão geral do risco

- Achados confirmados: [n]
- Prováveis: [n]
- Hipóteses: [n]
- P0: [n]
- P1: [n]
- P2: [n]
- P3: [n]

## 4. Matriz GUT

| ID | Achado | Confiança | G | U | T | GUT | Prioridade | Status | Reteste |
|---|---|---|---:|---:|---:|---:|---|---|---|
| F-001 | [título] | Confirmado | 5 | 5 | 4 | 100 | P0 | aberto | [pendente / AAAA-MM-DD: passou] |

Status: `aberto` → `corrigido` → `verificado` (prova registrada) → `aceito` (risco aceito pelo dono, com motivo).

## 5. Achados detalhados

### F-001 — [Título]

**Componente:** [Supabase/RLS/Edge/Storage/Auth/Cloudflare/etc.]  
**Confiança:** [Confirmado/Provável/Hipótese]  
**Status:** [aberto/corrigido/verificado/aceito]  
**Evidência:** [o que foi observado, sem segredo/dado real]  
**Caminho de reprodução:** [comando mínimo e autorizado + saída, sem PII]  
**Impacto:** [impacto técnico + negócio]  
**Por que G=[x], U=[y], T=[z]:** [justificativa breve]  
**Causa provável:** [causa]

#### Chamadores confirmados

| Objeto | Chamador | Role | Ação |
|---|---|---|---|
| [função/tabela/view/bucket] | [front / edge X / cron / policy Y / integração Z] | [anon/authenticated/service_role] | [manter / migrar / quebra aceita] |

Fontes consultadas: [grep no repo · edges com service_role · cron/triggers · pg_policy · pg_depend/prosrc · pg_stat_statements × pg_roles · integrações externas]

#### Como corrigir

1. [passo — alvo exato, uma mudança por vez]
2. [passo]
3. [rollback preparado: bloco que desfaz]

#### Prompt opcional para Lovable

[Prompt curto, específico, descrevendo controle esperado e proibindo alteração fora do escopo.]

#### Prova pós-correção (comando + saída esperada)

**Antes:** [comando + saída que demonstrou a falha — guardada antes do fix]  
**Depois esperado:** [pelo privilégio: `has_function_privilege`/`has_table_privilege`/`pg_policies` → valor esperado]  
**Depois pelo vetor real:** [mesmo `curl` → `42501`/`permission denied`/`[]` esperado]  
**Fluxo legítimo:** [o que continuou funcionando e como foi conferido]  
**Tripwire:** [query que deve voltar 0 linhas a cada deploy]

## 6. Plano de ação ordenado

### P0 — imediato
1. [ação]

### P1 — alta prioridade
1. [ação]

### P2 — próximo ciclo
1. [ação]

### P3 — backlog monitorado
1. [ação]

## 7. Verificação pós-correção

| ID | Reteste original | Prova por privilégio | Prova pelo vetor real | Fluxo legítimo | Caminho alternativo | Tripwire | Status |
|---|---|---|---|---|---|---|---|
| F-001 | [pendente / passou em AAAA-MM-DD] | [comando → saída] | [comando → saída] | [ok / quebrou: o quê] | [procurado: onde] | [criada / n.a.] | [verificado / aberto] |

## 8. Risco residual e pendências

[O que ainda não foi possível validar e por quê. Achados `aceito`: motivo e responsável.]

## 9. Próximos passos do aluno

1. [ação objetiva]
2. [ação objetiva]
3. [ação objetiva]
