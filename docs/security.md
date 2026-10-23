# Política e controles de segurança

## Modelo de distribuição

O Sentinela é open source e local-first. Cada pessoa executa sua própria cópia no computador; não há login, contas, backend hospedado pelo projeto, sincronização ou armazenamento central de relatórios.

## Controles implementados

- Não adicionar tokens, senhas, chaves privadas, cookies ou configurações locais ao Git.
- A interface PHP aceita apenas loopback (`127.0.0.1` / `::1`) e rejeita cabeçalhos de proxy encaminhado.
- Iniciar o servidor embutido PHP ligado a `127.0.0.1`; nunca usar `0.0.0.0`, proxy, túnel ou hospedagem pública.
- Banco SQLite, relatórios, rascunhos e escopos ficam em arquivos locais no computador do usuário.
- Não há conta de usuário, login, envio automático de e-mail ou sincronização de relatórios.
- Não tratar descoberta pública como autorização de teste.
- Auditoria passiva exige allowlist exata; verificação ativa exige allowlist separada e confirmação explícita.
- Toda requisição de auditoria valida escopo antes de DNS, bloqueia respostas DNS não públicas, fixa a conexão ao IP validado e mantém verificação TLS.
- Verificação ativa faz apenas um GET HTTPS para /, limita a leitura da resposta a 8192 bytes e não segue redirecionamentos.
- CI automatizado verifica testes Python e comportamento da interface local.

## Tráfego de rede

Consultas NVD acessam a API pública para recuperar dados; auditorias conectam-se aos ativos autorizados indicados pelo operador. Os relatórios e o histórico não são enviados a um servidor central do Sentinela.

## Limites

O Sentinela não foi projetado para hospedagem multiusuário. Não o disponibilize na internet nem em uma rede local como serviço compartilhado. Para uso por várias pessoas, cada pessoa deve instalar e executar sua própria cópia local.
