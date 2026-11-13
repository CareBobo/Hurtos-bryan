import csv, hashlib, os

# Paths
original_path = r'data/raw/Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv'
aux_paths = [
    r'data/raw/Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106_v2.csv',
    r'data/raw/sample.csv'
]

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# File size
size_bytes = os.path.getsize(original_path)
size_mb = size_bytes / (1024 * 1024)

# Detect encoding (try utf-8 then latin-1)
with open(original_path, 'rb') as f_bin:
    raw_sample = f_bin.read(4096)
encodings = ['utf-8', 'latin-1']
for enc in encodings:
    try:
        sample_text = raw_sample.decode(enc)
        break
    except UnicodeDecodeError:
        continue
else:
    enc = 'utf-8'
    sample_text = raw_sample.decode(enc, errors='replace')

# Detect delimiter using csv.Sniffer
dialect = csv.Sniffer().sniff(sample_text)
delimiter = dialect.delimiter

# Read header and count rows respecting quoted newlines
with open(original_path, 'r', encoding=enc, newline='') as f:
    reader = csv.reader(f, delimiter=delimiter)
    header = next(reader)
    num_columns = len(header)
    row_count = sum(1 for _ in reader)

# Read auxiliary headers
aux_headers = {}
for aux in aux_paths:
    try:
        with open(aux, 'r', encoding=enc, newline='') as f_aux:
            aux_header = f_aux.readline().strip()
        aux_headers[os.path.basename(aux)] = aux_header
    except Exception as e:
        aux_headers[os.path.basename(aux)] = f'ERROR: {e}'

# Output report
print('--- Integrity Check Report ---')
print(f'File: {original_path}')
print(f'SHA-256: {compute_sha256(original_path)}')
print(f'Size: {size_bytes} bytes ({size_mb:.2f} MB)')
print(f'Encoding detected: {enc}')
print(f'Delimiter detected: "{delimiter}"')
print(f'Number of columns: {num_columns}')
print('Columns: ' + ', '.join(header))
print(f'Number of data records (excluding header): {row_count}')
print('\nAuxiliary files headers:')
for name, hdr in aux_headers.items():
    print(f' - {name}: {hdr}')
print('--- End of Report ---')

