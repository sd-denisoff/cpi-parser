from pathlib import Path

from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = 'db.sqlite3'
ENGINE = create_engine(f'sqlite:////{BASE_DIR}/{DB_NAME}')
