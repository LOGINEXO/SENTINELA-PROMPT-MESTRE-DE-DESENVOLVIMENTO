# Instalação

## Requisitos

Python 3.11+ e pip.

## Ambiente virtual

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

## Validar a fundação

```bash
python -m sentinela.cli --help
python -m sentinela.cli --version
python -m pytest
```

Os comandos de CLI nesta etapa não fazem requisições de rede nem executam verificações em ativos.
