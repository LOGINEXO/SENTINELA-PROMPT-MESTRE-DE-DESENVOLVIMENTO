# Checklist de distribuição open source local

Esta lista é para publicar o código no GitHub e permitir que cada usuário execute sua própria instalação. **Não existe implantação de serviço central.**

## Código e CI

- [ ] Confirmar que o CI de testes Python passou no commit que será distribuído.
- [ ] Confirmar que a sintaxe PHP e o teste da interface local passaram.
- [ ] Confirmar que nenhum segredo, banco, relatório ou allowlist real foi versionado.
- [ ] Manter dependências e instruções de instalação atualizadas.

## Compatibilidade e instalação\n\n- [ ] Executar CI Python em Ubuntu e Windows com Python 3.11 e 3.12.\n- [ ] Validar sintaxe dos scripts de instalação/inicialização de Linux e Windows.\n- [ ] Confirmar que os instaladores preservam allowlists locais já existentes.\n- [ ] Confirmar que o inicializador usa o Python do ambiente virtual e mantém o painel em `127.0.0.1:8080`.\n- [ ] Documentar que macOS não faz parte das plataformas suportadas atualmente.\n\n## Execução local

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
