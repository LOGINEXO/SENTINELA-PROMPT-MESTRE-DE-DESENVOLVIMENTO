# Arquitetura do Sentinela

## Modelo de execução e armazenamento

O Sentinela é um aplicativo open source local-first, não um serviço hospedado. Não possui login, contas, backend central ou sincronização. Cada instalação grava a fila e o histórico em `reports/queue.sqlite3`, relatórios em `reports/` e rascunhos em `reports/email-drafts/` no computador local. A interface PHP aceita somente conexões de loopback. A rede é usada para consultar a API pública NVD e para conectar-se aos ativos explicitamente autorizados; relatórios não são enviados para um servidor central.

## Estado das etapas

- Etapa 1 — Fundação: concluída.
- Etapa 2 — Inteligência pública NVD/CVE: concluída.
- Etapa 3 — Relatórios JSON sanitizados: concluída.
- Etapa 4 — Auditoria passiva HTTPS/TLS: concluída.
- Etapa 5 — Escopo explícito e proteção de destinos: implementada.
- Etapa 6 — Interface PHP: implementada.
- Etapa 7 — Fila SQLite e controles cooperativos PLAY/PAUSE/STOP: implementada nesta branch, aguardando validação do CI.
- Etapa 8 — Rascunhos de e-mail em Markdown para revisão manual, sem envio automático: implementada nesta branch, aguardando validação do CI.
- Etapa 9 — Verificação ativa HTTPS limitada (um GET à raiz, escopo ativo separado e confirmação explícita): implementada nesta branch, aguardando CI.
- Etapa 10: planejada, não implementada.

## Etapa 5 — Escopo e controles de destino

A auditoria passiva exige uma lista local explícita em `config/authorized_targets.txt`. Esse arquivo não é versionado; o exemplo versionado contém apenas comentários e não autoriza nenhum ativo. Cada entrada precisa ser um hostname DNS exato. Curingas, endereços IP literais, portas alternativas e caminhos são rejeitados. Subdomínios não são incluídos implicitamente.

A execução falha fechada se a lista estiver ausente ou vazia. Antes de iniciar a conexão, o hostname solicitado é comparado à allowlist. Todas as respostas DNS precisam ser endereços públicos; se uma única resposta for privada, loopback, link-local ou não global, a operação é bloqueada. O cliente conecta diretamente ao IP público validado, usando o hostname original para SNI e validação do certificado TLS. Assim, uma alteração posterior da resposta DNS não muda o endereço da conexão já selecionado.

A função `validate_redirect` valida destinos de cabeçalhos `Location` para uso futuro: somente HTTPS/443, hostname exato no escopo e resolução pública. Ela não envia requisições. A auditoria atual não segue redirecionamentos.

Esses controles mitigam caminhos comuns de SSRF e DNS rebinding, mas não substituem autorização documentada, egress filtering, isolamento de rede ou revisão de segurança.

## Etapas anteriores

A Etapa 2 consulta explicitamente a API NVD CVE 2.0, normaliza os resultados e classifica prioridade técnica. Um CVE público não comprova que um ativo esteja vulnerável.

A Etapa 3 cria relatórios com envelope comum e exportação JSON sanitizada. Relatórios locais devem permanecer fora da raiz pública do servidor e ser revisados antes de compartilhamento.

A Etapa 4 faz uma única requisição `HEAD` HTTPS na porta 443, verifica TLS e registra cabeçalhos. Não há exploração, varredura de portas nem acompanhamento automático de redirecionamentos.

## Separação de responsabilidades

Inteligência pública, auditoria passiva, escopo, relatórios e futuras funções ativas são componentes separados. A presença de um ativo em dados públicos nunca concede autorização para testá-lo.

## Dados privados

Configurações locais, escopo real, credenciais e relatórios não devem ser versionados nem armazenados na raiz pública de um servidor web. O arquivo real `config/authorized_targets.txt` está no `.gitignore`.


## Etapa 6 — Interface PHP

A interface local está em `web/`. Ela chama a CLI Python com argumentos separados (sem shell), valida entradas, verifica a allowlist antes da auditoria, usa token CSRF e escapa saídas HTML. O acesso é limitado a loopback; não é um painel hospedado e não deve ser exposto à rede. Consulte `docs/php-interface.md`.


## Etapa 7 — Fila persistente

A fila usa SQLite em `reports/queue.sqlite3` por padrão e aceita apenas consultas públicas NVD e auditorias passivas limitadas à allowlist exata. A interface PHP apenas enfileira tarefas e altera o estado global; `sentinela.queue_worker` é um processo separado e persistente que retira tarefas uma por vez. PLAY libera a fila, PAUSE impede o início de novas tarefas e STOP cancela tarefas pendentes e impede novas retiradas até PLAY. A tarefa de rede já em andamento não é interrompida instantaneamente; ela termina sob os timeouts existentes e fica marcada como parada se o modo continuar STOP. Consulte `docs/queue-controls.md`.


## Etapa 9 — Verificação ativa limitada

A verificação ativa faz uma única requisição GET para `/` em HTTPS/443. Ela exige a allowlist local independente `config/authorized_active_targets.txt` e confirmação explícita na criação da tarefa. O worker relê essa allowlist no momento da execução. O destino é resolvido e validado como IP público e a conexão é fixada nesse IP, com verificação TLS normal. Redirecionamentos não são seguidos e o corpo da resposta não é persistido (a leitura é limitada a 8192 bytes). Não há exploração, varredura de portas ou enumeração de diretórios. Consulte `docs/active-audit.md`.
