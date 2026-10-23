# Etapa 7 — Fila e controles PLAY / PAUSE / STOP

A fila usa SQLite persistente (por padrão `reports/queue.sqlite3`, ignorado pelo Git). São aceitos consulta pública NVD, auditoria passiva HTTPS e verificação ativa HTTPS limitada. A tarefa ativa exige uma allowlist separada e confirmação explícita. Não há execução arbitrária de comandos, varredura de portas, exploração ou envio de e-mails. A verificação ativa executa um único GET HTTPS à raiz; veja `docs/active-audit.md`. Rascunhos editáveis e não enviados são tratados na Etapa 8; consulte `docs/email-drafts.md`.

## Iniciar o worker

Instale as dependências e configure o escopo local antes de enfileirar auditorias. Em um terminal separado, na raiz do projeto, mantenha o worker em execução:

```bash
python -m sentinela.queue_worker
```

O worker fica aguardando tarefas e respeita o estado global da fila. Para encerrar o processo do worker, use Ctrl+C; isso não apaga o histórico. O controle STOP interrompe novas retiradas de tarefas e cancela tarefas que ainda estavam na fila. Uma requisição de rede já em andamento não pode ser interrompida instantaneamente; ela termina dentro dos timeouts existentes e então é marcada como parada.

## CLI

```bash
python -m sentinela.queue_cli add-nvd --query "OpenSSH" --limit 10
python -m sentinela.queue_cli add-audit --host "app.minha-empresa.example"
python -m sentinela.queue_cli add-active-audit --host "app.minha-empresa.example" --confirm-authorized
python -m sentinela.queue_cli status
python -m sentinela.queue_cli control pause
python -m sentinela.queue_cli control play
python -m sentinela.queue_cli control stop
```

O modo inicial da fila é PLAY. PAUSE impede que novas tarefas comecem; a tarefa que já está em execução pode terminar. PLAY retoma o processamento. STOP marca como paradas as tarefas pendentes e impede novas execuções até novo PLAY. Se uma nova tarefa for adicionada enquanto STOP está ativo, ela fica aguardando e só será executada após PLAY.

## Interface PHP

O painel em `web/index.php` passa a enfileirar as duas ações e exibir o estado/histórico. Os botões PLAY, PAUSE e STOP alteram o estado persistente da fila; o worker precisa estar ativo em um processo separado para consumir tarefas. Proteja o painel com autenticação antes de disponibilizá-lo a outras pessoas. A base SQLite contém resultados e deve permanecer fora da raiz pública e ser protegida por permissões do sistema operacional.

## Limitações

- Um único worker é recomendado nesta etapa.
- PAUSE é cooperativo: não interrompe uma tarefa já iniciada.
- STOP cancela tarefas pendentes; tarefa em andamento é marcada como parada ao terminar.
- A fila não implementa agendamento, repetição automática, múltiplos workers, autenticação web ou controle de acesso por usuário.
