# -*- coding: utf-8 -*-
"""
Script para generar las figuras complementarias y compilar el Artículo Científico
en formato IEEE (.docx) cumpliendo con más de 4.000 palabras y la estructura oficial del docente.
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. GENERACIÓN DE FIGURAS COMPLEMENTARIAS
# -----------------------------------------------------------------------------
def generate_figures():
    # 1.1 Matriz de Asociación Cramér's V
    cols = ['Departamento', 'Modalidad', 'Arma/Medio', 'Género', 'Grupo Etario']
    matrix = np.array([
        [1.000, 0.434, 0.310, 0.101, 0.019],
        [0.434, 1.000, 0.079, 0.097, 0.034],
        [0.310, 0.079, 1.000, 0.053, 0.047],
        [0.101, 0.097, 0.053, 1.000, 0.353],
        [0.019, 0.034, 0.047, 0.353, 1.000]
    ])

    fig, ax = plt.subplots(figsize=(6.5, 4.8), dpi=300)
    cax = ax.matshow(matrix, cmap='Blues')
    fig.colorbar(cax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, fontsize=9, fontweight='bold', rotation=30, ha='left')
    ax.set_yticklabels(cols, fontsize=9, fontweight='bold')

    for i in range(len(cols)):
        for j in range(len(cols)):
            val = matrix[i, j]
            color = 'white' if val > 0.4 else 'black'
            ax.text(j, i, f'{val:.3f}', ha='center', va='center', color=color, fontweight='bold', fontsize=9.5)

    plt.title('Matriz de Coeficiente V de Cramér (Asociación Categórica)', fontsize=11, fontweight='bold', pad=25)
    plt.tight_layout()
    cramer_img = FIGURES_DIR / "fig_cramer_v.png"
    plt.savefig(cramer_img)
    plt.close()
    print("Figura Cramér V guardada en:", cramer_img)

    # 1.2 Auditoría de Calidad y Tratamiento de Valores Faltantes
    fig, ax = plt.subplots(figsize=(6.5, 3.8), dpi=300)
    vars_audit = ['Departamento', 'Municipio', 'Código DANE', 'Fecha Hecho', 'Modalidad', 'Cantidad', 'Género', 'Grupo Etario']
    missing_counts = [0, 0, 0, 0, 0, 0, 712, 205]
    colors = ['#10B981']*6 + ['#F59E0B', '#EF4444']

    bars = ax.barh(vars_audit, missing_counts, color=colors, height=0.6)
    ax.set_xlabel('Registros Faltantes / Imputados con "NO REPORTADO" (N=656.635)', fontsize=9, fontweight='bold')
    ax.set_title('Auditoría de Calidad de Datos: Integridad y Cero Registros Eliminados', fontsize=11, fontweight='bold', pad=15)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    for bar, count in zip(bars, missing_counts):
        if count > 0:
            ax.text(bar.get_width() + 15, bar.get_y() + bar.get_height()/2, f'{count:,} (Imputados)', va='center', fontsize=9, fontweight='bold', color='#1E293B')
        else:
            ax.text(10, bar.get_y() + bar.get_height()/2, '0 nulos (100% íntegro)', va='center', fontsize=8.5, color='#047857', fontweight='bold')

    ax.set_xlim(0, 950)
    plt.tight_layout()
    audit_img = FIGURES_DIR / "fig_calidad_datos.png"
    plt.savefig(audit_img)
    plt.close()
    print("Figura Calidad de Datos guardada en:", audit_img)

if __name__ == "__main__":
    generate_figures()
