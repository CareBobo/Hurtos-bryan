-- =============================================================================
-- PROYECTO MINERÍA DE DATOS: HURTO POR MODALIDADES EN COLOMBIA
-- Base de Datos: PostgreSQL (Neon / Cloud PostgreSQL)
-- Script: 01_create_schema.sql (VERSIÓN SEGURA E IDEMPOTENTE)
-- =============================================================================
-- NOTA DE SEGURIDAD:
-- Se eliminaron las sentencias destructivas DROP TABLE ... CASCADE para prevenir
-- la pérdida accidental de información en bases de datos con datos cargados.
-- Este script emplea CREATE TABLE IF NOT EXISTS y CREATE INDEX IF NOT EXISTS,
-- garantizando que si las tablas ya existen, NO se eliminan ni se alteran los datos.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. TABLA DE STAGING (Carga fiel de los datos crudos del CSV sin transformaciones)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stg_hurtos (
    csv_row_num     BIGINT PRIMARY KEY,
    departamento    VARCHAR(100),
    municipio       VARCHAR(150),
    codigo_dane     VARCHAR(20),
    armas_medios    VARCHAR(100),
    fecha_hecho     VARCHAR(20),
    genero          VARCHAR(50),
    grupo_etario    VARCHAR(50),
    tipo_de_hurto   VARCHAR(150),
    cantidad        VARCHAR(20)
);

-- -----------------------------------------------------------------------------
-- 2. TABLAS DE DIMENSIONES (Star Schema)
-- -----------------------------------------------------------------------------

-- 2.1 Dimensión Temporal
CREATE TABLE IF NOT EXISTS dim_fecha (
    dim_fecha_id    SERIAL PRIMARY KEY,
    fecha           DATE UNIQUE NOT NULL,
    año             INT NOT NULL,
    mes             INT NOT NULL,
    nombre_mes      VARCHAR(20) NOT NULL,
    dia             INT NOT NULL,
    trimestre       INT NOT NULL,
    semana_año      INT NOT NULL,
    dia_semana      VARCHAR(20) NOT NULL
);

-- 2.2 Dimensión Geográfica: Departamentos
CREATE TABLE IF NOT EXISTS dim_departamento (
    dim_depto_id    SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) UNIQUE NOT NULL
);

-- 2.3 Dimensión Geográfica: Municipios
CREATE TABLE IF NOT EXISTS dim_municipio (
    dim_muni_id     SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    codigo_dane     VARCHAR(20) NOT NULL,
    dim_depto_id    INT NOT NULL,
    CONSTRAINT fk_muni_depto FOREIGN KEY (dim_depto_id) 
        REFERENCES dim_departamento (dim_depto_id) ON DELETE CASCADE,
    CONSTRAINT uq_muni_dane_depto UNIQUE (nombre, codigo_dane, dim_depto_id)
);

-- 2.4 Dimensión Arma / Medio Empleado
CREATE TABLE IF NOT EXISTS dim_arma_medio (
    dim_arma_id     SERIAL PRIMARY KEY,
    descripcion     VARCHAR(100) UNIQUE NOT NULL
);

-- 2.5 Dimensión Género (con categoría para valores no reportados/imputados)
CREATE TABLE IF NOT EXISTS dim_genero (
    dim_genero_id   SERIAL PRIMARY KEY,
    valor           VARCHAR(50) UNIQUE NOT NULL
);

-- 2.6 Dimensión Grupo Etario (con categoría para valores no reportados/imputados)
CREATE TABLE IF NOT EXISTS dim_grupo_etario (
    dim_grupo_id    SERIAL PRIMARY KEY,
    rango           VARCHAR(50) UNIQUE NOT NULL
);

-- 2.7 Dimensión Tipo de Hurto / Modalidad Jurídica
CREATE TABLE IF NOT EXISTS dim_tipo_hurto (
    dim_tipo_id     SERIAL PRIMARY KEY,
    descripcion     VARCHAR(150) UNIQUE NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. TABLA DE HECHOS (Fact Table)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_hurtos (
    fact_hurto_id   BIGSERIAL PRIMARY KEY,
    csv_row_num     BIGINT NOT NULL UNIQUE,
    dim_fecha_id    INT NOT NULL,
    dim_muni_id     INT NOT NULL,
    dim_arma_id     INT NOT NULL,
    dim_genero_id   INT NOT NULL,
    dim_grupo_id    INT NOT NULL,
    dim_tipo_id     INT NOT NULL,
    cantidad        INT NOT NULL DEFAULT 1,

    CONSTRAINT fk_fact_stg FOREIGN KEY (csv_row_num) 
        REFERENCES stg_hurtos (csv_row_num) ON DELETE CASCADE,
    CONSTRAINT fk_fact_fecha FOREIGN KEY (dim_fecha_id) 
        REFERENCES dim_fecha (dim_fecha_id),
    CONSTRAINT fk_fact_muni FOREIGN KEY (dim_muni_id) 
        REFERENCES dim_municipio (dim_muni_id),
    CONSTRAINT fk_fact_arma FOREIGN KEY (dim_arma_id) 
        REFERENCES dim_arma_medio (dim_arma_id),
    CONSTRAINT fk_fact_genero FOREIGN KEY (dim_genero_id) 
        REFERENCES dim_genero (dim_genero_id),
    CONSTRAINT fk_fact_grupo FOREIGN KEY (dim_grupo_id) 
        REFERENCES dim_grupo_etario (dim_grupo_id),
    CONSTRAINT fk_fact_tipo FOREIGN KEY (dim_tipo_id) 
        REFERENCES dim_tipo_hurto (dim_tipo_id),
    CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0)
);

-- -----------------------------------------------------------------------------
-- 4. ÍNDICES DE RENDIMIENTO (Creación segura si no existen)
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fact_fecha   ON fact_hurtos (dim_fecha_id);
CREATE INDEX IF NOT EXISTS idx_fact_muni    ON fact_hurtos (dim_muni_id);
CREATE INDEX IF NOT EXISTS idx_fact_arma    ON fact_hurtos (dim_arma_id);
CREATE INDEX IF NOT EXISTS idx_fact_genero  ON fact_hurtos (dim_genero_id);
CREATE INDEX IF NOT EXISTS idx_fact_grupo   ON fact_hurtos (dim_grupo_id);
CREATE INDEX IF NOT EXISTS idx_fact_tipo    ON fact_hurtos (dim_tipo_id);
CREATE INDEX IF NOT EXISTS idx_dim_fecha_dt ON dim_fecha (fecha);
CREATE INDEX IF NOT EXISTS idx_dim_muni_cod ON dim_municipio (codigo_dane);
