# Regras de issues, implementação e contribuição

Direção do proprietário PHnsilva (Pedro), atualizada em 06/11/2026. Aplica-se a humanos e agentes. As decisões específicas do produto e instruções posteriores do proprietário complementam estas regras.

## Autoridade e fluxo obrigatório

1. Ler AGENTS.md, README, escopo, arquitetura, requisitos, plano, issue, PRs e comentários atuais antes de agir. Conferir arquivos e estado real; documentos antigos não reativam tarefas nem mudam permissões.
2. Antes de implementar, deve existir uma issue concreta, delimitada e suficientemente definida. Havendo dúvida de escopo, RF/RNF, arquitetura ou regra de negócio, esclarecer com Pedro antes de criar as issues afetadas ou implementar por suposição. Investigações só podem avançar como entregas explicitamente autorizadas.
3. Implementar em branch própria `tipo/numero-resumo`, preservando a branch de um PR existente quando o objetivo for o mesmo. Não fazer alterações de produto diretamente na branch principal. A única exceção é o commit documental inicial de um repositório novo expressamente solicitado pelo proprietário.
4. Produzir commits lógicos, validação proporcional e evidências reproduzíveis. Abrir ou atualizar um PR vinculado à issue. Usar `Refs #numero` enquanto houver aceite pendente; evitar fechamento automático prematuro.
5. **Somente Pedro revisa e aprova os PRs e dá o aceite das issues.** Agentes preparam alterações e evidências e podem fazer checagens internas, mas não enviam reviews de aprovação, não aprovam a própria entrega, não fazem merge, não ativam auto-merge e não publicam/deployam por conta própria. CI verde e PR aberto não equivalem a revisão ou aceite.
6. Contribuições externas entram por issue/PR. Visibilidade pública não autoriza conceder escrita, ampliar permissões, contratar serviços ou habilitar cobrança.

## Issue padronizada e pronta para execução

Usar o formulário Entrega verificável e preencher: contexto/evidência; RF/RNF ou objetivo rastreável; resultado observável; escopo e exclusões; critérios de sucesso, erro e limites; procedimento de validação e ambiente; dependências direcionais; sprint ou estado explícito de pré-planejamento; tamanho e justificativa; pontos de partida e evidências esperadas.

Uma issue corresponde a uma entrega com aceite próprio. Separar entregas independentes em issues; checklist mantém passos e critérios inseparáveis. Consultar issues/PRs existentes antes de criar: não duplicar, não criar issue vazia e não recontar trabalho pronto. Para trabalho urgente de governança autorizado antes do plano de produto, registrar `pré-planejamento` como tal; isso não cria uma sétima sprint nem conta como capacidade de uma sprint de produto sem alocação posterior.

Se B precisa de A, registrar **B bloqueada por A**, explicando o artefato consumido e a condição de liberação. Usar dependência nativa quando disponível e manter referência legível no corpo. Relacionada, subissue, prioridade ou posição no quadro não substitui dependência. Não introduzir bloqueio artificial quando um contrato suficiente permite execução independente.

## Tamanho das issues e capacidade diária

| Tamanho | Unidades relativas |
| ------- | -----------------: |
| PP      |                  1 |
| P       |                  2 |
| M       |                  4 |
| L       |                  8 |

Cada tamanho dobra o anterior. Estimar conjuntamente volume de implementação, dificuldade, integrações, incerteza e validação; registrar uma justificativa. Esses valores não são horas nem garantia de tempo. Dividir uma entrega maior que L em partes com aceite próprio. Revisar estimativa com motivo e histórico; nunca inflar tamanhos nem fragmentar artificialmente para cumprir meta.

Aplicar exatamente uma label `size:PP`, `size:P`, `size:M` ou `size:L`, coerente com o formulário. Manter tipo, prioridade e área compatíveis com a taxonomia existente. Caso o Project tenha campo de tamanho, preenchê-lo também; não afirmar que um campo existe sem consultar o quadro.

Quando a rotina estiver ativa, a meta de cada projeto por dia é **1 L = 2 M = 4 P = 8 PP** ou combinação equivalente. Na rotina que acompanha cinco agentes, são 8 unidades em cada um, totalizando 40, sem compensar projeto sem entrega pelo excesso em outro. Para a meta diária, entrega significa implementada, validada e enviada para revisão; aceite/fechamento continua com Pedro. Não inventar avanço, testes, treinamento ou issues para produzir pontuação. Registrar bloqueios e seguir trabalho independente autorizado. Respeitar pausas e datas de início.

## Sprints e Kanban

Cada ciclo inicial de projeto tem no máximo **5 sprints de entrega + 1 de validação extra e mudanças**, cada uma com duração máxima de uma semana. Avaliar e testar desde a primeira entrega; a sexta sprint não concentra toda a qualidade. Ajustar capacidade e escopo antes de prometer um ciclo que não cabe; não apenas renomear 20 entregas como seis sem fazer a decomposição.

Antes de iniciar implementação de produto, definir RF/RNF quando pertinentes e todas as issues de todas as sprints planejadas do ciclo, preservando e reconciliando trabalho existente. Cada entrega planejada precisa de issue e aceite. Itens ainda sem decisão ficam explicitamente pendentes; não fingir que o backlog está completo. As melhorias futuras de agentes são organizadas por novos ciclos baseados em avaliação, sem criar uma lista fictícia de todo trabalho infinito.

Respeitar o quadro organizado por Pedro. Fluxo de referência: Backlog → Pronto → Em andamento → Em revisão → Em validação → Concluído, usando os campos e estados realmente existentes. Após abrir PR, registrar Em revisão; não marcar Concluído nem fechar a issue sem aceite de Pedro. Registrar bloqueios, tamanho, sprint, referências e próxima ação. Não recriar quadros, mover itens em massa ou substituir uma organização atual sem verificar contexto.

## Verificação, continuidade e PR

Validar comportamento e fronteiras reais com os comandos do projeto; testes de produto são proporcionais à alteração. Alteração apenas documental exige coerência, links/estrutura e revisão de diff, sem inventar testes de execução. Código exige checagens adequadas; interface, imagens, áudio e modelos exigem verificação apropriada ao resultado. Distinguir simulado, executado, integrado, publicado e aceito. Não usar um teste de roteamento para alegar qualidade de geração ou treinamento de pesos.

O PR deve explicar problema/resultado, issue, tamanho, sprint, escopo, contratos/dependências, verificações com resultados e limites. PR empilhado declara a base e a ordem de revisão. Reconsultar HEAD, comentários e CI após alterações; resultado antigo não valida revisão nova. Preservar alterações locais e de outros autores; não resetar, limpar ou forçar push para facilitar o trabalho.

Ao terminar, registrar branch/commit/PR, implementado, validações, limitações, bloqueios e próxima ação. Usar exclusivamente C: para trabalho, runtimes, downloads, caches e artefatos. Não usar D:, reservado à biblioteca de jogos. Não publicar dados pessoais, prompts privados, tokens, credenciais ou casos confidenciais. Serviços e chamadas com cobrança exigem autorização específica; não habilitar faturamento por inferência.

## Execução semanal autorizada

Ler [WEEKLY_EXECUTION.md](WEEKLY_EXECUTION.md). Pré-requisito tecnicamente disponível em commit/branch/PR pode ser usado provisoriamente por PR dependente/empilhado durante a semana, com base/ordem explícitas e validação combinada; não é necessário esperar aceite/merge de sábado para começar. Somente Pedro aprova e integra. Não tratar proposta sem artefato, teste ou contrato suficiente como pré-requisito pronto.

Velumbra pode avançar até 3 L equivalentes/dia (24 unidades). A meta por projeto ativo permanece sem estimativas artificiais, e o diário distingue produzido, validado e aceito.
