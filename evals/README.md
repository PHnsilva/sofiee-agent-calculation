# Casos e protocolo de avaliação — Cálculo

Os arquivos development/cases.json e regression/cases.json são conjuntos públicos, sintéticos e versionados v1.0.0. A rubrica cobre frações, porcentagem, conversão, solução simbólica, condições de integral e incompatibilidade dimensional. Os resultados aritméticos exatos marcados deterministicCheck são recalculados com fractions.Fraction; os cenários simbólicos permanecem critérios para uma ferramenta futura e exigirão revisão humana.

O compartimento reserve tem política v1.0.0 e fica sob custódia de Pedro, fora do repositório; ainda não foi populado. Nenhum dado privado foi criado ou publicado. A divisão evita usar os casos de regressão como conjunto secreto.

O verificador valida casos e cálculos determinísticos dos fixtures, não executa SymPy, ferramenta MCP, modelo ou baseline. Nenhum ganho de cálculo é alegado.

## Execução

Na raiz do repositório, execute scripts/validate_eval_cases.py com CPython 3.13.15. O programa valida versão, separação, cobertura de ferramentas, critérios e invariantes determinísticas aplicáveis. Um caso aprovado pelo validador de fixtures significa apenas que seus dados/rubricas são coerentes; não representa avaliação do agente, execução, baseline ou aceite humano.
