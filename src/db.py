"""
Módulo central para conexión a PostgreSQL Neon / Local utilizando psycopg v3.
"""
import os
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg

# Cargar variables de entorno desde el .env del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

def get_connection_string():
    conn_str = os.getenv("NEON_CONN") or os.getenv("LOCAL_PG_CONN")
    if not conn_str:
        return None
    # Eliminar comillas accidentales si existen
    conn_str = conn_str.strip()
    if (conn_str.startswith('"') and conn_str.endswith('"')) or (conn_str.startswith("'") and conn_str.endswith("'")):
        conn_str = conn_str[1:-1]
    return conn_str

@contextmanager
def get_connection():
    """Context manager que retorna una conexión activa a PostgreSQL."""
    conn_str = get_connection_string()
    if not conn_str:
        raise ValueError(
            "No se encontró la variable NEON_CONN en el archivo .env. "
            "Por favor crea o edita el archivo .env con tu cadena de conexión de Neon."
        )
    conn = psycopg.connect(conn_str)
    try:
        yield conn
    finally:
        conn.close()
