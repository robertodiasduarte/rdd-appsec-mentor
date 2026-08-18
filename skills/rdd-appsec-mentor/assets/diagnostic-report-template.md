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

| ID | Achado | Confiança | G | U | T | GUT | Prioridade |
|---|---|---|---:|---:|---:|---:|---|
| F-001 | [título] | Confirmado | 5 | 5 | 4 | 100 | P0 |

## 5. Achados detalhados

### F-001 — [Título]

**Componente:** [Supabase/RLS/Edge/Storage/Auth/Cloudflare/etc.]  
**Confiança:** [Confirmado/Provável/Hipótese]  
**Evidência:** [o que foi observado, sem segredo/dado real]  
**Impacto:** [impacto técnico + negócio]  
**Por que G=[x], U=[y], T=[z]:** [justificativa breve]  
**Causa provável:** [causa]

#### Como corrigir

1. [passo]
2. [passo]
3. [passo]

#### Prompt opcional para Lovable

[Prompt curto, específico, descrevendo controle esperado e proibindo alteração fora do escopo.]

#### Como provar que corrigiu

**Antes:** [teste e resultado anterior]  
**Depois esperado:** [resultado seguro]  
**Teste de regressão:** [como evitar reabertura]

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

- [ ] Repetir teste original.
- [ ] Validar fluxo legítimo.
- [ ] Procurar caminho alternativo.
- [ ] Registrar evidência antes/depois.
- [ ] Adicionar teste recorrente quando aplicável.

## 8. Risco residual e pendências

[O que ainda não foi possível validar e por quê.]

## 9. Próximos passos do aluno

1. [ação objetiva]
2. [ação objetiva]
3. [ação objetiva]
