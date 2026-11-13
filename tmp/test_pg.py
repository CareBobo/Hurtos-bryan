import os, sys
try:
    import psycopg
except Exception as e:
    print('psycopg import error:', e)
    sys.exit(1)

# intentar conectar usando variables de entorno o fallback
conn_str = os.getenv('LOCAL_PG_CONN', 'postgresql://localhost:5432/postgres')
print('Attempting connection to', conn_str)
try:
    conn = psycopg.connect(conn_str, autocommit=True)
    with conn.cursor() as cur:
        cur.execute('SELECT version();')
        print('PostgreSQL version:', cur.fetchone())
    conn.close()
except Exception as e:
    print('Connection error:', e)
    sys.exit(1)

