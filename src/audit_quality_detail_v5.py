import os
import sys
import hashlib
import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PROJECT_ROOT / 'data' / 'raw' / 'Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv'
EXPECTED_SHA256 = '2d09645b764f7a03d59d3f8c91f70049a8a80d9aa036456921b2d787fe9f1e79'

def compute_sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def load_csv():
    for delim in [',', ';', '\t']:
        try:
            df = pd.read_csv(RAW_CSV, delimiter=delim, dtype=str, engine='python')
            if df.shape[1] > 1:
                return df, delim
        except Exception:
            continue
    raise RuntimeError('Unable to read CSV')

def normalize(txt):
    import unicodedata, re
    if pd.isna(txt):
        return ''
    txt = unicodedata.normalize('NFKD', str(txt))
    txt = txt.encode('ASCII', 'ignore').decode('ASCII')
    txt = re.sub(r'[^A-Za-z0-9]', '', txt).lower()
    return txt

def main():
    # SHA
    sha = compute_sha256(RAW_CSV)
    if sha.lower() != EXPECTED_SHA256.lower():
        logging.error('SHA mismatch')
        sys.exit(1)
    df, delim = load_csv()
    df.columns = df.columns.str.strip()
    out = []
    out.append('=== DETALLES ADICIONALES DE AUDITORÍA (Plan 6.5) ===')
    out.append(f'Rows: {len(df)}  Delimiter: "{delim}"')

    # 1. Turbaco rows (any dept)
    out.append('\n--- Registros de TURBACO (independientes del DEPARTAMENTO) ---')
    turb_mask = df['MUNICIPIO'].astype(str).str.upper() == 'TURBACO'
    turb_df = df[turb_mask]
    if turb_df.empty:
        out.append('No se encontró ningún registro con MUNICIPIO = TURBACO')
    else:
        for idx, row in turb_df.iterrows():
            out.append(f"  idx {idx}: DEPARTAMENTO={row.get('DEPARTAMENTO','')}, CODIGO DANE={row.get('CODIGO DANE','')}, FECHA HECHO={row.get('FECHA HECHO','')}")

    # 2. Códigos DANE con formato inesperado (no 8 dígitos numeric)
    out.append('\n--- Códigos DANE con formato inesperado (no 8 dígitos numéricos) ---')
    cod_series = df['CODIGO DANE'].dropna().astype(str).str.strip()
    invalid = cod_series[~cod_series.str.fullmatch(r'\d{8}')].unique()
    out.append(f'Cantidad: {len(invalid)}')
    for code in invalid[:20]:
        out.append(f'  {code}')
    if len(invalid) > 20:
        out.append(f'  ... (y {len(invalid)-20} más)')

    # 3. Códigos asociados a varios municipios
    out.append('\n--- Códigos DANE asociados a >1 municipio ---')
    combos = df[['CODIGO DANE', 'MUNICIPIO']].dropna()
    code_multi = combos.groupby('CODIGO DANE')['MUNICIPIO'].nunique()
    multi_codes = code_multi[code_multi>1]
    out.append(f'Cantidad: {len(multi_codes)}')
    for code, cnt in multi_codes.head(20).items():
        out.append(f'  {code}: {cnt} municipios')
    if len(multi_codes) > 20:
        out.append('  ...')

    # 4. Municipios asociados a >1 código DANE
    out.append('\n--- Municipios asociados a >1 código DANE ---')
    muni_multi = combos.groupby('MUNICIPIO')['CODIGO DANE'].nunique()
    multi_munis = muni_multi[muni_multi>1]
    out.append(f'Cantidad: {len(multi_munis)}')
    for muni, cnt in multi_munis.head(20).items():
        out.append(f'  {muni}: {cnt} códigos')
    if len(multi_munis) > 20:
        out.append('  ...')

    # 5. Filas con cualquier NaN (real missing) por columna
    out.append('\n--- Filas con al menos un NaN (valor real faltante) ---')
    missing_mask = df.isna().any(axis=1)
    idxs = df[missing_mask].index.tolist()
    out.append(f'Número de filas con NaN: {len(idxs)}')
    for i in idxs[:10]:
        out.append(f'  fila {i}: {df.loc[i].to_dict()}')
    if len(idxs) > 10:
        out.append(f'  ... (y {len(idxs)-10} más)')

    # 6. Resumen de GENERO y GRUPO ETARIO faltantes
    out.append('\n--- Resumen de valores NaN en columnas clave ---')
    for col in ['GENERO','GRUPO ETARIO','TIPO DE HURTO']:
        nan_cnt = df[col].isna().sum()
        out.append(f'{col}: {nan_cnt} NaN')

    # 7. Participación de Atlántico recalculada sin filtro de nombre exacto (normalizado)
    out.append('\n--- Re‑cálculo de participación de Atlántico (normalizado) ---')
    atl_mask = df['DEPARTAMENTO'].apply(normalize) == 'atlantico'
    total_atl = atl_mask.sum()
    pct = total_atl / len(df) * 100
    out.append(f'Registros Atlántico (normalizado): {total_atl} ({pct:.2f} %)')

    print('\n'.join(out))

if __name__ == '__main__':
    main()

