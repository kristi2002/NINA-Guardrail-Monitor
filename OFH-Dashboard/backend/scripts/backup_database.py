#!/usr/bin/env python3
"""
Database Backup Script for NINA Guardrail Monitor
Creates PostgreSQL database backups with timestamp and optional compression
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

def get_database_config():
    """Get database configuration from environment variables"""
    db_url = os.getenv('DATABASE_URL', '')
    
    if db_url:
        # Parse DATABASE_URL: postgresql://user:password@host:port/dbname
        if db_url.startswith('postgresql://'):
            parts = db_url.replace('postgresql://', '').split('@')
            if len(parts) == 2:
                user_pass = parts[0].split(':')
                host_db = parts[1].split('/')
                if len(user_pass) == 2 and len(host_db) == 2:
                    user = user_pass[0]
                    password = user_pass[1]
                    host_port = host_db[0].split(':')
                    host = host_port[0]
                    port = host_port[1] if len(host_port) > 1 else '5432'
                    dbname = host_db[1]
                    return {
                        'host': host,
                        'port': port,
                        'user': user,
                        'password': password,
                        'dbname': dbname
                    }
    
    # Fallback to individual environment variables
    return {
        'host': os.getenv('POSTGRES_HOST', os.getenv('DATABASE_HOST', 'localhost')),
        'port': os.getenv('POSTGRES_PORT', os.getenv('DATABASE_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', os.getenv('DATABASE_USER', 'nina_user')),
        'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DATABASE_PASSWORD', 'nina_pass')),
        'dbname': os.getenv('POSTGRES_DB', os.getenv('DATABASE_NAME', 'nina_db'))
    }

def create_backup(backup_dir='backups', compress=False, docker_container=None):
    """
    Create a database backup
    
    Args:
        backup_dir: Directory to store backups
        compress: Whether to compress the backup
        docker_container: Docker container name (if running in Docker)
    """
    config = get_database_config()
    
    # Create backup directory
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_path / f"nina_db_backup_{timestamp}.sql"
    if compress:
        backup_file = backup_path / f"nina_db_backup_{timestamp}.sql.gz"
    
    print("=" * 60)
    print("NINA Guardrail Monitor - Database Backup")
    print("=" * 60)
    print(f"Database: {config['dbname']}")
    print(f"Host: {config['host']}:{config['port']}")
    print(f"Backup file: {backup_file}")
    print("=" * 60)
    
    # Build pg_dump command
    if docker_container:
        # Run pg_dump inside Docker container
        cmd = [
            'docker', 'exec', docker_container,
            'pg_dump',
            '-h', 'localhost',  # Inside container, use localhost
            '-U', config['user'],
            '-d', config['dbname'],
            '-F', 'c' if compress else 'p',  # Custom format for compression, plain for uncompressed
            '--no-owner',
            '--no-acl'
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = config['password']
        
        # Execute backup
        try:
            if compress:
                # For compressed backup, pipe through gzip
                with open(backup_file, 'wb') as f:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    gzip_process = subprocess.Popen(
                        ['gzip'],
                        stdin=process.stdout,
                        stdout=f,
                        stderr=subprocess.PIPE
                    )
                    process.stdout.close()
                    stdout, stderr = gzip_process.communicate()
                    if process.returncode != 0:
                        stderr = process.stderr.read()
                        raise subprocess.CalledProcessError(process.returncode, cmd, stderr)
            else:
                with open(backup_file, 'wb') as f:
                    result = subprocess.run(
                        cmd,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        check=True
                    )
        except subprocess.CalledProcessError as e:
            print(f"❌ Backup failed: {e.stderr.decode()}")
            sys.exit(1)
    else:
        # Run pg_dump locally
        cmd = [
            'pg_dump',
            '-h', config['host'],
            '-p', config['port'],
            '-U', config['user'],
            '-d', config['dbname'],
            '-F', 'c' if compress else 'p',
            '--no-owner',
            '--no-acl',
            '-f', str(backup_file)
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = config['password']
        
        try:
            if compress:
                # For compressed backup, pipe through gzip
                with open(backup_file, 'wb') as f:
                    process = subprocess.Popen(
                        cmd[:-1],  # Remove -f flag
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    gzip_process = subprocess.Popen(
                        ['gzip'],
                        stdin=process.stdout,
                        stdout=f,
                        stderr=subprocess.PIPE
                    )
                    process.stdout.close()
                    stdout, stderr = gzip_process.communicate()
                    if process.returncode != 0:
                        stderr = process.stderr.read()
                        raise subprocess.CalledProcessError(process.returncode, cmd, stderr)
            else:
                result = subprocess.run(
                    cmd,
                    env=env,
                    check=True,
                    capture_output=True
                )
        except subprocess.CalledProcessError as e:
            print(f"❌ Backup failed: {e.stderr.decode()}")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ Error: pg_dump not found. Install PostgreSQL client tools.")
            print("   On Ubuntu/Debian: sudo apt-get install postgresql-client")
            print("   On macOS: brew install postgresql")
            print("   On Windows: Install PostgreSQL from https://www.postgresql.org/download/")
            sys.exit(1)
    
    # Get file size
    file_size = backup_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    print(f"✅ Backup created successfully!")
    print(f"   File: {backup_file}")
    print(f"   Size: {size_mb:.2f} MB")
    print("=" * 60)
    
    return backup_file

def restore_backup(backup_file, docker_container=None):
    """
    Restore database from backup
    
    Args:
        backup_file: Path to backup file
        docker_container: Docker container name (if running in Docker)
    """
    config = get_database_config()
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"❌ Error: Backup file not found: {backup_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("NINA Guardrail Monitor - Database Restore")
    print("=" * 60)
    print(f"⚠️  WARNING: This will overwrite the existing database!")
    print(f"Database: {config['dbname']}")
    print(f"Host: {config['host']}:{config['port']}")
    print(f"Backup file: {backup_file}")
    print("=" * 60)
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Restore cancelled.")
        sys.exit(0)
    
    # Determine if backup is compressed
    is_compressed = backup_path.suffix == '.gz'
    
    # Build restore command
    if docker_container:
        if is_compressed:
            # Decompress and restore
            cmd = [
                'docker', 'exec', '-i', docker_container,
                'bash', '-c',
                f'gunzip | psql -h localhost -U {config["user"]} -d {config["dbname"]}'
            ]
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            with open(backup_path, 'rb') as f:
                process = subprocess.Popen(
                    ['gunzip'],
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                restore_process = subprocess.Popen(
                    [
                        'docker', 'exec', '-i', docker_container,
                        'psql',
                        '-h', 'localhost',
                        '-U', config['user'],
                        '-d', config['dbname']
                    ],
                    stdin=process.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                process.stdout.close()
                stdout, stderr = restore_process.communicate()
                if restore_process.returncode != 0:
                    print(f"❌ Restore failed: {stderr.decode()}")
                    sys.exit(1)
        else:
            cmd = [
                'docker', 'exec', '-i', docker_container,
                'psql',
                '-h', 'localhost',
                '-U', config['user'],
                '-d', config['dbname']
            ]
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            with open(backup_path, 'rb') as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    env=env,
                    check=True,
                    capture_output=True
                )
    else:
        if is_compressed:
            # Decompress and restore
            process = subprocess.Popen(
                ['gunzip', '-c', str(backup_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            restore_cmd = [
                'psql',
                '-h', config['host'],
                '-p', config['port'],
                '-U', config['user'],
                '-d', config['dbname']
            ]
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            restore_process = subprocess.Popen(
                restore_cmd,
                stdin=process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            process.stdout.close()
            stdout, stderr = restore_process.communicate()
            if restore_process.returncode != 0:
                print(f"❌ Restore failed: {stderr.decode()}")
                sys.exit(1)
        else:
            cmd = [
                'psql',
                '-h', config['host'],
                '-p', config['port'],
                '-U', config['user'],
                '-d', config['dbname'],
                '-f', str(backup_path)
            ]
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            try:
                result = subprocess.run(
                    cmd,
                    env=env,
                    check=True,
                    capture_output=True
                )
            except FileNotFoundError:
                print("❌ Error: psql not found. Install PostgreSQL client tools.")
                sys.exit(1)
    
    print("✅ Database restored successfully!")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Backup or restore PostgreSQL database')
    parser.add_argument(
        'action',
        choices=['backup', 'restore'],
        help='Action to perform: backup or restore'
    )
    parser.add_argument(
        '--file',
        '-f',
        help='Backup file path (required for restore)'
    )
    parser.add_argument(
        '--dir',
        '-d',
        default='backups',
        help='Backup directory (default: backups)'
    )
    parser.add_argument(
        '--compress',
        '-c',
        action='store_true',
        help='Compress backup (creates .sql.gz file)'
    )
    parser.add_argument(
        '--docker',
        help='Docker container name (e.g., nina-postgres)'
    )
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        create_backup(
            backup_dir=args.dir,
            compress=args.compress,
            docker_container=args.docker
        )
    elif args.action == 'restore':
        if not args.file:
            print("❌ Error: --file is required for restore")
            sys.exit(1)
        restore_backup(
            backup_file=args.file,
            docker_container=args.docker
        )

if __name__ == '__main__':
    main()

