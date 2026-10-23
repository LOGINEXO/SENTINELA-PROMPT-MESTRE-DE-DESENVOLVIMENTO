#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
command -v php >/dev/null 2>&1 || { echo "ERRO: PHP 8.0+ não encontrado." >&2; exit 1; }
[[ -x "$PYTHON" ]] || { echo "ERRO: ambiente não instalado. Execute ./scripts/install-linux.sh primeiro." >&2; exit 1; }
php -r 'exit(version_compare(PHP_VERSION, "8.0.0", ">=") ? 0 : 1);' || { echo "ERRO: é necessário PHP 8.0 ou superior." >&2; exit 1; }

mkdir -p reports
export SENTINELA_PYTHON="$PYTHON"
"$PYTHON" -m sentinela.queue_worker > reports/worker.log 2>&1 &
WORKER_PID=$!
cleanup() {
  kill "$WORKER_PID" 2>/dev/null || true
  wait "$WORKER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

printf 'Sentinela ativo em http://127.0.0.1:8080\n'
printf 'Mantenha este terminal aberto. Pressione Ctrl+C para encerrar.\n'
php -S 127.0.0.1:8080 -t web
