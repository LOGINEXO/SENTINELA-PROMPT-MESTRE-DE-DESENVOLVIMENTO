# Etapa 4 — Auditoria passiva HTTPS

A auditoria passiva envia uma única requisição HTTP `HEAD /` sobre HTTPS na porta 443 ao hostname informado. Ela verifica a cadeia do certificado TLS usando o contexto de confiança padrão do Python e registra a versão TLS, cifra, dados básicos do certificado, status HTTP e presença de cabeçalhos de segurança.

## Uso

~~~bash
python -m sentinela.audit example.com
python -m sentinela.audit example.com --export-json example-audit.json
~~~

Substitua `example.com` por um hostname que você possui ou para o qual tem autorização expressa para realizar a verificação. O relatório pode ser gravado em `reports/` e passa pela sanitização comum do Sentinela.

## Limites e controles

- Somente HTTPS, porta 443, hostname DNS; não aceita IP literal, credenciais na URL, caminhos, query strings nem fragmentos.
- Resolve o hostname e bloqueia a operação se qualquer resposta DNS for não pública, incluindo endereços privados, loopback e link-local.
- Conecta diretamente a um IP público validado, mantendo o hostname para SNI e validação do certificado, reduzindo o risco de DNS rebinding entre resolução e conexão.
- Timeout configurável internamente limitado a 15 segundos.
- Uma requisição HEAD, sem varredura de portas, exploração, enumeração de diretórios ou testes de vulnerabilidade.
- Não segue redirecionamentos. Se o servidor responder 301/302, esse status é registrado e o destino não é acessado.
- Não desabilita a validação do certificado TLS.
- Registra a presença de Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Referrer-Policy e Permissions-Policy.

A ausência de um cabeçalho não prova, isoladamente, uma vulnerabilidade. Respostas HEAD podem diferir de GET e o resultado pode variar por CDN, proxy ou configuração de borda. Um hostname público não implica autorização; use apenas ativos autorizados. Esta funcionalidade não constitui auditoria completa nem teste de penetração.
