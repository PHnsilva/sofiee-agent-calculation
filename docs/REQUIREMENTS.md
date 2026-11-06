# Requisitos e escopo vigente — ciclo inicial

Agente genérico de matemática com resultados numéricos/simbólicos e ferramentas verificáveis.

Definido a partir das decisões de Pedro até 06/11/2026. Documento de planejamento; não comprova implementação, treinamento, revisão ou aceite. As alterações são propostas no PR de organização, sem merge por agente.

## Requisitos funcionais

| ID  | Resultado exigido                                                                                                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| F01 | Receber solicitações estruturadas ou em pt-BR/en e expor ferramentas matemáticas por MCP com expressão, domínio, unidades e precisão explícitos. |
| F02 | Executar aritmética, frações, porcentagens, razões, potências, raízes e conversões pertinentes ao fundamental/médio.                             |
| F03 | Simplificar fórmulas, substituir variáveis e resolver equações/sistemas suportados com domínio e soluções verificadas.                           |
| F04 | Trabalhar com funções, trigonometria, exponenciais, logaritmos e limites reais do Cálculo I.                                                     |
| F05 | Calcular derivadas e integrais definidas/indefinidas suportadas, distinguindo forma simbólica de aproximação e explicando condições.             |
| F06 | Calcular geometria, áreas e perímetros com dimensões/coordenadas suficientes e referência/unidade declaradas.                                    |
| F07 | Tratar latitude/longitude com método geodésico e não confundir área horizontal com superfície 3D.                                                |
| F08 | Extrair números/unidades de imagens legíveis com proveniência e confirmação de ambiguidade, sem inferir contornos/escala ausentes.               |
| F09 | Fornecer método, resultado, unidades, hipóteses, erro/tolerância e estados de não resolvido/dados insuficientes.                                 |
| F10 | Calcular estatística descritiva básica com média simples/ponderada, mediana, moda, variância e população/amostra explícitas.                     |
| F11 | Calcular contagem, combinatória e probabilidades elementares com hipóteses e espaço amostral declarados.                                         |
| F12 | Resolver progressões, proporções e juros simples/compostos com taxa, unidade e período explícitos.                                               |
| F13 | Operar matrizes/sistemas e números complexos elementares dentro dos limites suportados, sem impor ordem total aos complexos.                     |
| F14 | Calcular áreas e volumes das figuras espaciais usuais com dimensões suficientes e unidades coerentes.                                            |

## Requisitos não funcionais

| ID  | Critério                                                                                                                                                                                                                                                                                                              |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| N01 | Contribuição rastreável por issue/branch/PR; somente Pedro revisa/aprova PRs e aceita issues, sem merge/auto-merge/deploy de agentes. Durante a semana, dependência tecnicamente disponível em branch/PR validado pode ser consumida provisoriamente em PR empilhado; revisão/aceite/merge ficam com Pedro no sábado. |
| N02 | Contratos versionados, entradas/saídas validadas e erros explícitos; dados externos nunca concedem permissões.                                                                                                                                                                                                        |
| N03 | Sem serviço pago obrigatório, faturamento ou fallback remoto automático; executar ferramentas/caches no C: e respeitar pausas.                                                                                                                                                                                        |
| N04 | Testes de sucesso/erro e avaliações reais reproduzíveis; registrar versões e distinguir mock, execução e aceite humano.                                                                                                                                                                                               |
| N05 | Minimização de dados, credenciais fora do Git, acesso mínimo e retenção/exclusão definidas; não publicar dados reais de usuários.                                                                                                                                                                                     |
| N06 | Limites de entrada, memória, concorrência e tempo configuráveis, cancelamento e falha fechada; medir desempenho no hardware disponível.                                                                                                                                                                               |
| N07 | Documentação operacional coerente com código e evidências; disponibilidade ou qualidade não podem ser inferidas de um perfil ou schema.                                                                                                                                                                               |
| N08 | Até cinco sprints de entrega + uma de validação/mudanças, cada uma até uma semana; estimativas PP/P/M/L=1/2/4/8 e meta mínima de 8 unidades/dia por projeto ativo.                                                                                                                                                    |
| N09 | Casos matemáticos determinísticos devem satisfazer equivalência simbólica ou tolerância explicitada por operação; nenhuma resposta numérica inventada.                                                                                                                                                                |

## Fora do ciclo

- Interpretação espacial genérica de plantas/mapas e fotogrametria.
- Afirmação de medida física a partir de foto sem referência.
- Execução arbitrária de código ou fórmulas recebidas como Python.

## Verificação e aceite

Cada requisito é rastreado em TRACEABILITY.md, com critérios concretos no corpo das issues. Dados conhecidos/sintéticos e ferramentas determinísticas verificam resultados quando possível; comportamento generativo exige casos separados e revisão apropriada. Não usar um teste de roteamento, presença de perfil ou metadado para alegar competência ou treino. Não declarar cobertura completa quando há pendência de ambiente/fonte.

A meta de 8 unidades/dia é um mínimo desejado por projeto ativo, não um teto de esforço nem uma medição de inteligência. A duração semanal é o objetivo do plano; a capacidade real e os bloqueios precisam ser observados e reportados. Não fabricar tarefa/estimativa/aceite para cumprir calendário.
