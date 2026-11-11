# Contratos MCP de cálculo — v1

`contracts.json` propõe schemas fechados para operações aritméticas, simbólicas e conversão de unidades. É a interface planejada da issue #5; ainda não há runtime, parser, motor matemático ou servidor MCP neste repositório.

| Ferramenta | Escopo do contrato |
| --- | --- |
| `calculation.evaluate` | Operações numéricas fechadas com operandos decimais, domínio e precisão declarados |
| `calculation.symbolic` | Simplificação, substituição, solução, limites, derivadas e integrais sobre expressão matemática |
| `calculation.convertUnits` | Conversão dimensional com quantidade, unidade de origem/destino e casas decimais |

Resultados distinguem exato, aproximado, dados insuficientes, operação não suportada e ambiguidade; os erros têm códigos explícitos para expressão inválida, domínio, divisão por zero e unidades incompatíveis. Os parâmetros não aceitam fonte Python nem selecionam executáveis. Operações simbólicas precisam de parser matemático restrito; schema válido não significa que a operação é implementada ou correta. Não se afirma aqui cobertura de geometria, estatística ou inferência.

## Exemplos e verificação

Cada ferramenta inclui exemplos válidos/inválidos, resultado e erro. Execute `C:/SDKs/Python313/python.exe scripts/validate_contracts.py` (ou `python scripts/validate_contracts.py` com Python 3.13 no `PATH`). O verificador usa só a biblioteca padrão para conferir os exemplos e o subconjunto de keywords empregado; não é um validador completo da especificação JSON Schema nem uma prova matemática.

## Evolução

Versões incompatíveis exigem migração explícita. A implementação futura precisa validar os schemas no runtime Python/SDK escolhido, restringir e testar a gramática das expressões, comparar contas com resultados determinísticos, e declarar tolerâncias e limites observados. Nenhuma dependência foi instalada ou selecionada nesta entrega.
