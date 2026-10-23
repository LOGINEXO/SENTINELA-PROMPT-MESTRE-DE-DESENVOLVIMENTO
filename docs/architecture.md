# Arquitetura do Sentinela

## Etapa atual: Fundação

A Etapa 1 estabelece a estrutura do repositório, o pacote Python, o CLI, a configuração de exemplo, a validação local da configuração, a documentação e os testes básicos. O CLI não realiza requisições de rede nem executa verificações em ativos.

## Módulos planejados por etapa

- Etapa 2 — inteligência pública: ingestão de avisos e vulnerabilidades de fontes públicas.
- Etapa 3 — relatórios locais: formato comum, sanitização e exportação.
- Etapa 4 — auditoria passiva: verificações HTTPS, TLS e cabeçalhos em ativos autorizados.
- Etapa 5 — controle de escopo: validação de destinos, SSRF, DNS rebinding e redirecionamentos.
- Etapa 6 — interface PHP: painel e integração segura com o motor Python.
- Etapa 7 — execução: fila controlada e estados PLAY/PAUSE/STOP.
- Etapa 8 — e-mails: rascunhos revisáveis e provedores configuráveis.
- Etapa 9 — testes ativos: somente verificações não destrutivas em ambientes autorizados.
- Etapa 10 — publicação: revisão de segurança e preparação para distribuição.

Esses módulos não são considerados implementados apenas por estarem descritos nesta arquitetura.

## Separação de responsabilidades

A inteligência pública, a auditoria autorizada, a validação, os relatórios e a execução serão componentes separados. A descoberta de uma vulnerabilidade pública nunca autoriza automaticamente testar os domínios potencialmente afetados.

## Configuração e dados

Os exemplos não contêm credenciais. Configurações privadas, listas reais de autorização, bancos locais e relatórios devem permanecer fora do controle de versão. Relatórios devem ficar fora da raiz pública do servidor web.

## Dependências

A fundação usa a biblioteca padrão do Python. pytest é dependência de desenvolvimento/teste. Dependências de rede e outras bibliotecas só devem ser adicionadas quando uma etapa exigir seu uso e os motivos forem documentados.
