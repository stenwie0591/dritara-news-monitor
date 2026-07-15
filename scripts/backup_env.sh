#!/bin/bash
# Backup .env in cartella sicura locale
set -eu
umask 077
BACKUP_DIR="$HOME/.dritara_backup"
SOURCE="$(dirname "$0")/../.env"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
chmod 600 "$SOURCE"
DESTINATION="$BACKUP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
cp "$SOURCE" "$DESTINATION"
chmod 600 "$DESTINATION"
echo "✅ Backup salvato in $BACKUP_DIR"
