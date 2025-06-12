import os
import sys
import asyncio
from pathlib import Path

# Ensure /app is in the Python path for Docker
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run database migrations"""
    settings = get_settings()
    print(f"[DEBUG] Using database URL: {settings.database_url}")
    
    # Update alembic.ini with the correct database URL
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    print(f"[DEBUG] Reading alembic.ini from: {alembic_ini_path}")
    with open(alembic_ini_path, "r") as f:
        content = f.read()
    print("[DEBUG] alembic.ini before replacement:\n" + content)
    
    # Replace the placeholder database URL with the actual one
    if "sqlalchemy.url = driver://user:pass@localhost/dbname" not in content:
        print("[ERROR] Placeholder for sqlalchemy.url not found in alembic.ini!")
    content = content.replace(
        "sqlalchemy.url = driver://user:pass@localhost/dbname",
        f"sqlalchemy.url = {settings.database_url}"
    )
    print("[DEBUG] alembic.ini after replacement:\n" + content)
    
    with open(alembic_ini_path, "w") as f:
        f.write(content)
    print("[DEBUG] alembic.ini updated successfully.")
    
    # Run the migrations using alembic's API
    print("[DEBUG] Running Alembic migrations...")
    alembic_cfg = Config(alembic_ini_path)
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    run_migrations() 