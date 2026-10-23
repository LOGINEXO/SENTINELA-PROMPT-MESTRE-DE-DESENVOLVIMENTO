# Checklist de revisão e publicação — Etapa 10

Esta lista prepara o projeto para implantação. Marque cada item somente depois de verificar no ambiente real.

## Código e CI

- [ ] Revisar as alterações da versão e confirmar que nenhum segredo ou arquivo de escopo local foi versionado.
- [ ] CI de testes Python concluído com sucesso no commit que será publicado.
- [ ] CI de sintaxe PHP concluído com sucesso no mesmo commit.
- [ ] Revisar dependências e atualizar somente com testes.
- [ ] Confirmar que os testes não enviam requisições de auditoria a alvos externos.

## Configuração e segredos

- [ ] Definir `SENTINELA_WEB_USERNAME` e `SENTINELA_WEB_PASSWORD` no ambiente do processo PHP; senha exclusiva com 16+ caracteres.
- [ ] Confirmar que credenciais ausentes/curtas fazem o painel falhar fechado com HTTP 503.
- [ ] Confirmar que credenciais incorretas recebem HTTP 401 e credenciais válidas permitem acesso.
- [ ] Não armazenar segredos em arquivos versionados, no diretório público ou nos logs.
- [ ] Criar as allowlists locais passiva e ativa somente com hostnames para os quais há autorização documentada.
- [ ] Manter relatórios, banco SQLite, ambiente virtual e raiz do projeto fora do document root público.

## Hospedagem

- [ ] Configurar o document root exclusivamente para `web/`.
- [ ] Configurar HTTPS/TLS válido para qualquer acesso remoto.
- [ ] Restringir o painel por VPN/firewall/IP confiável quando possível.
- [ ] Configurar timeout, limites de requisições, logs e monitoramento.
- [ ] Confirmar que o servidor PHP encaminha as variáveis de ambiente e os campos `PHP_AUTH_USER` / `PHP_AUTH_PW`.
- [ ] Executar o worker como serviço dedicado, com usuário de sistema de privilégios mínimos.
- [ ] Confirmar permissões mínimas de leitura/escrita para `config/`, banco de fila e `reports/`.

## Teste de aceitação

- [ ] Abrir o painel sem credenciais e confirmar HTTP 401 quando o ambiente está configurado.
- [ ] Configurar credenciais ausentes e confirmar HTTP 503.
- [ ] Testar CSRF inválido e confirmar HTTP 403.
- [ ] Enfileirar apenas uma consulta NVD de teste e confirmar seu estado na fila.
- [ ] Verificar que PAUSE impede o início de novas tarefas e STOP cancela tarefas pendentes.
- [ ] Confirmar que rascunhos de e-mail são criados localmente e nunca enviados automaticamente.
- [ ] Confirmar que auditorias passiva/ativa recusam hostnames fora de suas allowlists.
- [ ] Não executar verificação ativa até documentar autorização explícita do ativo.

## Limites desta revisão

CI verde não é certificação de segurança nem prova de que uma hospedagem está configurada corretamente. Esta alteração não implanta o sistema em uma hospedagem, não cria credenciais reais, não preenche allowlists e não testa ativos externos. Só declarar publicação concluída depois de cumprir e registrar os itens acima.
