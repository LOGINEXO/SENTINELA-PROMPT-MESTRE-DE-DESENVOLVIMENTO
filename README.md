# Sentinela

Plataforma modular de inteligência e auditoria de segurança defensiva. O projeto está na **Etapa 1 — Fundação**. Nesta etapa, o CLI valida configurações locais; ainda não há coleta de inteligência, scanners, interface web ou execução automática.

## Requisitos

- Python 3.11 ou superior
- Git
- pip

O código de execução da fundação usa apenas a biblioteca padrão do Python. pytest é usado nos testes. Nenhuma requisição de rede é feita.

## Instalação

Crie e ative um ambiente virtual.

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

## Verificação

Na raiz do repositório:

~~~bash
python -m sentinela.cli --help
python -m sentinela.cli --version
python -m sentinela.cli --check-config
python -m pytest -q
~~~

Para validar outro arquivo JSON:

~~~bash
python -m sentinela.cli --check-config caminho/para/settings.json
~~~

A validação é local. Ela não inicia scanners, não acessa hosts e não cria arquivos de relatório.

## Estrutura atual

- **sentinela/**: pacote Python e CLI da fundação.
- **config/**: exemplos de configuração e de escopo autorizado.
- **tests/**: testes automatizados da fundação e da validação de configuração.
- **docs/**: arquitetura, instalação e políticas de segurança.
- **reports/**: diretório reservado para relatórios locais; conteúdo gerado é ignorado pelo Git.
- **.github/workflows/tests.yml**: execução automatizada dos testes no GitHub Actions.

## Etapas do projeto

- [ ] Etapa 1 — Fundação: estrutura, configuração, ambiente, documentação e testes básicos; aguardando validação final no CI.
- [ ] Etapa 2 — Inteligência pública (NVD/CVE).
- [ ] Etapa 3 — Relatórios locais.
- [ ] Etapa 4 — Auditoria passiva.
- [ ] Etapa 5 — Controle de escopo e mitigação de SSRF/DNS rebinding.
- [ ] Etapa 6 — Interface PHP.
- [ ] Etapa 7 — Fila e controles PLAY/PAUSE/STOP.
- [ ] Etapa 8 — Rascunhos de e-mail e revisão manual.
- [ ] Etapa 9 — Testes ativos autorizados.
- [ ] Etapa 10 — Revisão e publicação.

Cada etapa será implementada e validada separadamente. A conclusão da Etapa 1 não significa que os módulos das etapas seguintes já existam.

## Princípios de segurança

- Inteligência pública não concede autorização para testar um ativo.
- Testes ativos futuros devem exigir escopo e autorização explícitos.
- Não armazene segredos, tokens, cookies de sessão ou respostas completas potencialmente sensíveis.
- Mantenha configurações locais e relatórios fora da raiz pública de qualquer servidor.
- Não execute verificações contra sistemas de terceiros sem autorização válida.
- A configuração de exemplo mantém rede desabilitada e exige autorização para futuras verificações ativas.

Consulte docs/architecture.md, docs/installation.md, docs/security.md e docs/responsible-disclosure.md.

## Configuração

.env.example e config/settings.example.json contêm apenas valores de exemplo. Não coloque credenciais reais no Git. O arquivo config/authorized_targets.example.txt é apenas um modelo e não concede autorização.

## Contribuição

Antes de propor novos módulos, leia a arquitetura e a política de segurança. Não declare funcionalidades concluídas sem testes reais e resultados verificáveis.

## Licença

Licença MIT. Consulte LICENSE.
