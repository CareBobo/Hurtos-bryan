"""
Script de procesamiento y generación de modelo dimensional en CSV para Power BI y PostgreSQL.
Regla de oro: No se borra ningún registro del dataset original (656.635 filas preservadas).
Imputación:
 - GENERO nulos -> 'NO REPORTADO'
 - GRUPO ETARIO nulos -> 'NO REPORTADO'
"""
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv"
OUT_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUT_POWERBI = PROJECT_ROOT / "data" / "power_bi"

def run_processing():
    print(f"Leyendo dataset original desde: {DATA_RAW}")
    if not DATA_RAW.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {DATA_RAW}")

    OUT_PROCESSED.mkdir(parents=True, exist_ok=True)
    OUT_POWERBI.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_RAW, encoding="utf-8", low_memory=False)
    total_filas = len(df)
    print(f"Total registros leídos: {total_filas:,}")

    # Limpieza de espacios en columnas
    df.columns = [c.strip() for c in df.columns]

    # Normalización de textos
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].astype(str).str.strip().str.upper()
    df["MUNICIPIO"] = df["MUNICIPIO"].astype(str).str.strip()
    df["CODIGO DANE"] = df["CODIGO DANE"].astype(str).str.strip()
    df["ARMAS MEDIOS"] = df["ARMAS MEDIOS"].astype(str).str.strip()
    df["TIPO DE HURTO"] = df["TIPO DE HURTO"].astype(str).str.strip()
    
    # Imputación de valores faltantes (SIN BORRAR REGISTROS)
    df["GENERO"] = df["GENERO"].fillna("NO REPORTADO").astype(str).str.strip()
    df["GENERO"] = df["GENERO"].replace({"nan": "NO REPORTADO", "": "NO REPORTADO", "NO REPORTA": "NO REPORTADO"})

    df["GRUPO ETARIO"] = df["GRUPO ETARIO"].fillna("NO REPORTADO").astype(str).str.strip()
    df["GRUPO ETARIO"] = df["GRUPO ETARIO"].replace({"nan": "NO REPORTADO", "": "NO REPORTADO"})

    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(1).astype(int)

    # Procesamiento de Fechas (formato DD/MM/YYYY)
    df["FECHA_DT"] = pd.to_datetime(df["FECHA HECHO"], format="%d/%m/%Y", errors="coerce")
    
    # Validación de no pérdida de filas
    assert len(df) == total_filas, f"Error: Se perdieron registros ({len(df)} != {total_filas})"
    print(f"✅ Integridad verificada: 100% de registros preservados ({total_filas:,})")

    # 1. Dimensión Fecha
    print("Generando dim_fecha...")
    unique_fechas = df[["FECHA_DT", "FECHA HECHO"]].drop_duplicates().sort_values("FECHA_DT").reset_index(drop=True)
    dim_fecha = pd.DataFrame()
    dim_fecha["fecha"] = unique_fechas["FECHA_DT"].dt.strftime("%Y-%m-%d")
    dim_fecha["fecha_corta"] = unique_fechas["FECHA HECHO"]
    dim_fecha["año"] = unique_fechas["FECHA_DT"].dt.year
    dim_fecha["mes"] = unique_fechas["FECHA_DT"].dt.month
    
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    dim_fecha["nombre_mes"] = dim_fecha["mes"].map(meses_es)
    dim_fecha["dia"] = unique_fechas["FECHA_DT"].dt.day
    dim_fecha["trimestre"] = unique_fechas["FECHA_DT"].dt.quarter
    dim_fecha["semana_año"] = unique_fechas["FECHA_DT"].dt.isocalendar().week
    
    dias_es = {
        0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
        4: "Viernes", 5: "Sábado", 6: "Domingo"
    }
    dim_fecha["dia_semana"] = unique_fechas["FECHA_DT"].dt.dayofweek.map(dias_es)
    dim_fecha.insert(0, "dim_fecha_id", range(1, len(dim_fecha) + 1))
    dim_fecha.to_csv(OUT_PROCESSED / "dim_fecha.csv", index=False, encoding="utf-8")

    # 2. Dimensión Departamento
    print("Generando dim_departamento...")
    deptos = pd.DataFrame({"nombre": sorted(df["DEPARTAMENTO"].unique())})
    deptos.insert(0, "dim_depto_id", range(1, len(deptos) + 1))
    deptos.to_csv(OUT_PROCESSED / "dim_departamento.csv", index=False, encoding="utf-8")
    depto_map = dict(zip(deptos["nombre"], deptos["dim_depto_id"]))

    # 3. Dimensión Municipio
    print("Generando dim_municipio...")
    munis = df[["DEPARTAMENTO", "MUNICIPIO", "CODIGO DANE"]].drop_duplicates().sort_values(["DEPARTAMENTO", "MUNICIPIO"]).reset_index(drop=True)
    munis["dim_depto_id"] = munis["DEPARTAMENTO"].map(depto_map)
    munis_dim = pd.DataFrame({
        "dim_muni_id": range(1, len(munis) + 1),
        "nombre": munis["MUNICIPIO"],
        "codigo_dane": munis["CODIGO DANE"],
        "dim_depto_id": munis["dim_depto_id"]
    })
    munis_dim.to_csv(OUT_PROCESSED / "dim_municipio.csv", index=False, encoding="utf-8")
    
    # 4. Dimensión Arma / Medio
    print("Generando dim_arma_medio...")
    armas = pd.DataFrame({"descripcion": sorted(df["ARMAS MEDIOS"].unique())})
    armas.insert(0, "dim_arma_id", range(1, len(armas) + 1))
    armas.to_csv(OUT_PROCESSED / "dim_arma_medio.csv", index=False, encoding="utf-8")
    arma_map = dict(zip(armas["descripcion"], armas["dim_arma_id"]))

    # 5. Dimensión Género
    print("Generando dim_genero...")
    generos = pd.DataFrame({"valor": sorted(df["GENERO"].unique())})
    generos.insert(0, "dim_genero_id", range(1, len(generos) + 1))
    generos.to_csv(OUT_PROCESSED / "dim_genero.csv", index=False, encoding="utf-8")
    genero_map = dict(zip(generos["valor"], generos["dim_genero_id"]))

    # 6. Dimensión Grupo Etario
    print("Generando dim_grupo_etario...")
    grupos = pd.DataFrame({"rango": sorted(df["GRUPO ETARIO"].unique())})
    grupos.insert(0, "dim_grupo_id", range(1, len(grupos) + 1))
    grupos.to_csv(OUT_PROCESSED / "dim_grupo_etario.csv", index=False, encoding="utf-8")
    grupo_map = dict(zip(grupos["rango"], grupos["dim_grupo_id"]))

    # 7. Dimensión Tipo de Hurto
    print("Generando dim_tipo_hurto...")
    tipos = pd.DataFrame({"descripcion": sorted(df["TIPO DE HURTO"].unique())})
    tipos.insert(0, "dim_tipo_id", range(1, len(tipos) + 1))
    tipos.to_csv(OUT_PROCESSED / "dim_tipo_hurto.csv", index=False, encoding="utf-8")
    tipo_map = dict(zip(tipos["descripcion"], tipos["dim_tipo_id"]))

    # 8. Generar Dataset Enriquecido / Optimizado para Power BI (Flat & Fast)
    print("Generando dataset consolidado para Power BI...")
    df_powerbi = pd.DataFrame()
    df_powerbi["ID_REGISTRO"] = range(1, len(df) + 1)
    df_powerbi["FECHA"] = df["FECHA_DT"].dt.strftime("%Y-%m-%d")
    df_powerbi["AÑO"] = df["FECHA_DT"].dt.year
    df_powerbi["MES"] = df["FECHA_DT"].dt.month
    df_powerbi["NOMBRE_MES"] = df_powerbi["MES"].map(meses_es)
    df_powerbi["DIA"] = df["FECHA_DT"].dt.day
    df_powerbi["TRIMESTRE"] = "T" + df["FECHA_DT"].dt.quarter.astype(str)
    df_powerbi["DIA_SEMANA"] = df["FECHA_DT"].dt.dayofweek.map(dias_es)
    df_powerbi["DEPARTAMENTO"] = df["DEPARTAMENTO"]
    df_powerbi["MUNICIPIO"] = df["MUNICIPIO"]
    df_powerbi["CODIGO_DANE"] = df["CODIGO DANE"]
    df_powerbi["MODALIDAD_HURTO"] = df["TIPO DE HURTO"].str.replace("ARTÍCULO 239. ", "", regex=False)
    df_powerbi["ARMA_MEDIO"] = df["ARMAS MEDIOS"]
    df_powerbi["GENERO"] = df["GENERO"]
    df_powerbi["GRUPO_ETARIO"] = df["GRUPO ETARIO"]
    df_powerbi["CANTIDAD"] = df["CANTIDAD"]

    out_csv = OUT_POWERBI / "hurtos_powerbi_dataset.csv"
    df_powerbi.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"✅ Dataset para Power BI exportado exitosamente en: {out_csv} ({len(df_powerbi):,} filas)")

if __name__ == "__main__":
    run_processing()

