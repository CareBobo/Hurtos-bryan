"""
Test script for validating the Neon PostgreSQL connection.
It uses the central `get_connection` helper from src.db.
The script prints:
  - PostgreSQL version
  - Current database name (should be 'hurto_colombia')
It never prints the connection string or password.
"""

from src.db import get_connection

def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            cur.execute("SELECT current_database();")
            db_name = cur.fetchone()[0]
            print("✅ Conexión a Neon exitosa")
            print(f"PostgreSQL version: {version}")
            print(f"Base de datos activa: {db_name}")

if __name__ == "__main__":
    main()

