"""
Central module for connecting to Neon PostgreSQL using psycopg (version 3).

Usage example:
    from src.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            print(cur.fetchone())
"""

import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg

# Load environment variables from .env (searches parent directories as well)
load_dotenv()

NEON_CONN = os.getenv("NEON_CONN")
if not NEON_CONN:
    # Fallback to a local PostgreSQL instance for development / testing
    NEON_CONN = os.getenv("LOCAL_PG_CONN", "postgresql://localhost:5432/postgres")
    if not NEON_CONN:
        raise RuntimeError(
            "NEON_CONN not found in environment and no fallback provided. Set .env or LOCAL_PG_CONN."
        )

@contextmanager
def get_connection():
    """Context manager that yields a psycopg2 connection and closes it automatically."""
    conn = psycopg.connect(NEON_CONN)
    try:
        yield conn
    finally:
        conn.close()
