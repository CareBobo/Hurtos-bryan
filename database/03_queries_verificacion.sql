-- =============================================================================
-- CONSULTAS DE VERIFICACIÓN Y AUDITORÍA - POSTGRESQL NEON
-- Proyecto: Minería de Datos - Detección de Patrones de Hurto en Colombia
-- =============================================================================

-- 1. Verificación del volumen total de registros (Debe ser exactamente 656.635)
SELECT 'stg_hurtos' AS tabla, COUNT(*) AS total_registros FROM stg_hurtos
UNION ALL
SELECT 'fact_hurtos' AS tabla, COUNT(*) AS total_registros FROM fact_hurtos;

-- 2. Conteo de registros en cada una de las tablas dimensionales
SELECT 'dim_fecha' AS dimension, COUNT(*) AS total FROM dim_fecha
UNION ALL
SELECT 'dim_departamento' AS dimension, COUNT(*) FROM dim_departamento
UNION ALL
SELECT 'dim_municipio' AS dimension, COUNT(*) FROM dim_municipio
UNION ALL
SELECT 'dim_arma_medio' AS dimension, COUNT(*) FROM dim_arma_medio
UNION ALL
SELECT 'dim_genero' AS dimension, COUNT(*) FROM dim_genero
UNION ALL
SELECT 'dim_grupo_etario' AS dimension, COUNT(*) FROM dim_grupo_etario
UNION ALL
SELECT 'dim_tipo_hurto' AS dimension, COUNT(*) FROM dim_tipo_hurto;

-- 3. Auditoría de Integridad Referencial (Debe retornar 0 registros huérfanos)
SELECT COUNT(*) AS registros_huerfanos
FROM fact_hurtos fh
LEFT JOIN dim_fecha df ON fh.dim_fecha_id = df.dim_fecha_id
LEFT JOIN dim_municipio dm ON fh.dim_muni_id = dm.dim_muni_id
LEFT JOIN dim_arma_medio da ON fh.dim_arma_id = da.dim_arma_id
LEFT JOIN dim_genero dg ON fh.dim_genero_id = dg.dim_genero_id
LEFT JOIN dim_grupo_etario dgt ON fh.dim_grupo_id = dgt.dim_grupo_id
LEFT JOIN dim_tipo_hurto dt ON fh.dim_tipo_id = dt.dim_tipo_id
WHERE df.dim_fecha_id IS NULL 
   OR dm.dim_muni_id IS NULL 
   OR da.dim_arma_id IS NULL
   OR dg.dim_genero_id IS NULL 
   OR dgt.dim_grupo_id IS NULL 
   OR dt.dim_tipo_id IS NULL;

-- 4. Verificación de imputación de valores faltantes (Cero pérdida de datos)
SELECT dg.valor AS genero, COUNT(fh.fact_hurto_id) AS total_hechos, 
       ROUND(COUNT(fh.fact_hurto_id) * 100.0 / 656635, 3) AS porcentaje
FROM fact_hurtos fh
JOIN dim_genero dg ON fh.dim_genero_id = dg.dim_genero_id
GROUP BY dg.valor
ORDER BY total_hechos DESC;

SELECT dge.rango AS grupo_etario, COUNT(fh.fact_hurto_id) AS total_hechos,
       ROUND(COUNT(fh.fact_hurto_id) * 100.0 / 656635, 3) AS porcentaje
FROM fact_hurtos fh
JOIN dim_grupo_etario dge ON fh.dim_grupo_id = dge.dim_grupo_id
GROUP BY dge.rango
ORDER BY total_hechos DESC;

-- 5. Consulta Analítica: Top 10 Departamentos con Mayor Incidencia de Hurtos
SELECT 
    dd.nombre AS departamento,
    COUNT(fh.fact_hurto_id) AS total_hurtos,
    SUM(CASE WHEN dt.descripcion LIKE '%MOTOCICLETAS%' THEN 1 ELSE 0 END) AS hurto_motos,
    SUM(CASE WHEN dt.descripcion LIKE '%AUTOMOTORES%' THEN 1 ELSE 0 END) AS hurto_automotores,
    ROUND(COUNT(fh.fact_hurto_id) * 100.0 / 656635, 2) AS pct_nacional
FROM fact_hurtos fh
JOIN dim_municipio dm ON fh.dim_muni_id = dm.dim_muni_id
JOIN dim_departamento dd ON dm.dim_depto_id = dd.dim_depto_id
JOIN dim_tipo_hurto dt ON fh.dim_tipo_id = dt.dim_tipo_id
GROUP BY dd.nombre
ORDER BY total_hurtos DESC
LIMIT 10;

-- 6. Consulta Analítica: Tendencia Temporal Anual (2010 a 2025)
SELECT 
    df.año,
    COUNT(fh.fact_hurto_id) AS total_hurtos
FROM fact_hurtos fh
JOIN dim_fecha df ON fh.dim_fecha_id = df.dim_fecha_id
GROUP BY df.año
ORDER BY df.año ASC;

