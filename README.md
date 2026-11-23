# Sistema de Analítica y Minería de Datos: Hurto por Modalidades en Colombia (2010–2026)

**Asignatura:** Minería de Datos  
**Estudiante / Autor:** Bryan  
**Fuente Oficial de Datos:** Policía Nacional de Colombia — Dirección de Investigación Criminal e INTERPOL (DIJIN)  
**Volumen del Registro Histórico:** 656.635 hechos delictivos (1 de enero de 2010 al 31 de julio de 2026, periodo parcial)  
**Arquitectura del Sistema:** Pipeline ETL Streaming + Modelo Dimensional Cloud en PostgreSQL Neon + Aplicación Interactiva Streamlit (7 Módulos EDA) + Panel Ejecutivo Power BI Desktop  

---

## 📑 Tabla de Contenidos

1. [Descripción General del Proyecto](#1-descripción-general-del-proyecto)
2. [Arquitectura del Proyecto y Stack Tecnológico](#2-arquitectura-del-proyecto-y-stack-tecnológico)
3. [Estructura de Directorios y Archivos](#3-estructura-de-directorios-y-archivos)
4. [Requisitos Previos del Sistema](#4-requisitos-previos-del-sistema)
5. [Instalación Paso a Paso en Windows (PowerShell)](#5-instalación-paso-a-paso-en-windows-powershell)
6. [Configuración de PostgreSQL Neon en la Nube](#6-configuración-de-postgresql-neon-en-la-nube)
7. [Preparación, Transformación y Carga de Datos](#7-preparación-transformación-y-carga-de-datos)
8. [Ejecución de Pruebas y Auditorías de Integridad](#8-ejecución-de-pruebas-y-auditorías-de-integridad)
9. [Ejecución de la Aplicación Web Interactiva (Streamlit)](#9-ejecución-de-la-aplicación-web-interactiva-streamlit)
10. [Módulos del Análisis Exploratorio de Datos (EDA)](#10-módulos-del-análisis-exploratorio-de-datos-eda)
11. [Integración con Microsoft Power BI](#11-integración-con-microsoft-power-bi)
12. [Solución de Problemas Frecuentes (Troubleshooting)](#12-solución-de-problemas-frecuentes-troubleshooting)
13. [Seguridad, Confidencialidad y Protección de Credenciales](#13-seguridad-confidencialidad-y-protección-de-credenciales)
14. [Autoría, Contexto Institucional y Propósito Académico](#14-autoría-contexto-institucional-y-propósito-académico)

---

## 1. Descripción General del Proyecto

Este proyecto constituye una solución integral de **Minería de Datos e Ingeniería de Software** diseñada para la extracción, auditoría, modelamiento relacional dimensional, análisis exploratorio interactivo y formulación de políticas públicas basadas en evidencia sobre el fenómeno delictivo del hurto a vehículos en Colombia.

El sistema procesa el registro histórico unificado oficial de la **Policía Nacional de Colombia**, compuesto por **656.635 eventos** tipificados bajo el *Artículo 239 del Código Penal Colombiano (Hurto)* correspondientes a dos modalidades críticas: **Hurto de Motocicletas** (497.736 hechos, 75,80%) y **Hurto de Automotores** (158.899 hechos, 24,20%), ocurridos entre el **1 de enero de 2010 y el 31 de julio de 2026** (siendo el año 2026 un periodo parcial registrado de siete meses).

### Objetivos Esenciales del Desarrollo:
1. **Preservación Total de la Información (Cero Atrición):** Demostrar una ingeniería de datos metodológicamente rigurosa sin sesgo de selección, donde **no se elimina ninguna fila** del dataset crudo ($N = 656.635$ filas originales $\equiv 656.635$ filas procesadas), aplicando técnicas de imputación categórica explícita (`NO REPORTADO`) en variables administrativas incompletas.
2. **Modelamiento Dimensional en la Nube (Star Schema):** Implementar un esquema estrella relacional normalizado en la plataforma serverless **PostgreSQL Neon**, con claves primarias, claves sustitutas (*surrogate keys*), restricciones de integridad referencial (`FOREIGN KEY`) e índices B-Tree de alto rendimiento analítico.
3. **Analítica Exploratoria Interactiva (EDA):** Proveer una interfaz web desarrollada en **Streamlit** organizada en siete módulos temáticos para el filtrado multidimensional dinámico, análisis univariado, descomposición temporal longitudinal, concentración territorial bajo el Principio de Pareto, análisis asociativo mediante el coeficiente de Cramér's V y detección rigurosa de valores atípicos mediante el método de Rango Intercuartílico (IQR).
4. **Inteligencia de Negocios y Soporte a Decisiones:** Disponer de un panel gerencial en **Power BI Desktop** conectado al modelo dimensional, soportado por un catálogo validado de **11 medidas analíticas DAX**.

---

## 2. Arquitectura del Proyecto y Stack Tecnológico

El sistema fue concebido bajo una arquitectura desacoplada por capas: almacenamiento de datos en la nube, procesamiento de ingeniería de datos en Python, capa de analítica y aplicación web, y capa de visualización de inteligencia de negocios.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA DE FUENTE DE DATOS CRUDA                        │
│   Policía Nacional de Colombia (CSV Oficial: 656.635 registros, 84.8 MB)│
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│             CAPA DE INGENIERÍA DE DATOS Y PIPELINES (Python)           │
│  • src/process_dimensions.py -> Generación Star Schema en CSV           │
│  • src/load_to_neon.py       -> Carga streaming COPY hacia la nube     │
│  • src/etl.py                -> Limpieza auxiliar con 0 atrición        │
│  • src/db.py                 -> Conexión segura con psycopg v3         │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌───────────────────────────────────────┐ ┌──────────────────────────────┐
│ CAPA DE ALMACENAMIENTO RELACIONAL     │ │ CAPA DE APLICACIÓN WEB (EDA) │
│ Cloud PostgreSQL (Neon.tech)          │ │ Streamlit (app.py)           │
│  • Tabla Staging (stg_hurtos)         │ │  • 7 Módulos de Analítica    │
│  • 7 Tablas Dimensionales (Star)      │ │  • Filtrado dinámico en RAM  │
│  • 1 Tabla de Hechos (fact_hurtos)    │ │  • Visualizaciones Plotly    │
│  • 8 Índices B-Tree optimizados       │ │  • Pruebas SciPy (Cramér's V)│
└──────────────────┬────────────────────┘ └──────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│             CAPA DE BUSINESS INTELLIGENCE (Power BI Desktop)           │
│  • Archivo: power_bi/bryan power BI.pbix (28.8 MB)                     │
│  • Modelo Dimensional VertiPaq en estrella (1:*)                       │
│  • 11 Medidas Analíticas DAX oficiales                                 │
└────────────────────────────────────────────────────────────────────────┘
```

### Funciones Específicas de Cada Componente Tecnológico:

| Herramienta / Biblioteca | Versión Requerida | Función Real en el Proyecto |
| :--- | :--- | :--- |
| **Python** | `>=3.11` (probado en 3.13.5) | Lenguaje base para los scripts de ingeniería, scripts de auditoría, pipelines de carga streaming y servidor de la aplicación web. |
| **Streamlit** | `>=1.30.0` (instalado 1.67.0) | Framework web interactivo que orquesta los 7 módulos del EDA (`app.py`), permitiendo interactividad en tiempo real mediante widgets y caché en memoria (`@st.cache_data`). |
| **Pandas** | `>=2.0.0` (instalado 3.0.3) | Manipulación y transformación tabular masiva, imputación de nulos, agrupaciones espaciotemporales, tablas de contingencia y generación de archivos CSV procesados. |
| **NumPy** | `>=1.24.0` (instalado 2.5.0) | Operaciones vectorizadas de alto rendimiento, filtrado lógico mediante máscaras booleanas y cálculos numéricos. |
| **Plotly** | `>=5.18.0` (instalado 7.1.0) | Renderizado de visualizaciones interactivas en Streamlit (gráficos donut, gráficos de barras ordenados, histogramas de frecuencia, diagramas de caja y series de líneas temporales). |
| **SciPy** | `>=1.11.0` (instalado 1.18.1) | Cálculo estadístico del test de independencia de Chi-cuadrado (`scipy.stats.chi2_contingency`) para computar la matriz de correlación no paramétrica mediante el coeficiente **V de Cramér**. |
| **SQLAlchemy** | `>=2.0.0` (instalado 2.0.51) | Abstracción de conexión relacional y ejecución estructurada de consultas SQL para auditorías y canalizaciones auxiliares. |
| **psycopg (v3)** | `>=3.1.0` (instalado 3.3.9) | Conector nativo de alto rendimiento para PostgreSQL. Gestiona la transmisión masiva vía streaming con el protocolo binario `COPY ... FROM STDIN`. |
| **python-dotenv** | `>=1.0.0` (instalado 1.0.0) | Lectura transparente y segura de las credenciales de entorno almacenadas en el archivo `.env`, aislando los secretos de conexión. |
| **PostgreSQL Neon** | Cloud Serverless (v16/17) | Motor de base de datos relacional en la nube donde reside el modelo dimensional físico optimizado para consultas analíticas estructuradas. |
| **Microsoft Power BI**| Desktop (2024–2026) | Herramienta de visualización ejecutiva basada en el motor VertiPaq, con relaciones relacionales en estrella y 11 medidas DAX precompiladas. |

---

## 3. Estructura de Directorios y Archivos

A continuación se detalla la estructura física verificada del proyecto `Hurtos-bryan`:

```
Hurtos-bryan/
│
├── data/
│   ├── Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv  # Dataset primario original INTACTO (656.635 filas, 84.8 MB)
│   ├── processed/                                                   # Tablas dimensionales normalizadas en formato CSV
│   │   ├── dim_fecha.csv                                            # Dimensión temporal (fecha, año, mes, trimestre, etc.)
│   │   ├── dim_departamento.csv                                     # Dimensión geográfica departamental (33 registros)
│   │   ├── dim_municipio.csv                                        # Dimensión municipal vinculada a DANE y departamento
│   │   ├── dim_arma_medio.csv                                       # Catálogo de 12 armas y mecanismos delictivos
│   │   ├── dim_genero.csv                                           # Dimensión demográfica (Masculino, Femenino, NO REPORTADO)
│   │   ├── dim_grupo_etario.csv                                     # Ciclo vital (Adultos, Adolescentes, Menores, NO REPORTADO)
│   │   ├── dim_tipo_hurto.csv                                       # Modalidad legal (HURTO MOTOCICLETAS vs AUTOMOTORES)
│   │   ├── fact_hurtos.csv                                          # Tabla de hechos principal (656.635 filas con llaves foráneas)
│   │   └── processed_auxiliary.csv                                  # Salida auxiliar del pipeline etl.py (656.635 filas)
│   └── power_bi/
│       └── hurtos_powerbi_dataset.csv                               # Dataset desnormalizado optimizado para carga ágil
│
├── database/
│   ├── 01_create_schema.sql                                         # DDL del esquema estrella idempotente (CREATE IF NOT EXISTS e índices)
│   └── 03_queries_verificacion.sql                                  # Batería de 6 consultas SQL de auditoría e integridad en Neon
│
├── power_bi/
│   ├── bryan power BI.pbix                                          # Dashboard ejecutivo compilado en Power BI Desktop (28.8 MB)
│   ├── README_POWER_BI.md                                           # Manual técnico de relaciones del modelo, vistas y DAX
│   └── dax_measures.txt                                             # Catálogo formal de las 11 fórmulas DAX implementadas
│
├── src/
│   ├── __init__.py                                                  # Inicializador de módulo Python del paquete src
│   ├── db.py                                                        # Gestor central de conexión relacional a Neon (psycopg v3)
│   ├── load_to_neon.py                                              # Pipeline ETL streaming: crea esquema, carga staging y puebla estrella
│   ├── process_dimensions.py                                        # Extractor y constructor de los CSVs del Star Schema (0 eliminaciones)
│   ├── etl.py                                                       # Pipeline auxiliar de normalización y limpieza local
│   ├── test_neon_connection.py                                      # Script de verificación inmediata de conectividad a la nube Neon
│   ├── integrity_check.py                                           # Verificación de integridad hash SHA-256, delimitador y encoding
│   ├── diagnostic.py                                                # Diagnóstico exploratorio de tipos de datos, fechas y nulos
│   ├── diagnostic_exploratory.py                                    # Diagnóstico exhaustivo con verificación de consistencia
│   ├── audit_definitive_v6_6.py                                     # Auditoría estadística rigurosa de frecuencias y distribuciones
│   ├── audit_quality_v5.py                                          # Script de aseguramiento metódico de calidad de datos
│   ├── audit_quality_detail_v5.py                                   # Detalle de auditoría de variables categóricas
│   ├── plan_6_7_audit.py                                            # Script de auditoría de cruces multivariados
│   ├── generate_figures_article.py                                  # Exportador de figuras de alta resolución para documentación
│   ├── build_full_ieee_word.py                                      # Generador de informe científico en formato docx
│   ├── build_full_ieee_word_corrected.py                            # Versión revisada del compilador de artículo científico
│   └── create_schema.sql                                            # Copia sincronizada del DDL para ejecución desde src
│
├── .streamlit/
│   └── config.toml                                                  # Configuración del servidor Streamlit y estilos de interfaz
│
├── logs/
│   └── load_neon_log.txt                                            # Registro cronológico del pipeline de carga a Neon
│
├── app.py                                                           # Aplicación interactiva principal en Streamlit (7 Módulos EDA)
├── Iniciar_Streamlit.bat                                            # Lanzador rápido por doble clic para Windows
├── requirements.txt                                                 # Catálogo de dependencias oficiales del entorno Python
├── .env.example                                                     # Plantilla pública de variables de entorno (sin contraseñas)
├── .env                                                             # Archivo local de credenciales (IGNORADO POR GIT POR SEGURIDAD)
├── .gitignore                                                       # Reglas estrictas de exclusión para Git y control de versiones
└── README.md                                                        # Documentación maestra técnica y académica del proyecto
```

---

## 4. Requisitos Previos del Sistema

Para desplegar y ejecutar el proyecto desde cero en un entorno Windows se requiere contar con las siguientes herramientas instaladas:

1. **Python:**
   * Versión compatible: **Python 3.11, 3.12 o 3.13** (probado y validado en Python 3.13.5 de 64 bits).
   * Se debe asegurar que la opción *"Add python.exe to PATH"* se encuentre habilitada durante la instalación.
2. **Navegador Web:**
   * Google Chrome, Microsoft Edge, Mozilla Firefox u Opera en versiones recientes, para renderizar la aplicación web Streamlit en `http://localhost:8501`.
3. **Cuenta y Base de Datos en Neon (PostgreSQL Serverless):**
   * Cuenta activa gratuita o de pago en [https://console.neon.tech](https://console.neon.tech).
   * Se requiere disponer de la cadena de conexión URI con parámetro `sslmode=require`.
4. **Editor de Código (Recomendado):**
   * **Visual Studio Code** (con la extensión oficial de Python de Microsoft).
5. **Microsoft Power BI Desktop (Para el panel gerencial):**
   * Versión gratuita de escritorio para Windows, requerida para abrir y explorar el archivo `bryan power BI.pbix`.
6. **Git para Windows (Opcional pero recomendado):**
   * Necesario si se realiza la clonación desde un repositorio remoto.

---

## 5. Instalación Paso a Paso en Windows (PowerShell)

Siga rigurosamente esta secuencia de comandos ejecutados en **Windows PowerShell** para inicializar el proyecto en un entorno virtual aislado:

### Paso 1: Abrir la Carpeta del Proyecto en la Terminal
Abra una ventana de PowerShell y navegue hasta el directorio donde se ubica el proyecto:

```powershell
cd "c:\Users\pc\Desktop\TRABAJO DE BRYAN\Hurtos-bryan"
```

### Paso 2: Verificar la Instalación de Python
Compruebe que el intérprete de Python esté disponible en la consola y corresponda a una versión soportada:

```powershell
python --version
```
*Salida esperada:* `Python 3.11.x`, `Python 3.12.x` o `Python 3.13.x`.

### Paso 3: Configurar la Política de Ejecución de Scripts (PowerShell)
En Windows, PowerShell restringe por defecto la ejecución de scripts locales. Habilite la ejecución para el proceso actual sin comprometer la seguridad global del sistema operativo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

### Paso 4: Crear el Entorno Virtual Aislado
Cree un entorno virtual denominado `.venv` en la raíz del proyecto para evitar conflictos de bibliotecas con el sistema global:

```powershell
python -m venv .venv
```

### Paso 5: Activar el Entorno Virtual
Active el entorno virtual recién creado:

```powershell
.\.venv\Scripts\Activate.ps1
```
*Confirmación:* En el indicador de la terminal aparecerá el prefijo `(.venv)`.

*(Nota alternativa para símbolo del sistema CMD: `.\.venv\Scripts\activate.bat`)*.

### Paso 6: Actualizar el Administrador de Paquetes Pip
```powershell
python -m pip install --upgrade pip
```

### Paso 7: Instalar las Dependencias del Proyecto
Instale todos los paquetes especificados en el archivo [requirements.txt](file:///c:/Users/pc/Desktop/TRABAJO%20DE%20BRYAN/Hurtos-bryan/requirements.txt):

```powershell
pip install -r requirements.txt
```

### Paso 8: Comprobar la Instalación de las Bibliotecas
Valide que las dependencias críticas hayan quedado operativas mediante un comando de verificación en una sola línea:

```powershell
python -c "import pandas, numpy, scipy, sqlalchemy, psycopg, streamlit, plotly, dotenv; print('✅ Todas las dependencias se importaron correctamente.')"
```

---

## 6. Configuración de PostgreSQL Neon en la Nube

El proyecto utiliza **PostgreSQL Serverless** alojado en la plataforma en la nube **Neon** ([neon.tech](https://neon.tech)), lo cual permite consultas transaccionales remotas e integridad referencial estricta.

### Procedimiento de Configuración:

1. **Creación del Proyecto en Neon:**
   * Inicie sesión en [https://console.neon.tech](https://console.neon.tech).
   * Cree un nuevo proyecto (por ejemplo: `hurto-colombia-analytics`) seleccionando la región más cercana (ej. `us-east-2` o `us-east-1`) con PostgreSQL 16 o 17.
   * Se creará automáticamente una base de datos por defecto llamada `neondb`.

2. **Obtención de la Cadena de Conexión (Connection String):**
   * En el panel de Neon (Dashboard), localice la sección **Connection Details**.
   * Seleccione el modo **Connection string** y asegúrese de que incluya `psql` o el formato URI estándar:
     ```
     postgresql://<usuario>:<password>@<endpoint-id>.neon.tech/neondb?sslmode=require
     ```
   * Copie dicha cadena al portapapeles.

3. **Configuración del Archivo de Variables de Entorno (`.env`):**
   * En la raíz de `Hurtos-bryan/`, cree su archivo `.env` a partir de la plantilla:
     ```powershell
     Copy-Item .env.example .env
     ```
   * Abra el archivo `.env` con un editor de texto plano (Notepad o VS Code) y pegue su cadena real en la variable `NEON_CONN`:
     ```env
     # Configuración de Conexión a Base de Datos PostgreSQL Neon
     NEON_CONN=postgresql://neondb_owner:npg_MiClaveSecreta@ep-cool-fog-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
     
     # Conexión local alternativa de respaldo (opcional)
     LOCAL_PG_CONN=postgresql://postgres:postgres@localhost:5432/hurto_colombia
     ```
   * **Importante:** No comparta ni publique este archivo. El archivo `.gitignore` ya se encuentra configurado para protegerlo.

4. **Verificación de Conectividad con la Nube:**
   * Ejecute el script de prueba de conectividad provisto en `src/test_neon_connection.py`:
     ```powershell
     python src/test_neon_connection.py
     ```
   * *Salida esperada (con conexión a internet activa):*
     ```
     Intentando conectar a PostgreSQL Neon...
     ✅ Conexión a Neon PostgreSQL exitosa!
     Versión de PostgreSQL: PostgreSQL 16.x on x86_64-pc-linux-gnu ...
     Base de datos activa:   neondb
     ```

5. **Creación del Esquema Físico (DDL):**
   * El esquema relacional está diseñado de manera idempotente (`CREATE TABLE IF NOT EXISTS`) en el script [database/01_create_schema.sql](file:///c:/Users/pc/Desktop/TRABAJO%20DE%20BRYAN/Hurtos-bryan/database/01_create_schema.sql).
   * Puede ejecutarse automáticamente como parte del pipeline `load_to_neon.py` o directamente desde la consola SQL web de Neon copiando y pegando el contenido del archivo SQL.

---

## 7. Preparación, Transformación y Carga de Datos

### Ubicación y Nombre del Archivo CSV Original
El pipeline requiere que el dataset crudo provisto por la Policía Nacional se ubique con la siguiente ruta y denominación exacta:

```
Hurtos-bryan/data/Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv
```
* **Dimensiones:** 656.635 filas de datos y 1 fila de encabezado (9 columnas originales).
* **Tamaño:** ~84,77 MB.
* **Codificación:** UTF-8 sin BOM, delimitado por comas (`,`).

### Transformaciones y Reglas de Integridad (Cero Atrición)
Durante la ingesta y preparación no se aplica ningún filtro de eliminación (`dropna()`), garantizando el 100% de representatividad estadística:
1. **Normalización Textual:** Limpieza de espacios en blanco al inicio y final (`strip()`), y conversión a mayúsculas sostenidas en departamentos y municipios.
2. **Estandarización de Fechas:** Conversión de la columna `FECHA HECHO` (`DD/MM/YYYY`) a tipos de datos temporales `DATE`, derivando automáticamente la jerarquía dimensional: año, mes, nombre de mes en español, día, trimestre, semana del año y día de la semana.
3. **Imputación Categórica Controlada:**
   * **Variable Género:** 712 registros con valor nulo o en blanco son imputados explícitamente como `'NO REPORTADO'`, conservando los 656.635 hechos.
   * **Variable Grupo Etario:** 205 registros sin clasificación etaria son imputados explícitamente como `'NO REPORTADO'`.
   * En `app.py` se generan adicionalmente las banderas booleanas `GENERO_ES_IMPUTADO` y `GRUPO_ETARIO_ES_IMPUTADO` para permitir auditoría y trazabilidad científica.
4. **Validación Numérica:** La columna `CANTIDAD` se estandariza a números enteros positivos mediante coerción y restricción SQL `CHECK (cantidad > 0)`.
5. **Aserciones Estrictas:**
   ```python
   assert len(df) == 656635, "Error de atrición: el volumen no coincide con el original"
   ```

### Ejecución del Proceso de Carga Streaming a Neon
Para ejecutar el pipeline automatizado completo que crea las tablas, carga la tabla de *staging* mediante streaming binario y puebla el esquema estrella:

```powershell
python src/load_to_neon.py
```

*Fases del Script `src/load_to_neon.py`:*
1. **Ejecución DDL:** Aplica `database/01_create_schema.sql`.
2. **Streaming COPY Nativo:** Emplea el comando de alto rendimiento de PostgreSQL `COPY stg_hurtos FROM STDIN` utilizando buffers de lectura en memoria, transmitiendo los 656.635 registros en segundos.
3. **Poblado de Dimensiones:** Ejecuta sentencias `INSERT INTO dim_... SELECT DISTINCT ...` para poblar `dim_fecha`, `dim_departamento`, `dim_municipio`, `dim_arma_medio`, `dim_genero`, `dim_grupo_etario` y `dim_tipo_hurto`.
4. **Poblado de la Tabla de Hechos:** Inserta en `fact_hurtos` uniendo la tabla staging con cada una de las 7 dimensiones relacionales.
5. **Auditoría Transaccional:** Comprueba que `COUNT(*) == 656635` y verifica que no existan llaves foráneas huérfanas antes de confirmar la transacción (`commit`).

### Generación Local de Archivos CSV Procesados (Opcional)
Si se desea regenerar los archivos CSV de cada dimensión y la tabla de hechos en la carpeta local `data/processed/` para cargarlos directamente en Power BI:

```powershell
python src/process_dimensions.py
```

---

## 8. Ejecución de Pruebas y Auditorías de Integridad

El repositorio incorpora una serie de scripts de diagnóstico y auditoría para verificar la calidad, consistencia y reproducibilidad de los datos:

### 1. Prueba de Conectividad con PostgreSQL Neon
Valida que las credenciales del archivo `.env` sean correctas y que la base de datos responda:
```powershell
python src/test_neon_connection.py
```

### 2. Prueba de Integridad de la Fuente de Datos (Hash y Estructura)
Verifica el archivo CSV original calculando su hash criptográfico SHA-256, verificando el número exacto de filas, columnas, codificación y delimitador:
```powershell
python src/integrity_check.py
```
*Resultados verificados:*
* **SHA-256:** `2d09645b764f7a03d59d3f8c91f70049a8a80d9aa036456921b2d787fe9f1e79`
* **Codificación:** UTF-8
* **Delimitador:** Coma (`,`)
* **Registros de datos:** 656.635 filas (sin incluir el encabezado)
* **Columnas:** 9

### 3. Auditoría de Calidad y No Atrición del Pipeline ETL Auxiliar
Valida que el script de procesamiento auxiliar `src/etl.py` preserve el 100% de las filas tras imputar nulos:
```powershell
python src/etl.py
```
*Salida esperada:*
```
Ejecutando pipeline ETL auxiliar...
Registros originales cargados: 656,635
Registros tras limpieza (0 eliminados): 656,635
Resultado auxiliar guardado en: ...\data\processed\processed_auxiliary.csv
```

### 4. Auditoría Estadística de Frecuencias y Distribuciones
Para auditar las tablas de contingencia, cuartiles y consistencia de categorías:
```powershell
python src/audit_definitive_v6_6.py
```

### 5. Consultas de Verificación en PostgreSQL Neon (SQL)
Desde la consola SQL de Neon o mediante un cliente como DBeaver / pgAdmin, se puede ejecutar el script [database/03_queries_verificacion.sql](file:///c:/Users/pc/Desktop/TRABAJO%20DE%20BRYAN/Hurtos-bryan/database/03_queries_verificacion.sql), el cual valida:
* Conteo de staging (`stg_hurtos` = 656.635).
* Conteo de tabla de hechos (`fact_hurtos` = 656.635).
* Conteo de cada una de las 7 tablas de dimensiones.
* **Auditoría de integridad referencial:** Consulta con `LEFT JOIN` que retorna `0 registros huérfanos`.
* Verificación porcentual de imputación en género y grupo etario.

---

## 9. Ejecución de la Aplicación Web Interactiva (Streamlit)

La herramienta principal para la visualización exploratoria interactiva es la aplicación web desarrollada en **Streamlit** ([app.py](file:///c:/Users/pc/Desktop/TRABAJO%20DE%20BRYAN/Hurtos-bryan/app.py)).

### Comando de Inicio:
Asegúrese de tener el entorno virtual activado y ejecute en PowerShell:

```powershell
streamlit run app.py
```

### Método Alternativo por Doble Clic (Windows):
Haga doble clic sobre el archivo ejecutable por lotes [Iniciar_Streamlit.bat](file:///c:/Users/pc/Desktop/TRABAJO%20DE%20BRYAN/Hurtos-bryan/Iniciar_Streamlit.bat), el cual inicializa automáticamente la aplicación en la consola.

### Acceso y Navegación:
* Una vez iniciado el servidor local, se abrirá de forma automática su navegador web predeterminado en la URL:
  ```
  http://localhost:8501
  ```
* **Barra Lateral de Navegación (Sidebar):**
  * **Selector de Módulos:** Permite conmutar instantáneamente entre los 7 módulos temáticos del sistema.
  * **Filtro Temporal Dinámico:** Selector deslizante (*slider*) para acotar el rango de años entre **2010 y 2026** (indicando 2026 como periodo parcial registrado de 7 meses).
  * **Filtro de Modalidad de Hurto:** Casilla múltiple para alternar entre *Hurto Motocicletas* y *Hurto Automotores*.
  * **Filtro de Departamentos:** Menú desplegable múltiple para focalizar el análisis en entidades territoriales específicas.

---

## 10. Módulos del Análisis Exploratorio de Datos (EDA)

La aplicación `app.py` integra siete módulos analíticos especializados:

### Módulo 1: 📋 Visión General & KPIs
* **Tarjetas Métricas Ejecutivas:** Total de incidentes analizados, proporción de motocicletas vs. automotores, departamento con mayor volumen delictivo (Antioquia) y mecanismo de mayor incidencia (Llave Maestra).
* **Distribución Proporcional:** Gráfico de donut interactivo que visualiza la proporción nacional (75,80% motocicletas vs. 24,20% automotores).
* **Serie Temporal Comparativa Anual:** Gráfico longitudinal comparando la evolución año a año de ambas modalidades delictivas.

### Módulo 2: 🧹 Calidad de Datos & Limpieza Metodológica
* **Justificación de Cero Atrición:** Documentación técnica de cómo se conservan los 656.635 registros sin eliminar observaciones incompletas.
* **Auditoría de Valores Faltantes:** Identificación cuantitativa de los 712 registros con género nulo (0,108%) y 205 registros sin grupo etario (0,031%).
* **Estrategia de Imputación:** Visualización del proceso de asignación a la categoría controlada `'NO REPORTADO'` y exhibición de las columnas de trazabilidad (`GENERO_ES_IMPUTADO` y `GRUPO_ETARIO_ES_IMPUTADO`).

### Módulo 3: 📊 Análisis Univariado y Detección de Atípicos (IQR)
* **Histogramas de Distribución Temporal:** Frecuencias absolutas y relativas de ocurrencia por año.
* **Diagramas de Barras Univariados:** Desglose del Top 10 de mecanismos empleados, distribución por género y composición por grupo etario.
* **Diagramas de Caja (Boxplots) Agregados:** Distribución de conteos de incidentes a nivel departamental y municipal, evaluando la asimetría de la distribución territorial sin tratar identificadores como variables continuas.
* **Detección Estadística de Valores Atípicos:** Cálculo riguroso mediante el método del Rango Intercuartílico (IQR):
  $$\text{IQR} = Q_3 - Q_1$$
  $$\text{Límite Inferior} = Q_1 - 1.5 \times \text{IQR}$$
  $$\text{Límite Superior} = Q_3 + 1.5 \times \text{IQR}$$
  Visualización precisa de las entidades territoriales que superan el límite superior teórico (focos atípicos metropolitanos).

### Módulo 4: 📈 Serie Temporal & Estacionalidad
* **Evolución Longitudinal Mensual:** Serie de tiempo con 199 meses observados entre enero de 2010 y julio de 2026. Se etiqueta expresamente el año 2026 como periodo parcial hasta julio.
* **Patrón Estacional Mensual:** Agregación acumulada por mes calendario (enero a diciembre) para identificar meses de pico y valles de criminalidad.
* **Tasa de Variación Interanual (YoY %):** Cálculo del crecimiento o decrecimiento porcentual interanual del delito.

### Módulo 5: 🗺️ Concentración Territorial (Curva de Pareto)
* **Ranking Departamental:** Visualización del Top 15 de departamentos encabezado por Antioquia (144.040 hechos), Bogotá D.C. (113.399 hechos) y Valle del Cauca (104.537 hechos).
* **Ranking Municipal:** Top 15 de cabeceras municipales más impactadas (Bogotá, Medellín, Cali, Barranquilla, Soacha, etc.).
* **Evaluación del Principio de Pareto:** Confirmación matemática de la concentración del 80% nacional sobre el ordenamiento descendente de los 1.052 municipios.

### Módulo 6: 🔗 Correlaciones & Modus Operandi (Cramér's V)
* **Matriz de Asociación Categórica:** Implementación del coeficiente **V de Cramér** a partir de tablas de contingencia bivariadas y el estadístico Chi-cuadrado de Pearson calculado con SciPy.
* **Cruces Bivariados:** Tablas de contingencia cruzando Modalidad de Hurto vs. Arma/Medio, Género vs. Modalidad, y Departamento vs. Arma.

### Módulo 7: 💡 Hallazgos Analíticos y Recomendaciones de Política Pública
* **Tabla Exhaustiva de Armas y Medios:** Presentación de las **12 categorías oficiales** registradas en el CSV original al 100,00%, con cálculo dinámico de porcentajes tomando como denominador el total de cada modalidad (497.736 en motos y 158.899 en autos).
* **Verificación de Hiperconcentración Municipal:** Demostración empírica de que **exactamente 52 municipios** (4,94% de los 1.052 municipios del país) concentran el **80,08%** de los hurtos del país (municipio 51 alcanza 79,87% y municipio 52 supera el umbral con 80,08%). El Top 10 concentra el 57,41% y las 3 principales áreas metropolitanas (Bogotá, Medellín y Cali) acumulan por sí solas el 43,82% nacional.
* **Perfil Demográfico Riguroso:** Tabla de frecuencias con la justificación de los 205 registros sin edad (conservados como `No Reportado` para 0% atrición) y distribución por género.
* **Homogeneidad Semanal:** Comprobación estadística de una distribución uniforme entre los 7 días de la semana (oscilación entre 13,87% los domingos y 14,84% los viernes).
* **Propuestas Prospectivas de Política Pública:** Cuatro recomendaciones operativas orientadas a la toma de decisiones (focalización territorial en 52 nodos, control registral al mercado de autopartes, mitigación frente a llaves maestras y protocolos prioritarios para armas de fuego), delimitadas claramente como propuestas y no como resultados comprobados de efectividad.

---

## 11. Integración con Microsoft Power BI

El proyecto incluye un tablero ejecutivo preconstruido y validado ubicado en:
```
Hurtos-bryan/power_bi/bryan power BI.pbix
```
* **Tamaño del archivo:** ~28,85 MB.
* **Motor:** VertiPaq en memoria (Power BI Desktop).

### Opciones de Conexión a Datos en Power BI:
1. **Conexión Directa a la Nube Neon PostgreSQL:**
   * En Power BI Desktop: `Obtener datos` -> `Base de datos PostgreSQL`.
   * **Servidor:** El host de Neon (ejemplo: `ep-cool-fog-123456.us-east-2.aws.neon.tech`).
   * **Base de datos:** `neondb`.
   * **Modo de Conectividad:** `Importar`.
   * Se ingresan las credenciales de usuario y contraseña de Neon en la ventana de autenticación de base de datos.
2. **Carga desde CSVs Normalizados (Modo Recomendado Offline):**
   * Se cargan directamente los 8 archivos CSV generados en `data/processed/` (`fact_hurtos.csv` y las 7 tablas `dim_*.csv`).

### Modelo Dimensional en Estrella en Power BI:
En la vista **Modelo** de Power BI Desktop, se encuentran configuradas las relaciones `1 a Varios (1:*)` con dirección de filtro cruzado única desde cada dimensión hacia la tabla central `fact_hurtos`:
* `dim_fecha[dim_fecha_id]` (1) $\longrightarrow$ `fact_hurtos[dim_fecha_id]` (*)
* `dim_municipio[dim_muni_id]` (1) $\longrightarrow$ `fact_hurtos[dim_muni_id]` (*)
* `dim_departamento[dim_depto_id]` (1) $\longrightarrow$ `dim_municipio[dim_depto_id]` (*)
* `dim_arma_medio[dim_arma_id]` (1) $\longrightarrow$ `fact_hurtos[dim_arma_id]` (*)
* `dim_genero[dim_genero_id]` (1) $\longrightarrow$ `fact_hurtos[dim_genero_id]` (*)
* `dim_grupo_etario[dim_grupo_id]` (1) $\longrightarrow$ `fact_hurtos[dim_grupo_id]` (*)
* `dim_tipo_hurto[dim_tipo_id]` (1) $\longrightarrow$ `fact_hurtos[dim_tipo_id]` (*)

### Catálogo de Medidas DAX Oficiales (11 Medidas Reales):
El panel contiene **11 medidas analíticas DAX reales** documentadas en [power_bi/dax_measures.txt](file:///c:/Users/pc/Desktop/TRABAJO%20DE%20BRYAN/Hurtos-bryan/power_bi/dax_measures.txt):

1. **Total Hurtos:** `COUNTROWS(fact_hurtos)`
2. **Hurtos Motocicletas:** `CALCULATE([Total Hurtos], dim_tipo_hurto[descripcion] = "ARTÍCULO 239. HURTO MOTOCICLETAS")`
3. **Hurtos Automotores:** `CALCULATE([Total Hurtos], dim_tipo_hurto[descripcion] = "ARTÍCULO 239. HURTO AUTOMOTORES")`
4. **% Hurtos Motos:** `DIVIDE([Hurtos Motocicletas], [Total Hurtos], 0)`
5. **% Hurtos Autos:** `DIVIDE([Hurtos Automotores], [Total Hurtos], 0)`
6. **Hurtos Arma de Fuego:** `CALCULATE([Total Hurtos], dim_arma_medio[descripcion] = "ARMA DE FUEGO")`
7. **% Uso Arma de Fuego:** `DIVIDE([Hurtos Arma de Fuego], [Total Hurtos], 0)`
8. **Hurtos Llave Maestra:** `CALCULATE([Total Hurtos], dim_arma_medio[descripcion] = "LLAVE MAESTRA")`
9. **% Llave Maestra:** `DIVIDE([Hurtos Llave Maestra], [Total Hurtos], 0)`
10. **Hurtos Antioquia:** `CALCULATE([Total Hurtos], dim_departamento[nombre] = "ANTIOQUIA")`
11. **Ratio Motos vs Autos:** `DIVIDE([Hurtos Motocicletas], [Hurtos Automotores], 0)`

---

## 12. Solución de Problemas Frecuentes (Troubleshooting)

A continuación se listan incidentes técnicos documentados y sus soluciones comprobadas:

### A. Python no es reconocido como comando en Windows
* **Síntoma:** `'python' no se reconoce como un comando interno o externo, programa o archivo por lotes ejecutable.`
* **Causa:** La ruta de instalación de Python no fue agregada a la variable de entorno `PATH` del sistema.
* **Solución:** Reinstale Python asegurándose de marcar la casilla *"Add python.exe to PATH"*, o agregue manualmente la ruta (ej. `C:\Users\<Usuario>\AppData\Local\Programs\Python\Python313\`) a las variables de entorno de Windows.

### B. Error de directiva de ejecución al activar el entorno virtual en PowerShell
* **Síntoma:** `.\.venv\Scripts\Activate.ps1 : No se puede cargar el archivo... porque la ejecución de scripts está deshabilitada en este sistema.`
* **Causa:** Política de seguridad restrictiva predeterminada de Windows PowerShell (`Restricted`).
* **Solución:** Ejecute en la misma consola antes de activar:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
  .\.venv\Scripts\Activate.ps1
  ```

### C. Error `ValueError: No se encontró la variable NEON_CONN en el archivo .env`
* **Síntoma:** Al ejecutar scripts que interactúan con la base de datos se genera un error de variable no encontrada.
* **Causa:** No existe el archivo `.env` en la raíz de `Hurtos-bryan/` o la variable `NEON_CONN` está vacía.
* **Solución:** Copie `.env.example` a `.env` y agregue su cadena de conexión válida de Neon.

### D. Error de resolución DNS `[Errno 11001] getaddrinfo failed` al conectar a Neon
* **Síntoma:** Error de red al intentar conectarse al host de Neon.
* **Causa:** Pérdida de conectividad a internet en la máquina o ejecución en un entorno sandbox aislado sin salida a la red pública.
* **Solución:** Verifique la conexión a internet de su equipo. Neon es una base de datos en la nube y requiere salida HTTPS/TCP en el puerto 5432. Si se encuentra sin internet, puede utilizar la variable `LOCAL_PG_CONN` en `.env` apuntando a una base de datos local en PostgreSQL.

### E. Error `FileNotFoundError: No se encontró el archivo CSV original`
* **Síntoma:** Al ejecutar `app.py` o los scripts de ETL se detiene el programa indicando que el archivo no existe.
* **Causa:** El archivo CSV no se encuentra en `data/` o fue renombrado.
* **Solución:** Asegúrese de que el archivo conserve su nombre exacto:  
  `data/Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv`.

### F. Conflicto de puerto en Streamlit (`Port 8501 is already in use`)
* **Síntoma:** Streamlit advierte que el puerto 8501 está ocupado.
* **Causa:** Hay otra instancia de Streamlit corriendo en segundo plano.
* **Solución:** Inicie la aplicación asignando un puerto alternativo:
  ```powershell
  streamlit run app.py --server.port 8502
  ```

### G. Requerimiento del conector Npgsql en Power BI al conectar con PostgreSQL
* **Síntoma:** Power BI solicita la instalación de componentes adicionales para conectar a PostgreSQL.
* **Solución:** Descargue e instale el conector Npgsql oficial para Windows, o utilice la **Opción A** cargando directamente los CSVs dimensionales generados en `data/processed/`.

---

## 13. Seguridad, Confidencialidad y Protección de Credenciales

Este proyecto implementa buenas prácticas de seguridad informática y protección de datos:

1. **Aislamiento Estricto de Secretos:** Las contraseñas, tokens y cadenas de conexión de la base de datos Neon residen única y exclusivamente en el archivo local `.env`.
2. **Plantilla Pública Segura (`.env.example`):** En el repositorio se comparte únicamente una plantilla con valores ficticios y placeholders (`TU_PASSWORD_AQUI`), impidiendo la fuga involuntaria de credenciales.
3. **Exclusión en Control de Versiones (`.gitignore`):** El archivo [.gitignore](file:///c:/Users/pc/Desktop/TRABAJO%20DE%20BRYAN/Hurtos-bryan/.gitignore) contiene reglas específicas para bloquear la inclusión de variables sensibles:
   ```gitignore
   # Variables de entorno y credenciales (SEGURIDAD ESTRICTA)
   .env
   .env.*
   *.env
   !.env.example
   ```
4. **Protección de Datos Crudos:** Las carpetas temporales (`tmp/`) y archivos auxiliares intermedios se encuentran excluidos para evitar el almacenamiento redundante de datos transaccionales.

---

## 14. Autoría, Contexto Institucional y Propósito Académico

* **Proyecto:** Minería de Datos: Análisis Exploratorio y Modelamiento Dimensional de Hurtos por Modalidades en Colombia (2010–2026 parcial).
* **Autor / Estudiante:** Bryan.
* **Ámbito Académico:** Trabajo de investigación cuantitativa y entrega formal de software para la asignatura de **Minería de Datos**.
* **Fuente Primaria:** Registro administrativo oficial de criminalidad de la Policía Nacional de Colombia.
* **Licencia y Uso:** Proyecto desarrollado con propósitos estrictamente académicos y de investigación científica en analítica de datos aplicada a la seguridad ciudadana.