import os, hashlib, pandas as pd, unicodedata, re, json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PROJECT_ROOT / 'data' / 'raw' / 'Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv'
EXPECTED_SHA256 = '2d09645b764f7a03d59d3f8c91f70049a8a80d9aa036456921b2d787fe9f1e79'

def compute_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

sha = compute_sha256(RAW_CSV)
print(f'SHA-256: {sha}')
print('SHA match:', sha.lower() == EXPECTED_SHA256.lower())

# Load CSV preserving original strings (empty fields become NaN).
# dtype=str keeps everything as strings, pandas will still parse empty cells as NaN.

df = pd.read_csv(RAW_CSV, dtype=str, engine='python')
print('Rows, Columns:', df.shape)

# ------------------------------------------------
# 1. DEPARTAMENTO analysis
dept_series = df['DEPARTAMENTO']
dept_counts = dept_series.value_counts(dropna=False)
print('\n--- DEPARTAMENTO distinct values and frequencies ---')
for val, cnt in dept_counts.items():
    # Represent NaN as <NaN>
    label = '<NaN>' if pd.isna(val) else repr(val)
    print(f'{label}: {cnt}')

# Detect leading/trailing spaces, invisible chars, tildes differences
print('\n--- DEPARTAMENTO anomalies ---')
for val in dept_counts.index:
    if pd.isna(val):
        continue
    s = str(val)
    if s != s.strip():
        print(f'Value {repr(s)} has leading/trailing spaces')
    # invisible Unicode characters (zero-width spaces, etc.)
    if re.search(r'[\u200B-\u200D\uFEFF]', s):
        print(f'Value {repr(s)} contains invisible Unicode chars')
    # tildes vs plain letters
    norm = unicodedata.normalize('NFD', s)
    plain = norm.encode('ascii', 'ignore').decode('utf-8')
    if plain.upper() != s.upper():
        print(f'Value {repr(s)} differs by tildes/case from {plain}')

# Normalized comparison for ATLANTICO variants
norm_dept = dept_series.astype(str).apply(lambda x: unicodedata.normalize('NFD', x).encode('ascii','ignore').decode('utf-8')).str.upper().str.strip()
atl_mask = norm_dept == 'ATLANTICO'
atl_count = atl_mask.sum()
print('\nRegistros donde DEPARTAMENTO normalizado es ATLANTICO:', atl_count)

# Show original records where MUNICIPIO is Barranquilla (case-insensitive)
print('\n--- Registros con MUNICIPIO "Barranquilla" ---')
mask_barr = df['MUNICIPIO'].astype(str).str.contains('Barranquilla', case=False, na=False)
rows_barr = df[mask_barr]
print('Cantidad:', len(rows_barr))
print(rows_barr.head().to_string(index=False))

# ------------------------------------------------
# 2. CANTIDAD analysis
cant_series = df['CANTIDAD']
unique_cant = cant_series.value_counts(dropna=False).sort_index()
print('\n--- CANTIDAD distinct values and frequencies ---')
for val, cnt in unique_cant.items():
    label = '<NaN>' if pd.isna(val) else repr(val)
    print(f'{label}: {cnt}')
# Identify value '2'
if '2' in unique_cant.index:
    idx_2 = df.index[df['CANTIDAD'] == '2'].tolist()
    print('\nRegistros con CANTIDAD = 2 (indices, 0‑based):', idx_2)
else:
    print('\nNo registros con CANTIDAD = 2')
# Empty strings / NaN
empty_mask = cant_series.astype(str).str.strip() == ''
nan_mask = cant_series.isna()
print('CANTIDAD vacíos (empty strings):', empty_mask.sum())
print('CANTIDAD NaN:', nan_mask.sum())
# Numeric sum verification
numeric = pd.to_numeric(cant_series, errors='coerce')
numeric_sum = numeric.sum(skipna=True)
manual_sum = sum((int(v) * c) for v, c in unique_cant.items() if not pd.isna(v) and str(v).strip()!='')
print('Suma numérica:', numeric_sum)
print('Suma manual (valor*freq):', manual_sum)
print('Suma coinciden:', numeric_sum == manual_sum)

# ------------------------------------------------
# 3. CODIGO DANE analysis
code_series = df['CODIGO DANE']
mask_zero = code_series == '00000000'
zero_rows = df[mask_zero]
print('\n--- Registros con CODIGO DANE = 00000000 ---')
print('Cantidad:', len(zero_rows))
if len(zero_rows)>0:
    print(zero_rows.head().to_string(index=False))
# Length distribution
length_dist = code_series.dropna().astype(str).apply(len).value_counts().sort_index()
print('\nDistribución de longitudes de CODIGO DANE:')
for l, cnt in length_dist.items():
    print(f'{l} dígitos: {cnt}')
# Codes with >1 municipio
code_muni = df[['CODIGO DANE','MUNICIPIO']].dropna()
code_multi_muni = code_muni.groupby('CODIGO DANE')['MUNICIPIO'].nunique()
code_multi = code_multi_muni[code_multi_muni > 1]
print('\nCódigos DANE asociados a >1 municipio:', len(code_multi))
if not code_multi.empty:
    print('Ejemplos:', list(code_multi.index)[:5])
# Municipios with >1 code
muni_code = df[['MUNICIPIO','CODIGO DANE']].dropna()
muni_multi_code = muni_code.groupby('MUNICIPIO')['CODIGO DANE'].nunique()
muni_multi = muni_multi_code[muni_multi_code > 1]
print('\nMunicipios asociados a >1 CODIGO DANE:', len(muni_multi))
if not muni_multi.empty:
    print('Ejemplos:', list(muni_multi.index)[:5])

# ------------------------------------------------
# 4. Missing values analysis
total_rows, total_cols = df.shape
missing_counts = {}
rows_with_missing = set()
for col in df.columns:
    series = df[col]
    nan_mask = series.isna()
    empty_mask = series.astype(str).str.strip() == ''
    space_mask = series.astype(str).apply(lambda x: isinstance(x, str) and x != '' and x.isspace())
    miss_mask = nan_mask | empty_mask | space_mask
    miss_cnt = miss_mask.sum()
    missing_counts[col] = int(miss_cnt)
    rows_with_missing.update(df[miss_mask].index.tolist())
print('\n--- Valores faltantes ---')
print('Celdas faltantes totales:', sum(missing_counts.values()))
print('Filas afectadas (al menos una celda faltante):', len(rows_with_missing))
print('Detalle por columna:')
for col, cnt in missing_counts.items():
    print(f'  {col}: {cnt}')
# Show first 10 affected row indices (1‑based for readability)
print('Primeros 10 índices de filas con faltantes (1‑based):', [i+1 for i in sorted(rows_with_missing)[:10]])
# Compare with missing_values.csv if exists
missing_csv_path = PROJECT_ROOT / 'reports' / 'diagnostics' / 'missing_values.csv'
if missing_csv_path.is_file():
    missing_df = pd.read_csv(missing_csv_path)
    print('\nArchivo missing_values.csv encontrado, filas:', missing_df.shape[0])
else:
    print('\nArchivo missing_values.csv NO encontrado')

# ------------------------------------------------
# 5. Final validation summary
print('\n--- VALIDACIÓN FINAL ---')
print('SHA‑256 coincide con esperado:', sha.lower() == EXPECTED_SHA256.lower())
print('Número de filas:', total_rows)
print('Concordancia con Plan 6.6 (filas, SHA): ver arriba')

