# Contratos de cálculo — v1.2.0

`contracts.json` define schemas fechados para operações aritméticas, simbólicas, conversão de unidades e estatística descritiva. A versão 1.2.0 acrescenta `calculation.statistics`; as versões anteriores adicionaram variação percentual e decimais com vírgula. Cada número usa somente um separador decimal; agrupamento de milhares não é aceito.

| Ferramenta | Escopo do contrato |
| --- | --- |
| `calculation.evaluate` | Operações numéricas fechadas com operandos inteiros, decimais ou frações racionais, domínio e precisão declarados |
| `calculation.symbolic` | Simplificação, substituição, solução, limites, derivadas e integrais sobre expressão matemática |
| `calculation.convertUnits` | Conversão dimensional com quantidade, unidade de origem/destino e casas decimais |
| `calculation.statistics` | Média, média ponderada, mediana, moda e variância populacional/amostral em dados numéricos exatos |

## Estatística descritiva

Valores e pesos são strings numéricas decimais ou frações racionais. A média ponderada requer um peso não negativo por observação e soma dos pesos positiva; os pesos são normalizados pela soma e não precisam somar um. Variância populacional usa divisor `n`; variância amostral usa `n−1` e exige ao menos duas observações. A unidade da variância é representada como `(unidade)²`.

Conjunto vazio retorna `insufficient_data`. Dados fora da gramática numérica, pesos negativos, contagem de pesos divergente ou soma de pesos zero retornam `invalid_request`. A moda retorna todas as observações empatadas na maior frequência, ordenadas numericamente; quando todos os valores são distintos, cada valor é retornado como moda segundo essa convenção. A propriedade `modes` carrega esse conjunto; operações escalares usam `value`.

Precisão exata retorna frações reduzidas. Precisão decimal usa arredondamento half-even e informa um limite de erro para resultados aproximados. A operação e o método identificam a convenção aplicada; saídas não alegam avaliação de modelo.

## Erros e limites

Resultados distinguem exato, aproximado, dados insuficientes e operação não suportada. Erros têm códigos explícitos. Entradas e resultados estatísticos estão limitados a 1.000 observações e aos limites de tamanho do contrato. A aritmética determinística usa frações racionais e falha de modo explícito se a representação ou o resultado exceder os limites.

Os parâmetros não aceitam código Python nem selecionam executáveis. Operações simbólicas usam gramática matemática restrita; schema válido não significa que toda operação simbólica está implementada ou correta.

## Validação

Cada ferramenta inclui exemplos válidos/inválidos, resultado e erro. `python scripts/validate_contracts.py` confere os exemplos com um subconjunto local de JSON Schema; não é um validador completo nem uma prova matemática. A suíte de comportamento cobre resultados, fronteiras e limites. A interface MCP stdio publica os schemas do contrato e foi exercitada por cliente local nos testes.

Versões incompatíveis exigem migração explícita. Nenhuma inferência ou treinamento de modelo é necessária para as operações determinísticas deste contrato.
