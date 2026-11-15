import os

import database
from app import UPLOAD_DIR, app

os.makedirs(os.path.dirname(database.DB_PATH), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
database.init_db()