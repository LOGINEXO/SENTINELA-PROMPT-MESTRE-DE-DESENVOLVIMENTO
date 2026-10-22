# Política e controles de segurança

- Não adicionar tokens, senhas, chaves privadas, cookies ou arquivos de configuração locais ao Git.
- Manter relatórios fora da raiz pública do servidor web.
- Não tratar descoberta pública como autorização de teste.
- Antes de qualquer requisição futura, validar o escopo, resolver e validar destinos, verificar cada redirecionamento e bloquear endereços locais/internos por padrão.
- Implementar limites de tempo, concorrência e quantidade de requisições, além de cancelamento seguro.
- Sanitizar logs e evidências; não armazenar corpos completos de respostas potencialmente sensíveis.
- Usar permissões mínimas e revisar dependências.
- Nenhum scanner ou componente de rede é implementado na Etapa 1.

Esta documentação descreve requisitos de projeto; não afirma que controles de etapas futuras já foram implementados.
