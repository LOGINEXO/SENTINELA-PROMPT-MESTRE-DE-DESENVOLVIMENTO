#!/usr/bin/env bash
set -Eeuo pipefail
REPO_URL="https://github.com/LOGINEXO/SENTINELA-PROMPT-MESTRE-DE-DESENVOLVIMENTO/archive/refs/heads/main.zip"
DEST="${HOME}/Sentinela"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "SENTINELA — INSTALADOR LINUX"
echo "Instala dependencias pelo gerenciador da distribuicao; pode solicitar senha sudo."
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y curl unzip ca-certificates python3 python3-venv python3-pip php-cli
  PY="$(command -v python3)"
  VER="$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  if [[ "$(printf '%s\n' "$VER" "3.11" | sort -V | head -n1)" != "3.11" ]]; then
    if grep -qi Ubuntu /etc/os-release; then
      sudo apt-get install -y software-properties-common
      sudo add-apt-repository -y ppa:deadsnakes/ppa
      sudo apt-get update
      sudo apt-get install -y python3.12 python3.12-venv
      PY="$(command -v python3.12)"
    else
      echo "Python encontrado: $VER. E necessario Python 3.11+. Atualize a distribuicao ou instale Python 3.11+." >&2
      exit 2
    fi
  fi
  mkdir -p "$TMP/bin"; ln -sf "$PY" "$TMP/bin/python3"; export PATH="$TMP/bin:$PATH"
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y curl unzip ca-certificates python3.12 python3.12-pip php-cli
  mkdir -p "$TMP/bin"; ln -sf "$(command -v python3.12)" "$TMP/bin/python3"; export PATH="$TMP/bin:$PATH"
elif command -v pacman >/dev/null 2>&1; then
  sudo pacman -Sy --needed --noconfirm curl unzip ca-certificates python python-pip php
else
  echo "Distribuicao nao suportada automaticamente. Suportadas: Debian/Ubuntu/Mint, Fedora e Arch." >&2
  exit 2
fi
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ obrigatorio"'
php -r 'if (PHP_VERSION_ID < 80000) { fwrite(STDERR, "PHP CLI 8.0+ obrigatorio\n"); exit(1); }'
[[ ! -e "$DEST" ]] || DEST="${HOME}/Sentinela-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEST"
curl -fL "$REPO_URL" -o "$TMP/source.zip"
unzip -q "$TMP/source.zip" -d "$TMP/source"
ROOT="$(find "$TMP/source" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
[[ -n "$ROOT" ]] || { echo "Falha ao extrair repositorio." >&2; exit 1; }
cp -a "$ROOT"/. "$DEST"/
bash "$DEST/scripts/install-linux.sh"
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/sentinela.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Sentinela
Comment=Iniciar painel local do Sentinela
Exec=bash -lc 'cd "$DEST" && ./scripts/start-linux.sh'
Terminal=true
Categories=Utility;Security;
EOF
chmod +x "$HOME/.local/share/applications/sentinela.desktop"
echo "Instalacao concluida. Inicie pelo menu de aplicativos ou execute: bash \"$DEST/scripts/start-linux.sh\""
