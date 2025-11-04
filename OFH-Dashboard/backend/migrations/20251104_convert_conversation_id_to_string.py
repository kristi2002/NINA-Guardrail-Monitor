#!/usr/bin/env python3
"""
Convert conversation_sessions.id from INTEGER to VARCHAR(50).

This migration changes the id column type to match the model definition.
The model expects: id = Column(String(50), primary_key=True, index=True)

WARNING: This migration requires dropping and recreating foreign key constraints
if the table has existing data. For empty tables, it's safe to run.

Safe to re-run; checks if column is already VARCHAR before altering.
"""

import os
import logging
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

TABLE_NAME = 'conversation_sessions'
COLUMN_NAME = 'id'

def check_column_type(conn, column_name: str, is_postgresql: bool) -> str:
    """Check the current data type of a column"""
    try:
        if is_postgresql:
            result = conn.execute(text("""
                SELECT data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = :table_name AND column_name = :column_name
            """), {'table_name': TABLE_NAME, 'column_name': column_name})
            row = result.fetchone()
            if row:
                data_type = row[0].upper()
                if data_type == 'CHARACTER VARYING' or data_type == 'VARCHAR':
                    max_length = row[1]
                    return f"VARCHAR({max_length})" if max_length else "VARCHAR"
                return data_type
        else:
            # SQLite
            result = conn.execute(text("PRAGMA table_info(:table_name)"), {'table_name': TABLE_NAME})
            rows = result.fetchall()
            for row in rows:
                if row[1] == column_name:  # column name is at index 1
                    return row[2].upper()  # data type is at index 2
        return None
    except Exception as e:
        logger.error(f"Error checking column type: {e}")
        return None

def main():
    """Main migration function"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    is_postgresql = database_url.startswith('postgresql://') or database_url.startswith('postgres://')
    
    logger.info(f"Connecting to database: {'PostgreSQL' if is_postgresql else 'SQLite'}")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if table exists
            if is_postgresql:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = :table_name
                    )
                """), {'table_name': TABLE_NAME})
                row = result.fetchone()
                table_exists = row and row[0] if row else False
            else:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=:table_name
                """), {'table_name': TABLE_NAME})
                table_exists = result.fetchone() is not None
            
            if not table_exists:
                logger.warning(f"Table {TABLE_NAME} does not exist. Skipping migration.")
                return
            
            # Check current column type
            current_type = check_column_type(conn, COLUMN_NAME, is_postgresql)
            logger.info(f"Current type of {TABLE_NAME}.{COLUMN_NAME}: {current_type}")
            
            if current_type and ('VARCHAR' in current_type.upper() or 'CHARACTER VARYING' in current_type.upper()):
                logger.info(f"Column {COLUMN_NAME} is already VARCHAR. Migration not needed.")
                return
            
            if not current_type:
                logger.warning(f"Column {COLUMN_NAME} not found. Creating table with correct schema.")
                return
            
            # For PostgreSQL: ALTER COLUMN type
            if is_postgresql:
                logger.info(f"Converting {TABLE_NAME}.{COLUMN_NAME} from {current_type} to VARCHAR(50)...")
                
                # Check if there are foreign key constraints referencing this column
                fk_result = conn.execute(text("""
                    SELECT tc.constraint_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND kcu.column_name = :column_name
                        AND kcu.table_name != :table_name
                """), {'table_name': TABLE_NAME, 'column_name': COLUMN_NAME})
                
                fk_constraints = [row[0] for row in fk_result.fetchall()]
                
                if fk_constraints:
                    logger.warning(f"Found {len(fk_constraints)} foreign key constraint(s) referencing this column.")
                    logger.warning("This migration requires dropping foreign keys. For production, manual migration is recommended.")
                    logger.warning("Skipping automatic migration to prevent data loss.")
                    return
                
                # Check if table has data
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
                row_count = count_result.fetchone()[0]
                
                if row_count > 0:
                    logger.warning(f"Table has {row_count} row(s). Cannot safely convert INTEGER to VARCHAR without data migration.")
                    logger.warning("Please manually migrate data or clear the table first.")
                    return
                
                # Alter column type
                conn.execute(text(f'ALTER TABLE {TABLE_NAME} ALTER COLUMN {COLUMN_NAME} TYPE VARCHAR(50)'))
                conn.commit()
                logger.info(f"✅ Successfully converted {TABLE_NAME}.{COLUMN_NAME} to VARCHAR(50)")
            
            else:
                # SQLite: Requires table recreation
                logger.info("SQLite detected. Converting column type requires table recreation.")
                logger.warning("SQLite migration not implemented. Please recreate the table with VARCHAR id.")
                logger.warning("For SQLite, you can drop and recreate the table if it's empty.")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()

