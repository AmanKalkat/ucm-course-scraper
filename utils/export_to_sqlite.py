import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
import json

load_dotenv()

def export_to_sqlite():
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')

    pg_connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    pg_engine = create_engine(pg_connection_string)

    df = pd.read_sql_table('courses', con=pg_engine)

    # Convert list/dict columns to JSON strings for SQLite compatibility
    json_columns = ['prereqs', 'coreqs', 'class_levels', 'credits']
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.dumps(x) if x is not None else None)

    sqlite_path = '../course_catalog.db'
    sqlite_connection_string = f'sqlite:///{sqlite_path}'
    sqlite_engine = create_engine(sqlite_connection_string)

    print(f"Exporting {len(df)} rows to SQLite file")
    df.to_sql('courses', con=sqlite_engine, if_exists='replace', index=False)

    print(f"Successfully exported to {sqlite_path}")
    print(f"  - Total rows: {len(df)}")
    print(f"  - Columns: {', '.join(df.columns)}")

if __name__ == "__main__":
    export_to_sqlite()
