# Contratos de cálculo — v1.2.0

`contracts.json` define schemas fechados para operações aritméticas, simbólicas, conversão de unidades e soma de grandezas. A versão 1.2.0 acrescenta soma dimensional e unidades de área; também mantém variação percentual e aceita ponto ou vírgula como único separador decimal em operandos e quantidades. Agrupamento de milhares não é aceito.

| Ferramenta | Escopo do contrato |
| --- | --- |
| `calculation.evaluate` | Operações numéricas fechadas com operandos inteiros, decimais ou frações racionais, domínio e precisão declarados |
| `calculation.symbolic` | Simplificação e substituição em polinômios racionais limitados; solução, limites, derivadas e integrais usam os limites descritos pela implementação |
| `calculation.convertUnits` | Conversão dimensional com quantidade, unidade de origem/destino e casas decimais |
| `calculation.addQuantities` | Soma exata de duas grandezas compatíveis, normalizadas para a unidade da primeira quantidade |

As conversões de área reconhecem `mm²`, `cm²`, `m²`, `ha` e `km²`. A soma conserva os valores e unidades originais, apresenta os termos normalizados como frações exatas e rejeita dimensões incompatíveis ou unidades fora da tabela suportada.

Resultados distinguem exato, aproximado, dados insuficientes, operação não suportada e ambiguidade; erros têm códigos explícitos para expressão inválida, domínio, divisão por zero e unidades incompatíveis. A variação percentual usa `(novo - antigo) / antigo × 100`; base antiga zero é indefinida e retorna ambiguidade. Precisão decimal usa arredondamento half-even e informa limite de erro quando o resultado é aproximado. A simplificação/substituição aceita somente números racionais, nomes, `+`, `-`, `*`, divisão por constante não nula e potências inteiras pequenas; há limites de símbolos, nós, grau, termos, coeficientes e tamanho do resultado. A árvore sintática é convertida por uma lista fechada de nós para o motor simbólico; nenhuma função de parsing que execute texto é usada. Substituir exige um valor para cada variável presente, sem aceitar duplicatas ou variáveis extras silenciosamente. O resultado não cobre restrições de domínio de expressões racionais com denominadores variáveis, que permanecem não suportadas. Não se afirma aqui cobertura de geometria, estatística ou inferência.

O runtime fixa SymPy 1.14.0 e mpmath 1.3.0 no lock. As versões e licenças declaradas pelos mantenedores estão em [PyPI: SymPy 1.14.0](https://pypi.org/project/sympy/1.14.0/) e [PyPI: mpmath 1.3.0](https://pypi.org/project/mpmath/1.3.0/); a faixa de dependência `mpmath >=1.1.0,<1.4` evita a versão 1.4.x, que não satisfaz o metadado do SymPy 1.14.0. O [parser do SymPy baseado em texto documenta uso de `eval`](https://docs.sympy.org/latest/modules/parsing.html); o runtime não usa `parse_expr` nem `sympify` para entrada de usuário.

## Exemplos e verificação

Cada ferramenta inclui exemplos válidos/inválidos, resultado e erro. O runtime determinístico e o CLI executam a aritmética contratada; a interface MCP permanece em entrega separada. Execute `C:/SDKs/Python313/python.exe scripts/validate_contracts.py` (ou `python scripts/validate_contracts.py` com Python 3.13 no `PATH`). O verificador usa só a biblioteca padrão para conferir exemplos e o subconjunto de keywords empregado; não é um validador completo do JSON Schema nem uma prova matemática. A suíte de comportamento cobre as operações e os limites implementados.

## Evolução

Versões incompatíveis exigem migração explícita. A implementação futura precisa validar os schemas no runtime Python/SDK escolhido, restringir e testar a gramática das expressões, comparar contas com resultados determinísticos, e declarar tolerâncias e limites observados.
