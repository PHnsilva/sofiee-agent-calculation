# Ambiente local de Cálculo

Inventário em 09/11/2026, antes de instalar dependências. Coleta local no Windows 11 Pro, build 26200; nenhum nome de usuário, nome de máquina ou identificador exclusivo foi registrado.

| Recurso | Resultado observado |
| --- | --- |
| CPU | Win32_Processor reportou Intel Core i3-10100F, 4 núcleos/8 threads, 3.60 GHz |
| RAM | Win32_ComputerSystem reportou 15.9 GiB de memória física total |
| GPU | Win32_VideoController reportou AMD Radeon RX 580 2048SP e 4095 MiB de memória do adaptador |
| Python escolhido para as ferramentas S1 | CPython 3.13.15 em C:\SDKs\Python313; licença local LICENSE.txt, PSF-2.0 |
| Dependências de terceiros | Nenhuma selecionada para esta etapa; requirements.lock permanece sem pacotes |
| Ferramentas não escolhidas para este projeto | Node 24.19.0/npm 11.17.0; o plano do agente escolhe Python |

O inventário de GPU não demonstra capacidade para um modelo específico. Nenhum modelo foi baixado ou executado. O runtime, a licença e o lock cobrem os verificadores de fixtures atuais; seleção do SDK MCP e de ferramentas de domínio fica para as issues de implementação correspondentes, após critério de necessidade e compatibilidade. Não instalar um pacote antecipadamente não equivale a validar essas integrações.

## Criar e verificar um ambiente limpo

Use o interpretador instalado em C: e o caminho de ambiente abaixo, também em C:. Crie o venv sem pip porque o lock não tem dependências externas:

    C:\SDKs\Python313\python.exe -m venv --without-pip C:\DevData\Codex\agents\venvs\sofiee-agent-calculation-py313-20261109
    C:\DevData\Codex\agents\venvs\sofiee-agent-calculation-py313-20261109\Scripts\python.exe scripts\check_environment.py

O verificador exige CPython 3.13.15, prefixos no C:, arquivo de licença presente, lock coerente e nenhuma dependência externa. Em caso de ausência ou versão incompatível, ele encerra com erro antes de qualquer instalação. Não há etapa de rede.

## Limites

Este é um ambiente limpo para validação estrutural e fixtures. Não comprova servidor MCP, modelo, voz/áudio, conectores ou capacidade de produção. O lock de dependências permanecerá vazio até uma issue selecionar e justificar as bibliotecas necessárias e suas licenças.
