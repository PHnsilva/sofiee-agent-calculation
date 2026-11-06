# Execução semanal por dependências e revisão de sábado

Regra explícita de Pedro em 06/11/2026: organizar por dependências sem paralisar a implementação durante a semana por esperar revisão/merge. Pedro revisa os PRs e integra no sábado; agentes não aprovam nem fazem merge. A revisão ainda pode exigir correções — não pressupor que todo PR será aceito.

## Dependência técnica não é espera automática por fechamento da issue

- Antes de iniciar B, identificar exatamente o artefato de A necessário: schema, decisão dentro do escopo aprovado, implementação, fixture ou ferramenta. Uma seta nativa é rastreabilidade técnica, não exigência de que A esteja fechada para qualquer trabalho em B.
- Se o artefato necessário já está disponível num commit/branch/PR e tem validação técnica suficiente, o proprietário autorizou consumi-lo **provisoriamente**. Registrar SHA, limitações, testes e o vínculo; não dizer que foi revisado, integrado ou aceito.
- B usa a branch de A como base quando precisa do código ainda não integrado; C pode usar B. Declarar a cadeia A → B → C, bases e ordem de integração no corpo de cada PR. Testar a árvore combinada e atualizar as evidências no HEAD atual.
- Não consumir uma promessa, um schema ainda indefinido ou um mock como se fosse implementação real. Preparar partes independentes contra um contrato explícito, distinguindo teste de contrato de homologação.
- Mudança de requisito/regra de negócio não aprovada continua exigindo esclarecimento com Pedro. Essa regra não concede acesso externo, não autoriza custo, não libera produção e não equivale a aceite antecipado.

## Fila para a semana

Ler a DAG e preparar uma sequência com pré-requisitos fornecidos cedo, mais uma reserva independente. Não usar o número da issue como ordem. Sprints podem terminar antes de sete dias e a próxima pode começar; não aguardar uma semana artificialmente quando há trabalho pronto.

Ao selecionar a fila diária, conferir para cada item: artefato disponível e SHA, ambiente, contrato, validação possível e dependência externa. Separar implementação local de homologação em conta/dispositivo/fonte quando tiverem aceites distintos. Se faltar Mac, credencial, acesso da fonte, quota ou modelo útil, registrar a condição externa e escolher outra issue independente realmente executável. Não contornar controle de acesso nem fingir teste real para cumprir meta.

O quadro conserva estados do proprietário e registra `Bloqueio` e `Base técnica`. Itens em revisão podem fornecer artefatos provisórios; o agente deve verificar o que o PR efetivamente entrega, pois nem todo PR é completo. Não marcar issue como concluída só para remover um ícone de dependência.

## Preparar sábado

Entregar PRs coerentes e encadeados quando necessário, com bases/ordem, escopo, issues/tamanhos, comandos/resultados, evidências e limitações. Reconferir conflitos e CI dos HEADs atuais antes da revisão. Preservar branches/autoria; não usar force push, reset ou descarte de trabalho para ocultar conflitos.

Somente Pedro revisa, aprova e integra. Depois de sua decisão, alinhar bases e próximas entregas, corrigir regressões e manter rastreabilidade. PR reprovado ou requisito não atendido não pode ser contabilizado como aceito.

## Cadência

Nos projetos ativos, meta mínima de 1 L equivalente/dia (PP=1, P=2, M=4, L=8). Nos cinco agentes, vale para cada projeto, totalizando 40 unidades. Velumbra está autorizado a avançar **até 3 L equivalentes/dia (24 unidades)**, mantendo validação, estimativas honestas e prioridade de terminar mais cedo. Isso não muda automaticamente o modelo/esforço configurado e não garante produtividade medida.

Sofiee segue pausado até 21/11/2026; SlothGeo é separado e só começa em 21/11. Nenhuma dessas regras reativa rotinas ou antecipa implementação adiada.
