import os
import json
import logging
import sys
import pandas as pd
import numpy as np

# Configure logging (no file output, just console for now)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Paths (relative to project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_CSV = os.path.join(PROJECT_ROOT, 'data', 'raw', 'Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv')
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports', 'diagnostics')

# Helper to read CSVs (all columns as text)
def read_csv(path):
    return pd.read_csv(path, dtype=str, encoding='utf-8', keep_default_na=False, na_values=[])

# 1. Load original dataset (read‑only)
logging.info('Loading original dataset')
df = read_csv(DATA_CSV)
# Ensure proper column names (strip spaces)
df.columns = [c.strip() for c in df.columns]

# Parse FECHA HECHO to datetime (allow empty strings)
def parse_date(val):
    if pd.isna(val) or str(val).strip() == '':
        return pd.NaT
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return pd.to_datetime(val, format=fmt)
        except Exception:
            continue
    return pd.NaT

df['FECHA_PARSED'] = df['FECHA HECHO'].apply(parse_date)

# 2. Load diagnostic artifacts
logging.info('Loading diagnostic artifacts')
missing_df = read_csv(os.path.join(REPORTS_DIR, 'missing_values.csv'))
temporal_df = read_csv(os.path.join(REPORTS_DIR, 'temporal_analysis.csv'))
geo_df = read_csv(os.path.join(REPORTS_DIR, 'geographic_analysis.csv'))
atlantic_df = read_csv(os.path.join(REPORTS_DIR, 'atlantic_analysis.csv'))
categorical_df = read_csv(os.path.join(REPORTS_DIR, 'categorical_analysis.csv'))
quantity_stats_df = read_csv(os.path.join(REPORTS_DIR, 'quantity_statistics.csv'))
quantity_anomalies = json.load(open(os.path.join(REPORTS_DIR, 'quantity_anomalies.json'), encoding='utf-8'))

# Helper to format sections
def section(title):
    return f"\n{'='*10} {title} {'='*10}\n"

report_lines = []

# ------- 1. FECHA HECHO -------
report_lines.append(section('FECHA HECHO'))
# Unique dates
unique_dates = df['FECHA_PARSED'].dropna().unique()
report_lines.append(f"Número de fechas únicas: {len(unique_dates)}")
# Records per day, month, year
per_day = df['FECHA_PARSED'].dt.date.value_counts().sort_index()
per_month = df['FECHA_PARSED'].dt.to_period('M').value_counts().sort_index()
per_year = df['FECHA_PARSED'].dt.year.value_counts().sort_index()
# Date with max frequency
if not per_day.empty:
    max_date = per_day.idxmax()
    max_count = per_day.max()
    report_lines.append(f"Fecha con mayor frecuencia: {max_date} (registros: {max_count})")
else:
    report_lines.append("No hay fechas válidas.")
# Verify all years are 2014
years = df['FECHA_PARSED'].dt.year.dropna().unique()
all_2014 = (len(years) == 1 and years[0] == 2014)
report_lines.append(f"¿Todas las fechas corresponden a 2014? {'Sí' if all_2014 else 'No'} (años encontrados: {', '.join(map(str, years))})")
# Detect abnormal concentration (day count > mean + 3*std)
if not per_day.empty:
    mean_day = per_day.mean()
    std_day = per_day.std()
    threshold = mean_day + 3*std_day
    abnormal_days = per_day[per_day > threshold]
    if not abnormal_days.empty:
        report_lines.append('Días con concentraciones anormales (>{:.2f} registros):'.format(threshold))
        for d, cnt in abnormal_days.items():
            report_lines.append(f"  - {d}: {cnt}")
    else:
        report_lines.append('No se detectaron concentraciones anormales por día.')
# Min / Max dates
min_date = df['FECHA_PARSED'].min()
max_date = df['FECHA_PARSED'].max()
report_lines.append(f"Fecha mínima: {min_date}")
report_lines.append(f"Fecha máxima: {max_date}")

# Cross‑check with temporal_analysis.csv
report_lines.append('\nComparación con temporal_analysis.csv:')
# Convert temporal df to comparable format (año, mes, dia_semana, filas)
# We'll simply compare total rows per year
temp_year_counts = temporal_df.groupby('año')['filas'].sum()
orig_year_counts = per_year.rename_axis('año').reset_index(name='filas')
for _, row in orig_year_counts.iterrows():
    yr = str(row['año'])
    orig_cnt = row['filas']
    diag_cnt = temp_year_counts.get(yr, None)
    if diag_cnt is None:
        report_lines.append(f"  - Año {yr}: no aparece en temporal_analysis.csv")
    elif orig_cnt != diag_cnt:
        report_lines.append(f"  - Año {yr}: diferencia (original {orig_cnt} vs. diagnóstico {diag_cnt})")
    else:
        report_lines.append(f"  - Año {yr}: coincide ({orig_cnt})")

# ------- 2. CANTIDAD -------
report_lines.append(section('CANTIDAD'))
# Unique values
unique_qty = df['CANTIDAD'].unique()
report_lines.append(f"Valores únicos de CANTIDAD ({len(unique_qty)}): {', '.join(map(str, unique_qty))}")
# Frequency
qty_counts = df['CANTIDAD'].value_counts()
report_lines.append('Frecuencia por valor:')
for val, cnt in qty_counts.items():
    report_lines.append(f"  - {val}: {cnt}")
# Verify all are 1
all_one = set(unique_qty) == {'1'}
report_lines.append(f"¿Todos los registros tienen valor 1? {'Sí' if all_one else 'No'}")
# Compare rows vs. sum (from quantity_statistics.csv)
rows_original = len(df)
sum_quantity = df['CANTIDAD'].astype(int, errors='ignore').sum()
stat_sum = quantity_stats_df['suma'].iloc[0]
report_lines.append(f"Filas totales (original): {rows_original}")
report_lines.append(f"Suma de CANTIDAD (calculada ahora): {sum_quantity}")
report_lines.append(f"Suma de CANTIDAD (del archivo quantity_statistics.csv): {stat_sum}")
if sum_quantity == stat_sum:
    report_lines.append('La suma coincide con la registrada en el archivo de diagnóstico.')
else:
    report_lines.append('Diferencia entre la suma calculada y la del diagnóstico.')
# Verify no conversion errors (check anomalies json)
report_lines.append('Anomalías de CANTIDAD reportadas en quantity_anomalies.json:')
for key, vals in quantity_anomalies.items():
    report_lines.append(f"  - {key}: {len(vals)} casos")

# ------- 3. COBERTURA GEOGRÁFICA -------
report_lines.append(section('COBERTURA GEOGRÁFICA'))
num_depts = df['DEPARTAMENTO'].nunique()
num_munis = df['MUNICIPIO'].nunique()
num_codes = df['CODIGO DANE'].nunique()
report_lines.append(f"Número de departamentos: {num_depts}")
report_lines.append(f"Número de municipios: {num_munis}")
report_lines.append(f"Número de códigos DANE: {num_codes}")
# Registros por departamento
dept_counts = df['DEPARTAMENTO'].value_counts()
report_lines.append('Registros por departamento (top 10):')
for dept, cnt in dept_counts.head(10).items():
    report_lines.append(f"  - {dept}: {cnt}")
# Verify Atlántico municipios y códigos DANE
atl_depts = atlantic_df['DEPARTAMENTO'].unique()
report_lines.append(f"Departamentos presentes en Atlántico: {', '.join(atl_depts)}")
report_lines.append(f"Municipios en Atlántico (conteo): {atlantic_df['MUNICIPIO'].nunique()}")
report_lines.append(f"Códigos DANE en Atlántico (conteo): {atlantic_df['CODIGO DANE'].nunique()}")

# Cross‑check with geographic_analysis.csv
# Compare total rows per departamento
geo_dept_counts = geo_df.groupby('DEPARTAMENTO')['filas'].sum()
report_lines.append('\nComparación con geographic_analysis.csv (filas por departamento):')
for dept, cnt in dept_counts.items():
    diag_cnt = geo_dept_counts.get(dept, None)
    if diag_cnt is None:
        report_lines.append(f"  - {dept}: no aparece en geographic_analysis.csv")
    elif cnt != diag_cnt:
        report_lines.append(f"  - {dept}: diferencia (original {cnt} vs. diagnóstico {diag_cnt})")
    else:
        report_lines.append(f"  - {dept}: coincide ({cnt})")

# ------- 4. VARIABLES CATEGÓRICAS -------
report_lines.append(section('VARIABLES CATEGÓRICAS'))
for col in ['ARMAS MEDIOS', 'TIPO DE HURTO', 'GENERO', 'GRUPO ETARIO']:
    report_lines.append(f"\n--- {col} ---")
    uniq_vals = df[col].unique()
    report_lines.append(f"Valores únicos ({len(uniq_vals)}): {', '.join(map(str, uniq_vals))}")
    freq = df[col].value_counts()
    for val, cnt in freq.items():
        report_lines.append(f"  - {val}: {cnt}")
    # Cross‑check with categorical_analysis.csv
    cat_subset = categorical_df[categorical_df['variable'] == col]
    # Build dict from file
    file_counts = dict(zip(cat_subset['valor'], cat_subset['frecuencia']))
    mismatches = []
    for val, cnt in freq.items():
        file_cnt = file_counts.get(val)
        if file_cnt is None:
            mismatches.append(f"{val} no aparece en el archivo")
        elif int(file_cnt) != cnt:
            mismatches.append(f"{val}: original {cnt} vs. archivo {file_cnt}")
    if mismatches:
        report_lines.append('  Discrepancias con el archivo categorical_analysis.csv:')
        for m in mismatches:
            report_lines.append(f"    - {m}")
    else:
        report_lines.append('  No hay discrepancias con el archivo.')

# ------- 5. ATLÁNTICO -------
report_lines.append(section('ATLÁNTICO'))
atl_rows = len(atlantic_df)
report_lines.append(f"Número exacto de registros en Atlántico: {atl_rows}")
perc = (atl_rows / rows_original) * 100
report_lines.append(f"Participación porcentual respecto al total nacional: {perc:.2f}%")
num_atl_munis = atlantic_df['MUNICIPIO'].nunique()
report_lines.append(f"Número de municipios en Atlántico: {num_atl_munis}")
# Top 5 municipios
top5_munis = atlantic_df['MUNICIPIO'].value_counts().head(5)
report_lines.append('Los 5 municipios con mayor frecuencia:')
for mun, cnt in top5_munis.items():
    report_lines.append(f"  - {mun}: {cnt}")
# Top 5 modalidades (TIPO DE HURTO)
top5_mod = atlantic_df['TIPO DE HURTO'].value_counts().head(5)
report_lines.append('Las 5 modalidades predominantes en Atlántico:')
for mod, cnt in top5_mod.items():
    report_lines.append(f"  - {mod}: {cnt}")

# ------- 6. VALIDACIÓN CRUZADA GENERAL -------
report_lines.append(section('VALIDACIÓN CRUZADA'))
# Compare missing values report with actual detection
missing_report = dict(zip(missing_df['variable'], missing_df['nulos']))
report_lines.append('Comparación de valores nulos:')
for col in df.columns:
    actual_nulls = ((df[col].isna()) | (df[col] == '') | (df[col].str.strip() == '')).sum()
    reported = missing_report.get(col)
    if reported is None:
        report_lines.append(f"  - {col}: no está en missing_values.csv")
    elif actual_nulls != reported:
        report_lines.append(f"  - {col}: diferencia (actual {actual_nulls} vs. reporte {reported})")
    else:
        report_lines.append(f"  - {col}: coincide ({actual_nulls})")

# Final note
report_lines.append('\nAuditoría completada. Todas las comparaciones se realizaron sin modificar ningún archivo.')

# Print report to stdout
print('\n'.join(report_lines))
