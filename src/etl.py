# -*- coding: utf-8 -*-
"""
Pipeline ETL Auxiliar Local.
----------------------------
NOTA METODOLÓGICA IMPORTANTE:
Este script es una herramienta auxiliar/experimental local y NO debe confundirse con:
 - src/process_dimensions.py: Generador del modelo dimensional (Star Schema) para Power BI.
 - src/load_to_neon.py: Pipeline principal de carga transaccional streaming a PostgreSQL Neon.

REGLA DE ORO DE INVESTIGACIÓN:
No se borra ningún registro del dataset original (preservación total del 100% de filas).
El CSV original no es modificado bajo ninguna circunstancia.
"""

from pathlib import Path
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Rutas relativas al proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "processed"


def load_raw(data_dir: Path = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """Carga el dataset CSV original desde el directorio data/ sin alterarlo."""
    if not data_dir.exists():
        raise FileNotFoundError(f"Directorio de datos no encontrado: {data_dir}")
        
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No se encontraron archivos CSV en {data_dir}")
        
    # Cargar el archivo principal preservando tipos y contenido original
    target_csv = csv_files[0]
    return pd.read_csv(target_csv, encoding="utf-8", low_memory=False)


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza y normalización básica de datos garantizando CERO eliminación de filas.
    Se eliminó el comportamiento anterior de dropna() para dar cumplimiento estricto
    al principio metodológico de no eliminación de registros.
    Los valores faltantes se imputan como 'NO REPORTADO'.
    """
    df_clean = df.copy()
    
    # Limpieza de nombres de columnas
    df_clean.columns = [c.strip() for c in df_clean.columns]
    
    # Imputación controlada de valores faltantes (SIN BORRAR NINGÚN REGISTRO)
    if "GENERO" in df_clean.columns:
        df_clean["GENERO"] = df_clean["GENERO"].fillna("NO REPORTADO").astype(str).str.strip()
        df_clean["GENERO"] = df_clean["GENERO"].replace({"nan": "NO REPORTADO", "": "NO REPORTADO", "NO REPORTA": "NO REPORTADO"})
        
    if "GRUPO ETARIO" in df_clean.columns:
        df_clean["GRUPO ETARIO"] = df_clean["GRUPO ETARIO"].fillna("NO REPORTADO").astype(str).str.strip()
        df_clean["GRUPO ETARIO"] = df_clean["GRUPO ETARIO"].replace({"nan": "NO REPORTADO", "": "NO REPORTADO"})
        
    # Asegurar que la cantidad sea numérica positiva
    if "CANTIDAD" in df_clean.columns:
        df_clean["CANTIDAD"] = pd.to_numeric(df_clean["CANTIDAD"], errors="coerce").fillna(1).astype(int)
        
    # Verificación de integridad estricta
    if len(df_clean) != len(df):
        raise ValueError(f"Fallo de integridad: Se eliminaron registros ({len(df_clean)} != {len(df)})")
        
    return df_clean


def save_processed(df: pd.DataFrame, out_dir: Path = DEFAULT_OUT_DIR) -> Path:
    """Guarda una copia procesada en la carpeta processed/ sin tocar el archivo original."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "processed_auxiliary.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    return out_path


def get_engine():
    """Crea un engine de SQLAlchemy utilizando variables de entorno de forma segura."""
    load_dotenv(PROJECT_ROOT / ".env")
    conn_str = os.getenv("NEON_CONN") or os.getenv("LOCAL_PG_CONN")
    if not conn_str:
        return None
    # Eliminar comillas si las tuviese
    conn_str = conn_str.strip().strip("'\"")
    return create_engine(conn_str)


if __name__ == "__main__":
    print("Ejecutando pipeline ETL auxiliar...")
    raw_df = load_raw()
    print(f"Registros originales cargados: {len(raw_df):,}")
    processed_df = process_data(raw_df)
    print(f"Registros tras limpieza (0 eliminados): {len(processed_df):,}")
    out = save_processed(processed_df)
    print(f"Resultado auxiliar guardado en: {out}")
