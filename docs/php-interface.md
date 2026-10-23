# Etapa 6 — Interface PHP

A interface em `web/index.php` oferece consulta pública NVD/CVE e auditoria passiva HTTPS de hostname previamente autorizado, enfileirando essas tarefas em SQLite. O painel exibe o estado, o histórico e os controles PLAY/PAUSE/STOP. Para tarefas concluídas, é possível gerar um rascunho de e-mail local, que não é enviado automaticamente. O processo worker deve ser iniciado separadamente conforme `docs/queue-controls.md`.

## Requisitos

- PHP 8.0+ recomendado, com sessões, `proc_open` e suporte a HTTP Basic Auth (`PHP_AUTH_USER` / `PHP_AUTH_PW`) habilitados.
- Python 3.11+ e dependências do projeto instaladas no servidor.
- Arquivo local `config/authorized_targets.txt` preenchido com hostnames autorizados. O arquivo não deve ser versionado.
- Servidor web configurado para servir **somente** o diretório `web/`; a raiz do repositório deve ficar fora do document root público.
- Variáveis de ambiente `SENTINELA_WEB_USERNAME` e `SENTINELA_WEB_PASSWORD` configuradas no processo PHP. A senha deve ter pelo menos 16 caracteres e ser exclusiva.

## Autenticação obrigatória

O painel exige HTTP Basic Auth. Se as variáveis de ambiente não estiverem configuradas, ou se a senha tiver menos de 16 caracteres, o painel responde com HTTP 503 e não processa ações. Credenciais incorretas recebem HTTP 401. Não use valores de exemplo em produção e não coloque segredos no Git.

Configure as variáveis no ambiente do serviço PHP/web server ou no gerenciador de segredos da hospedagem. O arquivo `.env.example` é apenas documentação e **não é carregado automaticamente** pelo PHP. Em instalações PHP-FPM/FastCGI, confirme que o servidor encaminha as variáveis de ambiente ao processo e que `PHP_AUTH_USER` / `PHP_AUTH_PW` chegam corretamente ao PHP.

**Acesso remoto exige HTTPS/TLS.** Não publique o painel em HTTP aberto. Para desenvolvimento local, limite o servidor a `127.0.0.1`.

## Execução local

Na raiz do projeto, configure primeiro o escopo autorizado seguindo o README. Defina as variáveis no terminal antes de iniciar o PHP. Exemplo em PowerShell (substitua os valores por credenciais próprias):

```powershell
$env:SENTINELA_WEB_USERNAME = "sentinela-admin"
$env:SENTINELA_WEB_PASSWORD = "substitua-por-uma-senha-unica-com-mais-de-16-caracteres"
php -S 127.0.0.1:8080 -t web
```

Abra `http://127.0.0.1:8080`; o navegador solicitará usuário e senha. O servidor embutido é para desenvolvimento local, não para exposição pública. Se o executável Python não for encontrado pelo processo PHP, configure `SENTINELA_PYTHON` com o caminho do interpretador do ambiente virtual.

## Controles implementados

- HTTP Basic Auth obrigatório, com falha fechada quando as variáveis estão ausentes ou a senha é curta.
- Token CSRF de sessão verificado em cada POST.
- Escape de conteúdo dinâmico HTML e cabeçalhos básicos de segurança.
- Validação de tamanho/formato para entradas e limite NVD entre 1 e 100.
- Verificação prévia de hostname na allowlist local para a auditoria; o núcleo Python repete a validação e as verificações DNS/IP.
- Saída do processo limitada e exibida como texto escapado, não como HTML.
- Nenhuma credencial NVD é solicitada ou armazenada na interface.
- `web/.htaccess` desativa listagem de diretórios em Apache.

## Limitações operacionais

Autenticação do painel não substitui controles de acesso da infraestrutura. Use TLS, restrinja acesso por rede/VPN quando possível, aplique limites de requisições e timeout no servidor web e monitore o serviço. A execução acontece em worker separado. Os rascunhos ficam em `reports/email-drafts/`; revise manualmente destinatários e conteúdo. Não mantenha relatórios, escopo real, segredos ou a raiz do repositório sob o document root público.
