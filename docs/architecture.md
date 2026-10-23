# Arquitetura do Sentinela

## Estado das etapas

- Etapa 1 — Fundação: concluída.
- Etapa 2 — Inteligência pública NVD/CVE: concluída.
- Etapa 3 — Relatórios JSON sanitizados: concluída.
- Etapa 4 — Auditoria passiva HTTPS/TLS: concluída.
- Etapa 5 — Escopo explícito e proteção de destinos: implementada.
- Etapa 6 — Interface PHP síncrona: implementada nesta branch, aguardando validação do CI.
- Etapas 7–10: planejadas, não implementadas.

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

A interface pública está em `web/`. Ela chama a CLI Python com argumentos separados (sem shell), valida entradas, verifica a allowlist antes da auditoria, usa token CSRF e escapa saídas HTML. O document root deve apontar exclusivamente para `web/`; o escopo real e os relatórios devem permanecer fora da raiz pública. A interface é síncrona e não fornece fila, pausa ou cancelamento; não deve ser exposta publicamente sem autenticação e controles operacionais adicionais. Consulte `docs/php-interface.md`.
