# Política e controles de segurança

## Controles implementados

- Não adicionar tokens, senhas, chaves privadas, cookies ou configurações locais ao Git.
- Painel PHP protegido por HTTP Basic Auth; falha fechada (HTTP 503) se as credenciais não estiverem configuradas ou a senha tiver menos de 16 caracteres.
- Exigir HTTPS/TLS para acesso remoto ao painel; limitar o servidor PHP embutido a loopback para desenvolvimento.
- Manter relatórios, banco SQLite, arquivos de escopo reais e arquivos de ambiente fora da raiz pública do servidor web.
- Não tratar descoberta pública como autorização de teste.
- Auditoria passiva exige allowlist exata; verificação ativa exige allowlist separada e confirmação explícita.
- Toda requisição de auditoria valida escopo antes de DNS, bloqueia respostas DNS não públicas, fixa a conexão ao IP validado e mantém verificação TLS.
- Verificação ativa faz apenas um GET HTTPS para /, limita a leitura da resposta a 8192 bytes e não segue redirecionamentos.
- Rascunhos de e-mail são locais e não são enviados automaticamente.
- CI automatizado verifica testes Python e sintaxe PHP.

## Verificações antes da publicação

Consulte `docs/release-checklist.md`. A aprovação do CI não substitui revisão operacional, configuração de TLS, credenciais de produção, allowlists locais e isolamento de rede.

## Limites conhecidos

- A autenticação HTTP Basic depende de configuração correta do servidor para disponibilizar `PHP_AUTH_USER` e `PHP_AUTH_PW`.
- A autenticação da aplicação não substitui VPN, firewall, limitação de requisições, monitoramento nem gerenciamento seguro de segredos.
- Não há scanner de portas, exploração, enumeração de diretórios, envio automático de e-mails ou teste contra alvos reais executado pelo CI.
