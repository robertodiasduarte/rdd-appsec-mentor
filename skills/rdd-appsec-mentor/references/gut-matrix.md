# Matriz GUT para riscos de AppSec

A matriz GUT desta Skill serve para ordenar a fila de correção. Ela não substitui CVSS, análise jurídica, threat modeling ou julgamento do responsável pelo negócio.

## Escala

### G — Gravidade

| Nota | Critério |
|---|---|
| 1 | Impacto mínimo; sem dado sensível e sem privilégio relevante. |
| 2 | Impacto limitado; afeta função secundária ou poucos dados sintéticos/não sensíveis. |
| 3 | Impacto relevante; exposição ou alteração restrita, abuso de conta comum ou indisponibilidade localizada. |
| 4 | Impacto alto; dados sensíveis, acesso cruzado entre usuários/organizações, fraude relevante ou privilégio administrativo parcial. |
| 5 | Impacto crítico; tomada de conta/admin, grande exposição de dados, segredo privilegiado, bypass amplo de autorização ou dano operacional severo. |

### U — Urgência

| Nota | Critério |
|---|---|
| 1 | Pode entrar no backlog; baixa exposição e controles compensatórios sólidos. |
| 2 | Corrigir em ciclo normal; exploração exige condições pouco prováveis. |
| 3 | Corrigir em curto prazo; caminho de exploração plausível e componente exposto. |
| 4 | Corrigir rapidamente; exploração simples ou alcance amplo. |
| 5 | Ação imediata; falha pública, segredo privilegiado exposto, acesso não autorizado confirmado ou abuso em andamento. |

### T — Tendência

| Nota | Critério |
|---|---|
| 1 | Risco estável e pouco provável de se ampliar sozinho. |
| 2 | Crescimento lento ou limitado. |
| 3 | Pode aumentar com novos usuários/dados/releases. |
| 4 | Deve piorar com o crescimento, novas tabelas, novos papéis ou mudanças frequentes. |
| 5 | Pode escalar rapidamente, reaparecer silenciosamente ou expor cada novo registro/usuário. |

## Cálculo

`GUT = G × U × T`

Faixas internas desta Skill:

| Score | Prioridade | Diretriz |
|---:|---|---|
| 80–125 | P0 | Conter/corrigir imediatamente; validar no mesmo ciclo. |
| 45–79 | P1 | Corrigir com alta prioridade antes de novas features relevantes. |
| 20–44 | P2 | Planejar correção próxima e adicionar teste de regressão. |
| 1–19 | P3 | Backlog monitorado; corrigir conforme contexto e custo. |

Em empate, ordenar por: maior Gravidade, depois maior Urgência, depois maior Tendência.

## Regras de pontuação

- Pontuar o risco **observado**, não um cenário hipotético extremo.
- Se a evidência for `Hipótese`, manter a pontuação provisória e indicar que depende de confirmação.
- Segredo privilegiado comprovadamente exposto tende a ter U=5 enquanto não for rotacionado.
- Falha de autorização entre duas contas sintéticas pode ter G alto mesmo sem acessar dado real.
- Não inflar GUT para chamar atenção; explicar cada nota em uma frase.
