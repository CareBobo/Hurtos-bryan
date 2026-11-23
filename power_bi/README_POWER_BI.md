# GUÍA OFICIAL PARA CONSTRUIR EL DASHBOARD EN POWER BI (.PBIX)
**Proyecto:** Minería de Datos - Detección de Patrones de Hurto en Colombia (656.635 Hechos)  
**Autor:** Bryan  

---

## 🎯 1. Opciones de Conexión a Datos

Power BI Desktop te ofrece dos formas para cargar los datos:

### Opción A (Recomendada para Modelo Estrella):
1. Abre **Power BI Desktop**.
2. Haz clic en **Obtener datos** -> **Texto o CSV**.
3. Carga cada uno de los archivos ubicados en la carpeta `data/processed/`:
   * `fact_hurtos.csv` (Tabla de hechos: 656.635 registros)
   * `dim_fecha.csv` (Dimensión temporal)
   * `dim_departamento.csv` (Departamentos)
   * `dim_municipio.csv` (Municipios con código DANE)
   * `dim_arma_medio.csv` (Armas y medios empleados)
   * `dim_genero.csv` (Género de la víctima)
   * `dim_grupo_etario.csv` (Grupo etario)
   * `dim_tipo_hurto.csv` (Modalidad de hurto)

### Opción B (Conexión Directa a la Nube Neon PostgreSQL):
1. En Power BI Desktop: **Obtener datos** -> **Base de datos PostgreSQL**.
2. Servidor: Pega el host de tu Neon (ej. `ep-cool-fog-123456.us-east-2.aws.neon.tech`).
3. Base de datos: `neondb` (o el nombre que le diste).
4. Modo de conectividad: **Importar**.
5. Selecciona las tablas del esquema `public`.

---

## 📐 2. Modelo de Datos y Relaciones (Star Schema)

En la vista **Modelo** de Power BI, verifica o crea las siguientes relaciones (todas de **1 a varios / 1:* ** con dirección de filtro cruzado única):

* `dim_fecha[dim_fecha_id]` (1)  ----->  `fact_hurtos[dim_fecha_id]` (*)
* `dim_municipio[dim_muni_id]` (1) ----->  `fact_hurtos[dim_muni_id]` (*)
* `dim_departamento[dim_depto_id]` (1) -----> `dim_municipio[dim_depto_id]` (*)
* `dim_arma_medio[dim_arma_id]` (1) ----->  `fact_hurtos[dim_arma_id]` (*)
* `dim_genero[dim_genero_id]` (1)  ----->  `fact_hurtos[dim_genero_id]` (*)
* `dim_grupo_etario[dim_grupo_id]` (1) -----> `fact_hurtos[dim_grupo_id]` (*)
* `dim_tipo_hurto[dim_tipo_id]` (1) -----> `fact_hurtos[dim_tipo_id]` (*)

*(Captura obligatoria: Toma una captura de esta pantalla de relaciones para el artículo).*

---

## 🧮 3. Catálogo Oficial de Medidas DAX (11 Medidas Reales)

Crea una tabla de medidas dedicada o agrégalas directamente en la tabla `fact_hurtos`. El catálogo contiene exactamente **11 medidas analíticas**:

### A. Medidas de Volumen y Recuento (3 Medidas)
1. **Total de Incidentes:**
   ```dax
   Total Hurtos = COUNTROWS(fact_hurtos)
   ```
2. **Hurtos de Motocicletas:**
   ```dax
   Hurtos Motocicletas = 
   CALCULATE(
       [Total Hurtos],
       dim_tipo_hurto[descripcion] = "ARTÍCULO 239. HURTO MOTOCICLETAS"
   )
   ```
3. **Hurtos de Automotores:**
   ```dax
   Hurtos Automotores = 
   CALCULATE(
       [Total Hurtos],
       dim_tipo_hurto[descripcion] = "ARTÍCULO 239. HURTO AUTOMOTORES"
   )
   ```

### B. Medidas de Proporción y Tasas Porcentuales (3 Medidas)
4. **% Participación Motocicletas:**
   ```dax
   % Hurtos Motos = 
   DIVIDE([Hurtos Motocicletas], [Total Hurtos], 0)
   ```
5. **% Participación Automotores:**
   ```dax
   % Hurtos Autos = 
   DIVIDE([Hurtos Automotores], [Total Hurtos], 0)
   ```
6. **% Hurto a Mano Armada:**
   ```dax
   % Uso Arma de Fuego = 
   DIVIDE([Hurtos Arma de Fuego], [Total Hurtos], 0)
   ```

### C. Medidas de Modus Operandi y Armas (3 Medidas)
7. **Hurtos con Arma de Fuego:**
   ```dax
   Hurtos Arma de Fuego = 
   CALCULATE(
       [Total Hurtos],
       dim_arma_medio[descripcion] = "ARMA DE FUEGO"
   )
   ```
8. **Hurtos con Llave Maestra:**
   ```dax
   Hurtos Llave Maestra = 
   CALCULATE(
       [Total Hurtos],
       dim_arma_medio[descripcion] = "LLAVE MAESTRA"
   )
   ```
9. **Hurtos Sin Armas (Oportunidad / Descuido):**
   ```dax
   Hurtos Sin Armas = 
   CALCULATE(
       [Total Hurtos],
       dim_arma_medio[descripcion] = "SIN EMPLEO DE ARMAS"
   )
   ```

### D. Medidas de Inteligencia Temporal y YoY (2 Medidas)
10. **Hurtos Mismo Periodo Año Anterior (YoY):**
    ```dax
    Hurtos LY = 
    CALCULATE(
        [Total Hurtos],
        SAMEPERIODLASTYEAR(dim_fecha[fecha])
    )
    ```
11. **Variación Interanual (%):**
    ```dax
    Variación YoY % = 
    DIVIDE([Total Hurtos] - [Hurtos LY], [Hurtos LY], 0)
    ```

---

## 🖥️ 4. Estructura de Páginas del Dashboard

Te sugerimos diseñar 2 o 3 páginas en el informe:

### Página 1: Visión Estratégica y KPIs Ejecutivos
* **Tarjetas KPI arriba:** `[Total Hurtos]`, `[Hurtos Motocicletas]`, `[Hurtos Automotores]`, `[% Uso Arma de Fuego]`.
* **Segmentadores (Filtros):** Año (`dim_fecha[año]`), Modalidad (`dim_tipo_hurto[descripcion]`), Departamento (`dim_departamento[nombre]`).
* **Gráfico de Líneas:** Evolución Anual/Mensual (`dim_fecha[fecha]` en eje X, `[Total Hurtos]` en eje Y).
* **Gráfico de Donut:** Proporción Motos vs Carros.

### Página 2: Modus Operandi y Perfil Demográfico
* **Gráfico de Barras Horizontales:** Top 7 Armas y Medios Empleados (`dim_arma_medio[descripcion]`).
* **Gráfico de Columnas Agrupadas:** Distribución por Género (`dim_genero[valor]`) y Grupo Etario (`dim_grupo_etario[rango]`).
* **Matriz:** Cruce de Armas vs Tipo de Hurto.

### Página 3: Focalización Geoespacial y Ranking Municipal
* **Gráfico de Barras Horizontales:** Top 10 Departamentos más críticos.
* **Tabla o Mapa:** Municipios críticos con indicador de Pareto.

---

## 📸 5. Lista de Capturas de Pantalla Obligatorias para el Documento
1. Captura de la vista **Modelo** mostrando las tablas y relaciones estrella.
2. Captura del panel de **Medidas DAX** en el editor de fórmulas.
3. Captura del **Dashboard interactivo completo** (Página 1 y Página 2).
4. Archivo del proyecto compilado: `bryan power BI.pbix` (ubicado directamente en esta carpeta `power_bi/`).

