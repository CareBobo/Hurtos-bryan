import os
import sys
import hashlib
import json
import logging
import pandas as pd
from pathlib import Path

# Configure simple console logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PROJECT_ROOT / 'data' / 'raw' / 'Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv'
DIAG_DIR = PROJECT_ROOT / 'reports' / 'diagnostics'
EXPECTED_SHA256 = '2d09645b764f7a03d59d3f8c91f70049a8a80d9aa036456921b2d787fe9f1e79'

def compute_sha256(path: Path) -> str:
    """Compute SHA‑256 of a file reading in binary mode in chunks."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def detect_encoding_and_delimiter(path: Path):
    """Detect file encoding with chardet and a plausible delimiter (comma, semicolon, tab)."""
    try:
        import chardet
    except ImportError:
        logging.warning('chardet not installed, defaulting to utf-8 encoding')
        encoding = 'utf-8'
    else:
        raw = path.read_bytes()[:10000]
        encoding = chardet.detect(raw).get('encoding') or 'utf-8'
    # Try delimiters
    delimiters = [',', ';', '\t']
    for delim in delimiters:
        try:
            df = pd.read_csv(path, encoding=encoding, delimiter=delim, dtype=str, engine='python')
            if df.shape[1] > 1:
                return encoding, delim
        except Exception:
            continue
    raise RuntimeError('Unable to detect delimiter for CSV')

def load_original_csv():
    enc, delim = detect_encoding_and_delimiter(RAW_CSV)
    df = pd.read_csv(RAW_CSV, encoding=enc, delimiter=delim, dtype=str, engine='python')
    df.columns = df.columns.str.strip()
    return df, enc, delim

def parse_fecha_hecho(df: pd.DataFrame) -> pd.DataFrame:
    col = 'FECHA HECHO'
    if col not in df.columns:
        raise KeyError(f"Column '{col}' not found in CSV")
    def parse_one(val):
        if pd.isna(val) or str(val).strip() == '':
            return pd.NaT
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                return pd.to_datetime(val, format=fmt)
            except Exception:
                continue
        return pd.NaT
    df['FECHA_PARSED'] = df[col].apply(parse_one)
    return df

def load_diagnostic_file(fname: str):
    path = DIAG_DIR / fname
    if not path.exists():
        logging.info(f"Diagnostic file '{fname}' not found; skipping.")
        return None
    if fname.endswith('.csv'):
        return pd.read_csv(path, dtype=str)
    if fname.endswith('.json'):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    if fname.endswith('.md'):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def temporal_audit(df: pd.DataFrame):
    dates = df['FECHA_PARSED']
    unique_dates = dates.dropna().unique()
    uniques_count = len(unique_dates)
    min_date = dates.min()
    max_date = dates.max()
    # Frequencies
    per_day = dates.dt.date.value_counts().sort_index()
    per_month = dates.dt.to_period('M').value_counts().sort_index()
    per_year = dates.dt.year.value_counts().sort_index()
    total_rows = len(df)
    sum_freq = per_day.sum()
    # Missing calendar days within range
    if pd.notna(min_date) and pd.notna(max_date):
        all_days = pd.date_range(start=min_date, end=max_date, freq='D')
        present_days = pd.to_datetime(per_day.index)
        missing_days = set(all_days.date) - set(present_days)
    else:
        missing_days = set()
    return {
        'unique_dates_count': uniques_count,
        'unique_dates_list': sorted([d.isoformat() for d in unique_dates]),
        'min_date': min_date,
        'max_date': max_date,
        'per_day': per_day,
        'per_month': per_month,
        'per_year': per_year,
        'sum_frequencies': int(sum_freq),
        'missing_days': sorted([d.isoformat() for d in missing_days]),
        'total_rows': total_rows,
    }

def geographic_audit(df: pd.DataFrame):
    departamentos = df['DEPARTAMENTO'].dropna().unique()
    municipios = df['MUNICIPIO'].dropna().unique()
    codigos = df['CODIGO DANE'].dropna().unique()
    muni_code_map = df[['MUNICIPIO', 'CODIGO DANE']].drop_duplicates()
    return {
        'departamentos': sorted(departamentos),
        'municipios': sorted(municipios),
        'codigos': sorted(codigos),
        'muni_code_map': muni_code_map,
    }

def atlantic_audit(df: pd.DataFrame):
    def normalize(txt):
        import unicodedata, re
        if pd.isna(txt):
            return ''
        txt = unicodedata.normalize('NFKD', txt)
        txt = txt.encode('ASCII', 'ignore').decode('ASCII')
        txt = re.sub(r'[^A-Za-z0-9]', '', txt).lower()
        return txt
    atl_mask = df['DEPARTAMENTO'].apply(normalize) == 'atlantico'
    atl_df = df[atl_mask]
    total_national = len(df)
    atl_rows = len(atl_df)
    barr_mask = atl_df['MUNICIPIO'].apply(normalize) == 'barranquilla'
    barr_rows = len(atl_df[barr_mask])
    other_munis = atl_df[~barr_mask]['MUNICIPIO'].dropna().unique()
    participation = (atl_rows / total_national) * 100 if total_national else 0
    return {
        'total_atlantic_rows': atl_rows,
        'barranquilla_rows': barr_rows,
        'other_municipios': sorted(other_munis),
        'participation_pct': participation,
    }

def variable_audit(df: pd.DataFrame):
    cantidad_vals = df['CANTIDAD'].dropna().unique() if 'CANTIDAD' in df.columns else []
    armas_vals = df['ARMAS MEDIOS'].dropna().unique() if 'ARMAS MEDIOS' in df.columns else []
    grupo_vals = df['GRUPO ETARIO'].dropna().unique() if 'GRUPO ETARIO' in df.columns else []
    genero_vals = df['GENERO'].dropna().unique() if 'GENERO' in df.columns else []
    tipo_hurto_vals = df['TIPO DE HURTO'].dropna().unique() if 'TIPO DE HURTO' in df.columns else []
    return {
        'CANTIDAD': sorted(cantidad_vals),
        'ARMAS_MEDIOS': sorted(armas_vals),
        'GRUPO_ETARIO': sorted(grupo_vals),
        'GENERO': sorted(genero_vals),
        'TIPO_DE_HURTO': sorted(tipo_hurto_vals),
    }

def main():
    # Verify SHA-256
    actual_sha = compute_sha256(RAW_CSV)
    logging.info(f"Computed SHA-256: {actual_sha}")
    if actual_sha.lower() != EXPECTED_SHA256.lower():
        logging.error("SHA-256 mismatch! Expected %s but got %s. Aborting.", EXPECTED_SHA256, actual_sha)
        sys.exit(1)
    else:
        logging.info("SHA-256 matches expected value.")

    df, enc, delim = load_original_csv()
    logging.info(f"CSV loaded – encoding: {enc}, delimiter: '{delim}', rows: {len(df)}, columns: {len(df.columns)}")
    df = parse_fecha_hecho(df)
    temporal = temporal_audit(df)
    geographic = geographic_audit(df)
    atlantic = atlantic_audit(df)
    variables = variable_audit(df)
    diagnostics = {
        'missing_values.csv': load_diagnostic_file('missing_values.csv'),
        'duplicate_analysis.md': load_diagnostic_file('duplicate_analysis.md'),
        'temporal_analysis.csv': load_diagnostic_file('temporal_analysis.csv'),
        'geographic_analysis.csv': load_diagnostic_file('geographic_analysis.csv'),
        'atlantic_analysis.csv': load_diagnostic_file('atlantic_analysis.csv'),
        'categorical_analysis.csv': load_diagnostic_file('categorical_analysis.csv'),
        'quantity_statistics.csv': load_diagnostic_file('quantity_statistics.csv'),
        'quantity_anomalies.json': load_diagnostic_file('quantity_anomalies.json'),
    }
    out = []
    out.append('=== AUDITORÍA DEL DATASET (Plan 6.4) ===')
    out.append('\n--- Verificación de integridad (SHA-256) ---')
    out.append(f"SHA-256 coincide: {actual_sha.lower() == EXPECTED_SHA256.lower()}")
    out.append('\n--- Auditoría Temporal ---')
    out.append(f"Fechas únicas: {temporal['unique_dates_count']}")
    out.append('Lista de fechas únicas (ISO):')
    out.append(', '.join(temporal['unique_dates_list']))
    out.append(f"Rango: {temporal['min_date']} a {temporal['max_date']}")
    out.append(f"Total filas: {temporal['total_rows']}, suma frecuencias día: {temporal['sum_frequencies']}")
    out.append(f"Días faltantes ({len(temporal['missing_days'])}): {', '.join(temporal['missing_days'])}")
    out.append('Frecuencia por año:')
    for yr, cnt in temporal['per_year'].items():
        out.append(f"  {yr}: {cnt}")
    out.append('Frecuencia por mes (primeros 12):')
    for mon, cnt in temporal['per_month'].head(12).items():
        out.append(f"  {mon}: {cnt}")
    out.append('Frecuencia por día (primeras 30):')
    for day, cnt in temporal['per_day'].head(30).items():
        out.append(f"  {day}: {cnt}")
    expected_unique = [64, 366]
    if temporal['unique_dates_count'] not in expected_unique:
        out.append(f">>> Aviso: número de fechas únicas ({temporal['unique_dates_count']}) no coincide con 64 ni 366 esperado.")
    else:
        out.append('Número de fechas únicas coincide con una de las expectativas.')
    out.append('\n--- Auditoría Geográfica ---')
    out.append(f"Departamentos únicos: {len(geographic['departamentos'])}")
    out.append('Primeros 10 departamentos: ' + ', '.join(geographic['departamentos'][:10]))
    out.append(f"Municipios únicos: {len(geographic['municipios'])}")
    out.append('Primeros 13 municipios: ' + ', '.join(geographic['municipios'][:13]))
    out.append(f"Códigos DANE únicos: {len(geographic['codigos'])}")
    code_counts = geographic['muni_code_map']['CODIGO DANE'].value_counts()
    out.append('Distribución de códigos DANE por municipio (primeros 10): ' + ', '.join([f"{c}:{n}" for c, n in code_counts.head(10).items()]))
    out.append('\n--- Auditoría del Atlántico ---')
    out.append(f"Registros Atlántico: {atlantic['total_atlantic_rows']}")
    out.append(f"Registros Barranquilla: {atlantic['barranquilla_rows']}")
    out.append(f"Otros municipios ({len(atlantic['other_municipios'])}): {', '.join(atlantic['other_municipios'])}")
    out.append(f"Participación nacional: {atlantic['participation_pct']:.2f}%")
    out.append('\n--- Verificación de Variables ---')
    out.append(f"CANTIDAD valores únicos ({len(variables['CANTIDAD'])}): {', '.join(map(str, variables['CANTIDAD']))}")
    out.append(f"ARMAS MEDIOS valores únicos: {len(variables['ARMAS_MEDIOS'])}")
    out.append(f"GRUPO ETARIO valores únicos: {len(variables['GRUPO_ETARIO'])}")
    out.append(f"GENERO categorías ({len(variables['GENERO'])}): {', '.join(variables['GENERO'])}")
    out.append(f"TIPO DE HURTO categorías ({len(variables['TIPO_DE_HURTO'])}): {', '.join(variables['TIPO_DE_HURTO'])}")
    out.append('\n--- Comparación con Informes Previos ---')
    for fname, content in diagnostics.items():
        out.append(f"{fname}: {'ENCONTRADO' if content is not None else 'NO ENCONTRADO'}")
    if diagnostics.get('missing_values.csv') is not None:
        missing_df = diagnostics['missing_values.csv']
        # Compute rows with any missing or empty (after stripping) value
        def row_has_missing(row):
            for v in row:
                if pd.isna(v):
                    return True
                if isinstance(v, str) and v.strip() == '':
                    return True
            return False
        calc_missing = df.apply(row_has_missing, axis=1).sum()
        out.append(f"missing_values.csv filas: {len(missing_df)} vs cálculo interno: {calc_missing}")
    report = '\n'.join(out)
    print(report)

if __name__ == '__main__':
    main()
