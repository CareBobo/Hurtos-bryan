import os, sys, hashlib, datetime, platform, json, logging
import pandas as pd, numpy as np, csv, matplotlib

# ----------------------------------------------------------------------
# Logging configuration (must be the first thing executed)
log_path = os.path.join('reports', 'diagnostics', 'diagnostic_run.log')
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logging.info('--- Diagnostic script started ---')

# Versions and run info
PY_VER = platform.python_version()
PD_VER = pd.__version__
NP_VER = np.__version__
MG_VER = matplotlib.__version__
RUN_TIME = datetime.datetime.now().isoformat()
logging.info(f'Python version: {PY_VER}')
logging.info(f'Pandas version: {PD_VER}')
logging.info(f'NumPy version: {NP_VER}')
logging.info(f'Matplotlib version: {MG_VER}')
logging.info(f'Run time: {RUN_TIME}')

# ----------------------------------------------------------------------
# Expected SHA-256 of original CSV
HASH_EXPECTED = "2d09645b764f7a03d59d3f8c91f70049a8a80d9aa036456921b2d787fe9f1e79"
CSV_PATH = os.path.join('data', 'raw', 'Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv')

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(8192), b''):
            h.update(blk)
    return h.hexdigest()

try:
    hash_actual = compute_sha256(CSV_PATH)
    logging.info(f'Computed SHA-256: {hash_actual}')
    if hash_actual.lower() != HASH_EXPECTED.lower():
        raise ValueError(f'Hash mismatch. Expected {HASH_EXPECTED}, got {hash_actual}')
    else:
        logging.info('SHA-256 hash matches expected value.')
except Exception as e:
    logging.error(f'Error computing or verifying hash: {e}')
    raise

# ----------------------------------------------------------------------
# Helper to avoid overwriting existing files
def safe_write_csv(df, path):
    if os.path.exists(path):
        raise FileExistsError(f'Output file already exists: {path}')
    df.to_csv(path, index=False)
    logging.info(f'Created CSV: {path}')

def safe_write_md(text, path):
    if os.path.exists(path):
        raise FileExistsError(f'Output file already exists: {path}')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    logging.info(f'Created MD: {path}')

def safe_write_json(obj, path):
    if os.path.exists(path):
        raise FileExistsError(f'Output file already exists: {path}')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
    logging.info(f'Created JSON: {path}')

# ----------------------------------------------------------------------
# Read CSV: keep everything as text, no automatic NA conversion
logging.info('Reading CSV with all columns as text')
try:
    df = pd.read_csv(
        CSV_PATH,
        encoding='utf-8',
        sep=',',
        dtype=str,
        keep_default_na=False,
        na_values=[]
    )
    logging.info(f'CSV loaded, shape {df.shape}')
except Exception as e:
    logging.error(f'Error reading CSV: {e}')
    raise

# ----------------------------------------------------------------------
# 1. Null detection per column (NaN, empty string, only spaces)
null_counts = {}
for col in df.columns:
    series = df[col]
    is_nan = series.isna()
    is_empty = series == ''
    is_blank = series.str.strip() == ''
    null_counts[col] = (is_nan | is_empty | is_blank).sum()
null_df = pd.DataFrame({
    'variable': list(null_counts.keys()),
    'nulos': list(null_counts.values()),
    '%_nulos': [ (c/len(df))*100 for c in null_counts.values() ]
})
# Write missing values CSV
missing_path = os.path.join('reports','diagnostics','missing_values.csv')
safe_write_csv(null_df, missing_path)

# ----------------------------------------------------------------------
# 2. Duplicados exactos
dup_exact_mask = df.duplicated(keep=False)
dup_exact = df[dup_exact_mask]
dup_exact_count = len(dup_exact)
# Prepare MD content
md_dup = "# Duplicados exactos\n"

md_dup += "- Muestra (máx 20 filas):\n"
md_dup += "```\n" + dup_exact.head(20).to_string(index=False) + "\n```\n"

md_dup += "- Muestra (máx 20 filas):\n"
md_dup += "```\n" + dup_exact.head(20).to_string(index=False) + "\n```\n"

md_dup += "- Muestra (máx 20 filas):\n"
md_dup += "```\n" + dup_exact.head(20).to_string(index=False) + "\n```\n"

md_dup += "- Muestra (máx 20 filas):\n\n"
md_dup += "```\n" + dup_exact.head(20).to_string(index=False) + "\n```\n"

# 3. Duplicados parciales (clave de exploración)
partial_key = ['DEPARTAMENTO','MUNICIPIO','CODIGO DANE','FECHA HECHO']
dup_partial_mask = df.duplicated(subset=partial_key, keep=False)
dup_partial = df[dup_partial_mask]
dup_partial_rows = len(dup_partial)
comb_rep = dup_partial[partial_key].drop_duplicates()
comb_rep_count = len(comb_rep)
md_dup += "\n## Duplicados parciales (clave de exploración)\n"
md_dup += f"- Filas involucradas: {dup_partial_rows}\n"
md_dup += f"- Combinaciones repetidas: {comb_rep_count}\n"
md_dup += "- Muestra (máx 20 filas):\n"
md_dup += "```\n" + dup_partial.head(20).to_string(index=False) + "\n```\n"
md_dup += "\n*Nota:* Estas coincidencias pueden no ser errores reales.\n"
# Write duplicate analysis MD
dup_md_path = os.path.join('reports','diagnostics','duplicate_analysis.md')
safe_write_md(md_dup, dup_md_path)

# ----------------------------------------------------------------------
# 4. Normalization for ATLÁNTICO detection
def normalize_depto(txt):
    if pd.isna(txt):
        return ''
    txt = txt.strip().upper()
    for a,b in zip('ÁÉÍÓÚ', 'AEIOU'):
        txt = txt.replace(a,b)
    return txt
df['DEPARTAMENTO_NORM'] = df['DEPARTAMENTO'].apply(normalize_depto)
atl_mask = df['DEPARTAMENTO_NORM'].str.contains('ATLANTICO')
atlantic_df = df[atl_mask]
atlantic_path = os.path.join('reports','diagnostics','atlantic_analysis.csv')
safe_write_csv(atlantic_df, atlantic_path)

# ----------------------------------------------------------------------
# 5. FECHA HECHO handling

def parse_date_entry(val):
    if pd.isna(val) or str(val).strip() == '':
        return pd.NaT, 'faltante'
    s = str(val).strip()
    for fmt in ('%d/%m/%Y','%Y-%m-%d','%d-%m-%Y'):
        try:
            dt = datetime.datetime.strptime(s, fmt)
            return pd.Timestamp(dt), 'válida'
        except Exception:
            continue
    return pd.NaT, 'inválida'

parsed = df['FECHA HECHO'].apply(parse_date_entry)
df['FECHA_PARSED'] = parsed.apply(lambda x: x[0])
# Ensure datetime64 dtype
df['FECHA_PARSED'] = pd.to_datetime(df['FECHA_PARSED'], errors='coerce')
df['FECHA_ESTADO'] = parsed.apply(lambda x: x[1])

valid_mask = df['FECHA_ESTADO'] == 'válida'
missing_mask = df['FECHA_ESTADO'] == 'faltante'
invalid_mask = df['FECHA_ESTADO'] == 'inválida'

temporal_summary = {
    'válidas': int(valid_mask.sum()),
    'faltantes': int(missing_mask.sum()),
    'inválidas': int(invalid_mask.sum())
}
# Frequency by year/month/week_day (only valid dates)
if valid_mask.any():
    temp = df.loc[valid_mask, 'FECHA_PARSED']
    temp_df = pd.DataFrame({
        'año': temp.dt.year,
        'mes': temp.dt.month,
        'dia_semana': temp.dt.day_name()
    })
    temp_counts = temp_df.groupby(['año','mes','dia_semana']).size().reset_index(name='filas')
    temporal_path = os.path.join('reports','diagnostics','temporal_analysis.csv')
    safe_write_csv(temp_counts, temporal_path)
    min_date = temp.min()
    max_date = temp.max()
else:
    temp_counts = pd.DataFrame()
    min_date = max_date = None

# ----------------------------------------------------------------------
# 6. Geographic analysis (filas y suma CANTIDAD)
# First, handle CANTIDAD categorisation (see section 7)

def categorize_cantidad(val):
    if pd.isna(val) or str(val).strip() == '':
        return 'vacío', np.nan
    try:
        iv = int(val)
        if iv < 0:
            return 'negativo', iv
        elif iv == 0:
            return 'cero', iv
        else:
            return 'válido', iv
    except Exception:
        return 'no_numérico', np.nan

cat, num = zip(*df['CANTIDAD'].apply(categorize_cantidad))
df['CANTIDAD_CAT'] = cat
df['CANTIDAD_INT'] = num

geo = (
    df.groupby(['CODIGO DANE','DEPARTAMENTO','MUNICIPIO'])
      .agg(filas=('CODIGO DANE','size'), suma_cantidad=('CANTIDAD_INT','sum'))
      .reset_index()
)
geo_path = os.path.join('reports','diagnostics','geographic_analysis.csv')
safe_write_csv(geo, geo_path)

# ----------------------------------------------------------------------
# 7. Categorical variables frequencies
cat_cols = ['ARMAS MEDIOS','TIPO DE HURTO','GENERO','GRUPO ETARIO']
cat_frames = []
for c in cat_cols:
    cnt = df[c].value_counts(dropna=False).reset_index()
    cnt.columns = ['valor','frecuencia']
    cnt['variable'] = c
    cat_frames.append(cnt)
cat_df = pd.concat(cat_frames, ignore_index=True)
cat_path = os.path.join('reports','diagnostics','categorical_analysis.csv')
safe_write_csv(cat_df, cat_path)

# ----------------------------------------------------------------------
# 8. Quantity statistics and anomalies
quantity_stats = {
    'min': df['CANTIDAD_INT'].min(),
    'max': df['CANTIDAD_INT'].max(),
    'mean': df['CANTIDAD_INT'].mean(),
    'median': df['CANTIDAD_INT'].median(),
    'std': df['CANTIDAD_INT'].std(),
    'suma': df['CANTIDAD_INT'].sum()
}
qty_stats_path = os.path.join('reports','diagnostics','quantity_statistics.csv')
safe_write_csv(pd.DataFrame([quantity_stats]), qty_stats_path)

# Anomalies per category
anomalies = {
    'vacíos': df.loc[df['CANTIDAD_CAT']=='vacío', 'CANTIDAD'].unique().tolist(),
    'no_numéricos': df.loc[df['CANTIDAD_CAT']=='no_numérico', 'CANTIDAD'].unique().tolist(),
    'negativos': df.loc[df['CANTIDAD_CAT']=='negativo', 'CANTIDAD_INT'].unique().tolist(),
    'ceros': df.loc[df['CANTIDAD_CAT']=='cero', 'CANTIDAD_INT'].unique().tolist()
}
anom_path = os.path.join('reports','diagnostics','quantity_anomalies.json')
safe_write_json(anomalies, anom_path)

# ----------------------------------------------------------------------
# 9. Comparison rows vs sum quantity (no interpretation)
row_count = len(df)
sum_quantity = df['CANTIDAD_INT'].sum()

# ----------------------------------------------------------------------
# 10. Generate figures (matplotlib)
import matplotlib.pyplot as plt
fig_dir = os.path.join('reports','diagnostics','figures')

# 10.1 Hurtos por año (filas + suma cantidad on secondary axis)
if valid_mask.any():
    yearly_rows = df.loc[valid_mask].groupby(df.loc[valid_mask,'FECHA_PARSED'].dt.year).size()
    yearly_qty = df.loc[valid_mask].groupby(df.loc[valid_mask,'FECHA_PARSED'].dt.year)['CANTIDAD_INT'].sum()
    fig, ax1 = plt.subplots(figsize=(10,6))
    ax1.bar(yearly_rows.index.astype(str), yearly_rows.values, color='steelblue', label='Filas')
    ax1.set_xlabel('Año')
    ax1.set_ylabel('Número de filas')
    ax2 = ax1.twinx()
    ax2.plot(yearly_qty.index.astype(str), yearly_qty.values, color='darkorange', marker='o', label='Suma CANTIDAD')
    ax2.set_ylabel('Suma de CANTIDAD')
    plt.title('Hurtos por año')
    plt.suptitle('Elaboración propia con datos de la Policía Nacional', fontsize=8, style='italic')
    fig.tight_layout()
    fig_path = os.path.join(fig_dir, 'hurtos_por_año.png')
    plt.savefig(fig_path)
    plt.close(fig)
    logging.info(f'Created figure: {fig_path}')

# 10.2 Hurtos por departamento (filas + suma)
dept_rows = df.groupby('DEPARTAMENTO').size()
dept_qty = df.groupby('DEPARTAMENTO')['CANTIDAD_INT'].sum()
fig, ax1 = plt.subplots(figsize=(12,6))
ax1.bar(dept_rows.index, dept_rows.values, color='steelblue')
ax1.set_xlabel('Departamento')
ax1.set_ylabel('Número de filas')
ax2 = ax1.twinx()
ax2.plot(dept_qty.index, dept_qty.values, color='darkorange', marker='o')
ax2.set_ylabel('Suma de CANTIDAD')
plt.title('Hurtos por departamento')
plt.suptitle('Elaboración propia con datos de la Policía Nacional', fontsize=8, style='italic')
plt.xticks(rotation=45, ha='right')
fig_path = os.path.join(fig_dir, 'hurtos_por_departamento.png')
plt.savefig(fig_path, bbox_inches='tight')
plt.close(fig)
logging.info(f'Created figure: {fig_path}')

# 10.3 Atlántico por municipio (filas + suma)
if not atlantic_df.empty:
    atl_mun_rows = atlantic_df.groupby('MUNICIPIO').size()
    atl_mun_qty = atlantic_df.groupby('MUNICIPIO')['CANTIDAD_INT'].sum()
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.bar(atl_mun_rows.index, atl_mun_rows.values, color='steelblue')
    ax1.set_xlabel('Municipio (Atlántico)')
    ax1.set_ylabel('Número de filas')
    ax2 = ax1.twinx()
    ax2.plot(atl_mun_qty.index, atl_mun_qty.values, color='darkorange', marker='o')
    ax2.set_ylabel('Suma de CANTIDAD')
    plt.title('Hurtos en Atlántico por municipio')
    plt.suptitle('Elaboración propia con datos de la Policía Nacional', fontsize=8, style='italic')
    plt.xticks(rotation=45, ha='right')
    fig_path = os.path.join(fig_dir, 'atlantic_por_municipio.png')
    plt.savefig(fig_path, bbox_inches='tight')
    plt.close(fig)
    logging.info(f'Created figure: {fig_path}')

# 10.4 Tipo de hurto (filas only)
fig, ax = plt.subplots(figsize=(10,6))
tipo_counts = df['TIPO DE HURTO'].value_counts()
ax.bar(tipo_counts.index, tipo_counts.values, color='steelblue')
ax.set_xlabel('Tipo de hurto')
ax.set_ylabel('Frecuencia')
plt.title('Distribución de Tipo de hurto')
plt.suptitle('Elaboración propia con datos de la Policía Nacional', fontsize=8, style='italic')
plt.xticks(rotation=45, ha='right')
fig_path = os.path.join(fig_dir, 'tipo_de_hurto.png')
plt.savefig(fig_path, bbox_inches='tight')
plt.close(fig)
logging.info(f'Created figure: {fig_path}')

# 10.5 Armas y medios (filas only)
fig, ax = plt.subplots(figsize=(10,6))
armas_counts = df['ARMAS MEDIOS'].value_counts()
ax.bar(armas_counts.index, armas_counts.values, color='steelblue')
ax.set_xlabel('Armas y medios')
ax.set_ylabel('Frecuencia')
plt.title('Distribución de Armas y medios')
plt.suptitle('Elaboración propia con datos de la Policía Nacional', fontsize=8, style='italic')
plt.xticks(rotation=45, ha='right')
fig_path = os.path.join(fig_dir, 'armas_medios.png')
plt.savefig(fig_path, bbox_inches='tight')
plt.close(fig)
logging.info(f'Created figure: {fig_path}')

# 10.6 Género y grupo etario (filas only – stacked bar)
fig, ax = plt.subplots(figsize=(12,6))
gender_age = df.groupby(['GENERO','GRUPO ETARIO']).size().unstack(fill_value=0)
gender_age.plot(kind='bar', stacked=True, ax=ax)
ax.set_xlabel('Género')
ax.set_ylabel('Frecuencia')
plt.title('Distribución de Género y Grupo Etario')
plt.suptitle('Elaboración propia con datos de la Policía Nacional', fontsize=8, style='italic')
fig_path = os.path.join(fig_dir, 'genero_grupo_etario.png')
plt.savefig(fig_path, bbox_inches='tight')
plt.close(fig)
logging.info(f'Created figure: {fig_path}')

# ----------------------------------------------------------------------
# 11. Build diagnostic summary (MD)
summary_md = f"""# Diagnóstico exploratorio – Resumen

**Fecha de ejecución:** {RUN_TIME}

## Información del archivo
- **SHA‑256:** {hash_actual}
- **Tamaño:** {os.path.getsize(CSV_PATH)} bytes
- **Filas (registros):** {row_count}
- **Columnas:** {len(df.columns)} ({', '.join(df.columns)})

## Valores nulos por columna
(Archivo `missing_values.csv`)

## Duplicados
- Duplicados exactos: {dup_exact_count}
- Duplicados parciales (filas involucradas): {dup_partial_rows}
- Duplicados parciales (combinaciones repetidas): {comb_rep_count}

## Fechas
- Válidas: {temporal_summary['válidas']}
- Faltantes / vacías: {temporal_summary['faltantes']}
- Formato inválido: {temporal_summary['inválidas']}
- Rango de fechas válidas: {min_date.date() if min_date else 'N/A'} – {max_date.date() if max_date else 'N/A'}

## Cantidad
- Total filas: {row_count}
- Suma de CANTIDAD (incluye NaN como 0 en la suma): {sum_quantity}
- Estadísticas (archivo `quantity_statistics.csv`)
- Anomalías (archivo `quantity_anomalies.json`)

## Análisis geográfico
(Archivo `geographic_analysis.csv`)

## Análisis categórico
(Archivo `categorical_analysis.csv`)

## Atlántico
(Archivo `atlantic_analysis.csv`)

## Gráficos generados
- `hurtos_por_año.png`
- `hurtos_por_departamento.png`
- `atlantic_por_municipio.png`
- `tipo_de_hurto.png`
- `armas_medios.png`
- `genero_grupo_etario.png`

## Advertencias / notas
- No se modificó el CSV original.
- No se imputaron valores; los registros faltantes se mantienen como NaN.
- Las comparaciones entre número de filas y suma de CANTIDAD se presentan sin interpretación de su relación.
"""
summary_path = os.path.join('reports','diagnostics','diagnostic_summary.md')
safe_write_md(summary_md, summary_path)
logging.info('Diagnostic summary markdown created')

logging.info('--- Diagnostic script completed successfully ---')
