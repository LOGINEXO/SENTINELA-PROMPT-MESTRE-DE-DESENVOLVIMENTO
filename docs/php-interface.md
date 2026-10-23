# Etapa 6 — Interface PHP

A interface em `web/index.php` oferece consulta pública NVD/CVE e auditoria passiva HTTPS de hostname previamente autorizado, enfileirando essas tarefas em SQLite. O painel exibe o estado, o histórico e os controles PLAY/PAUSE/STOP. Para tarefas concluídas, é possível gerar um rascunho de e-mail local, que não é enviado automaticamente. O processo worker deve ser iniciado separadamente conforme `docs/queue-controls.md`.

## Requisitos

- PHP 8.0+ recomendado, com sessões e `proc_open` habilitados.
- Python 3.11+ e dependências do projeto instaladas no servidor.
- Arquivo local `config/authorized_targets.txt` preenchido com hostnames autorizados. O arquivo não deve ser versionado.
- Servidor web configurado para servir **somente** o diretório `web/`; o diretório raiz do repositório deve ficar fora do document root público.

## Execução local

Na raiz do projeto, configure primeiro o escopo autorizado seguindo o README. Em ambiente de desenvolvimento, inicie o servidor PHP embutido:

```bash
php -S 127.0.0.1:8080 -t web
```

Abra `http://127.0.0.1:8080`. O servidor embutido é para desenvolvimento local, não para exposição pública.

Se o executável Python não for encontrado pelo processo PHP, configure a variável de ambiente `SENTINELA_PYTHON` com o caminho do interpretador do ambiente virtual. O processo é iniciado com argumentos separados (sem shell), a partir da raiz do projeto.

## Controles implementados

- Token CSRF de sessão verificado em cada POST.
- Escape de conteúdo dinâmico HTML e cabeçalhos básicos de segurança.
- Validação de tamanho/formato para entradas e limite NVD entre 1 e 100.
- Verificação prévia de hostname na allowlist local para a auditoria; o núcleo Python repete a validação e as verificações DNS/IP da etapa 5.
- Saída do processo limitada e exibida como texto escapado, não como HTML.
- Nenhuma credencial NVD é solicitada ou armazenada na interface.
- `web/.htaccess` desativa listagem de diretórios em Apache.

## Limitações operacionais

A inclusão de tarefas e os controles são comandos curtos, mas a execução acontece em processo worker separado. Não publique esta interface sem autenticação/autorização de acesso, limites no servidor web, timeout de processo e monitoramento. A fila não substitui autenticação. Os rascunhos ficam em `reports/email-drafts/`; confira `docs/email-drafts.md` e revise manualmente destinatários e conteúdo. Configure TLS no servidor web quando acessar remotamente. Não mantenha relatórios, escopo real, segredos ou a raiz do repositório sob o document root público.
