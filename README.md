# Sentinela

Plataforma modular de inteligência e auditoria de segurança defensiva. O Sentinela está em fase inicial de fundação; os módulos de coleta e auditoria ainda não estão implementados.

## Requisitos

- Python 3.11 ou superior
- Git
- pytest para executar os testes

A fundação utiliza a biblioteca padrão do Python. Nenhuma requisição de rede é executada nesta etapa.

## Instalação

```bash
python -m venv .venv
```

Ative o ambiente:
- Windows PowerShell: .venv\\Scripts\\Activate.ps1
- Linux/macOS: source .venv/bin/activate

Instale as dependências de desenvolvimento:

```bash
python -m pip install -r requirements.txt
```

## Verificação inicial

```bash
python -m sentinela.cli --help
python -m pytest
```

## Estado do projeto

- [x] Etapa 1 — Fundação inicial, configuração de exemplo, documentação e testes básicos
- [ ] Etapa 2 — Inteligência pública (NVD/CVE)
- [ ] Etapa 3 — Relatórios locais
- [ ] Etapa 4 — Auditoria passiva
- [ ] Etapa 5 — Controle de escopo e mitigação de SSRF/DNS rebinding
- [ ] Etapa 6 — Interface PHP
- [ ] Etapa 7 — Fila e controles PLAY/PAUSE/STOP
- [ ] Etapa 8 — Rascunhos de e-mail e revisão manual
- [ ] Etapa 9 — Testes ativos autorizados
- [ ] Etapa 10 — Revisão e publicação

A marcação da Etapa 1 indica a estrutura inicial, não substitui a execução local dos testes nem representa uma auditoria de segurança completa.

## Princípios de segurança

- Inteligência pública não concede autorização para testar um ativo.
- Testes ativos devem exigir escopo e autorização explícitos.
- Não armazenar segredos, tokens, cookies de sessão ou respostas completas potencialmente sensíveis.
- Configurações locais e relatórios devem permanecer fora da raiz pública do servidor.
- Não execute verificações contra sistemas de terceiros sem autorização válida.

Consulte docs/security.md, docs/architecture.md e docs/responsible-disclosure.md.

## Configuração

Copie .env.example para um arquivo local .env se necessário. Não coloque credenciais reais no Git. O arquivo config/settings.example.json é apenas um modelo sem segredos.

## Contribuição

Contribuições são bem-vindas. Leia a documentação de segurança e abra uma issue para discutir alterações arquiteturais antes de adicionar módulos que façam requisições de rede.

## Licença

Este projeto é distribuído sob a licença MIT. Consulte LICENSE.
