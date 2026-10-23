# Sentinela

Plataforma modular de inteligência pública e auditoria defensiva de segurança. A **Etapa 1 — Fundação** foi validada no GitHub Actions; a **Etapa 2 — Inteligência pública** implementa consultas explícitas à API NVD/CVE 2.0. Não há scanner de ativos nesta etapa.

## Requisitos

- Python 3.11 ou superior
- Git
- pip

O motor usa a biblioteca padrão do Python. pytest é usado nos testes. A rede só é acessada quando uma consulta NVD é solicitada explicitamente pela CLI.

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
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
~~~

## Verificação local

~~~bash
python -m sentinela.cli --help
python -m sentinela.cli --version
python -m sentinela.cli --check-config
python -m pytest -q
~~~

## Consultar inteligência pública NVD/CVE

Busca por palavra-chave (consulta a API oficial; exige conectividade com a internet):

~~~bash
python -m sentinela.cli --nvd-search "OpenSSH" --limit 10
python -m sentinela.cli --nvd-search "OpenSSH" --modified-since "2026-10-01T00:00:00Z"
~~~

Consultar um CVE específico:

~~~bash
python -m sentinela.cli --nvd-cve CVE-2024-3094
~~~

Opcionalmente, defina NVD_API_KEY no ambiente para autenticar as consultas e receber a cota aplicável à chave. Não coloque a chave em arquivos versionados. Sem chave, a NVD pode aplicar limites mais restritos. O cliente usa timeout, limita a consulta a 100 resultados, informa erros de rede/limite e não repete requisições automaticamente.

A busca incremental aceita --modified-since e --modified-until com datas ISO 8601 e fuso horário; a janela máxima é de 120 dias conforme as regras da NVD. Os resultados normalizados incluem CVE, descrição, datas, estado, CVSS quando disponível, faixa de prioridade técnica derivada do CVSS, produtos/intervalos afetados indicados pela NVD e referências. Um indicador público **não comprova** que um site específico seja vulnerável: asset_confirmed permanece false e validation_status é new_public_indicator.

## Estrutura

- **sentinela/**: pacote Python e CLI.
- **sentinela/intelligence/nvd.py**: cliente e normalizador da API NVD 2.0.
- **config/**: exemplos de configuração e escopo autorizado.
- **tests/**: testes automatizados, incluindo respostas NVD simuladas sem chamadas externas.
- **docs/**: arquitetura, instalação e políticas de segurança.
- **reports/**: diretório reservado para relatórios locais.
- **.github/workflows/tests.yml**: testes automatizados no GitHub Actions.

## Etapas do projeto

- [x] Etapa 1 — Fundação: estrutura, configuração, documentação, testes básicos e CI validado.
- [ ] Etapa 2 — Inteligência pública: cliente NVD/CVE, normalização, erros e testes simulados; aguardando validação do CI desta versão.
- [ ] Etapa 3 — Relatórios locais.
- [ ] Etapa 4 — Auditoria passiva.
- [ ] Etapa 5 — Controle de escopo e mitigação de SSRF/DNS rebinding.
- [ ] Etapa 6 — Interface PHP.
- [ ] Etapa 7 — Fila e controles PLAY/PAUSE/STOP.
- [ ] Etapa 8 — Rascunhos de e-mail e revisão manual.
- [ ] Etapa 9 — Testes ativos autorizados.
- [ ] Etapa 10 — Revisão e publicação.

Cada etapa será implementada e validada separadamente. Não há consulta automática contínua, exploração de alvos, auditoria de sites nem envio de e-mails nesta etapa.

## Princípios de segurança

- Inteligência pública não concede autorização para testar um ativo.
- Testes ativos futuros exigirão escopo e autorização explícitos.
- Não armazene segredos, tokens, cookies de sessão ou respostas completas potencialmente sensíveis.
- Mantenha configurações privadas e relatórios fora da raiz pública de qualquer servidor.
- Não execute verificações contra sistemas de terceiros sem autorização válida.
- Arquivos de exemplo são modelos e não concedem autorização.

Consulte docs/architecture.md, docs/installation.md, docs/security.md e docs/responsible-disclosure.md.

## Configuração

.env.example e config/settings.example.json contêm somente valores de exemplo. A variável opcional NVD_API_KEY deve ser definida fora do repositório.

## Licença

Licença MIT. Consulte LICENSE.
