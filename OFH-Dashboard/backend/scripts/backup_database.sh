#!/bin/bash
#
# PostgreSQL Database Backup Script
# Creates compressed backups with automatic retention
#

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ofh-dashboard}"
DB_USER="${DB_USER:-nina_user}"
DB_NAME="${DB_NAME:-nina_db}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESS="${COMPRESS:-true}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

echo "=========================================="
echo "OFH Dashboard - Database Backup"
echo "=========================================="
echo "Database: $DB_NAME"
echo "Backup location: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo "❌ Error: pg_dump not found. Install PostgreSQL client tools."
    exit 1
fi

# Create backup
echo "📦 Creating database backup..."
if pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_FILE"; then
    echo "✅ Backup created: $BACKUP_FILE"
    
    # Compress backup if enabled
    if [ "$COMPRESS" = "true" ]; then
        echo "🗜️  Compressing backup..."
        gzip "$BACKUP_FILE"
        BACKUP_FILE="${BACKUP_FILE}.gz"
        echo "✅ Backup compressed: $BACKUP_FILE"
    fi
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "📊 Backup size: $BACKUP_SIZE"
    
else
    echo "❌ Backup failed!"
    exit 1
fi

# Clean up old backups
if [ -n "$RETENTION_DAYS" ]; then
    echo ""
    echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.dump*" -mtime +$RETENTION_DAYS)
    
    if [ -n "$OLD_BACKUPS" ]; then
        echo "$OLD_BACKUPS" | while read -r old_backup; do
            echo "   Removing: $(basename "$old_backup")"
            rm -f "$old_backup"
        done
        echo "✅ Old backups cleaned up"
    else
        echo "   No old backups to remove"
    fi
fi

# Display backup summary
echo ""
echo "=========================================="
echo "✅ Backup completed successfully!"
echo "=========================================="
echo "Backup file: $BACKUP_FILE"
echo "Backup size: $BACKUP_SIZE"
echo ""
echo "To restore:"
echo "  pg_restore -U $DB_USER -d $DB_NAME $BACKUP_FILE"
echo ""

