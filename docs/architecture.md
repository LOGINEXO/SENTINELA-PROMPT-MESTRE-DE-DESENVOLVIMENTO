# Arquitetura do Sentinela

## Etapa atual: Inteligência pública (Etapa 2 em validação)

A Etapa 1 estabeleceu a estrutura do repositório, o pacote Python, CLI, configuração local, documentação, testes básicos e CI. O GitHub Actions confirmou sucesso para a fundação.

A Etapa 2 acrescenta um cliente explícito para a API NVD CVE 2.0, normalização de resultados, tratamento de falhas HTTP/rede/JSON e testes simulados. O cliente consulta somente a API pública da NVD. Ele não acessa domínios descritos nos registros e não executa testes em ativos.

## Módulos planejados por etapa

- Etapa 1 — Fundação: concluída e validada.
- Etapa 2 — Inteligência pública: cliente NVD/CVE, normalização, tratamento de erros e testes simulados.
- Etapa 3 — Relatórios locais: formato comum, sanitização e exportação.
- Etapa 4 — Auditoria passiva: verificações HTTPS, TLS e cabeçalhos em ativos autorizados.
- Etapa 5 — Controle de escopo: validação de destinos, SSRF, DNS rebinding e redirecionamentos.
- Etapa 6 — Interface PHP: painel e integração segura com o motor Python.
- Etapa 7 — Execução: fila controlada e estados PLAY/PAUSE/STOP.
- Etapa 8 — E-mails: rascunhos revisáveis e provedores configuráveis.
- Etapa 9 — Testes ativos: somente verificações não destrutivas em ambientes autorizados.
- Etapa 10 — Publicação: revisão de segurança e preparação para distribuição.

Esses módulos não são considerados implementados apenas por estarem descritos nesta arquitetura.

## Inteligência pública e interpretação

A API NVD é a fonte de dados desta etapa. As consultas são iniciadas explicitamente pelo usuário via CLI; não há polling em segundo plano. A chave NVD_API_KEY é opcional e deve ser fornecida pelo ambiente, nunca pelo código versionado. O cliente aplica timeout, limite de até 100 resultados por consulta, deduplicação por CVE ID e mensagens de erro específicas.

Os registros normalizados incluem identificador, fonte, datas, estado, descrição, CVSS quando disponível, critérios/produtos afetados, intervalos de versão e referências. Todo registro começa como new_public_indicator, com asset_confirmed: false. A existência de um CVE não significa que um domínio específico esteja vulnerável.

## Separação de responsabilidades

A inteligência pública, a auditoria autorizada, a validação, os relatórios e a execução serão componentes separados. A descoberta de uma vulnerabilidade pública nunca autoriza automaticamente testar os domínios potencialmente afetados.

## Configuração e dados

Os exemplos não contêm credenciais. Configurações privadas, listas reais de autorização, bancos locais e relatórios devem permanecer fora do controle de versão. Relatórios devem ficar fora da raiz pública do servidor web.

## Dependências

A fundação e o cliente NVD usam a biblioteca padrão do Python. pytest é dependência de desenvolvimento/teste. Não foi adicionada dependência de runtime para esta etapa.
