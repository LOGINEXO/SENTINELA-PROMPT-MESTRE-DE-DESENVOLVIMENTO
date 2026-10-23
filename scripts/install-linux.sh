#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() { printf 'ERRO: %s\n' "$*" >&2; exit 1; }

command -v python3 >/dev/null 2>&1 || fail "Python 3.11+ não encontrado. Instale Python 3 e o módulo venv pelo gerenciador de pacotes da sua distribuição."
PYTHON="$(command -v python3)"
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || fail "É necessário Python 3.11 ou superior."
command -v php >/dev/null 2>&1 || fail "PHP 8.0+ não encontrado. Instale PHP CLI pelo gerenciador de pacotes da sua distribuição."
php -r 'exit(version_compare(PHP_VERSION, "8.0.0", ">=") ? 0 : 1);' || fail "É necessário PHP 8.0 ou superior."

if ! "$PYTHON" -m venv .venv; then
  fail "Não foi possível criar o ambiente virtual. Em Debian/Ubuntu, instale também o pacote python3-venv."
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

[[ -e config/authorized_targets.txt ]] || cp config/authorized_targets.example.txt config/authorized_targets.txt
[[ -e config/authorized_active_targets.txt ]] || cp config/authorized_active_targets.example.txt config/authorized_active_targets.txt
mkdir -p reports

printf '\nInstalação concluída. Para iniciar, execute:\n  ./scripts/start-linux.sh\n'
printf 'Depois abra http://127.0.0.1:8080 no navegador.\n'
