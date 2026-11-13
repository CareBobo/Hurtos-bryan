import os, sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).resolve().parents[1]
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

conn_str = os.getenv('NEON_CONN')
if not conn_str:
    sys.exit('NEON_CONN not set')
# Remove surrounding quotes if present
if conn_str.startswith('"') and conn_str.endswith('"'):
    conn_str = conn_str[1:-1]
print('Using connection string:', conn_str)

import psycopg
conn = psycopg.connect(conn_str)
with conn.cursor() as cur:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = [r[0] for r in cur.fetchall()]
    print('Tables:', tables)
    for t in tables:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}' ORDER BY ordinal_position;")
        cols = [c[0] for c in cur.fetchall()]
        print(t, cols)
conn.close()

