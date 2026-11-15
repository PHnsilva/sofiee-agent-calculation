# Contratos de cálculo — v1.1.0

`contracts.json` define schemas fechados para operações aritméticas, simbólicas e conversão de unidades. A versão 1.1.0 acrescenta variação percentual e aceita ponto ou vírgula como separador decimal em operandos e quantidades. Cada entrada usa somente um separador decimal; agrupamento de milhares não é aceito.

| Ferramenta | Escopo do contrato |
| --- | --- |
| `calculation.evaluate` | Operações numéricas fechadas com operandos inteiros, decimais ou frações racionais, domínio e precisão declarados |
| `calculation.symbolic` | Simplificação, substituição, solução, limites, derivadas e integrais sobre expressão matemática |
| `calculation.convertUnits` | Conversão dimensional com quantidade, unidade de origem/destino e casas decimais |

Resultados distinguem exato, aproximado, dados insuficientes, operação não suportada e ambiguidade; erros têm códigos explícitos para expressão inválida, domínio, divisão por zero e unidades incompatíveis. A variação percentual usa `(novo - antigo) / antigo × 100`; base antiga zero é indefinida e retorna ambiguidade. Precisão decimal usa arredondamento half-even e informa limite de erro quando o resultado é aproximado. Os parâmetros não aceitam fonte Python nem selecionam executáveis. Operações simbólicas usam gramática matemática restrita; schema válido não significa que toda operação está implementada ou correta. Não se afirma aqui cobertura de geometria, estatística ou inferência.

## Exemplos e verificação

Cada ferramenta inclui exemplos válidos/inválidos, resultado e erro. O runtime determinístico e o CLI executam a aritmética contratada; a interface MCP permanece em entrega separada. Execute `C:/SDKs/Python313/python.exe scripts/validate_contracts.py` (ou `python scripts/validate_contracts.py` com Python 3.13 no `PATH`). O verificador usa só a biblioteca padrão para conferir exemplos e o subconjunto de keywords empregado; não é um validador completo do JSON Schema nem uma prova matemática. A suíte de comportamento cobre as operações e os limites implementados.

## Evolução

Versões incompatíveis exigem migração explícita. A implementação futura precisa validar os schemas no runtime Python/SDK escolhido, restringir e testar a gramática das expressões, comparar contas com resultados determinísticos, e declarar tolerâncias e limites observados. Nenhuma dependência foi instalada ou selecionada nesta entrega.
