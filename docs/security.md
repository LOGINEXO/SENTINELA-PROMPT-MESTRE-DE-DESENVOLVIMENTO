# Política e controles de segurança

- Não adicionar tokens, senhas, chaves privadas, cookies ou arquivos de configuração locais ao Git.
- Manter relatórios fora da raiz pública do servidor web.
- Não tratar descoberta pública como autorização de teste.
- A auditoria passiva exige allowlist exata; a verificação ativa exige allowlist separada e confirmação explícita.
- Toda requisição de auditoria valida escopo antes de DNS, bloqueia qualquer resposta DNS não pública, fixa a conexão ao IP validado e mantém verificação TLS.
- A verificação ativa atual faz apenas um GET HTTPS para /, limita a leitura de resposta a 8192 bytes e não segue redirecionamentos.
- Implementar limites de tempo, concorrência e quantidade de requisições, além de cancelamento seguro.
- Sanitizar logs e evidências; não armazenar corpos completos de respostas potencialmente sensíveis.
- Usar permissões mínimas e revisar dependências.
- Não há scanner de portas, exploração, enumeração de diretórios ou payloads de teste.

Esta documentação descreve requisitos de projeto; não afirma que controles de etapas futuras já foram implementados.
