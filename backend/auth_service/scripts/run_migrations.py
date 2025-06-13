import os
import sys
import asyncio
from pathlib import Path

# Ensure /app is in the Python path for Docker
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run database migrations"""
    settings = get_settings()
    print(f"[INFO] Using database URL: {settings.database_url}")
    
    # Get alembic.ini path
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    print(f"[INFO] Using alembic.ini from: {alembic_ini_path}")
    
    # Create alembic config and set database URL programmatically
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    
    print("[INFO] Running Alembic migrations...")
    try:
        command.upgrade(alembic_cfg, "head")
        print("[INFO] Migrations completed successfully")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migrations() 