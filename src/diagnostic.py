#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pathlib
import logging
import pandas as pd

# Paths (relative to project root)
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
ARTIFACT_DIR = pathlib.Path(r"C:/Users/USER/.gemini/antigravity/brain/d171ffe9-003e-4c53-9581-b75fb2f9b841/artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=ARTIFACT_DIR / "diagnostic_run.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def list_csv_files():
    files = list(RAW_DIR.glob("*.csv"))
    with open(ARTIFACT_DIR / "diagnostic_file_list.txt", "w", encoding="utf-8") as f:
        for p in files:
            f.write(f"{p.name}\n")
    logging.info(f"Found {len(files)} CSV file(s) in raw folder.")
    return files

def read_csv_with_encoding(path):
    # Try utf-8 then latin-1
    for enc in ["utf-8", "latin-1"]:
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False)
            with open(ARTIFACT_DIR / "encoding_check.txt", "a", encoding="utf-8") as logf:
                logf.write(f"{path.name}: read successfully with {enc}\n")
            logging.info(f"{path.name} read with {enc} encoding.")
            return df, enc
        except UnicodeDecodeError:
            continue
    # If none work, raise
    raise UnicodeDecodeError(f"Unable to read {path} with tried encodings.")

def generate_diagnostics(df, filename_stem):
    total_records = len(df)
    total_columns = len(df.columns)
    dtypes = df.dtypes.astype(str).to_dict()
    null_counts = df.isna().sum()
    null_pct = (null_counts / total_records * 100).round(2)
    duplicate_count = df.duplicated().sum()
    duplicate_rows = df[df.duplicated(keep=False)]

    # Date period (look for column containing 'fecha')
    date_cols = [c for c in df.columns if 'fecha' in c.lower()]
    period = None
    if date_cols:
        try:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
            period = (df[date_cols[0]].min(), df[date_cols[0]].max())
        except Exception as e:
            logging.warning(f"Failed to parse dates in {date_cols[0]}: {e}")

    # Geographic coverage
    departamentos = df['departamento'].dropna().unique().tolist() if 'departamento' in df.columns else []
    municipios = df['municipio'].dropna().unique().tolist() if 'municipio' in df.columns else []

    # Categories & modalities
    categorias = df['categoria'].dropna().unique().tolist() if 'categoria' in df.columns else []
    modalidades = df['modalidad'].dropna().unique().tolist() if 'modalidad' in df.columns else []

    # Write summary markdown
    with open(ARTIFACT_DIR / f"diagnostic_summary.md", "w", encoding="utf-8") as out:
        out.write(f"# Diagnóstico del dataset `{filename_stem}`\n\n")
        out.write(f"**Registros totales:** {total_records}\n")
        out.write(f"**Columnas totales:** {total_columns}\n\n")
        out.write("## Variables\n")
        out.write("| Variable | Tipo | Nulos | % Nulos |\n|---|---|---|---|\n")
        for col in df.columns:
            out.write(f"| {col} | {dtypes[col]} | {null_counts[col]} | {null_pct[col]} |\n")
        out.write("\n---\n")
        out.write(f"**Duplicados exactos:** {duplicate_count}\n")
        if period:
            out.write(f"**Periodo de fechas:** {period[0].date()} a {period[1].date()}\n")
        out.write(f"**Departamentos encontrados:** {', '.join(map(str, departamentos))}\n")
        out.write(f"**Municipios encontrados:** {', '.join(map(str, municipios))}\n")
        out.write(f"**Categorías:** {', '.join(map(str, categorias))}\n")
        out.write(f"**Modalidades:** {', '.join(map(str, modalidades))}\n")

    # Save duplicated rows if any
    if not duplicate_rows.empty:
        duplicate_rows.to_csv(ARTIFACT_DIR / f"duplicados_{filename_stem}.csv", index=False)

    # Coverage analysis (national vs Atlántico)
    coverage_md = []
    coverage_md.append("## Cobertura geográfica y temporal\n")
    coverage_md.append(f"- Total departamentos presentes: {len(departamentos)}\n")
    if 'Atlantico' in departamentos or 'Atlántico' in departamentos:
        coverage_md.append("- El dataset incluye el departamento de Atlántico.\n")
    else:
        coverage_md.append("- El dataset **no** incluye el departamento de Atlántico.\n")
    if period:
        coverage_md.append(f"- Rango de fechas: {period[0].date()} a {period[1].date()}\n")
    else:
        coverage_md.append("- No se encontró columna de fechas clara.\n")
    with open(ARTIFACT_DIR / f"coverage_analysis.md", "w", encoding="utf-8") as covf:
        covf.writelines(coverage_md)

    # Save head of raw data for quick look
    df.head().to_csv(ARTIFACT_DIR / f"raw_head_{filename_stem}.csv", index=False)

    logging.info(f"Diagnostics generated for {filename_stem}")

def main():
    csv_files = list_csv_files()
    for csv_path in csv_files:
        df, enc = read_csv_with_encoding(csv_path)
        stem = csv_path.stem  # filename without extension
        generate_diagnostics(df, stem)

if __name__ == "__main__":
    main()

