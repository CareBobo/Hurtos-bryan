"""
Script de prueba para validar la conexión a PostgreSQL Neon.
Usa el conector central src.db.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.db import get_connection, get_connection_string

def main():
    conn_str = get_connection_string()
    if not conn_str:
        print("⚠️ No hay cadena de conexión configurada en el archivo .env.")
        print("Crea un archivo .env en la raíz del proyecto con la variable:")
        print("NEON_CONN=postgresql://usuario:password@ep-xyz.aws.neon.tech/neondb?sslmode=require")
        return

    print("Intentando conectar a PostgreSQL Neon...")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                cur.execute("SELECT current_database();")
                db_name = cur.fetchone()[0]
                print("✅ Conexión a Neon PostgreSQL exitosa!")
                print(f"Versión de PostgreSQL: {version}")
                print(f"Base de datos activa:   {db_name}")
    except Exception as e:
        print(f"❌ Error al conectar a Neon: {e}")

if __name__ == "__main__":
    main()
