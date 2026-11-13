-- ---------------------------------------------------------------
--  DDL para el modelo dimensional de PROYECTO_HURTO_COLOMBIA
--  Base de datos: hurto_colombia (Neon PostgreSQL)
-- ---------------------------------------------------------------

-- 1. Tabla de Staging (mantiene los valores originales)
CREATE TABLE stg_hurtos (
    csv_row_num   BIGINT   PRIMARY KEY,
    DEPARTAMENTO  TEXT,
    MUNICIPIO     TEXT,
    "CODIGO DANE" TEXT,
    "ARMAS MEDIOS" TEXT,
    "FECHA HECHO" TEXT,
    GENERO        TEXT,
    "GRUPO ETARIO" TEXT,
    "TIPO DE HURTO" TEXT,
    CANTIDAD      TEXT
);

-- 2. Dimensiones

-- 2.1 Dimensión Fecha
CREATE TABLE dim_fecha (
    dim_fecha_id   SERIAL PRIMARY KEY,
    fecha          DATE   UNIQUE,
    año            INT,
    mes            INT,
    dia            INT,
    trimestre      INT,
    semana_del_año INT,
    dia_semana     TEXT
);

-- 2.2 Dimensión Departamento
CREATE TABLE dim_departamento (
    dim_depto_id SERIAL PRIMARY KEY,
    nombre       TEXT   UNIQUE
);

-- 2.3 Dimensión Municipio
CREATE TABLE dim_municipio (
    dim_muni_id  SERIAL PRIMARY KEY,
    nombre       TEXT,
    codigo_dane  TEXT,
    dim_depto_id INT NOT NULL,
    CONSTRAINT fk_muni_depto
        FOREIGN KEY (dim_depto_id)
        REFERENCES dim_departamento (dim_depto_id),
    CONSTRAINT uniq_muni_codigo
        UNIQUE (codigo_dane, dim_depto_id),
    CONSTRAINT uq_dim_muni_depto
        UNIQUE (dim_muni_id, dim_depto_id)
);

-- 2.4 Dimensión Arma / Medio
CREATE TABLE dim_arma_medio (
    dim_arma_id SERIAL PRIMARY KEY,
    descripcion TEXT   UNIQUE
);

-- 2.5 Dimensión Género (incluye placeholder DESCONOCIDO)
CREATE TABLE dim_genero (
    dim_genero_id SERIAL PRIMARY KEY,
    valor         TEXT   UNIQUE
);

-- Insert placeholder for missing gender values
INSERT INTO dim_genero (valor) VALUES ('DESCONOCIDO')
ON CONFLICT (valor) DO NOTHING;

-- 2.6 Dimensión Grupo Etario (incluye placeholder DESCONOCIDO)
CREATE TABLE dim_grupo_etario (
    dim_grupo_id SERIAL PRIMARY KEY,
    rango        TEXT   UNIQUE
);

-- Insert placeholder for missing group‑age values
INSERT INTO dim_grupo_etario (rango) VALUES ('DESCONOCIDO')
ON CONFLICT (rango) DO NOTHING;

-- 2.7 Dimensión Tipo de Hurto
CREATE TABLE dim_tipo_hurto (
    dim_tipo_id SERIAL PRIMARY KEY,
    descripcion TEXT   UNIQUE
);

-- 3. Tabla de hechos (sin dim_depto_id; se obtiene vía municipio)
CREATE TABLE fact_hurtos (
    hurtos_id      BIGSERIAL PRIMARY KEY,
    csv_row_num    BIGINT NOT NULL,
    dim_fecha_id   INT    NOT NULL,
    dim_muni_id    INT    NOT NULL,
    dim_arma_id    INT    NOT NULL,
    dim_genero_id  INT    NOT NULL,
    dim_grupo_id   INT    NOT NULL,
    dim_tipo_id    INT    NOT NULL,
    cantidad       INT    NOT NULL,

    -- Trazabilidad única: evita carga duplicada
    CONSTRAINT uq_fact_csv_row UNIQUE (csv_row_num),

    -- FK a staging (trazabilidad)
    CONSTRAINT fk_fact_stg
        FOREIGN KEY (csv_row_num)
        REFERENCES stg_hurtos (csv_row_num),

    -- FK a dimensiones
    CONSTRAINT fk_fact_fecha
        FOREIGN KEY (dim_fecha_id)
        REFERENCES dim_fecha (dim_fecha_id),

    CONSTRAINT fk_fact_muni
        FOREIGN KEY (dim_muni_id)
        REFERENCES dim_municipio (dim_muni_id),

    CONSTRAINT fk_fact_arma
        FOREIGN KEY (dim_arma_id)
        REFERENCES dim_arma_medio (dim_arma_id),

    CONSTRAINT fk_fact_genero
        FOREIGN KEY (dim_genero_id)
        REFERENCES dim_genero (dim_genero_id),

    CONSTRAINT fk_fact_grupo
        FOREIGN KEY (dim_grupo_id)
        REFERENCES dim_grupo_etario (dim_grupo_id),

    CONSTRAINT fk_fact_tipo
        FOREIGN KEY (dim_tipo_id)
        REFERENCES dim_tipo_hurto (dim_tipo_id),

    -- Regla de negocio: cantidad siempre positiva
    CONSTRAINT chk_cantidad_pos CHECK (cantidad > 0)
);

-- 4. Índices de apoyo (B‑Tree) para acelerar consultas comunes
CREATE INDEX idx_fact_fecha   ON fact_hurtos (dim_fecha_id);
CREATE INDEX idx_fact_muni    ON fact_hurtos (dim_muni_id);
CREATE INDEX idx_fact_arma    ON fact_hurtos (dim_arma_id);
CREATE INDEX idx_fact_genero  ON fact_hurtos (dim_genero_id);
CREATE INDEX idx_fact_grupo   ON fact_hurtos (dim_grupo_id);
CREATE INDEX idx_fact_tipo    ON fact_hurtos (dim_tipo_id);
CREATE INDEX idx_fact_cantidad ON fact_hurtos (cantidad);

-- ---------------------------------------------------------------
-- Fin del DDL
-- ---------------------------------------------------------------

