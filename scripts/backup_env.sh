#!/bin/bash
# Backup .env in cartella sicura locale
BACKUP_DIR="$HOME/.dritara_backup"
mkdir -p "$BACKUP_DIR"
cp "$(dirname "$0")/../.env" "$BACKUP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup salvato in $BACKUP_DIR"
ls -la "$BACKUP_DIR"
