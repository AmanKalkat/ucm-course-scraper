from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# print(BASE_DIR)
DATABASE_URL = f"sqlite:///{BASE_DIR}/course_catalog.db"