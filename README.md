# Sentinela

Plataforma modular de inteligência pública e auditoria defensiva. Etapas 1–8: fundação, inteligência pública, relatórios JSON, auditoria passiva, controles de escopo, interface PHP, fila persistente e rascunhos de e-mail.

## Requisitos

- Python 3.11+
- Git e pip

## Instalação

Linux/macOS:

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
~~~

Windows PowerShell:

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
~~~

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

Linux/macOS:

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

A interface web fica em `web/index.php`. Configure o document root do servidor web **somente** para `web/`; mantenha o repositório, o escopo real e os relatórios fora da raiz pública. Requer PHP 8+ recomendado, Python 3.11+ e dependências instaladas. Para desenvolvimento local, execute na raiz do projeto `php -S 127.0.0.1:8080 -t web` e abra `http://127.0.0.1:8080`. Configure `SENTINELA_PYTHON` se o processo PHP não localizar o interpretador correto.

A interface enfileira consultas NVD e auditorias passivas autorizadas, exibe histórico e controles PLAY/PAUSE/STOP e permite gerar rascunhos de e-mail para revisão manual. Consulte [docs/php-interface.md](docs/php-interface.md), [docs/queue-controls.md](docs/queue-controls.md) e [docs/email-drafts.md](docs/email-drafts.md).

## Relatórios JSON

~~~bash
python -m sentinela.audit meu-dominio.example --export-json auditoria.json
python -m sentinela.cli --nvd-search "OpenSSH" --limit 10 --export-json cves.json
~~~

Os arquivos são gravados em `reports/`, sanitizados e ignorados pelo Git. A sanitização reduz exposição acidental, mas não substitui a revisão manual antes de compartilhar.

## Etapas

- [x] 1 — Fundação.
- [x] 2 — Inteligência pública NVD/CVE.
- [x] 3 — Relatórios locais JSON.
- [x] 4 — Auditoria passiva HTTPS/TLS.
- [x] 5 — Controles de escopo e mitigação de SSRF/DNS rebinding.
- [x] 6 — Interface PHP (síncrona; sem fila).
- [x] 7 — Fila persistente e controles PLAY/PAUSE/STOP.
- [x] 8 — Rascunhos de e-mail e revisão manual.
- [ ] 9 — Testes ativos autorizados.
- [ ] 10 — Revisão e publicação.

Inteligência pública não concede autorização para testar ativos. Etapas futuras de auditoria ativa exigirão escopo e autorização explícitos. Não há exploração, varredura de portas nem envio automático de e-mails. Os rascunhos são arquivos Markdown locais e exigem revisão humana.

## Estrutura e políticas

- `sentinela/intelligence/nvd.py`: cliente NVD/CVE.
- `sentinela/audit/`: auditoria HTTPS passiva.
- `sentinela/scope.py`: allowlist, resolução DNS e validação de destinos de redirecionamento.
- `sentinela/reports.py`: formato, sanitização e exportação JSON.
- `sentinela/queue.py`, `sentinela/queue_worker.py`, `sentinela/queue_cli.py`: fila SQLite, worker e controles.
- `sentinela/email_drafts.py`: geração de rascunhos de e-mail não enviados para revisão manual.
- `config/`: configurações e exemplos de escopo.
- `tests/`: testes automatizados offline.
- `reports/`: relatórios locais ignorados pelo Git.

Mantenha configurações privadas, escopo real e relatórios fora da raiz pública de servidores web. Consulte `docs/architecture.md`, `docs/security.md` e `docs/responsible-disclosure.md`.

## Licença

MIT. Consulte `LICENSE`.
