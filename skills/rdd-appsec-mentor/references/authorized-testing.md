# Teste autorizado e limites operacionais

## Objetivo

Permitir investigação defensiva suficiente para encontrar falhas em aplicações próprias ou formalmente autorizadas sem ampliar desnecessariamente o risco do teste.

## Gate obrigatório

Antes de qualquer teste do alvo, obter:

1. URL.
2. Confirmação de propriedade ou autorização explícita.
3. Ambiente: produção, staging ou desenvolvimento.
4. Restrições conhecidas de horário, volume ou dados.

Se a autorização não for confirmada, não investigar o alvo.

## Princípios

- Preferir staging.
- Usar duas contas sintéticas e dados fictícios.
- Reproduzir apenas o mínimo necessário para confirmar o problema.
- Evitar alterações destrutivas.
- Não usar força bruta, credential stuffing, DoS, scraping volumoso, bypass de pagamento, persistência ou exfiltração.
- Não acessar dados reais de outro cliente "só para provar".
- Se um teste puder escrever dados, criar um registro sintético claramente identificável e removê-lo apenas se isso fizer parte do escopo aprovado.
- Preservar logs antes de alterar uma configuração quando houver suspeita de incidente.

## Evidência mínima

Uma evidência boa responde:

- O que foi testado?
- Com qual conta sintética?
- Qual era o resultado esperado?
- Qual foi o resultado observado?
- Qual componente causou o comportamento?
- O teste pode ser repetido depois da correção?

Evitar publicar tokens, cookies, segredos, CPFs, e-mails reais, nomes de clientes ou payloads completos.

## Stop conditions

Parar e pedir orientação do responsável quando:

- o teste começa a retornar dados reais não esperados;
- a aplicação degrada ou apresenta aumento de erros;
- uma ação pode alterar muitos registros;
- o escopo não cobre o componente descoberto;
- há indício de comprometimento ativo e a preservação de evidência passa a ser prioridade.

## Nota

Esta Skill trata autorização como requisito operacional e ético. Questões jurídicas específicas dependem do caso e da jurisdição; quando necessário, o aluno deve consultar orientação jurídica apropriada.
