# RDD AppSec Mentor

Skill de diagnóstico de segurança para aplicações web construídas com IA — Lovable, "vibe coding", Supabase, Cloudflare e stacks equivalentes.

Você descreve a aplicação **que é sua** (ou que você tem autorização explícita para testar), e a skill conduz um diagnóstico defensivo: observa o que está exposto, investiga autorização, sessão, RLS, Storage, Edge Functions e chaves, e devolve um **relatório priorizado por matriz GUT** com passo a passo de correção e teste de verificação.

Feita para quem publicou um app funcionando e precisa saber o que ficou aberto — sem virar especialista em segurança para isso.

## O que ela faz

- **Exige autorização antes de tudo.** A primeira resposta pede a URL e a confirmação de que a aplicação é sua ou que você tem autorização do responsável. Sem isso, a skill não investiga alvo — só orienta hardening genérico e revisão do código que você mesmo enviar.
- **Começa pelo não destrutivo.** Observação pública e de baixo impacto primeiro; evidência adicional só quando necessária para confirmar um achado.
- **Investiga o que realmente quebra:** BOLA/IDOR, rotas administrativas acessíveis, invalidação de sessão, RLS e grants, funções `SECURITY DEFINER`, Edge Functions sem validação de token, buckets de Storage, segredos vazados no frontend e rotas de debug esquecidas em produção.
- **Não confunde suspeita com falha.** Todo achado carrega nível de confiança — `Confirmado`, `Provável` ou `Hipótese`. Achado sem reprodução não vira "confirmado".
- **Prioriza com GUT** (Gravidade × Urgência × Tendência), com cálculo determinístico por script — não por impressão.
- **Nunca declara a aplicação "100% segura".** O relatório declara escopo, evidências, limitações e risco residual.

## O que ela não faz

Não testa sistema de terceiros sem autorização. Não faz força bruta, credential stuffing, negação de serviço, evasão, persistência, exfiltração ou exploração além do necessário para confirmar a falha em ambiente autorizado. Não manipula dados reais de clientes durante os testes — só contas e dados sintéticos.

Também nunca pede chave secreta, `service_role`, senha real, token de sessão real, CPF, e-mail ou telefone. Se um segredo aparecer numa evidência, a skill orienta rotação e higieniza com `scripts/redact_secrets.py`.

## Instalação

Baixe o `.zip` da [última Release](../../releases/latest).

- **Claude (claude.ai):** Configurações → Capacidades → Skills → upload do `.zip` **sem descompactar**.
- **ChatGPT:** Configurações → Habilidades (`chatgpt.com/admin/skills`) → **+** → arraste o `.zip`. Sem acesso à administração? Crie um Projeto, envie os arquivos e instrua: *"Siga o SKILL.md que está nos arquivos deste projeto."*
- **Claude Code:** `npx skills add robertodiasduarte/rdd-appsec-mentor -a claude-code -y` (instala em `.claude/skills/` do projeto; com `-g`, em `~/.claude/skills/`).
- **Codex:** `npx skills add robertodiasduarte/rdd-appsec-mentor -a codex -y` (instala em `.agents/skills/` do projeto; com `-g`, em `~/.codex/skills/`).
- **Cursor, Kimi e outros:** mesmo comando com o nome do agente em `-a`. Sem Node.js, descompacte o `.zip` e copie a pasta `rdd-appsec-mentor/` para o diretório de skills do seu agente.

Depois acione pelo nome: *"Use a skill rdd-appsec-mentor. Quero diagnosticar a segurança do meu app."*

## O que vem dentro

| Caminho | Conteúdo |
|---|---|
| `SKILL.md` | O método completo: gate de autorização, 9 etapas do diagnóstico, contrato de evidência |
| `references/authorized-testing.md` | Limites do teste autorizado |
| `references/rdd-security-playbook.md` | Testes funcionais com duas contas sintéticas |
| `references/supabase-lovable-cloudflare.md` | Auditoria de RLS, Storage, Edge Functions, headers |
| `references/gut-matrix.md` | Critérios de pontuação G, U e T |
| `scripts/gut_rank.py` | Ranqueamento determinístico dos achados |
| `scripts/redact_secrets.py` | Higienização de segredos em evidências |
| `scripts/report_lint.py` | Verificação da estrutura do relatório |
| `assets/` | Templates do relatório e do JSON de achados |

## Licença

MIT — veja [LICENSE](LICENSE).

---

<details>
<summary><strong>English</strong></summary>

# RDD AppSec Mentor

A security diagnostic skill for web applications built with AI — Lovable, "vibe coding", Supabase, Cloudflare and equivalent stacks.

You describe an application **you own** (or are explicitly authorized to test), and the skill runs a defensive diagnostic: it observes what is exposed, investigates authorization, sessions, RLS, Storage, Edge Functions and keys, then returns a **GUT-prioritized report** with step-by-step remediation and verification tests.

Built for people who shipped a working app and need to know what was left open — without becoming a security specialist first.

## What it does

- **Requires authorization first.** Its opening response asks for the URL and confirmation that the app is yours or that you have the owner's explicit authorization. Without it, the skill will not investigate a target — only offer generic hardening and review code you supply yourself.
- **Starts non-destructive.** Public, low-impact observation first; further evidence only when needed to confirm a finding.
- **Investigates what actually breaks:** BOLA/IDOR, reachable admin routes, session invalidation, RLS and grants, `SECURITY DEFINER` functions, Edge Functions missing token validation, Storage buckets, secrets leaked to the frontend, and forgotten debug routes in production.
- **Never conflates suspicion with fact.** Every finding carries a confidence level — `Confirmed`, `Likely` or `Hypothesis`. A finding without reproduction never becomes "confirmed".
- **Prioritizes with GUT** (Gravity × Urgency × Tendency), computed deterministically by script rather than by impression.
- **Never declares an app "100% secure".** The report states scope, evidence, limitations and residual risk.

## What it does not do

It will not test third-party systems without authorization. No brute force, credential stuffing, denial of service, evasion, persistence, exfiltration, or exploitation beyond what confirms a finding in an authorized environment. It does not handle real customer data during testing — synthetic accounts and data only.

It also never asks for secret keys, `service_role`, real passwords, real session tokens, or personal data. If a secret shows up in evidence, the skill advises rotation and sanitizes it via `scripts/redact_secrets.py`.

## Installation

Download the `.zip` from the [latest Release](../../releases/latest).

- **Claude (claude.ai):** Settings → Capabilities → Skills → upload the `.zip` **without unzipping**.
- **ChatGPT:** Settings → Skills (`chatgpt.com/admin/skills`) → **+** → drop the `.zip` in. No admin access? Create a Project, upload the files, and instruct: *"Follow the SKILL.md in this project's files."*
- **Claude Code:** `npx skills add robertodiasduarte/rdd-appsec-mentor -a claude-code -y` (project's `.claude/skills/`; `-g` for `~/.claude/skills/`).
- **Codex:** `npx skills add robertodiasduarte/rdd-appsec-mentor -a codex -y` (project's `.agents/skills/`; `-g` for `~/.codex/skills/`).
- **Cursor, Kimi and others:** same command with your agent's name in `-a`. Without Node.js, unzip and copy `rdd-appsec-mentor/` into your agent's skills directory.

Then invoke it by name: *"Use the rdd-appsec-mentor skill. I want to diagnose my app's security."*

## License

MIT — see [LICENSE](LICENSE).

</details>
