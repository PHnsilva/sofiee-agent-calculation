# Contratos de cálculo — v1.3.0

`contracts.json` define schemas fechados para operações aritméticas, simbólicas, conversão de unidades, estatística descritiva, combinatória e probabilidade finita. A versão 1.3.0 acrescenta `calculation.combinatorics` e `calculation.probability`; v1.2.0 acrescentou `calculation.statistics`. Cada número decimal usa somente um separador; agrupamento de milhares não é aceito.

| Ferramenta | Escopo do contrato |
| --- | --- |
| `calculation.evaluate` | Operações numéricas fechadas com operandos inteiros, decimais ou frações racionais, domínio e precisão declarados |
| `calculation.symbolic` | Simplificação, substituição, solução, limites, derivadas e integrais sobre expressão matemática |
| `calculation.convertUnits` | Conversão dimensional com quantidade, unidade de origem/destino e casas decimais |
| `calculation.statistics` | Média, média ponderada, mediana, moda e variância populacional/amostral em dados numéricos exatos |
| `calculation.combinatorics` | Permutação, arranjo e combinação com ordem e repetição explícitas |
| `calculation.probability` | Probabilidade exata em espaço finito equiprovável e probabilidade condicional com contagens declaradas |

## Estatística descritiva

Valores e pesos são strings numéricas decimais ou frações racionais. A média ponderada requer um peso não negativo por observação e soma dos pesos positiva; os pesos são normalizados pela soma e não precisam somar um. Variância populacional usa divisor `n`; variância amostral usa `n−1` e exige ao menos duas observações. A unidade da variância é representada como `(unidade)²`.

Conjunto vazio retorna `insufficient_data`. Dados fora da gramática numérica, pesos negativos, contagem de pesos divergente ou soma de pesos zero retornam `invalid_request`. A moda retorna todas as observações empatadas na maior frequência, ordenadas numericamente; quando todos os valores são distintos, cada valor é retornado como moda segundo essa convenção. A propriedade `modes` carrega esse conjunto; operações escalares usam `value`.

Precisão exata retorna frações reduzidas. Precisão decimal usa arredondamento half-even e informa um limite de erro para resultados aproximados. A operação e o método identificam a convenção aplicada; saídas não alegam avaliação de modelo.

## Combinatória e probabilidade

`calculation.combinatorics` recebe `itemCount` entre 0 e 1.000. Permutação assume itens distintos, salvo se `multiplicities` declarar as frequências de itens indistinguíveis; nesse caso usa `n! / ∏(frequência!)`. Arranjo exige `selectionCount` e `allowRepetition`: sem repetição usa `n!/(n-r)!`, com repetição usa `n^r`; a ordem importa. Combinação também exige esses parâmetros: sem repetição usa `C(n,r)`, com repetição usa `C(n+r-1,r)`; a ordem não importa. `selectionCount` também está limitado a 1.000. A seleção de zero itens tem uma possibilidade; selecionar mais itens distintos do que existem sem repetição resulta em zero. Contagens acima de 1.000 caracteres retornam `unsupported` sem truncamento.

`calculation.probability` exige contagem favorável, tamanho positivo do espaço amostral (ambos de no máximo 1.000.000) e declaração `sampleSpaceModel: equiprobable`. Não estima distribuições contínuas, espaços não equiprováveis ou probabilidades sem esse espaço explícito. A operação condicional também exige a contagem do evento condicionante, da interseção e uma declaração `independent` ou `dependent`. Para independência, o runtime verifica a consistência exata das contagens declaradas; para dependência, calcula `|A∩B|/|B|`. Condicionar a um evento sem ocorrências retorna `ambiguous`; contagens incompatíveis com o espaço ou com a hipótese retornam `invalid_request`.

## Erros e limites

Resultados distinguem exato, aproximado, dados insuficientes e operação não suportada. Erros têm códigos explícitos. Entradas e resultados estatísticos estão limitados a 1.000 observações e aos limites de tamanho do contrato. A aritmética determinística usa frações racionais e falha de modo explícito se a representação ou o resultado exceder os limites.

Os parâmetros não aceitam código Python nem selecionam executáveis. Operações simbólicas usam gramática matemática restrita; schema válido não significa que toda operação simbólica está implementada ou correta.

## Validação

Cada ferramenta inclui exemplos válidos/inválidos, resultado e erro. `python scripts/validate_contracts.py` confere os exemplos com um subconjunto local de JSON Schema; não é um validador completo nem uma prova matemática. A suíte de comportamento cobre resultados, fronteiras e limites. A interface MCP stdio publica os schemas do contrato e foi exercitada por cliente local nos testes.

Versões incompatíveis exigem migração explícita. Nenhuma inferência ou treinamento de modelo é necessária para as operações determinísticas deste contrato.
