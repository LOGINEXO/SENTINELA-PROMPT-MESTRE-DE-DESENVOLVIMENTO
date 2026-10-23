# Checklist de distribuição open source local

Esta lista é para publicar o código no GitHub e permitir que cada usuário execute sua própria instalação. **Não existe implantação de serviço central.**

## Código e CI

- [ ] Confirmar que o CI de testes Python passou no commit que será distribuído.
- [ ] Confirmar que a sintaxe PHP e o teste da interface local passaram.
- [ ] Confirmar que nenhum segredo, banco, relatório ou allowlist real foi versionado.
- [ ] Manter dependências e instruções de instalação atualizadas.

## Execução local

- [ ] Confirmar que a interface abre em `127.0.0.1` sem login nem cadastro.
- [ ] Confirmar que a interface rejeita pedidos que não venham de loopback e cabeçalhos de proxy encaminhado.
- [ ] Confirmar que a fila SQLite é criada em `reports/queue.sqlite3` no computador local.
- [ ] Confirmar que relatórios JSON e rascunhos ficam no diretório local `reports/`.
- [ ] Confirmar que cada instalação tem seu próprio banco e histórico sem sincronização automática.
- [ ] Documentar que buscas NVD e auditorias autorizadas usam a rede, mas os relatórios não são enviados ao Sentinela como serviço central.

## Limites de distribuição

- [ ] Não publicar nem hospedar o painel como serviço web multiusuário.
- [ ] Não configurar analytics, telemetria ou upload central de relatórios.
- [ ] Manter as allowlists de autorização em arquivos locais ignorados pelo Git.
- [ ] Executar verificações ativas apenas com autorização documentada.

A publicação refere-se ao código-fonte e à documentação no GitHub. Os usuários executam o aplicativo e armazenam seus próprios dados localmente; não é necessário configurar hospedagem ou credenciais de login.
