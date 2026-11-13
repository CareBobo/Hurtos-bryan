import os, sys
import psycopg
conn_str = os.getenv('NEON_CONN') or os.getenv('LOCAL_PG_CONN')
if not conn_str:
    print('No connection string found')
    sys.exit(1)
print('Connecting to Neon...')
conn = psycopg.connect(conn_str)
with conn.cursor() as cur:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cur.fetchall()
    print('Tables:', tables)
    for tbl in tables:
        name = tbl[0]
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{name}' ORDER BY ordinal_position;")
        cols = [c[0] for c in cur.fetchall()]
        print(f'{name}: {cols}')
conn.close()

