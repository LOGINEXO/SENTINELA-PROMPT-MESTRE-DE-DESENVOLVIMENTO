# Interface local do Sentinela

A interface PHP é uma interface gráfica para a instalação local do Sentinela. **Não é um serviço hospedado nem uma aplicação multiusuário.** Não há cadastro, login, contas ou armazenamento central.

## Iniciar no computador do usuário

Requisitos: PHP 8+ recomendado, Python 3.11+ e dependências instaladas. Na raiz do repositório, abra PowerShell:

```powershell
$env:SENTINELA_LOCAL_MODE = "1"
php -S 127.0.0.1:8080 -t web
```

Abra `http://127.0.0.1:8080`. Não precisa configurar usuário nem senha. Mantenha o servidor ligado a `127.0.0.1`; não use `0.0.0.0`, proxy reverso, túnel ou hospedagem pública. A aplicação rejeita pedidos que não venham de loopback ou que contenham cabeçalhos de proxy encaminhado.

## Onde os dados ficam

- Banco SQLite da fila e histórico: `reports/queue.sqlite3` por padrão.
- Relatórios JSON: diretório `reports/` ou caminho local informado pelo comando de exportação.
- Rascunhos de e-mail: `reports/email-drafts/`.
- Listas de escopo: arquivos locais `config/authorized_targets.txt` e `config/authorized_active_targets.txt`, que não devem ser versionados.

Esses arquivos ficam no computador em que o Sentinela é executado. Cada instalação possui banco, histórico e relatórios próprios. O projeto não envia relatórios para servidor central nem sincroniza dados entre computadores. Se o usuário mover o repositório, copiar os arquivos locais ou configurar manualmente outro caminho, isso é uma ação local do usuário.

## Tráfego de rede esperado

A busca NVD consulta a API pública da NVD para obter informações de vulnerabilidades. As auditorias conectam-se aos hostnames que o usuário incluiu nas allowlists locais e para os quais tem autorização. Isso é tráfego de consulta/auditoria, não upload do relatório para um serviço do Sentinela.

## Proteções

- A interface só aceita conexões de loopback e rejeita cabeçalhos de proxy encaminhado.
- Formulários POST verificam token CSRF.
- Entradas são validadas e saídas HTML são escapadas.
- Auditorias respeitam allowlists locais separadas para escopo passivo e ativo.
- Rascunhos de e-mail são criados localmente e nunca enviados automaticamente.

Não exponha o servidor local na rede. A proteção local não substitui autorização documentada para auditar ativos.
