# Etapa 5 — Escopo explícito, SSRF e DNS rebinding

## Preparar a allowlist local

Copie `config/authorized_targets.example.txt` para `config/authorized_targets.txt` e edite o arquivo local. Adicione um hostname por linha, somente para ativos sob sua responsabilidade ou cobertos por autorização documentada. Linhas em branco e comentários `#` são ignorados. O arquivo de exemplo é vazio de propósito e não concede autorização. O arquivo real está no `.gitignore`.

## Política de hostname

- Apenas HTTPS na porta 443.
- Hostname DNS exato; sem curingas e sem autorização implícita de subdomínios.
- IPs literais, hostnames locais/reservados, credenciais embutidas, caminhos, query strings e fragmentos são recusados.
- O arquivo ausente ou sem entradas válidas interrompe a execução.
- Um destino fora da allowlist é rejeitado antes da resolução DNS.

## DNS e conexão

Todas as respostas DNS são examinadas. A presença de qualquer endereço que não seja globalmente roteável bloqueia a operação, inclusive respostas mistas públicas e privadas. O cliente seleciona um IP público validado e conecta diretamente a ele, sem resolver o nome novamente para estabelecer a conexão. O hostname original continua sendo usado no SNI e na validação do certificado TLS.

Esse pinning impede que uma segunda resolução DNS redirecione a conexão em meio à execução. Não elimina riscos do ambiente de rede; mantenha egress filtering e controles de isolamento.

## Redirecionamentos

A auditoria atual não segue redirecionamentos. A função `validate_redirect` existe para validar um cabeçalho `Location` antes de qualquer eventual uso futuro: exige HTTPS, porta 443, hostname na allowlist e resolução DNS pública. A função apenas valida e retorna dados; não faz requisições ao destino. Qualquer futura implementação de redirect deverá revalidar cada salto e conectar ao IP validado sem resolver novamente o hostname.

## Testes e limites

Os testes usam DNS e respostas HTTP simulados e não fazem varreduras externas. Esses controles reduzem riscos comuns de SSRF e DNS rebinding, mas não substituem autorização documentada, revisão humana, isolamento de rede nem uma auditoria de segurança independente.
