# Sentinela

Plataforma open source, local-first, de inteligência pública e auditoria defensiva. Cada instalação roda no próprio computador e mantém fila, banco SQLite, relatórios JSON e rascunhos localmente. Não há login, conta de usuário, servidor central ou sincronização de relatórios.

## Plataformas suportadas e requisitos

**Suporte oficial: Linux e Windows.** macOS não faz parte da matriz de suporte/testes atual.

- Python 3.11+
- PHP CLI 8.0+ para abrir a interface web local
- Git para clonar o repositório

## Instalação rápida

### Linux

Na raiz do repositório, execute:

```bash
bash scripts/install-linux.sh
bash scripts/start-linux.sh
```

### Windows (PowerShell)

Instale Python 3.11+ e PHP CLI 8.0+ e deixe ambos disponíveis no PATH. Na raiz do repositório, execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install-windows.ps1
.\scripts\start-windows.ps1
```

Nos dois sistemas, abra `http://127.0.0.1:8080` no navegador e mantenha o terminal aberto durante o uso. Os scripts iniciam a interface local e o worker da fila. O instalador prepara o ambiente virtual e não instala Python ou PHP no sistema operacional.

Detalhes: [guia de instalação](docs/installation.md).

## Verificação local

~~~bash
python -m sentinela.cli --help
python -m sentinela.cli --version
python -m sentinela.cli --check-config
python -m pytest -q
~~~

## Consultas públicas NVD/CVE

~~~bash
python -m sentinela.cli --nvd-search "OpenSSH" --limit 10
python -m sentinela.cli --nvd-search "OpenSSH" --modified-since "2026-10-01T00:00:00Z"
python -m sentinela.cli --nvd-cve CVE-2024-3094
~~~

As consultas NVD só são feitas quando solicitadas explicitamente. A variável opcional `NVD_API_KEY` deve ser definida no ambiente, nunca em arquivos versionados. As buscas incrementais aceitam datas ISO 8601 com fuso, em uma janela máxima de 120 dias. Um CVE público não confirma que um ativo específico esteja vulnerável.

## Etapa 4 — Auditoria passiva com escopo obrigatório

**A auditoria não roda sem uma allowlist local preenchida manualmente.** Copie o arquivo de exemplo e adicione apenas hostnames para os quais você tem autorização documentada.

Linux:

~~~bash
cp config/authorized_targets.example.txt config/authorized_targets.txt
~~~

Windows PowerShell:

~~~powershell
Copy-Item config/authorized_targets.example.txt config/authorized_targets.txt
~~~

Edite `config/authorized_targets.txt`, acrescente um hostname por linha e remova/comente os exemplos que não forem seus. O arquivo real é ignorado pelo Git.

~~~text
# Somente ativos explicitamente autorizados
meu-dominio.example
app.minha-empresa.example
~~~

Os nomes acima são exemplos ilustrativos, não autorização real. O arquivo de exemplo do repositório não autoriza nenhum alvo.

Execute a auditoria apenas contra um hostname presente no arquivo local:

~~~bash
python -m sentinela.audit meu-dominio.example
python -m sentinela.audit meu-dominio.example --export-json auditoria.json
~~~

A auditoria envia uma requisição `HEAD` por HTTPS na porta 443, verifica o certificado TLS e registra cabeçalhos de segurança. Não segue redirecionamentos. Não aceita IP literal, curingas, portas alternativas ou URLs com caminhos/credenciais.

## Etapa 5 — Escopo, DNS e redirecionamentos

- A lista de autorização é uma allowlist de hostnames exatos; curingas e subdomínios implícitos são recusados.
- A execução falha se o arquivo de escopo estiver ausente ou vazio.
- Todas as respostas DNS precisam ser endereços públicos. Respostas mistas públicas/privadas também são bloqueadas.
- A conexão usa diretamente um IP público validado, mantendo o hostname original para SNI e validação do certificado TLS.
- Há uma função para validar destinos de cabeçalho `Location` futuros, mas o programa atual não segue redirecionamentos nem faz requisição ao destino.
- Esses controles reduzem riscos de SSRF e DNS rebinding; não substituem isolamento de rede, autorização documentada e revisão de segurança.

Detalhes: [docs/scope-controls.md](docs/scope-controls.md) e [docs/passive-audit.md](docs/passive-audit.md).

## Etapa 6 — Interface PHP

A interface web fica em `web/index.php` e é **local-only**: não existe login, cadastro, hospedagem central nem armazenamento remoto de relatórios. Use `bash scripts/install-linux.sh` e `bash scripts/start-linux.sh` no Linux ou `.\scripts\install-windows.ps1` e `.\scripts\start-windows.ps1` no Windows. Abra `http://127.0.0.1:8080`. Os inicializadores definem `SENTINELA_PYTHON` para o ambiente virtual e iniciam o worker da fila. O servidor fica ligado somente a `127.0.0.1`. Cada instalação mantém seu próprio banco SQLite, histórico, relatórios e rascunhos em `reports/` no computador do usuário. Não publique o painel na internet, não use proxy/túnel e não altere o bind para `0.0.0.0`.

A interface enfileira consultas NVD, auditorias passivas e verificações ativas HTTPS limitadas com autorização separada, exibe histórico e controles PLAY/PAUSE/STOP e permite gerar rascunhos de e-mail. Consulte [docs/php-interface.md](docs/php-interface.md), [docs/queue-controls.md](docs/queue-controls.md), [docs/email-drafts.md](docs/email-drafts.md) e [docs/active-audit.md](docs/active-audit.md).

## Relatórios JSON

~~~bash
python -m sentinela.audit meu-dominio.example --export-json auditoria.json
python -m sentinela.cli --nvd-search "OpenSSH" --limit 10 --export-json cves.json
~~~

Os arquivos são gravados em `reports/` no computador onde o comando é executado, sanitizados e ignorados pelo Git. Cada PC mantém seu próprio histórico e relatórios; o projeto não os envia a um servidor central. A sanitização reduz exposição acidental, mas não substitui a revisão manual antes de compartilhar.

## Etapas

- [x] 1 — Fundação.
- [x] 2 — Inteligência pública NVD/CVE.
- [x] 3 — Relatórios locais JSON.
- [x] 4 — Auditoria passiva HTTPS/TLS.
- [x] 5 — Controles de escopo e mitigação de SSRF/DNS rebinding.
- [x] 6 — Interface PHP (síncrona; sem fila).
- [x] 7 — Fila persistente e controles PLAY/PAUSE/STOP.
- [x] 8 — Rascunhos de e-mail e revisão manual.
- [x] 9 — Verificação ativa HTTPS limitada, com escopo de autorização separado.
- [x] 10 — Revisão de segurança para distribuição open source local (não hospedar o painel como serviço). 
- [ ] 11 — Instalação e inicialização simplificadas para Linux e Windows; testes automatizados em ambos os sistemas (em validação).

Inteligência pública não concede autorização para testar ativos. A verificação ativa implementada faz somente um GET HTTPS à raiz de hostname em allowlist ativa separada, sem seguir redirecionamentos; não há exploração nem varredura de portas. Não há envio automático de e-mails.

## Estrutura e políticas

- `sentinela/intelligence/nvd.py`: cliente NVD/CVE.
- `sentinela/audit/passive.py`: auditoria HTTPS passiva.
- `sentinela/audit/active.py`: verificação ativa limitada (um GET HTTPS), apenas com escopo ativo separado.
- `sentinela/scope.py`: allowlist, resolução DNS e validação de destinos de redirecionamento.
- `sentinela/reports.py`: formato, sanitização e exportação JSON.
- `sentinela/queue.py`, `sentinela/queue_worker.py`, `sentinela/queue_cli.py`: fila SQLite, worker e controles.
- `sentinela/email_drafts.py`: geração de rascunhos de e-mail não enviados para revisão manual.
- `config/`: configurações e exemplos de escopo passivo e ativo.
- `tests/`: testes automatizados offline.
- `reports/`: relatórios locais ignorados pelo Git.

Mantenha configurações privadas, escopo real e relatórios fora da raiz pública de servidores web. Consulte `docs/architecture.md`, `docs/security.md`, `docs/responsible-disclosure.md` e a [checklist de distribuição](docs/release-checklist.md).

## Licença

MIT. Consulte `LICENSE`.
