import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, types
from sqlalchemy.dialects.postgresql import JSONB
import json

load_dotenv()

def parse_list_field(value):
    if pd.isna(value):
        return None

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        value_json = value.replace("'", '"')
        try:
            parsed = json.loads(value_json)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            clean_val = value.strip()
            return [clean_val] if clean_val else None

    return None


def parse_credits_field(value):
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        value_json = value.replace("'", '"')
        try:
            parsed = json.loads(value_json)
            if isinstance(parsed, list):
                return parsed
            return int(parsed)
        except json.JSONDecodeError:
            try:
                return int(value)
            except ValueError:
                return None

    return None

def prep_dataframe(df):
    df.columns = df.columns.str.replace(' ', '_')

    #will be converted str -> JSON
    list_columns = ['prereqs', 'coreqs', 'class_levels']

    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: parse_list_field(x))

    if 'credits' in df.columns:
        df['credits'] = df['credits'].apply(lambda x: parse_credits_field(x))

    return df

def load_excel_to_db(excel_path, catalog_year, engine, if_exists='append'):
    df = pd.read_excel(excel_path, na_values=["N/A"])
    df = prep_dataframe(df)

    # Add catalog_year column
    df['catalog_year'] = catalog_year

    data_types = {
        'catalog_year': types.String(10),
        'course_code': types.String(15),
        'course_name': types.String(255),
        'credits': JSONB,
        'course_description': types.Text,
        'prereqs': JSONB,
        'coreqs': JSONB,
        'class_levels': JSONB,
        'repeats_allowed_for_credit': types.Integer
    }

    df.to_sql(
        name='courses',
        con=engine,
        if_exists=if_exists,
        index=False,
        dtype=data_types
    )

    print(f"Successfully loaded {len(df)} rows from {excel_path} to 'courses' table with catalog_year '{catalog_year}'")

def create_db_engine():
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')

    connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    return create_engine(connection_string)

def main():
    engine = create_db_engine()

    spreadsheets_dir = Path('../spreadsheets')
    excel_files = list(spreadsheets_dir.glob('*.xlsx'))

    print(f"Found {len(excel_files)} Excel files to process")

    # Use 'replace' for the first file, 'append' for subsequent files
    first_file = True

    for excel_file in excel_files:
        # Extract catalog year from filename (e.g., '2024_2025' from '2024_2025.xlsx')
        catalog_year = excel_file.stem

        print(f"\nProcessing {excel_file.name}...")
        try:
            load_excel_to_db(
                excel_path=excel_file,
                catalog_year=catalog_year,
                engine=engine,
                if_exists='replace' if first_file else 'append'
            )
            first_file = False
        except Exception as e:
            print(f"Error with {excel_file.name}: {e}")

    print("\nAll files added to DB.")


if __name__ == "__main__":
    main()