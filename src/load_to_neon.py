"""
ETL robusto y transaccional para cargar el dataset en PostgreSQL Neon.
1. Ejecuta el esquema DDL dimensional (database/01_create_schema.sql).
2. Carga los 656.635 registros en la tabla de staging mediante COPY nativo streaming.
3. Puebla las dimensiones y la tabla de hechos respetando la regla: 0 FILAS BORRADAS.
4. Valida integridad referencial y conteos.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
import psycopg
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.db import get_connection, get_connection_string

CSV_PATH = PROJECT_ROOT / "data" / "Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv"
SCHEMA_SQL = PROJECT_ROOT / "database" / "01_create_schema.sql"
LOG_FILE = PROJECT_ROOT / "logs" / "load_neon_log.txt"

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted)
    LOG_FILE.parent.mkdir(exist_ok=True, parents=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def execute_schema(conn):
    log("Iniciando creación de esquema dimensional...")
    with conn.cursor() as cur:
        with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
            sql = f.read()
        cur.execute(sql)
    conn.commit()
    log("✅ Esquema DDL ejecutado exitosamente en Neon (Tablas e Índices creados).")

def load_staging_copy(conn):
    log("Cargando datos crudos a tabla de staging (stg_hurtos) vía streaming COPY...")
    start_t = time.time()
    
    with conn.cursor() as cur:
        copy_sql = """
            COPY stg_hurtos (
                csv_row_num, departamento, municipio, codigo_dane, 
                armas_medios, fecha_hecho, genero, grupo_etario, 
                tipo_de_hurto, cantidad
            ) FROM STDIN;
        """
        with cur.copy(copy_sql) as copy:
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)  # Saltar encabezado
                
                for row_idx, row in enumerate(reader, start=1):
                    clean_row = (
                        row_idx,
                        row[0].strip() if len(row) > 0 else "",
                        row[1].strip() if len(row) > 1 else "",
                        row[2].strip() if len(row) > 2 else "",
                        row[3].strip() if len(row) > 3 else "",
                        row[4].strip() if len(row) > 4 else "",
                        row[5].strip() if len(row) > 5 and row[5].strip() else "NO REPORTADO",
                        row[6].strip() if len(row) > 6 and row[6].strip() else "NO REPORTADO",
                        row[7].strip() if len(row) > 7 else "",
                        row[8].strip() if len(row) > 8 else "1",
                    )
                    copy.write_row(clean_row)
                    if row_idx % 100000 == 0:
                        log(f"   ... transmitidas {row_idx:,} filas a Neon")
    conn.commit()
    elapsed = time.time() - start_t
    
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM stg_hurtos;")
        cnt = cur.fetchone()[0]
    log(f"✅ Staging completado: {cnt:,} filas cargadas en {elapsed:.2f} s.")
    assert cnt == 656635, f"Discrepancia en staging: esperado 656635, obtenido {cnt}"

def populate_dimensions(conn):
    log("Poblando dimensiones analíticas...")
    with conn.cursor() as cur:
        # 1. Dimensión Fecha
        log(" - Poblando dim_fecha...")
        cur.execute("""
            INSERT INTO dim_fecha (fecha, año, mes, nombre_mes, dia, trimestre, semana_año, dia_semana)
            SELECT DISTINCT
                TO_DATE(fecha_hecho, 'DD/MM/YYYY') AS fecha,
                EXTRACT(YEAR FROM TO_DATE(fecha_hecho, 'DD/MM/YYYY'))::INT AS año,
                EXTRACT(MONTH FROM TO_DATE(fecha_hecho, 'DD/MM/YYYY'))::INT AS mes,
                TRIM(TO_CHAR(TO_DATE(fecha_hecho, 'DD/MM/YYYY'), 'Month')) AS nombre_mes,
                EXTRACT(DAY FROM TO_DATE(fecha_hecho, 'DD/MM/YYYY'))::INT AS dia,
                EXTRACT(QUARTER FROM TO_DATE(fecha_hecho, 'DD/MM/YYYY'))::INT AS trimestre,
                EXTRACT(WEEK FROM TO_DATE(fecha_hecho, 'DD/MM/YYYY'))::INT AS semana_año,
                TRIM(TO_CHAR(TO_DATE(fecha_hecho, 'DD/MM/YYYY'), 'Day')) AS dia_semana
            FROM stg_hurtos
            WHERE fecha_hecho IS NOT NULL
            ON CONFLICT (fecha) DO NOTHING;
        """)

        # 2. Dimensión Departamento
        log(" - Poblando dim_departamento...")
        cur.execute("""
            INSERT INTO dim_departamento (nombre)
            SELECT DISTINCT UPPER(TRIM(departamento))
            FROM stg_hurtos
            WHERE departamento IS NOT NULL AND TRIM(departamento) <> ''
            ON CONFLICT (nombre) DO NOTHING;
        """)

        # 3. Dimensión Municipio
        log(" - Poblando dim_municipio...")
        cur.execute("""
            INSERT INTO dim_municipio (nombre, codigo_dane, dim_depto_id)
            SELECT DISTINCT
                TRIM(s.municipio),
                TRIM(s.codigo_dane),
                d.dim_depto_id
            FROM stg_hurtos s
            JOIN dim_departamento d ON d.nombre = UPPER(TRIM(s.departamento))
            ON CONFLICT (nombre, codigo_dane, dim_depto_id) DO NOTHING;
        """)

        # 4. Dimensión Arma / Medio
        log(" - Poblando dim_arma_medio...")
        cur.execute("""
            INSERT INTO dim_arma_medio (descripcion)
            SELECT DISTINCT TRIM(armas_medios)
            FROM stg_hurtos
            WHERE armas_medios IS NOT NULL AND TRIM(armas_medios) <> ''
            ON CONFLICT (descripcion) DO NOTHING;
        """)

        # 5. Dimensión Género (incluyendo NO REPORTADO)
        log(" - Poblando dim_genero...")
        cur.execute("""
            INSERT INTO dim_genero (valor)
            SELECT DISTINCT 
                CASE 
                    WHEN genero IS NULL OR TRIM(genero) IN ('', 'NO REPORTA', 'NO REPORTADO') THEN 'NO REPORTADO'
                    ELSE TRIM(genero)
                END
            FROM stg_hurtos
            ON CONFLICT (valor) DO NOTHING;
        """)

        # 6. Dimensión Grupo Etario (incluyendo NO REPORTADO)
        log(" - Poblando dim_grupo_etario...")
        cur.execute("""
            INSERT INTO dim_grupo_etario (rango)
            SELECT DISTINCT 
                CASE 
                    WHEN grupo_etario IS NULL OR TRIM(grupo_etario) IN ('', 'NO REPORTADO') THEN 'NO REPORTADO'
                    ELSE TRIM(grupo_etario)
                END
            FROM stg_hurtos
            ON CONFLICT (rango) DO NOTHING;
        """)

        # 7. Dimensión Tipo de Hurto
        log(" - Poblando dim_tipo_hurto...")
        cur.execute("""
            INSERT INTO dim_tipo_hurto (descripcion)
            SELECT DISTINCT TRIM(tipo_de_hurto)
            FROM stg_hurtos
            WHERE tipo_de_hurto IS NOT NULL AND TRIM(tipo_de_hurto) <> ''
            ON CONFLICT (descripcion) DO NOTHING;
        """)
    conn.commit()
    log("✅ Todas las dimensiones pobladas con éxito.")

def populate_fact(conn):
    log("Poblando tabla de hechos (fact_hurtos)...")
    start_t = time.time()
    with conn.cursor() as cur:
        cur.execute("""
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
                ge.dim_grupo_id,
                t.dim_tipo_id,
                COALESCE(NULLIF(s.cantidad, '')::INT, 1)
            FROM stg_hurtos s
            JOIN dim_fecha f ON f.fecha = TO_DATE(s.fecha_hecho, 'DD/MM/YYYY')
            JOIN dim_departamento d ON d.nombre = UPPER(TRIM(s.departamento))
            JOIN dim_municipio m ON m.nombre = TRIM(s.municipio) 
                                AND m.codigo_dane = TRIM(s.codigo_dane) 
                                AND m.dim_depto_id = d.dim_depto_id
            JOIN dim_arma_medio a ON a.descripcion = TRIM(s.armas_medios)
            JOIN dim_genero g ON g.valor = (
                CASE 
                    WHEN s.genero IS NULL OR TRIM(s.genero) IN ('', 'NO REPORTA', 'NO REPORTADO') THEN 'NO REPORTADO'
                    ELSE TRIM(s.genero)
                END
            )
            JOIN dim_grupo_etario ge ON ge.rango = (
                CASE 
                    WHEN s.grupo_etario IS NULL OR TRIM(s.grupo_etario) IN ('', 'NO REPORTADO') THEN 'NO REPORTADO'
                    ELSE TRIM(s.grupo_etario)
                END
            )
            JOIN dim_tipo_hurto t ON t.descripcion = TRIM(s.tipo_de_hurto);
        """)
    conn.commit()
    elapsed = time.time() - start_t
    
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM fact_hurtos;")
        cnt = cur.fetchone()[0]
    log(f"✅ fact_hurtos poblada: {cnt:,} filas en {elapsed:.2f} s.")

def validate_data(conn):
    log("Ejecutando verificaciones de integridad y calidad...")
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM stg_hurtos;")
        stg_cnt = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM fact_hurtos;")
        fact_cnt = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM fact_hurtos fh
            LEFT JOIN dim_fecha df ON fh.dim_fecha_id = df.dim_fecha_id
            LEFT JOIN dim_municipio dm ON fh.dim_muni_id = dm.dim_muni_id
            LEFT JOIN dim_arma_medio da ON fh.dim_arma_id = da.dim_arma_id
            LEFT JOIN dim_genero dg ON fh.dim_genero_id = dg.dim_genero_id
            LEFT JOIN dim_grupo_etario dgt ON fh.dim_grupo_id = dgt.dim_grupo_id
            LEFT JOIN dim_tipo_hurto dt ON fh.dim_tipo_id = dt.dim_tipo_id
            WHERE df.dim_fecha_id IS NULL OR dm.dim_muni_id IS NULL OR da.dim_arma_id IS NULL
               OR dg.dim_genero_id IS NULL OR dgt.dim_grupo_id IS NULL OR dt.dim_tipo_id IS NULL;
        """)
        broken_fks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM fact_hurtos WHERE cantidad <= 0;")
        bad_cant = cur.fetchone()[0]

    log(f"   Staging count: {stg_cnt:,} filas")
    log(f"   Fact count:    {fact_cnt:,} filas")
    log(f"   Broken FKs:    {broken_fks} (debe ser 0)")
    log(f"   Bad Cantidad:  {bad_cant} (debe ser 0)")

    if stg_cnt == 656635 and fact_cnt == 656635 and broken_fks == 0 and bad_cant == 0:
        log("🎉 VERIFICACIÓN COMPLETA: Carga 100% íntegra, sin registros perdidos ni inconsistencias.")
    else:
        raise ValueError(f"Fallo en validación de datos: stg={stg_cnt}, fact={fact_cnt}, broken_fks={broken_fks}")

def main():
    conn_str = get_connection_string()
    if not conn_str:
        log("⚠️ No se ha configurado la variable NEON_CONN en el archivo .env.")
        sys.exit(1)

    log("Conectando a base de datos PostgreSQL Neon...")
    with get_connection() as conn:
        execute_schema(conn)
        load_staging_copy(conn)
        populate_dimensions(conn)
        populate_fact(conn)
        validate_data(conn)
    log("=== PROCESO DE CARGA A NEON FINALIZADO CON ÉXITO ===")

if __name__ == "__main__":
    main()
