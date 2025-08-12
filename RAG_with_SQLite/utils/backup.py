import os
import shutil
from datetime import datetime

DB_FILE = os.path.join(os.getcwd(), 'project_data.db')
BACKUP_DIR = os.path.join(os.getcwd(), 'backups')


def backup_database() -> str:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError(f'Database not found at {DB_FILE}')
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'project_data_{ts}.db')
    shutil.copy2(DB_FILE, backup_path)
    return backup_path
