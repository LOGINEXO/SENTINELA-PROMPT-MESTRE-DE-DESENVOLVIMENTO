# Instalação

## Requisitos

- Python 3.11 ou superior
- pip

## Ambiente virtual

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

## Validar a fundação

Execute na raiz do repositório:

~~~bash
python -m sentinela.cli --help
python -m sentinela.cli --version
python -m sentinela.cli --check-config
python -m pytest -q
~~~

Para validar um arquivo próprio, use:

~~~bash
python -m sentinela.cli --check-config caminho/para/settings.json
~~~

A validação apenas lê e verifica a estrutura do JSON. Não faz requisições de rede nem executa verificações em ativos. O arquivo de exemplo deve permanecer sem segredos.
