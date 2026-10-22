# Arquitetura inicial

## Limites da Etapa 1

O pacote Python sentinela/ contém apenas a fundação e um CLI sem atividade de rede. A aplicação web PHP, a fila, os provedores de inteligência e os scanners não fazem parte desta etapa.

## Separação planejada

- Inteligência pública: ingestão de avisos e vulnerabilidades de fontes públicas.
- Auditoria autorizada: verificações passivas e, futuramente, testes ativos explicitamente autorizados.
- Validação: normalização, classificação e estado de confiança dos achados.
- Relatórios: exportação local com minimização e sanitização de evidências.
- Interface e execução: integração futura com controle de tarefas e limites de execução.

A descoberta de uma vulnerabilidade pública nunca autoriza automaticamente testar os domínios potencialmente afetados.

## Configuração e dados

Os exemplos de configuração não contêm credenciais. Dados locais, relatórios, bancos e arquivos de autorização reais devem ficar fora do controle de versão.
