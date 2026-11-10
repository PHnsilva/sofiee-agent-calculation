<!-- BEGIN CURRENT PLAN 2026-11-06 -->

# sofiee-agent-calculation

Agente genérico de matemática com resultados numéricos/simbólicos e ferramentas verificáveis.

**Planejamento vigente em 06/11/2026: até 5 sprints de entrega + S6 de validação extra/mudanças.** As issues e a matriz documentam todo o ciclo; não comprovam implementação, treinamento, integração ou aceite. Preservar código e PRs existentes. Somente Pedro revisa/aprova PRs e aceita issues.

- [Requisitos e limites](docs/REQUIREMENTS.md)
- [Arquitetura e fronteiras](docs/ARCHITECTURE_PLAN.md)
- [Todas as sprints e issues](docs/DELIVERY_PLAN.md)
- [Rastreabilidade](docs/TRACEABILITY.md)
- [Execução semanal por dependências e PRs encadeados](docs/WEEKLY_EXECUTION.md)
- [Retomada diária](docs/EXECUTION_PLAN.md)
- [Contribuição](docs/CONTRIBUTION_POLICY.md)
- [Contratos MCP v1 — proposta da issue #5](contracts/v1/README.md)

Busca encontra fontes em qualquer lugar pertinente e preserva filtros do usuário; Validação escolhe a base adequada ao tipo de dado e verifica as referências independentemente. Não aplicar uma whitelist científica global ao Busca. O modelo pode ser compartilhado; as ferramentas e critérios de domínio são específicos.

Trabalho exclusivamente no C:, sem serviços pagos obrigatórios. SlothGeo é separado e adiado para 21/11, não um sexto agente desta rotina.
- Ambiente e versões locais: [inventário reproduzível](docs/LOCAL_ENVIRONMENT.md).
<!-- END CURRENT PLAN 2026-11-06 -->

<details>
<summary>Descrição anterior da base e propostas — consultar com o estado vivo dos PRs</summary>

# Sofiee — Agente de Cálculo

Cálculos necessários a sistemas e processos de empresas.

Projeto independente da linha Sofiee, criado a pedido de Pedro em 05/11/2026. Este commit inicial registra finalidade, limites e preparação para o planejamento. Ainda não existe runtime, modelo treinado, ferramenta MCP ou integração implementada.

## Planejamento pendente

Tipos de cálculo, precisão, unidades, entradas, saídas e critérios de correção. Casos de uso, contratos, avaliações, arquitetura, tecnologias e sprints serão definidos com Pedro no fim de semana. Consulte [o registro de escopo](docs/ESCOPO.md).

Depois dessa definição, todas as issues de todas as sprints planejadas devem ser criadas, com dependências e critérios de aceite. O formulário de issue já está disponível neste repositório.

## Portfólio

Este é um dos quatro agentes gerais: [comunicação](https://github.com/PHnsilva/sofiee-agent-communication), [cálculo](https://github.com/PHnsilva/sofiee-agent-calculation), [validação](https://github.com/PHnsilva/sofiee-agent-validation) e [busca](https://github.com/PHnsilva/sofiee-agent-search).

[SlothEngineer](https://github.com/PHnsilva/SlothEngineer) é um sistema separado, com direção inicial de especialização em DevOps. O chat **agents** acompanha os cinco projetos.

## Contribuições

O repositório é público para consulta e sugestões por issue ou PR. Mudanças posteriores ao bootstrap usam issue, branch e PR com evidências. Revisão e aceite são de Pedro.

</details>
