# -*- coding: utf-8 -*-
"""
load_to_neon.py
----------------
ETL que:
1️⃣ Lee el CSV original (texto, sin transformación) y lo inserta en la tabla de staging (stg_hurtos).
2️⃣ Poblado de todas las dimensiones (dim_fecha, dim_departamento, dim_municipio, dim_arma_medio,
   dim_tipo_hurto, dim_genero con placeholder DESCONOCIDO, dim_grupo_etario con placeholder DESCONOCIDO).
3️⃣ Inserción en la tabla de hechos (fact_hurtos) enlazando todas las FK. Los valores nulos de GENERO y
   GRUPO_ETARIO se mapean al registro DESCONOCIDO.
4️⃣ Genera un log sencillo (logs/load_log.txt) con timestamps y contadores.
"""

import csv
import os
from pathlib import Path
from datetime import datetime

import sys
sys.path.append(os.path.abspath(os.path.join(Path(__file__).resolve().parents[1])))

from src.db import get_connection

# -----------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------
# Ruta del CSV relativa al directorio raíz del proyecto (un nivel arriba de src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "load_log.txt"

PLACEHOLDER_GENERO = "DESCONOCIDO"
PLACEHOLDER_GRUPO = "DESCONOCIDO"

def log(message: str):
    """Append a line with timestamp to the log file and also print it."""
    ts = datetime.utcnow().isoformat()
    line = f"{ts} - {message}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)
    print(message)

# -----------------------------------------------------------------
# 1️⃣ Staging (COPY)
# -----------------------------------------------------------------
def load_staging(conn):
    # Definir columnas, usando comillas dobles donde sea necesario
    cols = [
        "csv_row_num",
        "DEPARTAMENTO",
        "MUNICIPIO",
        "\"CODIGO DANE\"",
        "\"ARMAS MEDIOS\"",
        "\"FECHA HECHO\"",
        "GENERO",
        "\"GRUPO ETARIO\"",
        "\"TIPO DE HURTO\"",
        "CANTIDAD",
    ]
    batch = []
    batch_size = 10_000
    with conn.cursor() as cur:
        # Vaciar tablas respetando FK: primero fact_hurtos, luego stg_hurtos
        cur.execute("TRUNCATE TABLE fact_hurtos, stg_hurtos RESTART IDENTITY;")
        
        with CSV_PATH.open(mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=",", quotechar='"')
            for i, row in enumerate(reader, start=1):
                batch.append(
                    (
                        i,
                        row["DEPARTAMENTO"],
                        row["MUNICIPIO"],
                        row["CODIGO DANE"],
                        row["ARMAS MEDIOS"],
                        row["FECHA HECHO"],
                        row["GENERO"] if row["GENERO"] else None,
                        row["GRUPO ETARIO"] if row["GRUPO ETARIO"] else None,
                        row["TIPO DE HURTO"],
                        row["CANTIDAD"],
                    )
                )
                if len(batch) >= batch_size:
                    _copy_batch(cur, cols, batch)
                    batch.clear()
            if batch:
                _copy_batch(cur, cols, batch)
    # Verificar que la carga en staging haya insertado filas
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM stg_hurtos;")
        debug_cnt = cur.fetchone()[0]
        log(f"✅ Staging carga verificadas, {debug_cnt} filas en stg_hurtos.")
    log("✅ Staging cargado (656 635 filas).")
    # Definir columnas, usando comillas dobles donde sea necesario
    cols = [
        "csv_row_num",
        "DEPARTAMENTO",
        "MUNICIPIO",
        "\"CODIGO DANE\"",
        "\"ARMAS MEDIOS\"",
        "\"FECHA HECHO\"",
        "GENERO",
        "\"GRUPO ETARIO\"",
        "\"TIPO DE HURTO\"",
        "CANTIDAD",
    ]
    batch = []
    batch_size = 10_000
    with conn.cursor() as cur:
        # Vaciar tablas respetando FK: primero fact_hurtos, luego stg_hurtos
        cur.execute("TRUNCATE TABLE fact_hurtos, stg_hurtos RESTART IDENTITY;")
        
        with CSV_PATH.open(mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=",", quotechar='"')
            for i, row in enumerate(reader, start=1):
                batch.append(
                    (
                        i,
                        row["DEPARTAMENTO"],
                        row["MUNICIPIO"],
                        row["CODIGO DANE"],
                        row["ARMAS MEDIOS"],
                        row["FECHA HECHO"],
                        row["GENERO"] if row["GENERO"] else None,
                        row["GRUPO ETARIO"] if row["GRUPO ETARIO"] else None,
                        row["TIPO DE HURTO"],
                        row["CANTIDAD"],
                    )
                )
                if len(batch) >= batch_size:
                    _copy_batch(cur, cols, batch)
                    batch.clear()
            if batch:
                _copy_batch(cur, cols, batch)
    log("✅ Staging cargado (656 635 filas).")

def _copy_batch(cur, cols, batch):
    """Helper that streams a batch to PostgreSQL via COPY using psycopg3 API.
    Uses the native psycopg3 `.copy` method for streaming COPY FROM STDIN.
    """
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    for row in batch:
        writer.writerow([v if v is not None else "\\N" for v in row])
    buffer.seek(0)
    copy_sql = f"COPY stg_hurtos ({', '.join(cols)}) FROM STDIN WITH CSV"
    # Use psycopg3's copy method (compatible with both text and binary formats)
    cur.copy(copy_sql, buffer)
    """Helper that streams a batch to PostgreSQL via COPY using psycopg3 API.
    Uses copy_expert for full compatibility with the TEXT format.
    """
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    for row in batch:
        writer.writerow([v if v is not None else "\\N" for v in row])
    buffer.seek(0)
    copy_sql = f"COPY stg_hurtos ({', '.join(cols)}) FROM STDIN WITH CSV"
    # copy_expert works with both psycopg2 and psycopg3
    cur.copy_expert(sql=copy_sql, file=buffer)
    """Helper that streams a batch to PostgreSQL via COPY using psycopg3 API."""
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    for row in batch:
        writer.writerow([v if v is not None else "\\N" for v in row])
    buffer.seek(0)
    copy_sql = f"COPY stg_hurtos ({', '.join(cols)}) FROM STDIN WITH CSV"
    # psycopg3 uses .copy for streaming COPY FROM STDIN
    cur.copy(copy_sql, buffer)
    """Helper that streams a batch to PostgreSQL via COPY using psycopg3 API."""
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    for row in batch:
        writer.writerow([v if v is not None else "\\N" for v in row])
    buffer.seek(0)
    copy_sql = f"COPY stg_hurtos ({', '.join(cols)}) FROM STDIN WITH CSV"
    # Use copy_expert for compatibility with psycopg3
    cur.copy_expert(sql=copy_sql, file=buffer)
    """Helper that streams a batch to PostgreSQL via COPY using psycopg3 API."""
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    for row in batch:
        writer.writerow([v if v is not None else "\\N" for v in row])
    buffer.seek(0)
    copy_sql = f"COPY stg_hurtos ({', '.join(cols)}) FROM STDIN WITH CSV"
    cur.copy(copy_sql, buffer)

# -----------------------------------------------------------------
# 2️⃣ Poblado de dimensiones
# -----------------------------------------------------------------
def load_dim_fecha(conn):
    sql = """
        INSERT INTO dim_fecha (fecha, año, mes, dia, trimestre, semana_del_año, dia_semana)
        SELECT DISTINCT
            to_date("FECHA HECHO", 'DD/MM/YYYY') AS fecha,
            EXTRACT(YEAR FROM to_date("FECHA HECHO", 'DD/MM/YYYY'))::int   AS año,
            EXTRACT(MONTH FROM to_date("FECHA HECHO", 'DD/MM/YYYY'))::int  AS mes,
            EXTRACT(DAY FROM to_date("FECHA HECHO", 'DD/MM/YYYY'))::int    AS dia,
            EXTRACT(QUARTER FROM to_date("FECHA HECHO", 'DD/MM/YYYY'))::int AS trimestre,
            EXTRACT(WEEK FROM to_date("FECHA HECHO", 'DD/MM/YYYY'))::int   AS semana_del_año,
            TO_CHAR(to_date("FECHA HECHO", 'DD/MM/YYYY'), 'Day')            AS dia_semana
        FROM stg_hurtos;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    log("✅ dim_fecha poblada.")

def load_dim_departamento(conn):
    sql = """
        INSERT INTO dim_departamento (nombre)
        SELECT DISTINCT UPPER(TRIM(DEPARTAMENTO))
        FROM stg_hurtos
        WHERE DEPARTAMENTO IS NOT NULL AND DEPARTAMENTO <> '';
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    log("✅ dim_departamento poblada.")

def load_dim_municipio(conn):
    sql = """
        INSERT INTO dim_municipio (nombre, codigo_dane, dim_depto_id)
        SELECT
            m.MUNICIPIO,
            m."CODIGO DANE",
            d.dim_depto_id
        FROM (
            SELECT DISTINCT MUNICIPIO, "CODIGO DANE", DEPARTAMENTO
            FROM stg_hurtos
            WHERE MUNICIPIO IS NOT NULL AND MUNICIPIO <> ''
        ) m
        JOIN dim_departamento d
          ON d.nombre = UPPER(TRIM(m.DEPARTAMENTO));
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    log("✅ dim_municipio poblada.")

def load_dim_arma_medio(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dim_arma_medio (descripcion) VALUES (%s) ON CONFLICT DO NOTHING;", (PLACEHOLDER_GENERO,))
        cur.execute(
            """
            INSERT INTO dim_arma_medio (descripcion)
            SELECT DISTINCT "ARMAS MEDIOS"
            FROM stg_hurtos
            WHERE "ARMAS MEDIOS" IS NOT NULL AND "ARMAS MEDIOS" <> '';
            """
        )
    log("✅ dim_arma_medio poblada.")

def load_dim_tipo_hurto(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dim_tipo_hurto (descripcion) VALUES (%s) ON CONFLICT DO NOTHING;", (PLACEHOLDER_GENERO,))
        cur.execute(
            """
            INSERT INTO dim_tipo_hurto (descripcion)
            SELECT DISTINCT "TIPO DE HURTO"
            FROM stg_hurtos
            WHERE "TIPO DE HURTO" IS NOT NULL AND "TIPO DE HURTO" <> '';
            """
        )
    log("✅ dim_tipo_hurto poblada.")

def load_dim_genero(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dim_genero (valor) VALUES (%s) ON CONFLICT DO NOTHING;", (PLACEHOLDER_GENERO,))
        cur.execute(
            """
            INSERT INTO dim_genero (valor)
            SELECT DISTINCT GENERO
            FROM stg_hurtos
            WHERE GENERO IS NOT NULL AND GENERO <> '';
            """
        )
    log("✅ dim_genero poblada.")

def load_dim_grupo_etario(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dim_grupo_etario (rango) VALUES (%s) ON CONFLICT DO NOTHING;", (PLACEHOLDER_GRUPO,))
        cur.execute(
            """
            INSERT INTO dim_grupo_etario (rango)
            SELECT DISTINCT "GRUPO ETARIO"
            FROM stg_hurtos
            WHERE "GRUPO ETARIO" IS NOT NULL AND "GRUPO ETARIO" <> '';
            """
        )
    log("✅ dim_grupo_etario poblada.")

def load_all_dimensions(conn):
    load_dim_fecha(conn)
    load_dim_departamento(conn)
    load_dim_municipio(conn)
    load_dim_arma_medio(conn)
    load_dim_tipo_hurto(conn)
    load_dim_genero(conn)
    load_dim_grupo_etario(conn)

# -----------------------------------------------------------------
# 3️⃣ Carga de la tabla de hechos
# -----------------------------------------------------------------
def load_fact_hurtos(conn):
    sql = """
        INSERT INTO fact_hurtos (
            csv_row_num,
            dim_fecha_id,
            dim_muni_id,
            dim_arma_id,
            dim_genero_id,
            dim_grupo_id,
            dim_tipo_id,
            cantidad
        )
        SELECT
            s.csv_row_num,
            f.dim_fecha_id,
            m.dim_muni_id,
            a.dim_arma_id,
            g.dim_genero_id,
            gt.dim_grupo_id,
            t.dim_tipo_id,
            CAST(s.CANTIDAD AS INT)
        FROM stg_hurtos s
        JOIN dim_fecha f      ON f.fecha = to_date(s."FECHA HECHO", 'DD/MM/YYYY')
        JOIN dim_departamento d ON d.nombre = UPPER(TRIM(s.DEPARTAMENTO))
        JOIN dim_municipio m   ON m.nombre = s.MUNICIPIO
                                   AND m.codigo_dane = s."CODIGO DANE"
                                   AND m.dim_depto_id = d.dim_depto_id
        JOIN dim_arma_medio a  ON a.descripcion = s."ARMAS MEDIOS"
        JOIN dim_genero g      ON g.valor = COALESCE(s.GENERO, %s)
        JOIN dim_grupo_etario gt ON gt.rango = COALESCE(s."GRUPO ETARIO", %s)
        JOIN dim_tipo_hurto t  ON t.descripcion = s."TIPO DE HURTO";
    """
    with conn.cursor() as cur:
        cur.execute(sql, (PLACEHOLDER_GENERO, PLACEHOLDER_GRUPO))
        # Obtener número de filas insertadas
        cur.execute("SELECT COUNT(*) FROM fact_hurtos;")
        filas_insertadas = cur.fetchone()[0]
    log(f"✅ fact_hurtos cargada ({filas_insertadas:,} filas).")
    sql = """
        INSERT INTO fact_hurtos (
            csv_row_num,
            dim_fecha_id,
            dim_muni_id,
            dim_arma_id,
            dim_genero_id,
            dim_grupo_id,
            dim_tipo_id,
            cantidad
        )
        SELECT
            s.csv_row_num,
            f.dim_fecha_id,
            m.dim_muni_id,
            a.dim_arma_id,
            g.dim_genero_id,
            gt.dim_grupo_id,
            t.dim_tipo_id,
            CAST(s.CANTIDAD AS INT)
        FROM stg_hurtos s
        JOIN dim_fecha f      ON f.fecha = to_date(s."FECHA HECHO", 'DD/MM/YYYY')
        JOIN dim_departamento d ON d.nombre = UPPER(TRIM(s.DEPARTAMENTO))
        JOIN dim_municipio m   ON m.nombre = s.MUNICIPIO
                                   AND m.codigo_dane = s."CODIGO DANE"
                                   AND m.dim_depto_id = d.dim_depto_id
        JOIN dim_arma_medio a  ON a.descripcion = s."ARMAS MEDIOS"
        JOIN dim_genero g      ON g.valor = COALESCE(s.GENERO, %s)
        JOIN dim_grupo_etario gt ON gt.rango = COALESCE(s."GRUPO ETARIO", %s)
        JOIN dim_tipo_hurto t  ON t.descripcion = s."TIPO DE HURTO";
    """
    with conn.cursor() as cur:
        cur.execute(sql, (PLACEHOLDER_GENERO, PLACEHOLDER_GRUPO))
    log("✅ fact_hurtos cargada (656 635 filas).")

# -----------------------------------------------------------------
# 4️⃣ Validaciones post‑carga
# -----------------------------------------------------------------
def run_validations(conn):
    import hashlib
    # 1. SHA‑256 del archivo
    expected_hash = "2d09645b764f7a03d59d3f8c91f70049a8a80d9aa036456921b2d787fe9f1e79"
    hasher = hashlib.sha256()
    with CSV_PATH.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(f"SHA‑256 mismatch: expected {expected_hash}, got {actual_hash}")
    log("✅ SHA‑256 verificado.")

    # 2. Número de filas del CSV (excluyendo header)
    with CSV_PATH.open('r', encoding='utf-8') as f:
        total_rows = sum(1 for _ in f) - 1
    if total_rows != 656635:
        raise ValueError(f"CSV row count mismatch: expected 656635, got {total_rows}")
    log("✅ Número de filas del CSV correcto.")

    with conn.cursor() as cur:
        # 3. Filas en staging
        cur.execute("SELECT COUNT(*) FROM stg_hurtos;")
        stg_cnt = cur.fetchone()[0]
        if stg_cnt != 656635:
            raise ValueError(f"Staging row count mismatch: expected 656635, got {stg_cnt}")
        log("✅ Staging contiene 656 635 filas.")

        # 4. Filas en fact_hurtos
        cur.execute("SELECT COUNT(*) FROM fact_hurtos;")
        fact_cnt = cur.fetchone()[0]
        if fact_cnt != 656635:
            raise ValueError(f"Fact row count mismatch: expected 656635, got {fact_cnt}")
        log("✅ Fact contiene 656 635 filas.")

        # 5. Integridad de FK
        cur.execute("""
            SELECT COUNT(*) FROM fact_hurtos fh
            LEFT JOIN dim_fecha df ON fh.dim_fecha_id = df.dim_fecha_id
            LEFT JOIN dim_municipio dm ON fh.dim_muni_id = dm.dim_muni_id
            LEFT JOIN dim_arma_medio da ON fh.dim_arma_id = da.dim_arma_id
            LEFT JOIN dim_genero dg ON fh.dim_genero_id = dg.dim_genero_id
            LEFT JOIN dim_grupo_etario dgt ON fh.dim_grupo_id = dgt.dim_grupo_id
            LEFT JOIN dim_tipo_hurto dt ON fh.dim_tipo_id = dt.dim_tipo_id
            WHERE df.dim_fecha_id IS NULL
               OR dm.dim_muni_id IS NULL
               OR da.dim_arma_id IS NULL
               OR dg.dim_genero_id IS NULL
               OR dgt.dim_grupo_id IS NULL
               OR dt.dim_tipo_id IS NULL;
        """)
        fk_issues = cur.fetchone()[0]
        if fk_issues != 0:
            raise ValueError(f"FK integrity check failed: {fk_issues} rows con referencias rotas")
        log("✅ Integridad de claves foráneas verificada.")

        # 6. Valores faltantes de GENERO y GRUPO ETARIO
        cur.execute("SELECT COUNT(*) FROM dim_genero WHERE valor = %s;", (PLACEHOLDER_GENERO,))
        gen_missing = cur.fetchone()[0]
        if gen_missing != 712:
            raise ValueError(f"Placeholder GENERO esperado 712, encontrado {gen_missing}")
        cur.execute("SELECT COUNT(*) FROM dim_grupo_etario WHERE rango = %s;", (PLACEHOLDER_GRUPO,))
        grp_missing = cur.fetchone()[0]
        if grp_missing != 205:
            raise ValueError(f"Placeholder GRUPO ETÁRIO esperado 205, encontrado {grp_missing}")
        log("✅ Valores faltantes de GENERO y GRUPO ETARIO correctamente asignados.")

        # 7. CANTIDAD positiva
        cur.execute("SELECT COUNT(*) FROM fact_hurtos WHERE cantidad <= 0;")
        bad_qty = cur.fetchone()[0]
        if bad_qty != 0:
            raise ValueError(f"Hay {bad_qty} filas con CANTIDAD no positiva.")
        log("✅ Todas las cantidades son positivas.")

# -----------------------------------------------------------------
# 5️⃣ Orquestación completa (transaccional)
# -----------------------------------------------------------------
def main():
    log("\n=== INICIO DE CARGA EN NEON (modo transaccional) ===")
    with get_connection() as conn:
        conn.autocommit = False
        try:
            # Truncate both tables en una sola instrucción para evitar problemas de FK
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE fact_hurtos, stg_hurtos RESTART IDENTITY;")
            load_staging(conn)
            load_all_dimensions(conn)
            load_fact_hurtos(conn)
            run_validations(conn)
            conn.commit()
            log("=== CARGA COMPLETADA SIN ERRORES ===\n")
        except Exception as exc:
            conn.rollback()
            log(f"❌ ETL abortado: {exc}")
            raise

if __name__ == "__main__":
    main()
