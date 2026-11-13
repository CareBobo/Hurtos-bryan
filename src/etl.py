import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from pathlib import Path


def load_raw(data_dir: Path = Path('data/raw')) -> pd.DataFrame:
    """Load raw CSV files from the data/raw directory.
    Currently loads the first CSV found; extend as needed.
    """
    csv_files = list(data_dir.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(f'No CSV files found in {data_dir}')
    return pd.read_csv(csv_files[0])


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder for data cleaning / feature engineering.
    For now, just returns the original DataFrame.
    """
    # Example: drop rows with missing values
    return df.dropna()


def save_processed(df: pd.DataFrame, out_dir: Path = Path('data/processed')):
    """Save the processed DataFrame to CSV.
    Creates the output directory if it does not exist.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'processed.csv'
    df.to_csv(out_path, index=False)
    return out_path


def get_engine() -> create_engine:
    """Create a SQLAlchemy engine using .env variables.
    This function will be fleshed out later when Neon connection details are added.
    """
    from dotenv import load_dotenv
    import os
    load_dotenv()
    # Placeholder – will be replaced with actual connection string.
    return create_engine('postgresql+psycopg2://')

if __name__ == '__main__':
    raw_df = load_raw()
    processed_df = process_data(raw_df)
    save_processed(processed_df)
    print('ETL pipeline executed successfully.')

