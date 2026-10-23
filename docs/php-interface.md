# Etapa 6 — Interface PHP

A interface em `web/index.php` oferece consulta pública NVD/CVE e auditoria passiva HTTPS de hostname previamente autorizado, enfileirando tarefas em SQLite. O painel exibe o estado, o histórico e os controles PLAY/PAUSE/STOP. Para tarefas concluídas, é possível gerar um rascunho de e-mail local, que não é enviado automaticamente. O processo worker deve ser iniciado separadamente conforme `docs/queue-controls.md`.

## Uso local simples

O projeto é código aberto e pode ser executado localmente sem criar conta nem senha. No PowerShell, na raiz do repositório:

```powershell
$env:SENTINELA_LOCAL_MODE = "1"
php -S 127.0.0.1:8080 -t web
```

Abra `http://127.0.0.1:8080`. O modo sem autenticação só funciona quando a conexão vem de loopback (`127.0.0.1` ou `::1`) e não há cabeçalhos de proxy encaminhado. Não mude o endereço do servidor para `0.0.0.0` e não use esse modo em hospedagem, container exposto, túnel ou reverse proxy.

## Acesso remoto / hospedagem

Para acesso por rede ou hospedagem, **não** defina `SENTINELA_LOCAL_MODE=1`. Configure `SENTINELA_WEB_USERNAME` e `SENTINELA_WEB_PASSWORD` no ambiente do processo PHP. A senha deve ter pelo menos 16 caracteres e ser exclusiva. O painel responde HTTP 503 se as credenciais não estiverem configuradas e HTTP 401 para credenciais ausentes/incorretas. Acesso remoto exige HTTPS/TLS; restrinja também por VPN/firewall quando possível.

O arquivo `.env.example` é apenas documentação e **não é carregado automaticamente** pelo PHP. Em instalações PHP-FPM/FastCGI, confirme que as variáveis chegam ao processo e que `PHP_AUTH_USER` / `PHP_AUTH_PW` são disponibilizados pelo servidor.

## Requisitos

- PHP 8.0+ recomendado, com sessões, `proc_open` e suporte a HTTP Basic Auth para hospedagem protegida.
- Python 3.11+ e dependências do projeto instaladas.
- Arquivo local `config/authorized_targets.txt` preenchido com hostnames autorizados. O arquivo não deve ser versionado.
- Servidor web configurado para servir **somente** o diretório `web/`; a raiz do repositório deve ficar fora do document root público.

## Controles implementados

- Modo local opcional sem senha, limitado a conexão loopback sem cabeçalhos de proxy.
- HTTP Basic Auth obrigatório para modo de hospedagem, com falha fechada quando as variáveis estão ausentes ou a senha é curta.
- Token CSRF de sessão verificado em cada POST.
- Escape de conteúdo dinâmico HTML e cabeçalhos básicos de segurança.
- Validação de tamanho/formato para entradas e limite NVD entre 1 e 100.
- Verificação prévia de hostname na allowlist local; o núcleo Python repete validação e verificações DNS/IP.
- Saída do processo limitada e exibida como texto escapado, não como HTML.
- `web/.htaccess` desativa listagem de diretórios em Apache.

A autenticação da aplicação não substitui os controles de acesso da infraestrutura. Os rascunhos ficam em `reports/email-drafts/`; revise manualmente destinatários e conteúdo. Não mantenha relatórios, escopo real, segredos ou a raiz do repositório sob o document root público.
