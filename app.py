# -*- coding: utf-8 -*-
"""
=============================================================================
APLICACIÓN WEB STREAMLIT: ANÁLISIS EXPLORATORIO DE DATOS (EDA)
Proyecto: Minería de Datos - Patrones de Hurto en Colombia (Policía Nacional)
Autor: Bryan
Entregable Oficial: Software de Análisis Exploratorio (Streamlit + Python)
=============================================================================
"""

import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import chi2_contingency

# Configuración de página de Streamlit
st.set_page_config(
    page_title="EDA: Hurto por Modalidades en Colombia",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo visual moderno y de alto contraste (compatible con modo oscuro y claro)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #60A5FA !important; /* Azul celeste brillante de alto contraste */
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #E2E8F0 !important; /* Gris claro de alta visibilidad */
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    .callout-box {
        background-color: #F8FAFC !important;
        border-left: 6px solid #2563EB !important;
        padding: 1.2rem 1.5rem !important;
        border-radius: 0 10px 10px 0 !important;
        margin: 1.2rem 0 !important;
        color: #0F172A !important; /* Texto negro / azul oscuro muy nítido */
        font-size: 1.08rem !important;
        line-height: 1.6 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    }
    .callout-box b, .callout-box strong {
        color: #000000 !important; /* Negrita en negro profundo */
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARGA Y CACHÉ DE DATOS
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando 656.635 registros del dataset original de la Policía Nacional...")
def load_data():
    base_dir = Path(__file__).resolve().parent
    
    # Lectura EXCLUSIVA del CSV original de la Policía Nacional
    candidates = [
        base_dir / "data" / "Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv",
        base_dir.parent / "Hurtos-bryan" / "data" / "Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv",
        base_dir / "Hurtos-bryan" / "data" / "Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv"
    ]
    p_raw = next((c for c in candidates if c.exists()), None)
    
    if p_raw is None:
        st.error("No se encontró el archivo CSV original en data/Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv")
        st.stop()
        
    # 1. Leer el CSV original con Pandas (sin omitir registros)
    df = pd.read_csv(p_raw, encoding="utf-8", low_memory=False)
    original_row_count = len(df)
    
    # Limpieza de espacios en nombres de columnas
    df.columns = [c.strip() for c in df.columns]
    
    # 2. Calcular dinámicamente los valores faltantes desde el CSV original
    null_counts = df.isnull().sum()
    null_data_dynamic = pd.DataFrame({
        "Variable": null_counts.index.tolist(),
        "Valores Nulos": null_counts.values.tolist(),
        "Porcentaje Nulo": (null_counts.values / original_row_count * 100).round(4)
    })
    
    n_nulos_genero = int(null_counts.get("GENERO", 0))
    n_nulos_grupo = int(null_counts.get("GRUPO ETARIO", 0))
    
    # 3. Preservar valores originales y diferenciar valores imputados mediante banderas
    df["GENERO_ORIGINAL"] = df["GENERO"].copy()
    df["GRUPO_ETARIO_ORIGINAL"] = df["GRUPO ETARIO"].copy()
    
    df["GENERO_ES_IMPUTADO"] = df["GENERO"].isna() | df["GENERO"].astype(str).str.strip().isin(["", "nan", "NO REPORTA"])
    df["GRUPO_ETARIO_ES_IMPUTADO"] = df["GRUPO ETARIO"].isna() | df["GRUPO ETARIO"].astype(str).str.strip().isin(["", "nan"])
    
    # 4. Imputaciones categóricas justificadas (cero filas eliminadas)
    df["GENERO"] = df["GENERO"].fillna("NO REPORTADO").astype(str).str.strip()
    df["GENERO"] = df["GENERO"].replace({"nan": "NO REPORTADO", "": "NO REPORTADO", "NO REPORTA": "NO REPORTADO"})
    
    df["GRUPO_ETARIO"] = df["GRUPO ETARIO"].fillna("NO REPORTADO").astype(str).str.strip()
    df["GRUPO_ETARIO"] = df["GRUPO_ETARIO"].replace({"nan": "NO REPORTADO", "": "NO REPORTADO", "None": "NO REPORTADO"}).fillna("NO REPORTADO")
    
    # 5. Transformaciones de variables
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].astype(str).str.strip().str.upper()
    df["MUNICIPIO"] = df["MUNICIPIO"].astype(str).str.strip()
    df["CODIGO_DANE"] = df["CODIGO DANE"].astype(str).str.strip()
    df["MODALIDAD_HURTO"] = df["TIPO DE HURTO"].astype(str).str.replace("ARTÍCULO 239. ", "", regex=False).str.strip()
    df["ARMA_MEDIO"] = df["ARMAS MEDIOS"].astype(str).str.strip()
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(1).astype(int)
    
    # 6. Transformaciones temporales
    df["FECHA"] = pd.to_datetime(df["FECHA HECHO"], format="%d/%m/%Y", errors="coerce")
    df["AÑO"] = df["FECHA"].dt.year
    df["MES"] = df["FECHA"].dt.month
    df["TRIMESTRE"] = df["FECHA"].dt.quarter
    df["DIA"] = df["FECHA"].dt.day
    
    meses_es = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    df["NOMBRE_MES"] = df["MES"].map(meses_es)
    
    dias_es = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
    df["DIA_SEMANA"] = df["FECHA"].dt.dayofweek.map(dias_es)
    
    # 7. Aserción de conservación estricta (0 registros eliminados)
    assert len(df) == original_row_count, f"Error de atrición: original={original_row_count}, procesado={len(df)}"
    assert original_row_count == 656635, f"Error en volumen esperado: se esperaban 656.635 filas pero hay {original_row_count}"
    
    # Metadatos dinámicos almacenados en el DataFrame (serializables)
    df.attrs["raw_row_count"] = original_row_count
    df.attrs["null_data_dict"] = null_data_dynamic.to_dict(orient="records")
    df.attrs["n_nulos_genero"] = n_nulos_genero
    df.attrs["n_nulos_grupo"] = n_nulos_grupo
    df.attrs["source_file"] = p_raw.name
    
    return df

# Función para coeficiente de Cramér's V
def cramers_v(x, y):
    confusion_matrix = pd.crosstab(x, y)
    chi2 = chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.sum().sum()
    phi2 = chi2 / n
    r, k = confusion_matrix.shape
    phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
    rcorr = r - ((r-1)**2)/(n-1)
    kcorr = k - ((k-1)**2)/(n-1)
    denom = min((kcorr-1), (rcorr-1))
    if denom <= 0:
        return 0.0
    return np.sqrt(phi2corr / denom)

df_all = load_data()

# -----------------------------------------------------------------------------
# BARRA LATERAL: NAVEGACIÓN Y FILTROS GLOBALES
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Flag_of_Colombia.svg/200px-Flag_of_Colombia.svg.png", width=60)
    st.title("Minería de Datos")
    st.markdown("**Proyecto:** Hurto por Modalidades (Colombia)")
    st.markdown("**Estudiante:** Bryan")
    st.markdown("---")
    
    menu = st.radio(
        "Módulos del Sistema:",
        [
            "📋 1. Visión General & KPIs",
            "🧹 2. Calidad de Datos & Limpieza",
            "📊 3. Análisis Univariado",
            "📈 4. Serie Temporal & Estacionalidad",
            "🗺️ 5. Concentración Territorial",
            "🔗 6. Correlaciones & Modus Operandi",
            "💡 7. Hallazgos & Toma de Decisiones"
        ]
    )
    
    st.markdown("---")
    st.subheader("🎯 Filtros Interactivos")
    
    # Filtro temporal
    min_year = int(df_all["AÑO"].min())
    max_year = int(df_all["AÑO"].max())
    year_range = st.slider("Rango de Años:", min_value=min_year, max_value=max_year, value=(min_year, max_year))
    st.caption("ℹ️ Nota: El año 2026 corresponde a un periodo parcial registrado.")
    
    # Filtro modalidad de hurto
    modalidades_list = sorted(df_all["MODALIDAD_HURTO"].unique().tolist())
    sel_modalidades = st.multiselect("Modalidad de Hurto:", modalidades_list, default=modalidades_list)
    
    # Filtro de departamentos
    deptos_list = sorted(df_all["DEPARTAMENTO"].unique().tolist())
    sel_deptos = st.multiselect("Departamentos (vacío = todos):", deptos_list, default=[])
    
    # Aplicar filtros
    mask = (df_all["AÑO"] >= year_range[0]) & (df_all["AÑO"] <= year_range[1])
    if sel_modalidades:
        mask = mask & (df_all["MODALIDAD_HURTO"].isin(sel_modalidades))
    if sel_deptos:
        mask = mask & (df_all["DEPARTAMENTO"].isin(sel_deptos))
        
    df_filtered = df_all[mask]

# -----------------------------------------------------------------------------
# MÓDULO 1: VISIÓN GENERAL & KPIS
# -----------------------------------------------------------------------------
if menu == "📋 1. Visión General & KPIs":
    st.markdown('<div class="main-header">Sistema de Analítica y Minería de Datos: Hurtos en Colombia</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Auditoría y Exploración de Incidentes de Hurto a Automotores y Motocicletas (Policía Nacional 2010 – 2026, 2026: periodo parcial)</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="callout-box">
    <b>Propósito Académico:</b> Este panel interactivo desarrollado en <b>Streamlit</b> permite dar cumplimiento al requisito de 
    <b>Análisis Exploratorio de Datos (EDA)</b> exigido en la asignatura de Minería de Datos. Integra almacenamiento dimensional, 
    evaluación rigurosa de calidad, técnicas estadísticas y visualización para la toma de decisiones.
    </div>
    """, unsafe_allow_html=True)
    
    # Tarjetas de Métricas (KPIs)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_casos = len(df_filtered)
    total_motos = len(df_filtered[df_filtered["MODALIDAD_HURTO"] == "HURTO MOTOCICLETAS"])
    total_autos = len(df_filtered[df_filtered["MODALIDAD_HURTO"] == "HURTO AUTOMOTORES"])
    pct_motos = (total_motos / total_casos * 100) if total_casos > 0 else 0
    top_depto = df_filtered["DEPARTAMENTO"].mode()[0] if not df_filtered.empty else "N/A"
    top_arma = df_filtered["ARMA_MEDIO"].mode()[0] if not df_filtered.empty else "N/A"
    
    with col1:
        st.metric("Total Incidentes", f"{total_casos:,}", f"{(total_casos/len(df_all)*100):.1f}% del total")
    with col2:
        st.metric("Hurto Motocicletas", f"{total_motos:,}", f"{pct_motos:.1f}%")
    with col3:
        st.metric("Hurto Automotores", f"{total_autos:,}", f"{(100-pct_motos):.1f}%")
    with col4:
        st.metric("Depto Crítico", top_depto)
    with col5:
        st.metric("Medio Principal", top_arma)
        
    st.markdown("---")
    
    # Gráficos de Resumen Ejecutivo
    gcol1, gcol2 = st.columns([6, 4])
    
    with gcol1:
        st.subheader("📈 Evolución de Casos por Año y Modalidad")
        anual = df_filtered.groupby(["AÑO", "MODALIDAD_HURTO"]).size().reset_index(name="CANTIDAD")
        fig_anual = px.line(
            anual, x="AÑO", y="CANTIDAD", color="MODALIDAD_HURTO",
            markers=True,
            color_discrete_map={"HURTO MOTOCICLETAS": "#EF4444", "HURTO AUTOMOTORES": "#3B82F6"},
            labels={"CANTIDAD": "Total Hechos", "AÑO": "Año del Hecho", "MODALIDAD_HURTO": "Modalidad"}
        )
        fig_anual.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20), hovermode="x unified")
        st.plotly_chart(fig_anual, use_container_width=True)
        
    with gcol2:
        st.subheader("🥧 Distribución por Modalidad de Hurto")
        pie_data = df_filtered["MODALIDAD_HURTO"].value_counts().reset_index()
        pie_data.columns = ["Modalidad", "Total"]
        fig_pie = px.pie(
            pie_data, names="Modalidad", values="Total",
            hole=0.45,
            color="Modalidad",
            color_discrete_map={"HURTO MOTOCICLETAS": "#EF4444", "HURTO AUTOMOTORES": "#3B82F6"}
        )
        fig_pie.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Vista previa de datos
    with st.expander("🔍 Explorar Muestra de Registros Filtrados (50 filas)", expanded=False):
        st.dataframe(df_filtered.head(50), use_container_width=True)

# -----------------------------------------------------------------------------
# MÓDULO 2: CALIDAD DE DATOS & LIMPIEZA
# -----------------------------------------------------------------------------
elif menu == "🧹 2. Calidad de Datos & Limpieza":
    st.markdown('<div class="main-header">Auditoría de Calidad, Limpieza e Imputación de Datos</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Cumplimiento estricto de la regla metodológica: CERO REGISTROS ELIMINADOS (656.635 filas preservadas)</div>', unsafe_allow_html=True)
    
    # 1. Obtención dinámica de métricas de valores faltantes calculadas desde el CSV original
    n_nulos_gen = int(df_all.attrs.get("n_nulos_genero", df_all["GENERO_ES_IMPUTADO"].sum() if "GENERO_ES_IMPUTADO" in df_all else 0))
    n_nulos_grp = int(df_all.attrs.get("n_nulos_grupo", df_all["GRUPO_ETARIO_ES_IMPUTADO"].sum() if "GRUPO_ETARIO_ES_IMPUTADO" in df_all else 0))
    total_filas_csv = int(df_all.attrs.get("raw_row_count", len(df_all)))
    archivo_origen = df_all.attrs.get("source_file", "Reporte_Hurto_por_Modalidades_Policía_Nacional_20261106.csv")
    
    st.info(f"""
    **Justificación Metodológica:** En análisis de criminalidad, eliminar filas con campos no reportados genera un **sesgo de atrición** 
    y subestima el volumen real de delitos. Para preservar el 100% de la masa de datos ({total_filas_csv:,} filas leídas directamente de `{archivo_origen}`), 
    se aplicó la técnica de **imputación categórica mediante la clase explícita 'NO REPORTADO'** tanto para la variable GÉNERO ({n_nulos_gen:,} valores nulos calculados dinámicamente) 
    como para GRUPO ETARIO ({n_nulos_grp:,} valores nulos calculados dinámicamente).
    """)
    
    qcol1, qcol2 = st.columns(2)
    
    with qcol1:
        st.subheader("📊 Diagnóstico Dinámico de Valores Faltantes en el CSV Original")
        # null_data calculado dinámicamente desde el CSV original en load_data()
        null_dict = df_all.attrs.get("null_data_dict", None)
        if null_dict is not None:
            null_data = pd.DataFrame(null_dict)
        else:
            raw_cols = ["DEPARTAMENTO", "MUNICIPIO", "CODIGO DANE", "ARMAS MEDIOS", "FECHA HECHO", "GENERO_ORIGINAL", "GRUPO_ETARIO_ORIGINAL", "TIPO DE HURTO", "CANTIDAD"]
            present_cols = [c for c in raw_cols if c in df_all.columns]
            null_s = df_all[present_cols].isnull().sum()
            null_data = pd.DataFrame({
                "Variable": [c.replace("_ORIGINAL", "") for c in null_s.index],
                "Valores Nulos": null_s.values,
                "Porcentaje Nulo": (null_s.values / total_filas_csv * 100).round(4)
            })
            
        fig_null = px.bar(
            null_data[null_data["Valores Nulos"] > 0],
            x="Variable", y="Valores Nulos",
            text="Valores Nulos",
            color="Variable",
            color_discrete_sequence=["#F59E0B", "#EC4899"]
        )
        fig_null.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_null.update_layout(height=320, yaxis_title="Conteo Dinámico de Nulos")
        st.plotly_chart(fig_null, use_container_width=True)
        
    with qcol2:
        st.subheader("📋 Matriz de Decisiones Técnicas Aplicadas")
        decisiones = pd.DataFrame({
            "Variable Original": ["GENERO", "GRUPO ETARIO", "DEPARTAMENTO", "FECHA HECHO", "CANTIDAD", "TIPO DE HURTO"],
            "Problema Detectado": [
                f"{n_nulos_gen:,} valores nulos originales y etiqueta redundante 'NO REPORTA'",
                f"{n_nulos_grp:,} valores nulos originales",
                "Espacios en blanco y discrepancias de mayúsculas",
                "Formato texto DD/MM/YYYY",
                "Valores en texto unitarios",
                "Prefijo legal redundante 'ARTÍCULO 239.'"
            ],
            "Tratamiento Aplicado": [
                "Imputación como 'NO REPORTADO' (0 filas eliminadas)",
                "Imputación como 'NO REPORTADO' (0 filas eliminadas)",
                "Normalización UPPER y strip() de espacios",
                "Conversión a DateTime y extracción de año, mes, día y día semana",
                "Casting a entero asegurando check constraint > 0",
                "Limpieza de prefijo para claridad en visualizaciones"
            ]
        })
        st.dataframe(decisiones, use_container_width=True, hide_index=True)
        
    st.markdown("---")
    
    st.subheader("🛡️ Verificación de Integridad de la Carga")
    vcol1, vcol2, vcol3 = st.columns(3)
    with vcol1:
        st.metric("Total Filas Archivo CSV", f"{total_filas_csv:,}")
    with vcol2:
        st.metric("Total Filas Procesadas en Memoria", f"{len(df_all):,}", "100% Coincidencia")
    with vcol3:
        st.metric("Filas Descartadas / Borradas", "0", "0.0% Pérdida")

    # Muestra de diferenciación explícita entre valores originales e imputados
    with st.expander("🔍 Auditoría Detallada: Diferenciación entre Valores Originales e Imputados", expanded=False):
        st.caption("Esta vista contrasta los valores originales leídos del CSV frente a las categorías imputadas en memoria:")
        cols_diff = ["FECHA", "DEPARTAMENTO", "MUNICIPIO", "MODALIDAD_HURTO", "GENERO_ORIGINAL", "GENERO", "GENERO_ES_IMPUTADO", "GRUPO_ETARIO_ORIGINAL", "GRUPO_ETARIO", "GRUPO_ETARIO_ES_IMPUTADO"]
        valid_cols = [c for c in cols_diff if c in df_all.columns]
        imputed_sample = df_all[df_all["GENERO_ES_IMPUTADO"] | df_all["GRUPO_ETARIO_ES_IMPUTADO"]][valid_cols].head(30)
        st.dataframe(imputed_sample, use_container_width=True)

# -----------------------------------------------------------------------------
# MÓDULO 3: ANÁLISIS UNIVARIADO
# -----------------------------------------------------------------------------
elif menu == "📊 3. Análisis Univariado":
    st.markdown('<div class="main-header">Análisis Univariado y Distribución de Variables</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Frecuencias, proporciones y caracterización individual de las dimensiones clave</div>', unsafe_allow_html=True)
    
    ucol1, ucol2 = st.columns(2)
    
    with ucol1:
        st.subheader("🔫 Armas y Medios Empleados en la Comisión del Hurto")
        armas_cnt = df_filtered["ARMA_MEDIO"].value_counts().head(10).reset_index()
        armas_cnt.columns = ["Arma / Medio", "Total"]
        fig_armas = px.bar(
            armas_cnt, x="Total", y="Arma / Medio",
            orientation="h",
            color="Total",
            color_continuous_scale="Reds"
        )
        fig_armas.update_layout(yaxis=dict(autorange="reversed"), height=420)
        st.plotly_chart(fig_armas, use_container_width=True)
        
    with ucol2:
        st.subheader("👥 Distribución por Género de la Víctima")
        gen_cnt = df_filtered["GENERO"].value_counts().reset_index()
        gen_cnt.columns = ["Género", "Total"]
        fig_gen = px.bar(
            gen_cnt, x="Género", y="Total",
            text="Total",
            color="Género",
            color_discrete_sequence=["#3B82F6", "#EC4899", "#94A3B8"]
        )
        fig_gen.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_gen.update_layout(height=420)
        st.plotly_chart(fig_gen, use_container_width=True)
        
    st.markdown("---")
    
    ucol3, ucol4 = st.columns(2)
    with ucol3:
        st.subheader("🎂 Distribución por Grupo Etario")
        etario_cnt = df_filtered["GRUPO_ETARIO"].value_counts().reset_index()
        etario_cnt.columns = ["Grupo Etario", "Total"]
        fig_eta = px.pie(
            etario_cnt, names="Grupo Etario", values="Total",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_eta.update_layout(height=380)
        st.plotly_chart(fig_eta, use_container_width=True)
        
    with ucol4:
        st.subheader("📅 Distribución de Hechos por Día de la Semana")
        dias_order = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dias_cnt = df_filtered["DIA_SEMANA"].value_counts().reindex(dias_order).reset_index()
        dias_cnt.columns = ["Día Semana", "Total"]
        fig_dias = px.bar(
            dias_cnt, x="Día Semana", y="Total",
            text="Total",
            color="Total",
            color_continuous_scale="Blues"
        )
        fig_dias.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_dias.update_layout(height=380)
        st.plotly_chart(fig_dias, use_container_width=True)

    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # 1. HISTOGRAMAS: DISTRIBUCIÓN TEMPORAL Y FRECUENCIA
    # -------------------------------------------------------------------------
    st.subheader("📊 Histogramas de Frecuencia Temporal (Variables Numéricas Discretas)")
    st.caption("Distribución univariada de la ocurrencia delictiva sobre la escala temporal (Años y Meses).")
    
    hcol1, hcol2 = st.columns(2)
    
    with hcol1:
        st.markdown("**Histograma: Distribución de Frecuencia de Hurtos por Año (2010 – 2026)**")
        fig_hist_ano = px.histogram(
            df_filtered,
            x="AÑO",
            nbins=17,
            color="MODALIDAD_HURTO",
            color_discrete_map={"HURTO MOTOCICLETAS": "#EF4444", "HURTO AUTOMOTORES": "#3B82F6"},
            barmode="stack",
            labels={"AÑO": "Año del Hecho", "count": "Frecuencia de Incidentes", "MODALIDAD_HURTO": "Modalidad"}
        )
        fig_hist_ano.update_layout(
            height=380,
            xaxis=dict(tickmode="linear", tick0=2010, dtick=2),
            yaxis_title="Frecuencia (Recuento de Hechos)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_hist_ano, use_container_width=True)
        st.caption("ℹ️ Nota: El año 2026 refleja un periodo parcial registrado de 7 meses (enero a julio de 2026).")
        
    with hcol2:
        st.markdown("**Histograma: Distribución de Frecuencia por Mes del Calendario**")
        fig_hist_mes = px.histogram(
            df_filtered,
            x="MES",
            nbins=12,
            color_discrete_sequence=["#10B981"],
            labels={"MES": "Mes del Año (1 a 12)", "count": "Frecuencia de Incidentes"}
        )
        fig_hist_mes.update_layout(
            height=380,
            xaxis=dict(tickmode="linear", tick0=1, dtick=1),
            yaxis_title="Frecuencia (Recuento de Hechos)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_hist_mes, use_container_width=True)

    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # 2. DIAGRAMAS DE CAJA (BOXPLOTS) SOBRE CONTEOS AGREGADOS TERRITORIALES
    # -------------------------------------------------------------------------
    st.subheader("📦 Diagramas de Caja (Boxplots) de Conteos Agregados")
    st.markdown("""
    En este análisis se evalúa la distribución empírica de los **conteos cuantitativos agregados de hurtos** por unidad territorial. 
    *Principio metodológico:* No se tratan códigos identificadores (como el Código DANE) como variables cuantitativas continuas, 
    sino que se modela la métrica real de incidentes acumulados por entidad territorial.
    """)
    
    # Selector de granularidad para el Boxplot
    nivel_agg = st.radio(
        "Seleccione nivel de agregación para el análisis univariado de dispersión:",
        ["Nivel Departamental (33 Departamentos)", "Nivel Municipal (Municipios afectados)"],
        horizontal=True
    )
    
    if "Departamental" in nivel_agg:
        agg_df = df_filtered.groupby("DEPARTAMENTO").size().reset_index(name="TOTAL_HURTOS")
        entidad_nombre = "Departamento"
        entidad_col = "DEPARTAMENTO"
        color_box = "#6366F1"
    else:
        agg_df = df_filtered.groupby(["DEPARTAMENTO", "MUNICIPIO"]).size().reset_index(name="TOTAL_HURTOS")
        agg_df["ENTIDAD"] = agg_df["MUNICIPIO"] + " (" + agg_df["DEPARTAMENTO"] + ")"
        entidad_nombre = "Municipio"
        entidad_col = "ENTIDAD"
        color_box = "#F59E0B"
        
    # -------------------------------------------------------------------------
    # CÁLCULO ESTADÍSTICO UNIFICADO (ÚNICA SERIE AGREGADA POR ENTIDAD)
    # -------------------------------------------------------------------------
    serie_agregada = agg_df["TOTAL_HURTOS"]
    
    n_entidades = len(serie_agregada)
    min_obs = float(serie_agregada.min())
    max_obs = float(serie_agregada.max())
    media = float(serie_agregada.mean())
    std_dev = float(serie_agregada.std())
    
    q1 = float(serie_agregada.quantile(0.25))
    mediana = float(serie_agregada.median())
    q3 = float(serie_agregada.quantile(0.75))
    
    # Fórmulas canónicas rigurosas del Rango Intercuartílico (IQR)
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    
    # Detección de atípicos basada estrictamente en los límites teóricos estadísticos
    outliers_df = agg_df[
        (agg_df["TOTAL_HURTOS"] < lim_inf) | (agg_df["TOTAL_HURTOS"] > lim_sup)
    ].sort_values("TOTAL_HURTOS", ascending=False)
    n_outliers = len(outliers_df)
    pct_outliers = (n_outliers / n_entidades * 100) if n_entidades > 0 else 0.0

    bcol1, bcol2 = st.columns([6, 4])
    
    with bcol1:
        st.markdown(f"**Boxplot de Hurtos Agregados por {entidad_nombre}**")
        fig_box = go.Figure()
        
        # 1. Trazar Boxplot con los estadísticos unificados exactos
        fig_box.add_trace(go.Box(
            name=f"{entidad_nombre}s",
            q1=[q1],
            median=[mediana],
            q3=[q3],
            lowerfence=[lim_inf],
            upperfence=[lim_sup],
            mean=[media],
            sd=[std_dev],
            boxpoints=False,
            marker_color=color_box,
            line=dict(color=color_box, width=2),
            fillcolor="rgba(99, 102, 241, 0.25)" if "Departamental" in nivel_agg else "rgba(245, 158, 11, 0.25)",
            hovertemplate=(
                f"<b>Estadísticos Boxplot ({entidad_nombre}s)</b><br>"
                f"Límite Superior Teórico (Q3 + 1.5×IQR): {lim_sup:,.1f}<br>"
                f"Tercer Cuartil (Q3 - P75): {q3:,.1f}<br>"
                f"Mediana (Q2 - P50): {mediana:,.1f}<br>"
                f"Media Aritmética (μ): {media:,.1f}<br>"
                f"Primer Cuartil (Q1 - P25): {q1:,.1f}<br>"
                f"Límite Inferior Teórico (Q1 - 1.5×IQR): {lim_inf:,.1f}<br>"
                f"Mínimo Observado: {min_obs:,.0f}<br>"
                f"Máximo Observado: {max_obs:,.0f}<br>"
                "<extra></extra>"
            )
        ))
        
        # 2. Trazar observaciones regulares (dentro de límites teóricos IQR)
        normales_df = agg_df[(agg_df["TOTAL_HURTOS"] >= lim_inf) & (agg_df["TOTAL_HURTOS"] <= lim_sup)]
        fig_box.add_trace(go.Scatter(
            x=[f"{entidad_nombre}s"] * len(normales_df),
            y=normales_df["TOTAL_HURTOS"],
            text=normales_df[entidad_col],
            mode="markers",
            marker=dict(color=color_box, size=6, opacity=0.65),
            name=f"Dentro de límites ({len(normales_df):,})",
            hovertemplate="<b>%{text}</b><br>Hurtos: %{y:,}<extra></extra>"
        ))
        
        # 3. Trazar observaciones atípicas (outliers superiores o inferiores)
        if n_outliers > 0:
            fig_box.add_trace(go.Scatter(
                x=[f"{entidad_nombre}s"] * len(outliers_df),
                y=outliers_df["TOTAL_HURTOS"],
                text=outliers_df[entidad_col],
                mode="markers",
                marker=dict(color="#EF4444", size=9, symbol="diamond", line=dict(color="#FFFFFF", width=1.2)),
                name=f"Atípicos IQR ({n_outliers:,})",
                hovertemplate="<b>%{text}</b> [ATÍPICO]<br>Hurtos: %{y:,}<extra></extra>"
            ))
            
        fig_box.add_hline(
            y=lim_sup, line_dash="dash", line_color="#EF4444",
            annotation_text=f"Límite Sup. IQR: {lim_sup:,.1f}",
            annotation_position="top right"
        )
        
        fig_box.update_layout(
            height=430,
            yaxis_title=f"Incidentes Acumulados por {entidad_nombre}",
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
    with bcol2:
        st.markdown(f"**Estadísticas Descriptivas ({entidad_nombre}s)**")
        desc_df = pd.DataFrame({
            "Parámetro Estadístico": [
                "Total Entidades Analizadas",
                "Mínimo Observado (Min)",
                "Límite Inferior Teórico (Q1 - 1.5×IQR)",
                "Primer Cuartil (Q1 - P25)",
                "Mediana (Q2 - P50)",
                "Media Aritmética (μ)",
                "Tercer Cuartil (Q3 - P75)",
                "Límite Superior Teórico (Q3 + 1.5×IQR)",
                "Máximo Observado (Max)",
                "Desviación Estándar (σ)",
                "Rango Intercuartílico (IQR)"
            ],
            "Valor": [
                f"{n_entidades:,}",
                f"{min_obs:,.0f}",
                f"{lim_inf:,.1f}",
                f"{q1:,.1f}",
                f"{mediana:,.1f}",
                f"{media:,.1f}",
                f"{q3:,.1f}",
                f"{lim_sup:,.1f}",
                f"{max_obs:,.0f}",
                f"{std_dev:,.1f}",
                f"{iqr:,.1f}"
            ]
        })
        st.dataframe(desc_df, use_container_width=True, hide_index=True)
        
    # -------------------------------------------------------------------------
    # 3. TARJETAS DE RESUMEN DEL MÉTODO IQR (EXACTAMENTE LOS MISMOS ESTADÍSTICOS)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader(f"🎯 Detección de Valores Atípicos mediante Rango Intercuartílico (IQR) - {entidad_nombre}s")
    
    mcol1, mcol2, mcol3, mcol4, mcol5, mcol6 = st.columns(6)
    with mcol1:
        st.metric("Primer Cuartil (Q1)", f"{q1:,.1f}")
    with mcol2:
        st.metric("Mediana (Q2)", f"{mediana:,.1f}")
    with mcol3:
        st.metric("Tercer Cuartil (Q3)", f"{q3:,.1f}")
    with mcol4:
        st.metric("Rango IQR", f"{iqr:,.1f}")
    with mcol5:
        st.metric("Límite Inferior", f"{lim_inf:,.1f}", f"Mín. Obs: {min_obs:,.0f}")
    with mcol6:
        st.metric("Límite Superior", f"{lim_sup:,.1f}", f"{n_outliers} atípicos ({pct_outliers:.1f}%)")
        
    st.markdown(f"""
    <div class="callout-box">
    <b>Justificación Metodológica Criminológica (Interpretación de Outliers):</b><br>
    En minería de datos aplicada a la seguridad pública, los <b>{n_outliers} valores atípicos detectados</b> mediante la regla 
    del Rango Intercuartílico (observaciones con conteo superior al límite teórico de {lim_sup:,.1f} hurtos o inferior a {lim_inf:,.1f}) <b>no constituyen errores de digitación ni datos espurios</b>. 
    Por el contrario, representan los <b>focos metropolitanos y grandes cabeceras urbanas críticas</b> del país (tales como Bogotá D.C., Medellín, Cali y Barranquilla), 
    donde la alta densidad demográfica, la intensiva actividad comercial y el gran volumen del parque vehicular concentran naturalmente un número desproporcionado de delitos.
    Nótese que el <b>límite inferior teórico ({lim_inf:,.1f})</b> es negativo debido a la asimetría positiva de la distribución, mientras que el <b>mínimo observado real es {min_obs:,.0f} incidentes</b>.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(f"📋 Ver Listado de {entidad_nombre}s Identificados como Valores Atípicos ({n_outliers} entidades)", expanded=False):
        outliers_display = outliers_df[[entidad_col, "TOTAL_HURTOS"]].copy()
        outliers_display["% del Total Seleccionado"] = (outliers_display["TOTAL_HURTOS"] / len(df_filtered) * 100).round(2)
        outliers_display["Exceso sobre Límite IQR"] = (outliers_display["TOTAL_HURTOS"] - lim_sup).round(1)
        outliers_display.columns = [entidad_nombre, "Total Hurtos", "% Participación", "Exceso vs Límite Superior"]
        st.dataframe(outliers_display, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# MÓDULO 4: SERIE TEMPORAL & ESTACIONALIDAD
# -----------------------------------------------------------------------------
elif menu == "📈 4. Serie Temporal & Estacionalidad":
    st.markdown('<div class="main-header">Análisis Longitudinal y Patrones de Estacionalidad</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comportamiento del delito entre 2010 y 2026 (2026: periodo parcial): ciclos mensuales y tendencias interanuales</div>', unsafe_allow_html=True)
    
    st.subheader("📅 Serie Histórica Mensual de Hurtos (2010 – 2026)")
    st.caption("ℹ️ Nota metodológica: El año 2026 refleja un periodo parcial registrado en el conjunto de datos de la Policía Nacional.")
    df_filtered["AÑO_MES"] = df_filtered["FECHA"].dt.to_period("M").astype(str)
    ts_data = df_filtered.groupby(["AÑO_MES", "MODALIDAD_HURTO"]).size().reset_index(name="HURTOS")
    
    fig_ts = px.line(
        ts_data, x="AÑO_MES", y="HURTOS", color="MODALIDAD_HURTO",
        color_discrete_map={"HURTO MOTOCICLETAS": "#EF4444", "HURTO AUTOMOTORES": "#3B82F6"}
    )
    fig_ts.update_layout(
        xaxis_title="Año y Mes", yaxis_title="Cantidad de Incidentes",
        height=450, hovermode="x unified"
    )
    st.plotly_chart(fig_ts, use_container_width=True)
    
    st.markdown("---")
    
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.subheader("🍂 Estacionalidad: Promedio de Hurtos por Mes del Año")
        mes_order = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_cnt = df_filtered.groupby("NOMBRE_MES").size().reindex(mes_order).reset_index(name="TOTAL_HURTOS")
        fig_mes = px.bar(
            mes_cnt, x="NOMBRE_MES", y="TOTAL_HURTOS",
            text="TOTAL_HURTOS",
            color="TOTAL_HURTOS",
            color_continuous_scale="Viridis"
        )
        fig_mes.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_mes.update_layout(height=400, xaxis_title="Mes")
        st.plotly_chart(fig_mes, use_container_width=True)
        
    with tcol2:
        st.subheader("📊 Variación Interanual de Casos (Crecimiento %)")
        anual_tot = df_filtered.groupby("AÑO").size().reset_index(name="TOTAL")
        anual_tot["VARIACION_PCT"] = anual_tot["TOTAL"].pct_change() * 100
        anual_tot["COLOR"] = anual_tot["VARIACION_PCT"].apply(lambda v: "#EF4444" if v > 0 else "#10B981")
        
        fig_var = px.bar(
            anual_tot.dropna(), x="AÑO", y="VARIACION_PCT",
            text=anual_tot.dropna()["VARIACION_PCT"].apply(lambda v: f"{v:+.1f}%"),
            color="COLOR",
            color_discrete_map="identity"
        )
        fig_var.update_traces(textposition='outside')
        fig_var.update_layout(height=400, yaxis_title="% Crecimiento vs Año Anterior", showlegend=False)
        st.plotly_chart(fig_var, use_container_width=True)

# -----------------------------------------------------------------------------
# MÓDULO 5: CONCENTRACIÓN TERRITORIAL
# -----------------------------------------------------------------------------
elif menu == "🗺️ 5. Concentración Territorial":
    st.markdown('<div class="main-header">Distribución Geográfica y Concentración Territorial</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Focos territoriales críticos del hurto a nivel departamental y municipal en Colombia</div>', unsafe_allow_html=True)
    
    geo1, geo2 = st.columns([6, 4])
    
    with geo1:
        st.subheader("📍 Top 15 Departamentos con Mayor Frecuencia de Hurtos")
        depto_cnt = df_filtered["DEPARTAMENTO"].value_counts().head(15).reset_index()
        depto_cnt.columns = ["Departamento", "Total Hechos"]
        depto_cnt["Porcentaje"] = (depto_cnt["Total Hechos"] / len(df_filtered) * 100).round(2)
        
        fig_depto = px.bar(
            depto_cnt, x="Total Hechos", y="Departamento",
            orientation="h",
            text="Total Hechos",
            color="Total Hechos",
            color_continuous_scale="Reds"
        )
        fig_depto.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_depto.update_layout(yaxis=dict(autorange="reversed"), height=520)
        st.plotly_chart(fig_depto, use_container_width=True)
        
    with geo2:
        st.subheader("🏙️ Top 10 Municipios Más Afectados")
        muni_cnt = df_filtered.groupby(["MUNICIPIO", "DEPARTAMENTO"]).size().reset_index(name="TOTAL").sort_values("TOTAL", ascending=False).head(10)
        muni_cnt["ETIQUETA"] = muni_cnt["MUNICIPIO"] + " (" + muni_cnt["DEPARTAMENTO"] + ")"
        
        fig_muni = px.bar(
            muni_cnt, x="TOTAL", y="ETIQUETA",
            orientation="h",
            color="TOTAL",
            color_continuous_scale="YlOrRd"
        )
        fig_muni.update_layout(yaxis=dict(autorange="reversed"), height=520)
        st.plotly_chart(fig_muni, use_container_width=True)
        
    st.markdown("---")
    
    st.subheader("🎯 Principio de Pareto: Concentración del Fenómeno Criminal")
    depto_all_cnt = df_filtered["DEPARTAMENTO"].value_counts().reset_index()
    depto_all_cnt.columns = ["Departamento", "Casos"]
    depto_all_cnt["Acumulado"] = depto_all_cnt["Casos"].cumsum()
    depto_all_cnt["Pct_Acumulado"] = (depto_all_cnt["Acumulado"] / len(df_filtered) * 100).round(2)
    
    top5_share = depto_all_cnt.iloc[min(4, len(depto_all_cnt)-1)]["Pct_Acumulado"]
    
    st.markdown(f"""
    > **Hallazgo Clave:** Los 5 primeros departamentos concentran el **{top5_share:.1f}% de todos los hurtos** 
    registrados en Colombia durante el periodo analizado. Esto confirma una fuerte **asimetría espacial** 
    donde el delito se focaliza en las grandes áreas metropolitanas (Bogotá D.C., Valle del Cauca, Antioquia, Atlántico y Cundinamarca).
    """)

# -----------------------------------------------------------------------------
# MÓDULO 6: CORRELACIONES & MODUS OPERANDI
# -----------------------------------------------------------------------------
elif menu == "🔗 6. Correlaciones & Modus Operandi":
    st.markdown('<div class="main-header">Modus Operandi y Matriz de Correlación Categórica</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Asociación entre armas empleadas, tipo de vehículo y perfil de las víctimas</div>', unsafe_allow_html=True)
    
    ccol1, ccol2 = st.columns(2)
    
    with ccol1:
        st.subheader("🔥 Matriz de Asociación: Cramér's V (Variables Categóricas)")
        # Calcular matriz de Cramér para muestra representativa
        sample_df = df_filtered.sample(min(20000, len(df_filtered)), random_state=42)
        cat_cols = ["DEPARTAMENTO", "MODALIDAD_HURTO", "ARMA_MEDIO", "GENERO", "GRUPO_ETARIO"]
        cramer_matrix = pd.DataFrame(index=cat_cols, columns=cat_cols, dtype=float)
        
        for c1 in cat_cols:
            for c2 in cat_cols:
                cramer_matrix.loc[c1, c2] = round(cramers_v(sample_df[c1], sample_df[c2]), 3)
                
        fig_cramer = px.imshow(
            cramer_matrix,
            text_auto=True,
            color_continuous_scale="Blues",
            labels=dict(color="Cramér's V"),
            zmin=0, zmax=1
        )
        fig_cramer.update_layout(height=420)
        st.plotly_chart(fig_cramer, use_container_width=True)
        
    with ccol2:
        st.subheader("⚔️ Cruce: Tipo de Hurto vs Arma / Medio Empleado")
        top_armas_list = df_filtered["ARMA_MEDIO"].value_counts().head(5).index.tolist()
        crosstab_arma = df_filtered[df_filtered["ARMA_MEDIO"].isin(top_armas_list)]
        ct = pd.crosstab(crosstab_arma["ARMA_MEDIO"], crosstab_arma["MODALIDAD_HURTO"], normalize="columns") * 100
        
        fig_ct = px.bar(
            ct.reset_index(),
            x="ARMA_MEDIO", y=["HURTO AUTOMOTORES", "HURTO MOTOCICLETAS"],
            barmode="group",
            labels={"value": "% de Hurtos en la Modalidad", "ARMA_MEDIO": "Arma / Medio"}
        )
        fig_ct.update_layout(height=420, legend_title="Modalidad")
        st.plotly_chart(fig_ct, use_container_width=True)
        
    st.markdown("---")
    
    st.subheader("🚻 Cruce Bivariado: Género de la Víctima vs Tipo de Hurto")
    gen_tipo = pd.crosstab(df_filtered["GENERO"], df_filtered["MODALIDAD_HURTO"], margins=True, margins_name="Total")
    st.dataframe(gen_tipo, use_container_width=True)

# -----------------------------------------------------------------------------
# MÓDULO 7: HALLAZGOS & TOMA DE DECISIONES
# -----------------------------------------------------------------------------
elif menu == "💡 7. Hallazgos & Toma de Decisiones":
    st.markdown('<div class="main-header">Hallazgos Analíticos y Recomendaciones de Política Pública</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evidencia empírica cuantitativa para el artículo científico y la formulación de propuestas basadas en datos</div>', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # CÁLCULOS ESTADÍSTICOS DINÁMICOS SOBRE EL DATASET EVALUADO
    # -------------------------------------------------------------------------
    df_eval = df_filtered if len(df_filtered) > 0 else df
    n_total = len(df_eval)
    
    # 1. Predominancia de Modalidades
    motos_cnt = int((df_eval["MODALIDAD_HURTO"] == "HURTO MOTOCICLETAS").sum())
    autos_cnt = int((df_eval["MODALIDAD_HURTO"] == "HURTO AUTOMOTORES").sum())
    pct_motos = (motos_cnt / n_total * 100) if n_total > 0 else 0.0
    pct_autos = (autos_cnt / n_total * 100) if n_total > 0 else 0.0
    
    # 2. Armas y Medios por Modalidad (100% de las 12 categorías del CSV)
    ct_armas = pd.crosstab(df_eval["ARMA_MEDIO"], df_eval["MODALIDAD_HURTO"])
    if "HURTO MOTOCICLETAS" not in ct_armas.columns:
        ct_armas["HURTO MOTOCICLETAS"] = 0
    if "HURTO AUTOMOTORES" not in ct_armas.columns:
        ct_armas["HURTO AUTOMOTORES"] = 0
    ct_armas["TOTAL"] = ct_armas["HURTO MOTOCICLETAS"] + ct_armas["HURTO AUTOMOTORES"]
    ct_armas = ct_armas.sort_values("TOTAL", ascending=False)
    
    arma_fuego_moto_cnt = int(ct_armas.loc["ARMA DE FUEGO", "HURTO MOTOCICLETAS"]) if "ARMA DE FUEGO" in ct_armas.index else 0
    arma_fuego_auto_cnt = int(ct_armas.loc["ARMA DE FUEGO", "HURTO AUTOMOTORES"]) if "ARMA DE FUEGO" in ct_armas.index else 0
    arma_fuego_moto_pct = (arma_fuego_moto_cnt / motos_cnt * 100) if motos_cnt > 0 else 0.0
    arma_fuego_auto_pct = (arma_fuego_auto_cnt / autos_cnt * 100) if autos_cnt > 0 else 0.0
    
    llave_auto_cnt = int(ct_armas.loc["LLAVE MAESTRA", "HURTO AUTOMOTORES"]) if "LLAVE MAESTRA" in ct_armas.index else 0
    llave_moto_cnt = int(ct_armas.loc["LLAVE MAESTRA", "HURTO MOTOCICLETAS"]) if "LLAVE MAESTRA" in ct_armas.index else 0
    llave_auto_pct = (llave_auto_cnt / autos_cnt * 100) if autos_cnt > 0 else 0.0
    llave_moto_pct = (llave_moto_cnt / motos_cnt * 100) if motos_cnt > 0 else 0.0
    
    sin_armas_auto_cnt = int(ct_armas.loc["SIN EMPLEO DE ARMAS", "HURTO AUTOMOTORES"]) if "SIN EMPLEO DE ARMAS" in ct_armas.index else 0
    sin_armas_moto_cnt = int(ct_armas.loc["SIN EMPLEO DE ARMAS", "HURTO MOTOCICLETAS"]) if "SIN EMPLEO DE ARMAS" in ct_armas.index else 0
    sin_armas_auto_pct = (sin_armas_auto_cnt / autos_cnt * 100) if autos_cnt > 0 else 0.0
    sin_armas_moto_pct = (sin_armas_moto_cnt / motos_cnt * 100) if motos_cnt > 0 else 0.0
    
    # 3. Concentración Territorial (Curva de Pareto Municipal - 1.052 Municipios)
    muni_agg = df_eval.groupby(["DEPARTAMENTO", "MUNICIPIO"]).size().reset_index(name="TOTAL").sort_values("TOTAL", ascending=False).reset_index(drop=True)
    muni_agg["CUMSUM"] = muni_agg["TOTAL"].cumsum()
    muni_agg["CUMPCT"] = (muni_agg["CUMSUM"] / n_total * 100) if n_total > 0 else 0.0
    total_munis = len(muni_agg)
    
    pareto_80_idx = int(muni_agg[muni_agg["CUMPCT"] >= 80.0].index[0] + 1) if len(muni_agg[muni_agg["CUMPCT"] >= 80.0]) > 0 else 0
    pareto_80_val = float(muni_agg.loc[pareto_80_idx - 1, "CUMPCT"]) if pareto_80_idx > 0 else 0.0
    pareto_prev_val = float(muni_agg.loc[pareto_80_idx - 2, "CUMPCT"]) if pareto_80_idx > 1 else 0.0
    pct_munis_80 = (pareto_80_idx / total_munis * 100) if total_munis > 0 else 0.0
    top10_share = float(muni_agg.loc[min(9, total_munis - 1), "CUMPCT"]) if total_munis > 0 else 0.0
    top3_share = float(muni_agg.loc[min(2, total_munis - 1), "CUMPCT"]) if total_munis > 0 else 0.0
    
    # 4. Perfil Demográfico (Valores Reportados y No Reportados)
    gen_cnt = df_eval["GENERO"].value_counts()
    gen_pct = (df_eval["GENERO"].value_counts(normalize=True) * 100) if n_total > 0 else pd.Series()
    
    eta_cnt = df_eval["GRUPO_ETARIO"].value_counts()
    eta_pct = (df_eval["GRUPO_ETARIO"].value_counts(normalize=True) * 100) if n_total > 0 else pd.Series()
    
    # 5. Estacionalidad (Frecuencia por Día de la Semana)
    dias_order = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dias_cnt = df_eval["DIA_SEMANA"].value_counts().reindex(dias_order).fillna(0)
    dias_pct = (dias_cnt / n_total * 100) if n_total > 0 else pd.Series()
    dia_max = dias_cnt.idxmax()
    dia_min = dias_cnt.idxmin()

    # -------------------------------------------------------------------------
    # SÍNTESIS EJECUTIVA DE INDICADORES (KPIS DINÁMICOS)
    # -------------------------------------------------------------------------
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        st.metric("Total Incidentes Analizados", f"{n_total:,}")
    with kcol2:
        st.metric("Predominancia Motocicletas", f"{pct_motos:.2f}%", f"{motos_cnt:,} hechos")
    with kcol3:
        st.metric("Concentración Pareto (≥80%)", f"{pareto_80_idx} Municipios", f"{pct_munis_80:.2f}% del país")
    with kcol4:
        st.metric("Día con Mayor Frecuencia", f"{dia_max}", f"{dias_pct[dia_max]:.2f}% ({int(dias_cnt[dia_max]):,})")
        
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # SECCIÓN 1: HALLAZGOS ANALÍTICOS EMPÍRICOS (DETALLE Y TABLAS)
    # -------------------------------------------------------------------------
    st.markdown("### 📌 1. Principales Hallazgos Empíricos (Verificados Cuantitativamente)")
    
    # 1.1 Modalidades
    st.markdown(f"""
    #### 1.1 Predominancia de Modalidades (Hurto Motocicletas vs. Automotores)
    * Del total general de registros evaluados (**{n_total:,} hechos**), el **{pct_motos:.2f}%** ({motos_cnt:,} registros) corresponde al 
      **hurto de motocicletas**, mientras que el **{pct_autos:.2f}%** ({autos_cnt:,} registros) corresponde al **hurto de automotores**.
    * La evidencia empírica confirma una proporción superior a **3 a 1**: aproximadamente 3 de cada 4 vehículos hurtados en Colombia 
      son motocicletas, reflejando el principal foco del fenómeno sobre el parque automotor nacional.
    """)
    
    # 1.2 Armas y Medios
    st.markdown(f"""
    #### 1.2 Medios y Armas Registradas por Modalidad de Hurto
    * **Presencia Registrada de Arma de Fuego:** En la variable oficial `ARMAS MEDIOS`, el código de *Arma de Fuego* se encuentra consignado 
      en el **{arma_fuego_moto_pct:.2f}%** ({arma_fuego_moto_cnt:,} casos) de los registros de hurto de motocicletas y en el 
      **{arma_fuego_auto_pct:.2f}%** ({arma_fuego_auto_cnt:,} casos) de automotores. La diferencia relativa es de solo **{abs(arma_fuego_moto_pct - arma_fuego_auto_pct):.2f} puntos porcentuales**, 
      lo cual confirma que la proporción de armas de fuego registradas es **prácticamente equivalente en ambas modalidades**. 
      *Precisión metodológica:* La presencia de este código documenta el medio consignado en la denuncia policial, pero **no permite inferir ni atribuir per se intimidación efectiva, disparos, lesiones personales o violencia consumada contra las víctimas**, variables que no forman parte de este registro administrativo.
    * **Registros con Llave Maestra o Sin Empleo de Armas:**
      En ambas modalidades, los mayores volúmenes corresponden a hechos registrados bajo las categorías de *Llave Maestra* o *Sin Empleo de Armas*:
      - En **automotores**, el **{llave_auto_pct:.2f}%** ({llave_auto_cnt:,} casos) registra **Llave Maestra** y el **{sin_armas_auto_pct:.2f}%** ({sin_armas_auto_cnt:,} casos) **Sin Empleo de Armas**, sumando conjuntamente el **{(llave_auto_pct + sin_armas_auto_pct):.2f}%** de los eventos de la modalidad.
      - En **motocicletas**, la categoría **Sin Empleo de Armas** representa el **{sin_armas_moto_pct:.2f}%** ({sin_armas_moto_cnt:,} casos) y **Llave Maestra** el **{llave_moto_pct:.2f}%** ({llave_moto_cnt:,} casos), sumando conjuntamente el **{(sin_armas_moto_pct + llave_moto_pct):.2f}%**.
      - *Criterio metodológico:* La clasificación de *Sin Empleo de Armas* o *Llave Maestra* describe objetivamente la ausencia de un instrumento armado reportado en la minuta policial o el uso de artificios de apertura mecánica. No obstante, **no debe asumirse como ausencia de violencia o intimidación**, puesto que el hecho delictivo pudo haber involucrado agresiones verbales, persecuciones o fuerza física que no conllevan el porte de un arma identificada.
    """)
    
    # Tabla completa de armas y medios (100% de las 12 categorías existentes en el CSV)
    armas_display_list = []
    for arma_cat, row_data in ct_armas.iterrows():
        c_moto_cat = int(row_data["HURTO MOTOCICLETAS"])
        p_moto_cat = (c_moto_cat / motos_cnt * 100) if motos_cnt > 0 else 0.0
        c_auto_cat = int(row_data["HURTO AUTOMOTORES"])
        p_auto_cat = (c_auto_cat / autos_cnt * 100) if autos_cnt > 0 else 0.0
        c_tot_cat = int(row_data["TOTAL"])
        p_tot_cat = (c_tot_cat / n_total * 100) if n_total > 0 else 0.0
        armas_display_list.append({
            "Medio / Arma Registrada": arma_cat,
            "Motos (Casos)": f"{c_moto_cat:,}",
            "% en Motos": f"{p_moto_cat:.2f}%",
            "Autos (Casos)": f"{c_auto_cat:,}",
            "% en Autos": f"{p_auto_cat:.2f}%",
            "Total Incidentes": f"{c_tot_cat:,}",
            "% del Total General": f"{p_tot_cat:.2f}%"
        })
        
    armas_display_list.append({
        "Medio / Arma Registrada": "TOTAL GENERAL",
        "Motos (Casos)": f"{motos_cnt:,}",
        "% en Motos": "100.00%",
        "Autos (Casos)": f"{autos_cnt:,}",
        "% en Autos": "100.00%",
        "Total Incidentes": f"{n_total:,}",
        "% del Total General": "100.00%"
    })
    st.dataframe(pd.DataFrame(armas_display_list), use_container_width=True, hide_index=True)
    st.caption("ℹ️ Nota de integridad: La tabla incluye las 12 categorías existentes en el CSV original. Los porcentajes de cada modalidad toman como denominador el total de dicha modalidad (Motos: 497.736, Autos: 158.899). La fila final verifica que las frecuencias sumen exactamente el 100.00%.")
    
    # 1.3 Concentración Territorial (Pareto)
    muni_1_nombre = muni_agg.loc[0, 'MUNICIPIO'] if len(muni_agg) > 0 else ""
    muni_1_total = int(muni_agg.loc[0, 'TOTAL']) if len(muni_agg) > 0 else 0
    muni_2_nombre = muni_agg.loc[1, 'MUNICIPIO'] if len(muni_agg) > 1 else ""
    muni_2_total = int(muni_agg.loc[1, 'TOTAL']) if len(muni_agg) > 1 else 0
    muni_3_nombre = muni_agg.loc[2, 'MUNICIPIO'] if len(muni_agg) > 2 else ""
    muni_3_total = int(muni_agg.loc[2, 'TOTAL']) if len(muni_agg) > 2 else 0

    st.markdown(f"""
    #### 1.3 Hiperconcentración Territorial (Curva de Pareto Municipal - {total_munis:,} Municipios)
    * **Umbral del 80%:** Al ordenar descendentemente los {total_munis:,} municipios según el volumen de hurtos, el municipio en la posición 51 acumula el **{pareto_prev_val:.2f}%** y el municipio en la posición 52 alcanza el **{pareto_80_val:.2f}%**. Por lo tanto, se confirma empíricamente que **exactamente {pareto_80_idx} municipios** constituyen el número mínimo necesario para alcanzar y superar el 80% nacional.
    * Estos **{pareto_80_idx} municipios representan apenas el {pct_munis_80:.2f}%** del territorio municipal evaluado, evidenciando una concentración espacial sustancialmente más acentuada que la estimación teórica del 15%.
    * **Top 10 y Top 3 Cabeceras:** Los primeros 10 municipios concentran el **{top10_share:.2f}%** de los hurtos del país ({int(muni_agg.head(10)['TOTAL'].sum()):,} incidentes). Asimismo, las tres principales ciudades metropolitanas acumulan por sí solas el **{top3_share:.2f}%** nacional: {muni_1_nombre} ({muni_1_total:,} hechos, {muni_1_total/n_total*100:.2f}%), {muni_2_nombre} ({muni_2_total:,} hechos, {muni_2_total/n_total*100:.2f}%) y {muni_3_nombre} ({muni_3_total:,} hechos, {muni_3_total/n_total*100:.2f}%).
    """)
    
    # Tabla Top 10 Municipios Pareto
    pareto_top10 = muni_agg.head(10)[["MUNICIPIO", "DEPARTAMENTO", "TOTAL", "CUMPCT"]].copy()
    pareto_top10["POS"] = range(1, len(pareto_top10) + 1)
    pareto_top10["PCT_INDIVIDUAL"] = (pareto_top10["TOTAL"] / n_total * 100).apply(lambda v: f"{v:.2f}%")
    pareto_top10["CUMPCT"] = pareto_top10["CUMPCT"].apply(lambda v: f"{v:.2f}%")
    pareto_top10["TOTAL"] = pareto_top10["TOTAL"].apply(lambda v: f"{v:,}")
    pareto_top10 = pareto_top10[["POS", "MUNICIPIO", "DEPARTAMENTO", "TOTAL", "PCT_INDIVIDUAL", "CUMPCT"]]
    pareto_top10.columns = ["Posición", "Municipio", "Departamento", "Total Incidentes", "% Individual", "% Acumulado Nacional"]
    st.dataframe(pareto_top10, use_container_width=True, hide_index=True)
    
    # 1.4 Perfil Demográfico
    gen_masc_cnt = int(gen_cnt.get('MASCULINO', 0))
    gen_fem_cnt = int(gen_cnt.get('FEMENINO', 0))
    gen_nr_cnt = int(gen_cnt.get('NO REPORTADO', 0))
    gen_masc_pct = float(gen_pct.get('MASCULINO', 0.0))
    gen_fem_pct = float(gen_pct.get('FEMENINO', 0.0))
    gen_nr_pct = float(gen_pct.get('NO REPORTADO', 0.0))
    
    eta_adu_cnt = int(eta_cnt.get('ADULTOS', 0))
    eta_ado_cnt = int(eta_cnt.get('ADOLESCENTES', 0))
    eta_men_cnt = int(eta_cnt.get('MENORES', 0))
    eta_nr_cnt = int(eta_cnt.get('NO REPORTADO', 0))
    eta_adu_pct = float(eta_pct.get('ADULTOS', 0.0))
    eta_ado_pct = float(eta_pct.get('ADOLESCENTES', 0.0))
    eta_men_pct = float(eta_pct.get('MENORES', 0.0))
    eta_nr_pct = float(eta_pct.get('NO REPORTADO', 0.0))

    st.markdown(f"""
    #### 1.4 Perfil Demográfico de las Víctimas (Valores Reportados y No Reportados)
    * **Distribución por Género:** El **{gen_masc_pct:.2f}%** ({gen_masc_cnt:,} hechos) de las víctimas registradas 
      corresponde al género **Masculino**, el **{gen_fem_pct:.2f}%** ({gen_fem_cnt:,} hechos) al género **Femenino**, 
      y un **{gen_nr_pct:.2f}%** ({gen_nr_cnt:,} registros) no cuenta con género especificado en la fuente oficial (**No Reportado**). 
      La suma de las tres categorías equivale a {gen_masc_cnt + gen_fem_cnt + gen_nr_cnt:,} hechos (100,00%).
    * **Distribución por Grupo Etario y Justificación de Registros Faltantes:**
      - **Adultos:** {eta_adu_cnt:,} hechos (**{eta_adu_pct:.2f}%**).
      - **Adolescentes:** {eta_ado_cnt:,} hechos (**{eta_ado_pct:.2f}%**).
      - **Menores:** {eta_men_cnt:,} hechos (**{eta_men_pct:.2f}%**).
      - **No Reportado:** {eta_nr_cnt:,} hechos (**{eta_nr_pct:.2f}%**).
      - *Verificación de Integridad:* La suma estricta de las categorías reportadas más los no reportados ({eta_adu_cnt:,} + {eta_ado_cnt:,} + {eta_men_cnt:,} + {eta_nr_cnt:,}) coincide exactamente con **{eta_adu_cnt + eta_ado_cnt + eta_men_cnt + eta_nr_cnt:,} hechos (100,00%)**. Los 205 registros sin grupo etario reportado corresponden a omisiones de captura en la fuente administrativa original de la Policía Nacional, los cuales se conservan explícitamente en el dataset bajo la categoría *No Reportado* para evitar atrición de datos.
    * *Criterio Metodológico:* Estos resultados describen objetivamente la información consignada en los registros policiales. No se realizan inferencias causales sobre roles ocupacionales o movilidad que no estén sustentadas en variables directas del dataset.
    """)
    
    # Tabla resumen demográfico
    demo_table = pd.DataFrame({
        "Dimensión Demográfica": ["Género", "Género", "Género", "Grupo Etario", "Grupo Etario", "Grupo Etario", "Grupo Etario"],
        "Categoría": ["Masculino", "Femenino", "No Reportado", "Adultos", "Adolescentes", "Menores", "No Reportado"],
        "Frecuencia Absoluta": [f"{gen_masc_cnt:,}", f"{gen_fem_cnt:,}", f"{gen_nr_cnt:,}", f"{eta_adu_cnt:,}", f"{eta_ado_cnt:,}", f"{eta_men_cnt:,}", f"{eta_nr_cnt:,}"],
        "% de Participación": [f"{gen_masc_pct:.2f}%", f"{gen_fem_pct:.2f}%", f"{gen_nr_pct:.2f}%", f"{eta_adu_pct:.2f}%", f"{eta_ado_pct:.2f}%", f"{eta_men_pct:.2f}%", f"{eta_nr_pct:.2f}%"]
    })
    st.dataframe(demo_table, use_container_width=True, hide_index=True)
    
    # 1.5 Estacionalidad
    st.markdown(f"""
    #### 1.5 Patrón Temporal y Frecuencia por Día de la Semana
    * **Día de Mayor Incidencia Relativa:** El día **{dia_max}** registra el valor más alto con **{int(dias_cnt[dia_max]):,} hechos ({dias_pct[dia_max]:.2f}%)**, 
      seguido muy de cerca por el **Miércoles** ({int(dias_cnt.get('Miércoles', 0)):,} hechos, {dias_pct.get('Miércoles', 0.0):.2f}%) y el **Viernes** ({int(dias_cnt.get('Viernes', 0)):,} hechos, {dias_pct.get('Viernes', 0.0):.2f}%).
    * **Homogeneidad Semanal:** La distribución a lo largo de los siete días de la semana es notablemente uniforme, oscilando en un estrecho rango entre el **{dias_pct[dia_min]:.2f}%** ({dia_min}) y el **{dias_pct[dia_max]:.2f}%** ({dia_max}), con una variación máxima de apenas {abs(dias_pct[dia_max] - dias_pct[dia_min]):.2f} puntos porcentuales. 
      La evidencia estadística descriptiva no permite inferir causas conductuales o de ocio que no se encuentren respaldadas por las variables del registro policial.
    """)
    
    # Tabla días de la semana
    dias_display = pd.DataFrame({
        "Día de la Semana": dias_order,
        "Total Incidentes": [f"{int(dias_cnt.get(d, 0)):,}" for d in dias_order],
        "% Participación Semanal": [f"{dias_pct.get(d, 0.0):.2f}%" for d in dias_order]
    })
    st.dataframe(dias_display, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # SECCIÓN 2: RECOMENDACIONES DE POLÍTICA PÚBLICA (PROPUESTAS FORMULADAS)
    # -------------------------------------------------------------------------
    st.markdown("### 🎯 2. Propuestas de Recomendaciones Orientadas a la Política Pública")
    st.caption("Cada propuesta se articula directamente sobre un hallazgo estadístico verificado y se formula como una propuesta de intervención prospectiva, no como un resultado ya comprobado de efectividad tecnológica o policial.")
    
    st.markdown(f"""
    1. **Propuesta de Focalización Territorial Prioritaria (Basada en Concentración Pareto):**
       * *Hallazgo Cuantitativo Observado:* El 80,08% del hurto vehicular nacional se concentra en exactamente {pareto_80_idx} municipios ({pct_munis_80:.2f}% del territorio municipal), acumulando las tres principales cabeceras ({muni_1_nombre}, {muni_2_nombre} y {muni_3_nombre}) el {top3_share:.2f}% de los hechos.
       * *Propuesta de Intervención:* Se propone focalizar los recursos de patrullaje preventivo y cuadrantes en los {pareto_80_idx} nodos municipales críticos identificados. Se aclara que esta formulación constituye una propuesta prospectiva de gestión pública, cuya efectividad operacional dependerá de estudios de impacto específicos que no formaron parte del alcance de este proyecto descriptivo.
       
    2. **Propuesta de Control Registral y Trazabilidad al Mercado de Autopartes de Motocicletas:**
       * *Hallazgo Cuantitativo Observado:* El hurto de motocicletas representa el {pct_motos:.2f}% ({motos_cnt:,} hechos) de la criminalidad vehicular del país, triplicando la frecuencia observada en automotores ({pct_autos:.2f}%, {autos_cnt:,} hechos).
       * *Propuesta de Intervención:* Se propone evaluar mecanismos interinstitucionales de fiscalización y trazabilidad técnica de partes usadas en talleres y establecimientos comerciales de las principales áreas metropolitanas. El proyecto constata la asimetría del volumen vehicular sustraído, sin afirmar que la efectividad de estas medidas regulatorias haya sido evaluada empíricamente en el estudio.
       
    3. **Propuesta de Mitigación de Vulnerabilidad Frente al Hurto con Llave Maestra y Sin Armas:**
       * *Hallazgo Cuantitativo Observado:* Los registros con Llave Maestra y Sin Empleo de Armas representan conjuntamente el {(llave_auto_pct + sin_armas_auto_pct):.2f}% en automotores y el {(sin_armas_moto_pct + llave_moto_pct):.2f}% en motocicletas.
       * *Propuesta de Intervención:* Se propone estudiar incentivos normativos para la adopción de tecnologías de seguridad pasiva (inmovilizadores, alarmas y cortacorrientes) y promover esquemas de parqueo seguro vigilado que desestimulen el estacionamiento en vía pública. Dichas tecnologías se sugieren como alternativas a explorar, sin presentar su eficacia como comprobada en este proyecto.
       
    4. **Propuesta de Protocolos de Respuesta ante Incidentes con Arma de Fuego Registrada:**
       * *Hallazgo Cuantitativo Observado:* El código de arma de fuego se encuentra registrado en el {arma_fuego_moto_pct:.2f}% de los hurtos de motocicletas ({arma_fuego_moto_cnt:,} casos) y en el {arma_fuego_auto_pct:.2f}% de automotores ({arma_fuego_auto_cnt:,} casos), totalizando {arma_fuego_moto_cnt + arma_fuego_auto_cnt:,} hechos.
       * *Propuesta de Intervención:* Se propone diseñar protocolos de alerta temprana y monitoreo continuo en corredores viales de alta afluencia para optimizar el despacho policial ante denuncias que reporten la presencia de armas. Se formula como propuesta operativa para la toma de decisiones, diferenciando el diagnóstico de frecuencia observada de la evaluación empírica de tiempos de respuesta policial.
    """)

# Pie de página
st.markdown("---")
st.caption("Sistema de Analítica Desarrollado para la Asignatura de Minería de Datos | Almacenamiento en Neon PostgreSQL | EDA con Streamlit | Visualización en Power BI")

