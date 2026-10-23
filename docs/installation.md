# Instalação e execução

O Sentinela é suportado para uso local em **Linux e Windows**. macOS não faz parte da matriz de suporte/testes desta etapa.

## Requisitos

- Python 3.11 ou superior
- PHP CLI 8.0 ou superior (necessário para a interface web local)
- Acesso à internet apenas para instalar dependências e, quando solicitado, consultar a NVD ou auditar alvos autorizados

O Git é necessário apenas para clonar o código-fonte. O Sentinela não exige conta, login, servidor central nem envio de relatórios.

## Linux

Na raiz do repositório, execute:

```bash
bash scripts/install-linux.sh
bash scripts/start-linux.sh
```

Abra `http://127.0.0.1:8080`. Mantenha o terminal aberto enquanto usar o painel; pressione Ctrl+C para encerrar. O script inicia o worker da fila junto com a interface PHP.

Se a criação do ambiente virtual falhar em Debian/Ubuntu, instale o pacote `python3-venv` pela distribuição e rode o instalador novamente. Instale Python e PHP CLI pelo gerenciador de pacotes oficial da sua distribuição.

## Windows (PowerShell)

Instale Python 3.11+ e PHP CLI 8.0+, deixando ambos disponíveis no PATH. Na raiz do repositório, abra PowerShell e execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install-windows.ps1
.\scripts\start-windows.ps1
```

A alteração de política vale apenas para a janela atual do PowerShell. Abra `http://127.0.0.1:8080`; mantenha a janela aberta durante o uso. Para encerrar, pressione Ctrl+C.

## O que a instalação prepara

- Ambiente virtual Python local em `.venv/`.
- Dependências necessárias aos testes.
- Arquivos locais de allowlist copiados dos exemplos, sem autorizar nenhum alvo por padrão.
- Diretório `reports/` para banco SQLite, relatórios e logs locais.

O instalador não instala automaticamente Python nem PHP no sistema operacional; esses requisitos devem estar instalados antes.

## Verificar a instalação

Linux:

```bash
.venv/bin/python -m sentinela.cli --help
.venv/bin/python -m sentinela.cli --version
.venv/bin/python -m sentinela.cli --check-config
.venv/bin/python -m pytest -q
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m sentinela.cli --help
.\.venv\Scripts\python.exe -m sentinela.cli --version
.\.venv\Scripts\python.exe -m sentinela.cli --check-config
.\.venv\Scripts\python.exe -m pytest -q
```

A validação de configuração apenas lê e verifica a estrutura do JSON. Não faz requisições de rede nem executa verificações em ativos.

## Segurança e dados

O painel fica vinculado somente a `127.0.0.1`. Não o exponha na LAN, internet, proxy reverso ou túnel, nem altere o endereço de bind para `0.0.0.0`.

Banco, fila, relatórios, rascunhos e logs permanecem no computador local. Consultas NVD e auditorias autorizadas fazem requisições de rede próprias; isso não é upload de relatórios para um servidor Sentinela. Não apague `reports/` ao atualizar se quiser preservar o histórico local.

Para usar auditoria passiva ou ativa, edite manualmente a allowlist correspondente e inclua somente hostnames para os quais você tenha autorização documentada. A cópia inicial contém apenas comentários e não autoriza alvos.
