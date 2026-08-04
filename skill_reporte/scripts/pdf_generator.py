"""
pdf_generator.py
================
Genera el PDF "Reporte Ventas y Margen — Loco Tequila" usando ReportLab.
Fiel al Design.md: banda maroon, logo SVG/PNG, tablas con highlight-cream,
gráficas matplotlib embebidas (barras+línea, barras apiladas; NO donas para tendencias).

Estructura de páginas:
  1  — Resumen Anual (dona + tabla canal×producto + clientes)
  2  — Resumen Semanal (dona + tabla canal×producto + clientes)
  3  — Histórico mensual (barras apiladas + línea roja plan)
  4-5  — Ventas Totales Por Producto (Semanal + Anual)
  6-7  — Ventas Totales Por Canal (Semanal + Anual)
  8-19 — 6 SKUs × 2 páginas
  20-31 — 6 clientes × 2 páginas
"""

import io
import os
import sys
import math
import copy
import base64
import textwrap
from typing import Optional, List, Dict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
pt = 1.0  # En ReportLab, 1 punto = 1 unidad (no hace falta importarlo)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.pdfgen import canvas as rl_canvas

import design_tokens as dt
from design_tokens import (
    BRAND_MAROON, BRAND_MAROON_DEEP, HEADER_TEXT, PAGE_BG, RULE_LINE,
    HIGHLIGHT_CREAM, NEG_VALUE, POS_VALUE, SECTION_TITLE, SECTION_SUBTITLE,
    PRODUCT_ORDER, PRODUCT_DISPLAY_NAMES, PRODUCT_COLORS,
    CANAL_ORDER, CANAL_COLORS,
    CHART_PLAN_LINE, CHART_LASTYEAR_AREA, CHART_GRID, CHART_LABEL,
    fmt_currency, fmt_pct, fmt_int, fmt_ticket,
    hex_to_rgb, hex_to_rgb255,
    PAGE_WIDTH_PT, PAGE_HEIGHT_PT, MARGIN_PT, HEADER_HEIGHT_PT, FOOTER_HEIGHT_PT,
)
from data_processor import LocoDataProcessor
from logo_processor import get_logo_for_pdf, get_logo_for_html, get_logo_drawing_for_pdf, make_white_svg, SVG_WHITE


# ---------------------------------------------------------------------------
# Helpers de color para ReportLab
# ---------------------------------------------------------------------------

def rl_color(hex_color: str) -> colors.HexColor:
    return colors.HexColor(hex_color)


MAROON_RL    = rl_color(BRAND_MAROON)
CREAM_RL     = rl_color(HIGHLIGHT_CREAM)
NEG_RL       = rl_color(NEG_VALUE)
WHITE_RL     = colors.white
BLACK_RL     = colors.black
GREY_RL      = rl_color(SECTION_SUBTITLE)
RULE_RL      = rl_color(RULE_LINE)


# ---------------------------------------------------------------------------
# Gráfica: Dona (solo págs. 1-2, como en el Design.md original)
# ---------------------------------------------------------------------------

def make_donut_chart(product_df: pd.DataFrame, total: float, size_inches=(3.5, 3.0)) -> bytes:
    """
    Dona de participación por producto.
    Retorna PNG bytes para embeber en ReportLab.
    """
    labels, values, clrs = [], [], []
    for prod in PRODUCT_ORDER:
        v = float(product_df.get(prod, 0))
        if v > 0:
            labels.append(PRODUCT_DISPLAY_NAMES.get(prod, prod))
            values.append(v)
            clrs.append(hex_to_rgb(PRODUCT_COLORS[prod]))

    if not values:
        values = [1]
        labels = ["Sin datos"]
        clrs   = [hex_to_rgb("#CCCCCC")]

    fig, ax = plt.subplots(figsize=size_inches)
    fig.patch.set_alpha(0)
    wedges, _ = ax.pie(
        values,
        labels=None,
        colors=clrs,
        startangle=90,
        wedgeprops=dict(width=0.5, edgecolor="white", linewidth=1.5),
    )
    # Centro
    ax.text(0, 0.08, fmt_currency(total), ha="center", va="center",
            fontsize=12, fontweight="bold", color=hex_to_rgb(SECTION_TITLE))
    ax.text(0, -0.18, "Total de ventas", ha="center", va="center",
            fontsize=7, color=hex_to_rgb(SECTION_SUBTITLE))
    ax.set_aspect("equal")
    plt.tight_layout(pad=0.2)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor="none", transparent=True)
    plt.close(fig)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Gráfica: Treemap de Voronoi (power diagram con áreas proporcionales)
# ---------------------------------------------------------------------------
# Se usa en lugar de la dona cuando hay más de 3 productos: la dona pierde
# legibilidad con muchas categorías, mientras que el treemap de Voronoi asigna
# a cada producto un área proporcional a su venta. El diagrama se calcula como
# un "power diagram" (Voronoi con pesos): el bisector entre dos sitios es una
# recta, así que cada celda es la intersección de semiplanos recortada contra
# un contorno circular. Los pesos se ajustan iterativamente (relajación tipo
# Balzer/Lloyd) hasta que el área de cada celda coincide con su objetivo.

def _clip_halfplane(poly, a, b, c):
    """Recorta el polígono conservando los puntos con a*x + b*y <= c."""
    if not poly:
        return poly
    res = []
    n = len(poly)
    for i in range(n):
        cur = poly[i]
        nxt = poly[(i + 1) % n]
        cur_in = (a * cur[0] + b * cur[1]) <= c + 1e-12
        nxt_in = (a * nxt[0] + b * nxt[1]) <= c + 1e-12
        if cur_in:
            res.append(cur)
        if cur_in != nxt_in:
            dx = nxt[0] - cur[0]
            dy = nxt[1] - cur[1]
            denom = a * dx + b * dy
            if abs(denom) > 1e-15:
                t = (c - (a * cur[0] + b * cur[1])) / denom
                res.append((cur[0] + t * dx, cur[1] + t * dy))
    return res


def _poly_area(poly):
    if len(poly) < 3:
        return 0.0
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def _poly_centroid(poly):
    n = len(poly)
    if n == 0:
        return (0.0, 0.0)
    if n < 3:
        return (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)
    A = cx = cy = 0.0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        A += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    A *= 0.5
    if abs(A) < 1e-15:
        return (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)
    return (cx / (6 * A), cy / (6 * A))


def _power_cells(sites, weights, boundary):
    """Celdas del power diagram: intersección de semiplanos bisectores."""
    cells = []
    n = len(sites)
    for i in range(n):
        poly = list(boundary)
        xi, yi = sites[i]
        wi = weights[i]
        for j in range(n):
            if j == i:
                continue
            xj, yj = sites[j]
            wj = weights[j]
            a = 2 * (xj - xi)
            b = 2 * (yj - yi)
            c = (xj * xj + yj * yj - wj) - (xi * xi + yi * yi - wi)
            poly = _clip_halfplane(poly, a, b, c)
            if not poly:
                break
        cells.append(poly)
    return cells


def _circle_boundary(cx, cy, r, n=96):
    return [(cx + r * math.cos(2 * math.pi * k / n),
             cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _voronoi_treemap_cells(values, iters=200, adapt=0.5):
    """Devuelve las celdas del treemap de Voronoi con áreas ~ proporcionales."""
    n = len(values)
    total = sum(values) or 1.0
    boundary = _circle_boundary(0.0, 0.0, 1.0)
    barea = _poly_area(boundary)
    target = [v / total * barea for v in values]

    # Semillas repartidas de forma determinista (ángulo áureo)
    ga = math.pi * (3 - math.sqrt(5))
    sites = [(0.55 * math.sqrt((i + 0.5) / n) * math.cos(i * ga),
              0.55 * math.sqrt((i + 0.5) / n) * math.sin(i * ga)) for i in range(n)]
    weights = [0.0] * n

    cells = _power_cells(sites, weights, boundary)
    for _ in range(iters):
        # Lloyd: mover cada sitio al centroide de su celda
        for i in range(n):
            if _poly_area(cells[i]) > 1e-9:
                cells_c = _poly_centroid(cells[i])
                sites[i] = cells_c
        cells = _power_cells(sites, weights, boundary)
        areas = [_poly_area(c) for c in cells]
        # Ajustar pesos hacia el área objetivo
        for i in range(n):
            weights[i] += (target[i] - areas[i]) * adapt
        wmin = min(weights)
        weights = [w - wmin for w in weights]
        # Clamp: cada sitio debe permanecer dentro de su propia celda
        for i in range(n):
            dmin = min(((sites[i][0] - sites[j][0]) ** 2 + (sites[i][1] - sites[j][1]) ** 2)
                       for j in range(n) if j != i)
            weights[i] = min(weights[i], dmin)
        cells = _power_cells(sites, weights, boundary)
    return cells


def make_voronoi_chart(product_df, total: float, size_inches=(3.0, 2.7),
                       show_total_above: bool = True) -> bytes:
    """
    Treemap de Voronoi de participación por producto (áreas proporcionales).
    Retorna PNG bytes. Si show_total_above, el total se rotula arriba del gráfico.
    """
    labels, values, clrs = [], [], []
    for prod in PRODUCT_ORDER:
        v = float(product_df.get(prod, 0))
        if v > 0:
            labels.append(PRODUCT_DISPLAY_NAMES.get(prod, prod))
            values.append(v)
            clrs.append(hex_to_rgb(PRODUCT_COLORS[prod]))

    fig, ax = plt.subplots(figsize=size_inches)
    fig.patch.set_alpha(0)

    if values:
        cells = _voronoi_treemap_cells(values)
        tot_area = sum(_poly_area(c) for c in cells) or 1.0
        for label, val, rgb, cell in zip(labels, values, clrs, cells):
            if len(cell) < 3:
                continue
            ax.add_patch(mpatches.Polygon(cell, closed=True, facecolor=rgb,
                                          edgecolor="white", linewidth=1.6))
            cx, cy = _poly_centroid(cell)
            frac = _poly_area(cell) / tot_area
            # Color de texto según luminancia del fondo (contraste)
            lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            txtcolor = "white" if lum < 0.55 else "#3A3A3A"
            if frac >= 0.05:
                ax.text(cx, cy + 0.07, label, ha="center", va="center",
                        fontsize=7.5, fontweight="bold", color=txtcolor)
                ax.text(cx, cy - 0.09, f"{frac * 100:.0f}%", ha="center",
                        va="center", fontsize=8.5, fontweight="bold", color=txtcolor)
            else:
                ax.text(cx, cy, f"{frac * 100:.0f}%", ha="center", va="center",
                        fontsize=6.5, fontweight="bold", color=txtcolor)
    else:
        ax.text(0, 0, "Sin datos", ha="center", va="center", fontsize=9,
                color=hex_to_rgb(SECTION_SUBTITLE))

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.08, 1.22 if show_total_above else 1.08)
    ax.set_aspect("equal")
    ax.axis("off")
    if show_total_above:
        ax.text(0, 1.15, fmt_currency(total), ha="center", va="center",
                fontsize=11, fontweight="bold", color=hex_to_rgb(SECTION_TITLE))
        ax.text(0, 1.03, "Total de ventas", ha="center", va="center",
                fontsize=7, color=hex_to_rgb(SECTION_SUBTITLE))
    plt.tight_layout(pad=0.1)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="none", transparent=True)
    plt.close(fig)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Gráfica: Barras apiladas + línea (Storytelling with Data: SIN pie/dona)
# ---------------------------------------------------------------------------

def make_stacked_bar_line(
    piv_df: pd.DataFrame,
    labels: list,
    categories: list,
    color_map: dict,
    cat_display: dict,
    line_values: list,
    line_label: str = "Total",
    x_label: str = "",
    y_label: str = "$MXN (sin IVA)",
    title: str = "",
    size_inches=(7.5, 2.8),
    separador_idx: Optional[int] = None,  # índice donde poner línea de año
) -> bytes:
    """
    Barras apiladas (por categoría) + línea roja de total/plan.
    Retorna PNG bytes.
    """
    fig, ax = plt.subplots(figsize=size_inches)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    n = len(labels)
    x = np.arange(n)
    bottom = np.zeros(n)

    for cat in categories:
        if cat not in piv_df.columns:
            continue
        vals = piv_df[cat].values.astype(float) / 1000  # miles
        c    = hex_to_rgb(color_map.get(cat, "#AAAAAA"))
        ax.bar(x, vals, bottom=bottom, color=c,
               label=cat_display.get(cat, cat), width=0.65)
        bottom += vals

    # Línea roja
    if line_values:
        lv = [v / 1000 for v in line_values]
        ax.plot(x, lv, color=hex_to_rgb(CHART_PLAN_LINE),
                linewidth=1.8, marker="o", markersize=3.5,
                label=line_label, zorder=5)
        # Etiquetas de la línea
        for xi, yv in zip(x, lv):
            if yv > 0:
                ax.text(xi, yv + max(lv) * 0.04, f"{yv:.0f}k",
                        ha="center", va="bottom", fontsize=5.5,
                        color=hex_to_rgb(CHART_PLAN_LINE))

    # Separador de año (punteado vertical)
    if separador_idx is not None and 0 < separador_idx < n:
        ax.axvline(x=separador_idx - 0.5, color="#999999", linestyle="--",
                   linewidth=1, alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6, rotation=35, ha="right")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}k"))
    ax.tick_params(axis="y", labelsize=6)
    ax.set_xlabel(x_label, fontsize=7)
    ax.set_ylabel(y_label, fontsize=7)
    ax.grid(axis="y", color=hex_to_rgb(CHART_GRID), linewidth=0.5, alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(0.01, 1.02, "Las ventas no incluyen IVA, IEPS",
            transform=ax.transAxes, fontsize=5, color="#888888")

    # Leyenda compacta
    handles, leg_labels = ax.get_legend_handles_labels()
    ax.legend(handles, leg_labels, fontsize=5.5, ncol=min(4, len(handles)),
              loc="upper left", framealpha=0.7, handlelength=1.2)

    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def make_combo_chart(
    semanas: list,
    series_dict: dict,  # {nombre: [valores]}
    color_map: dict,
    display_names: dict,
    plan_values: list,
    total_values: list,
    ly_values: list,
    title: str = "",
    y_label: str = "$MXN miles (sin IVA)",
    size_inches=(7.5, 2.5),
) -> bytes:
    """
    Gráfica combo: área año pasado + barras apiladas por categoría + línea plan.
    Fiel a Design.md §6.3 — reemplaza donas en páginas de tendencia.
    """
    fig, ax = plt.subplots(figsize=size_inches)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    n = len(semanas)
    x = np.arange(n)

    # Área "Año Pasado"
    if ly_values and any(v > 0 for v in ly_values):
        lv = [v / 1000 for v in ly_values]
        ax.fill_between(x, lv, alpha=0.55,
                        color=hex_to_rgb(CHART_LASTYEAR_AREA), label="Año Pasado")

    # Barras apiladas
    bottom = np.zeros(n)
    categories = [k for k in series_dict if k in color_map]
    for cat in categories:
        vals = np.array(series_dict[cat]) / 1000
        c    = hex_to_rgb(color_map.get(cat, "#AAAAAA"))
        ax.bar(x, vals, bottom=bottom, color=c,
               label=display_names.get(cat, cat), width=0.65, zorder=3)
        bottom += vals

    # Línea plan
    if plan_values and any(v > 0 for v in plan_values):
        pv = [v / 1000 for v in plan_values]
        ax.plot(x, pv, color=hex_to_rgb(CHART_PLAN_LINE),
                linewidth=1.8, marker="o", markersize=3, label="Plan", zorder=6)

    ax.set_xticks(x)
    ax.set_xticklabels(semanas, fontsize=6, rotation=35, ha="right")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}k"))
    ax.tick_params(axis="y", labelsize=6)
    ax.grid(axis="y", color=hex_to_rgb(CHART_GRID), linewidth=0.5, alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(0.01, 1.02, "Las ventas no incluyen IVA, IEPS",
            transform=ax.transAxes, fontsize=5, color="#888888")

    handles, leg_labels = ax.get_legend_handles_labels()
    ax.legend(handles, leg_labels, fontsize=5.5, ncol=min(5, len(handles)),
              loc="upper left", framealpha=0.7, handlelength=1.2)

    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def make_bar_chart_regional(df_regional: pd.DataFrame, size_inches=(7, 2.5)) -> bytes:
    """Gráfica de barras horizontales para análisis regional (top 15 estados)."""
    df = df_regional.head(15).sort_values("ventas", ascending=True)
    fig, ax = plt.subplots(figsize=size_inches)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.barh(df["region_o_estado"], df["ventas"] / 1000,
                   color=hex_to_rgb(BRAND_MAROON), alpha=0.85)
    for bar, val in zip(bars, df["ventas"].values):
        ax.text(bar.get_width() + max(df["ventas"].values / 1000) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                fmt_currency(val), va="center", fontsize=6,
                color=hex_to_rgb(CHART_LABEL))

    ax.set_xlabel("$MXN miles (sin IVA)", fontsize=7)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}k"))
    ax.tick_params(axis="y", labelsize=6)
    ax.tick_params(axis="x", labelsize=6)
    ax.grid(axis="x", color=hex_to_rgb(CHART_GRID), linewidth=0.5, alpha=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Clase constructora de páginas PDF
# ---------------------------------------------------------------------------

class LocoReportePDF:
    """
    Genera el PDF completo del reporte semanal de Loco Tequila.
    """

    def __init__(
        self,
        processor: LocoDataProcessor,
        output_path: str,
        logo_path: Optional[str] = None,
    ):
        self.proc        = processor
        self.output_path = output_path
        self.logo_path   = logo_path
        self.semana      = processor.semana
        self.anio        = processor.anio
        self._page_num   = 0

        # Tamaño A4 landscape
        self.PAGE_W = PAGE_WIDTH_PT
        self.PAGE_H = PAGE_HEIGHT_PT
        self.MARGIN = MARGIN_PT
        self.CONTENT_W = self.PAGE_W - 2 * self.MARGIN
        self.CONTENT_H = self.PAGE_H - HEADER_HEIGHT_PT - FOOTER_HEIGHT_PT - 2 * self.MARGIN

        # Pre-cargar logo UNA SOLA VEZ (evita procesar el SVG 30+ veces)
        self._logo_bytes   = None  # PNG bytes (si la conversion funcionó)
        self._logo_drawing = None  # rlg Drawing (fallback vector)
        self._logo_ready   = False
        self._init_logo()

    def _init_logo(self):
        """Procesa el logo una sola vez al crear la clase."""
        if not self.logo_path or not os.path.exists(self.logo_path):
            self._logo_ready = True
            return

        # Intento 1: PNG (necesita Cairo DLL o Pillow backend)
        png_path = get_logo_for_pdf(self.logo_path)
        if png_path and os.path.exists(png_path):
            try:
                with open(png_path, "rb") as f:
                    self._logo_bytes = f.read()
                print(f"[LOGO] PNG cargado: {png_path}")
                self._logo_ready = True
                return
            except Exception:
                pass

        # Intento 2: Drawing vectorial via svglib (no necesita Cairo DLL)
        try:
            white_path = SVG_WHITE
            if not os.path.exists(white_path):
                make_white_svg(self.logo_path, white_path)
            drawing = get_logo_drawing_for_pdf(white_path)
            if drawing is not None:
                self._logo_drawing = drawing
                print("[LOGO] Drawing SVG vectorial listo (renderPDF).")
        except Exception as e:
            print(f"[LOGO] Drawing fallido: {e}")

        self._logo_ready = True

    # ------------------------------------------------------------------
    # Generador principal
    # ------------------------------------------------------------------

    def generate(self):
        from reportlab.pdfgen import canvas as rl_canvas

        c = rl_canvas.Canvas(self.output_path,
                              pagesize=(self.PAGE_W, self.PAGE_H))
        c.setTitle(f"Reporte Loco Tequila — Semana {self.semana:02d} {self.anio}")
        c.setAuthor("Loco Tequila — Dirección de Finanzas")

        # Página 1: Resumen Anual (incluye el Voronoi/dona anual)
        self._page_num += 1
        self._draw_page_resumen(c, mode="anual")
        c.showPage()

        # Detalle Canal → Cliente → Producto ANUAL (justo tras el resumen anual)
        self._draw_pages_canal_cliente_producto(c, mode="anual", top_n=10)

        # Página siguiente: Resumen Semanal (incluye el Voronoi/dona semanal)
        self._page_num += 1
        self._draw_page_resumen(c, mode="semanal")
        c.showPage()

        # Detalle Canal → Cliente → Producto SEMANAL (justo tras el resumen semanal)
        self._draw_pages_canal_cliente_producto(c, mode="semanal", top_n=10)

        # Página 3: Semáforo de Comparativos (WoW / YoY / YTD / Rolling 52)
        self._page_num += 1
        self._draw_page_comparativos(c)
        c.showPage()

        # Página 4: Histórico mensual (gráfica)
        self._page_num += 1
        self._draw_page_historico(c)
        c.showPage()

        # Página: Histórico mensual — Tabla por Producto (tras la gráfica mensual)
        self._draw_page_historico_tabla(c)

        # Páginas 4-5: Totales por Producto
        for mode in ["semanal", "anual"]:
            self._page_num += 1
            self._draw_page_totales(c, group_by="producto", mode=mode)
            c.showPage()

        # Páginas 6-7: Totales por Canal
        for mode in ["semanal", "anual"]:
            self._page_num += 1
            self._draw_page_totales(c, group_by="canal", mode=mode)
            c.showPage()

        # Páginas 8-19: SKUs individuales
        for prod in PRODUCT_ORDER:
            for mode in ["semanal", "anual"]:
                self._page_num += 1
                self._draw_page_sku(c, producto=prod, mode=mode)
                c.showPage()

        # Páginas 20-31: Clientes top
        top_clientes = self.proc.get_top_clientes(mode="anual")
        for cliente in top_clientes:
            for mode in ["semanal", "anual"]:
                self._page_num += 1
                self._draw_page_cliente(c, cliente=cliente, mode=mode)
                c.showPage()

        c.save()
        print(f"[PDF] Guardado: {self.output_path}")

    # ------------------------------------------------------------------
    # Header y footer comunes
    # ------------------------------------------------------------------

    def _draw_header(self, c, subtitulo: str = ""):
        """Banda maroon con título + subtítulo + logo."""
        w, h = self.PAGE_W, self.PAGE_H
        # Fondo maroon
        c.setFillColor(MAROON_RL)
        c.rect(0, h - HEADER_HEIGHT_PT, w, HEADER_HEIGHT_PT, fill=1, stroke=0)
        # Sombra inferior
        c.setFillColor(rl_color(BRAND_MAROON_DEEP))
        c.rect(0, h - HEADER_HEIGHT_PT - 3, w, 3, fill=1, stroke=0)

        # Título
        c.setFillColor(WHITE_RL)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(self.MARGIN, h - HEADER_HEIGHT_PT + 26,
                     "Ventas y Margen")

        # Subtítulo
        c.setFont("Helvetica", 11)
        semana_label = f"De la Semana {self.semana:02d}-{self.anio}"
        if subtitulo:
            semana_label += f"  |  {subtitulo}"
        c.drawString(self.MARGIN, h - HEADER_HEIGHT_PT + 10, semana_label)

        # Logo (si existe)
        if self.logo_path and os.path.exists(self.logo_path):
            logo_h = HEADER_HEIGHT_PT - 10
            logo_w = logo_h * 2.5
            logo_x = w - self.MARGIN - logo_w
            logo_y = h - HEADER_HEIGHT_PT + 5

            drawn = False

            # Intento 1: PNG pre-cargado
            if self._logo_bytes:
                try:
                    from reportlab.lib.utils import ImageReader
                    img_reader = ImageReader(io.BytesIO(self._logo_bytes))
                    c.drawImage(img_reader, logo_x, logo_y,
                                width=logo_w, height=logo_h - 5,
                                preserveAspectRatio=True, mask="auto")
                    drawn = True
                except Exception:
                    pass

            # Intento 2: Drawing vectorial pre-cargado
            if not drawn and self._logo_drawing:
                drawn = self._draw_logo_vector(c, logo_x, logo_y, logo_w, logo_h - 5)

            # Fallback: texto LOCO TEQUILA
            if not drawn:
                c.setFont("Helvetica-Bold", 14)
                c.setFillColor(WHITE_RL)
                c.drawRightString(w - self.MARGIN, h - HEADER_HEIGHT_PT + 26, "LOCO")
                c.setFont("Helvetica", 8)
                c.drawRightString(w - self.MARGIN, h - HEADER_HEIGHT_PT + 14, "TEQUILA")
        else:
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(WHITE_RL)
            c.drawRightString(w - self.MARGIN, h - HEADER_HEIGHT_PT + 26, "LOCO")
            c.setFont("Helvetica", 8)
            c.drawRightString(w - self.MARGIN, h - HEADER_HEIGHT_PT + 14, "TEQUILA")

    def _load_logo(self) -> Optional[bytes]:
        """
        Carga el logo en version blanca (PNG) usando logo_processor.
        Pipeline: SVG original -> SVG blanco -> PNG (cairosvg o svglib).
        Si no se puede convertir a PNG, retorna None (se usara renderPDF.draw).
        """
        if not self.logo_path:
            return None
        ext = os.path.splitext(self.logo_path)[1].lower()
        if ext == ".png":
            with open(self.logo_path, "rb") as f:
                return f.read()
        if ext == ".svg":
            png_path = get_logo_for_pdf(self.logo_path)
            if png_path and os.path.exists(png_path):
                with open(png_path, "rb") as f:
                    return f.read()
        return None

    def _draw_logo_vector(self, c, x: float, y: float, w: float, h: float) -> bool:
        """
        Dibuja el SVG blanco pre-cargado (self._logo_drawing) con renderPDF.
        No re-procesa el SVG — usa el Drawing cacheado en __init__.
        """
        if self._logo_drawing is None:
            return False
        try:
            from reportlab.graphics import renderPDF
            import copy
            # Clonar el drawing para escalar sin mutar el objeto cacheado
            drawing = copy.deepcopy(self._logo_drawing)
            sx = w / drawing.width if drawing.width else 1
            sy = h / drawing.height if drawing.height else 1
            scale = min(sx, sy)
            drawing.width  = drawing.width * scale
            drawing.height = drawing.height * scale
            drawing.transform = (scale, 0, 0, scale, 0, 0)
            renderPDF.draw(drawing, c, x, y)
            return True
        except Exception as e:
            print(f"[LOGO] renderPDF.draw error: {e}")
            return False

    def _draw_footer(self, c):
        """Línea gris + número de página."""
        y_line = FOOTER_HEIGHT_PT
        c.setStrokeColor(RULE_RL)
        c.setLineWidth(0.5)
        c.line(self.MARGIN, y_line, self.PAGE_W - self.MARGIN, y_line)
        c.setFillColor(GREY_RL)
        c.setFont("Helvetica", 7)
        c.drawRightString(self.PAGE_W - self.MARGIN, 5, str(self._page_num))

    def _body_top(self) -> float:
        """Y donde empieza el cuerpo (bajo la banda maroon)."""
        return self.PAGE_H - HEADER_HEIGHT_PT - 4 - self.MARGIN

    # ------------------------------------------------------------------
    # Utilidades de dibujo
    # ------------------------------------------------------------------

    def _draw_section_title(self, c, title: str, subtitle: str, y: float) -> float:
        """Dibuja título + subtítulo de sección. Retorna nueva Y."""
        c.setFillColor(MAROON_RL)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(self.MARGIN, y, title)
        y -= 14
        c.setFillColor(GREY_RL)
        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN, y, subtitle)
        return y - 10

    def _draw_chart_title_bar(self, c, title: str, y: float, w: Optional[float] = None) -> float:
        """Barra maroon con texto de título de gráfica. Retorna nueva Y."""
        bw = w or self.CONTENT_W
        bar_h = 14
        c.setFillColor(MAROON_RL)
        c.rect(self.MARGIN, y - bar_h, bw, bar_h, fill=1, stroke=0)
        c.setFillColor(WHITE_RL)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(self.MARGIN + 4, y - bar_h + 4, title)
        return y - bar_h - 2

    def _embed_png(self, c, png_bytes: bytes, x: float, y: float,
                   w: float, h: float):
        """Embebe imagen PNG en el canvas en posición (x, y_bottom) con tamaño w×h."""
        from reportlab.lib.utils import ImageReader
        img = ImageReader(io.BytesIO(png_bytes))
        c.drawImage(img, x, y, width=w, height=h,
                    preserveAspectRatio=True, mask="auto")

    # ------------------------------------------------------------------
    # Tabla estilo Design.md
    # ------------------------------------------------------------------

    def _build_rl_table(
        self,
        data: list,          # lista de listas de strings
        col_widths: list,
        highlight_rows: list = None,    # índices de filas a highlight
        highlight_cols: list = None,    # índices de columnas a highlight
        neg_cells: list = None,         # list of (row, col) para texto rojo
        font_size: int = 7,
        repeat_rows: int = 0,           # nº de filas de encabezado a repetir al partir
        label_col: int = 0,             # columna de categoría (alineación especial)
        label_align: str = "LEFT",      # alineación de la columna de categoría
        sep_before_cols: list = None,   # columnas con línea vertical de separación
    ) -> Table:
        """Construye una Table de ReportLab con el estilo del reporte."""
        style_cmds = [
            ("FONTNAME",  (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",  (0, 0), (-1, -1), font_size),
            ("FONTNAME",  (0, 1), (-1, -1), "Helvetica"),
            # Por defecto todo a la derecha; la columna de categoría se alinea
            # según label_align (permite ponerla al centro en las comparativas).
            ("ALIGN",     (0, 0), (-1, -1), "RIGHT"),
            ("ALIGN",     (label_col, 0), (label_col, -1), label_align),
            ("VALIGN",    (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",      (0, 0), (-1, -1), 0.25, colors.HexColor(RULE_LINE)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
            # Encabezado
            ("BACKGROUND", (0, 0), (-1, 0), MAROON_RL),
            ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE_RL),
        ]

        # Categoría al centro (label_col != 0): resaltar en negrita el nombre
        if label_col != 0:
            style_cmds.append(("FONTNAME", (label_col, 1), (label_col, -1), "Helvetica-Bold"))

        # Separadores verticales de grupo (real | categoría | variaciones)
        if sep_before_cols:
            for ci in sep_before_cols:
                style_cmds.append(("LINEBEFORE", (ci, 0), (ci, -1), 0.8, MAROON_RL))

        # Filas resaltadas (Total, Ventas Netas)
        if highlight_rows:
            for ri in highlight_rows:
                style_cmds.append(("BACKGROUND", (0, ri), (-1, ri), CREAM_RL))
                style_cmds.append(("FONTNAME", (0, ri), (-1, ri), "Helvetica-Bold"))

        # Columnas resaltadas (Año Actual)
        if highlight_cols:
            for ci in highlight_cols:
                style_cmds.append(("BACKGROUND", (ci, 1), (ci, -1), CREAM_RL))
                style_cmds.append(("FONTNAME", (ci, 1), (ci, -1), "Helvetica-Bold"))

        # Celdas negativas en rojo
        if neg_cells:
            for (ri, ci) in neg_cells:
                style_cmds.append(("TEXTCOLOR", (ci, ri), (ci, ri), NEG_RL))

        tbl = Table(data, colWidths=col_widths, repeatRows=repeat_rows)
        tbl.setStyle(TableStyle(style_cmds))
        return tbl

    # ------------------------------------------------------------------
    # Página 1-2: Resumen (Dona + Tabla Canal×Producto + Detalle clientes)
    # ------------------------------------------------------------------

    def _draw_page_resumen(self, c, mode: str = "anual"):
        subtitle = "Resumen Anual" if mode == "anual" else "Resumen Semanal"
        self._draw_header(c, subtitulo=subtitle)
        self._draw_footer(c)

        y = self._body_top()
        y = self._draw_section_title(c, "Ventas Totales",
                                     f"Por Producto · Por Canal — {mode.capitalize()}",
                                     y)

        # --- Área izquierda: Dona (≤3 productos) o Treemap de Voronoi (>3) ---
        matriz = self.proc.get_matriz_canal_producto(mode=mode)
        total_row = matriz.loc["Total"] if "Total" in matriz.index else pd.Series(dtype=float)
        total_ventas = float(total_row.get("Total", 0))
        product_totals = {p: float(total_row.get(p, 0)) for p in PRODUCT_ORDER}

        # Con 3 o menos productos la dona es clara (total al centro); con más,
        # el treemap de Voronoi es más legible (total arriba del gráfico).
        n_productos = sum(1 for p in PRODUCT_ORDER if product_totals.get(p, 0) > 0)

        dona_w_pt = 190
        dona_h_pt = 160
        if n_productos <= 3:
            dona_png = make_donut_chart(product_totals, total_ventas,
                                        size_inches=(3.0, 2.5))
        else:
            dona_png = make_voronoi_chart(product_totals, total_ventas,
                                          size_inches=(3.0, 2.7),
                                          show_total_above=True)
        dona_y = y - dona_h_pt
        self._embed_png(c, dona_png, self.MARGIN, dona_y, dona_w_pt, dona_h_pt)

        # Leyenda de la dona (a la derecha de la dona)
        ley_x = self.MARGIN + dona_w_pt + 8
        ley_y = y - 12
        for prod in PRODUCT_ORDER:
            val = product_totals.get(prod, 0)
            if total_ventas > 0:
                pct = val / total_ventas * 100
            else:
                pct = 0
            color_hex = PRODUCT_COLORS.get(prod, "#999999")
            c.setFillColor(rl_color(color_hex))
            c.rect(ley_x, ley_y - 3, 8, 8, fill=1, stroke=0)
            c.setFillColor(BLACK_RL)
            c.setFont("Helvetica", 7)
            disp = PRODUCT_DISPLAY_NAMES.get(prod, prod)
            c.drawString(ley_x + 11, ley_y, disp)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(ley_x + 90, ley_y, fmt_currency(val))
            # Píldora de porcentaje
            pill_x = ley_x + 135
            c.setFillColor(rl_color("#F6E2E2"))
            c.roundRect(pill_x, ley_y - 2, 32, 10, 3, fill=1, stroke=0)
            c.setFillColor(rl_color("#9B1C31"))
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(pill_x + 16, ley_y + 1, f"{pct:.0f}%")
            ley_y -= 14

        # --- Tabla resumen Canal × Producto ---
        tbl_x = self.MARGIN + dona_w_pt + 8 + 180
        tbl_w = self.PAGE_W - tbl_x - self.MARGIN
        # Construir data
        header = ["Canal"] + [PRODUCT_DISPLAY_NAMES.get(p, p)[:8] for p in PRODUCT_ORDER] + ["Total"]
        rows = [header]
        neg_cells = []
        hi_rows = []
        for ri, idx in enumerate(list(matriz.index)):
            row_data = matriz.loc[idx]
            total_val = row_data.get("Total", 0)
            pct_val = (total_val / total_ventas * 100) if total_ventas > 0 else 0
            row = [idx]
            for p in PRODUCT_ORDER:
                row.append(fmt_currency(row_data.get(p, 0)))
            row.append(f"{fmt_currency(total_val)} ({pct_val:.0f}%)")
            rows.append(row)
            if idx == "Total":
                hi_rows.append(ri + 1)

        n_cols = len(header)
        col_w  = tbl_w / n_cols
        col_widths = [col_w * 1.6] + [col_w * 0.9] * (n_cols - 2) + [col_w * 1.3]

        tbl = self._build_rl_table(rows, col_widths,
                                    highlight_rows=hi_rows,
                                    highlight_cols=[n_cols - 1],
                                    font_size=6)
        tbl.wrapOn(c, tbl_w, 200)
        tbl_h = tbl._height
        tbl.drawOn(c, tbl_x, y - tbl_h)

        # --- Detalle por cliente (columna izquierda debajo de dona) ---
        det_y = dona_y - 12
        c.setFillColor(MAROON_RL)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.MARGIN, det_y, "Top Clientes")
        det_y -= 10

        top_clientes = self.proc.get_top_clientes(mode=mode)
        det_df = self.proc.get_detalle_clientes(top_clientes, mode=mode)

        if not det_df.empty:
            det_header = ["Cliente"] + [PRODUCT_DISPLAY_NAMES.get(p, p)[:7] for p in PRODUCT_ORDER] + ["Total"]
            det_rows   = [det_header]
            det_hi     = []
            for ri, (idx, row_data) in enumerate(det_df.iterrows()):
                tv = row_data.get("Total", 0)
                row = [str(idx)[:18]] + [fmt_currency(row_data.get(p, 0)) for p in PRODUCT_ORDER]
                row.append(fmt_currency(tv))
                det_rows.append(row)

            det_w  = self.CONTENT_W * 0.62
            nc_det = len(det_header)
            cw_det = [det_w / nc_det * 1.5] + [det_w / nc_det * 0.85] * (nc_det - 2) + [det_w / nc_det * 1.1]
            tbl_det = self._build_rl_table(det_rows, cw_det, font_size=6)
            tbl_det.wrapOn(c, det_w, 200)
            th_det = tbl_det._height
            if det_y - th_det > FOOTER_HEIGHT_PT + 5:
                tbl_det.drawOn(c, self.MARGIN, det_y - th_det)

    # ------------------------------------------------------------------
    # Páginas: Detalle por Canal → Cliente → Producto (paginado)
    # ------------------------------------------------------------------

    # Secciones de canal a desglosar (título, canal_reporte, sub_canal).
    # Off Trade se abre en Tradicional / Moderno + un total combinado; los demás
    # canales se muestran completos.
    _CANAL_SECCIONES = [
        ("Off Trade — Canal Tradicional",           "Off Trade",                       "Tradicional"),
        ("Off Trade — Canal Moderno",               "Off Trade",                       "Moderno"),
        ("Total Off Trade (Tradicional + Moderno)", "Off Trade",                       None),
        ("Centros de Consumo (On Trade)",           "Centros de Consumo (On Trade)",   None),
        ("Venta Directa",                           "Venta Directa",                   None),
        ("Familia y Amigos",                        "Familia y Amigos",                None),
    ]

    def _draw_pages_canal_cliente_producto(self, c, mode: str = "anual",
                                           top_n: int = 10):
        """
        Renderiza (con paginación automática) el desglose Canal → Cliente →
        Producto. Cada sección de canal es una tabla clientes × productos con
        columna Total (con %) y filas de 'Ventas Netas' y 'Participación %'.
        Gestiona sus propias páginas (header/footer + showPage al final).
        """
        anio = self.anio
        sem = self.semana
        period_lbl = "Anual (YTD)" if mode == "anual" else f"Semanal · S{sem:02d}"
        subt = f"Canal · Cliente · Producto — {period_lbl}"

        prod_disp = [PRODUCT_DISPLAY_NAMES.get(p, p) for p in PRODUCT_ORDER]
        ncols = 1 + len(PRODUCT_ORDER) + 1
        cw = self.CONTENT_W
        col_widths = ([cw * 0.20] +
                      [cw * (0.66 / len(PRODUCT_ORDER))] * len(PRODUCT_ORDER) +
                      [cw * 0.14])

        min_bottom = FOOTER_HEIGHT_PT + self.MARGIN

        def _start_page():
            self._page_num += 1
            self._draw_header(c, subtitulo=subt)
            self._draw_footer(c)
            yy = self._body_top()
            yy = self._draw_section_title(
                c, "Ventas por Canal, Cliente y Producto",
                f"Detalle canal → cliente → producto · {period_lbl} · $MXN sin IVA", yy)
            return yy - 6

        y = _start_page()

        for title, canal, sub in self._CANAL_SECCIONES:
            data = self.proc.get_cliente_producto_por_canal(
                canal, sub_canal=sub, mode=mode, top_n=top_n)
            if not data:
                continue

            piv = data["pivot"]
            total_sec = data["total"] or 1.0
            prod_tot = data["prod_tot"]

            # Encabezado + filas de clientes
            header = ["Cliente"] + prod_disp + ["Total"]
            rows = [header]
            for cliente, prow in piv.iterrows():
                tv = float(prow["Total"])
                pct = tv / total_sec * 100 if total_sec else 0
                fila = [str(cliente)[:24]]
                fila += [fmt_currency(float(prow[p])) for p in PRODUCT_ORDER]
                fila.append(f"{fmt_currency(tv)} ({pct:.0f}%)")
                rows.append(fila)

            # Fila Ventas Netas
            rows.append([f"Ventas Netas {anio}"] +
                        [fmt_currency(prod_tot[p]) for p in PRODUCT_ORDER] +
                        [fmt_currency(total_sec)])
            # Fila Participación %
            rows.append(["Participación %"] +
                        [f"{(prod_tot[p] / total_sec * 100 if total_sec else 0):.0f}%"
                         for p in PRODUCT_ORDER] +
                        ["100%"])

            n = len(rows)
            tbl = self._build_rl_table(
                rows, col_widths,
                highlight_rows=[n - 2, n - 1],
                highlight_cols=[ncols - 1],
                font_size=6,
                repeat_rows=1)  # repite encabezado si la tabla se parte

            # Título de la sección: necesita espacio para el título + al menos
            # el encabezado y unas filas; si no, salto de página.
            tbl.wrapOn(c, cw, 3000)
            if y - (14 + 60) < min_bottom:
                c.showPage()
                y = _start_page()

            c.setFillColor(MAROON_RL)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(self.MARGIN, y, title)
            y -= 14

            # Dibuja la tabla partiéndola entre páginas para llenar el espacio
            while tbl is not None:
                avail = y - min_bottom
                w_, h_ = tbl.wrap(cw, avail)
                if h_ <= avail:
                    tbl.drawOn(c, self.MARGIN, y - h_)
                    y -= h_ + 12
                    break
                parts = tbl.split(cw, avail)
                if not parts:
                    # No cabe ni el encabezado: nueva página y reintenta
                    c.showPage()
                    y = _start_page()
                    continue
                first = parts[0]
                fw, fh = first.wrap(cw, avail)
                first.drawOn(c, self.MARGIN, y - fh)
                tbl = parts[1] if len(parts) > 1 else None
                c.showPage()
                y = _start_page()

        c.showPage()

    # ------------------------------------------------------------------
    # Página: Histórico mensual — Tabla por Producto (basada en la gráfica)
    # ------------------------------------------------------------------

    def _draw_page_historico_tabla(self, c):
        """
        Tabla con el mismo detalle de la gráfica de histórico mensual: meses en
        filas × productos en columnas + Total. Va justo después de la gráfica
        mensual. Usa las mismas etiquetas de mes que la gráfica. Se paginta si
        hay muchos meses.
        """
        subt = "Histórico Mensual — Tabla por Producto"
        hist = self.proc.get_historico_mensual()

        prod_disp = [PRODUCT_DISPLAY_NAMES.get(p, p) for p in PRODUCT_ORDER]
        header = ["Mes"] + prod_disp + ["Total"]
        ncols = len(header)

        rows = [header]
        for _, hrow in hist.iterrows():
            fila = [str(hrow.get("label", ""))]
            fila += [fmt_currency(float(hrow.get(p, 0))) for p in PRODUCT_ORDER]
            fila.append(fmt_currency(float(hrow.get("Total", 0))))
            rows.append(fila)

        cw = self.CONTENT_W
        col_widths = ([cw * 0.12] +
                      [cw * (0.76 / len(PRODUCT_ORDER))] * len(PRODUCT_ORDER) +
                      [cw * 0.12])
        min_bottom = FOOTER_HEIGHT_PT + self.MARGIN

        def _start_page():
            self._page_num += 1
            self._draw_header(c, subtitulo=subt)
            self._draw_footer(c)
            yy = self._body_top()
            yy = self._draw_section_title(
                c, "Histórico de Ventas Mensuales — Tabla por Producto",
                "Ventas netas mensuales por producto · $MXN sin IVA", yy)
            return yy - 6

        y = _start_page()
        tbl = self._build_rl_table(
            rows, col_widths,
            highlight_cols=[ncols - 1],
            font_size=7,
            repeat_rows=1)

        while tbl is not None:
            avail = y - min_bottom
            w_, h_ = tbl.wrap(cw, avail)
            if h_ <= avail:
                tbl.drawOn(c, self.MARGIN, y - h_)
                break
            parts = tbl.split(cw, avail)
            if not parts:
                c.showPage()
                y = _start_page()
                continue
            first = parts[0]
            fw, fh = first.wrap(cw, avail)
            first.drawOn(c, self.MARGIN, y - fh)
            tbl = parts[1] if len(parts) > 1 else None
            c.showPage()
            y = _start_page()

        c.showPage()

    # ------------------------------------------------------------------
    # Página 3: Semáforo de Comparativos (4 ventanas estándar)
    # ------------------------------------------------------------------

    def _draw_page_comparativos(self, c):
        """Página dedicada a las 4 ventanas comparativas: WoW, YoY semanal, YTD vs LY, Rolling 52."""
        self._draw_header(c, subtitulo="Comparativo de Periodos")
        self._draw_footer(c)

        y = self._body_top()
        sem = self.proc.semana
        anio = self.proc.anio
        ly = anio - 1
        r = self.proc.get_resumen_ejecutivo()

        y = self._draw_section_title(
            c, "Semáforo de Comparativos",
            f"Semana {sem:02d} · {anio} — Ventas sin IVA | Ventanas: WoW · YoY Semanal · YTD vs LY · Rolling 52",
            y)

        # --- Datos de cada bloque ---
        sem_ant = sem - 1 if sem > 1 else 52
        sem_ant_anio = anio if sem > 1 else ly

        bloques = [
            {
                "titulo": f"A — Semana a Semana (WoW)",
                "sub": f"S{sem:02d}-{anio} vs S{sem_ant:02d}-{sem_ant_anio}",
                "actual": r["actual"]["ventas_netas"],
                "anterior": r["actual"]["ventas_netas"] - r["vs_semana_anterior"]["abs"],
                "var_abs": r["vs_semana_anterior"]["abs"],
                "var_pct": r["vs_semana_anterior"]["pct"],
                "label_a": f"S{sem:02d}-{anio}",
                "label_b": f"S{sem_ant:02d}-{sem_ant_anio}",
                "extra": f"Botellas: {r['actual'].get('botellas', 0):,.0f}   Ticket: ${r['actual'].get('ticket_promedio', 0):,.2f}",
            },
            {
                "titulo": f"B — Mismo Período Año Anterior (YoY Semanal)",
                "sub": f"S{sem:02d}-{anio} vs S{sem:02d}-{ly}",
                "actual": r["actual"]["ventas_netas"],
                "anterior": r["actual"]["ventas_netas"] - r["vs_anio_anterior"]["abs"],
                "var_abs": r["vs_anio_anterior"]["abs"],
                "var_pct": r["vs_anio_anterior"]["pct"],
                "label_a": f"S{sem:02d}-{anio}",
                "label_b": f"S{sem:02d}-{ly}",
                "extra": None,
            },
            {
                "titulo": f"C — Acumulado del Año (YTD vs LY)",
                "sub": f"YTD {anio} vs YTD {ly} (S01–S{sem:02d})",
                "actual": r["ytd_actual"]["ventas_netas"],
                "anterior": r["ytd_actual"]["ventas_netas"] - r["ytd_vs_ly"]["abs"],
                "var_abs": r["ytd_vs_ly"]["abs"],
                "var_pct": r["ytd_vs_ly"]["pct"],
                "label_a": f"YTD {anio}",
                "label_b": f"YTD {ly}",
                "extra": None,
            },
        ]

        # Rolling 52 (condicional)
        rolling = self.proc.get_rolling_52()
        if rolling:
            bloques.append({
                "titulo": f"D — Rolling 52 Semanas",
                "sub": f"{rolling['semanas_incluidas']} sem con datos",
                "actual": rolling["ventas_rolling"],
                "anterior": rolling["ventas_rolling_ly"],
                "var_abs": rolling["var_abs"],
                "var_pct": rolling["var_pct"],
                "label_a": rolling["label_a"],
                "label_b": rolling["label_b"],
                "extra": None,
            })

        # --- Dibujar cada bloque como tabla ---
        bloque_h = 62  # altura fija por bloque
        for bloque in bloques:
            # Título del bloque
            c.setFillColor(MAROON_RL)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(self.MARGIN, y, bloque["titulo"])
            c.setFillColor(GREY_RL)
            c.setFont("Helvetica", 8)
            c.drawString(self.MARGIN, y - 12, bloque["sub"])

            # Tabla de valores
            actual   = bloque["actual"]
            anterior = bloque["anterior"]
            var_abs  = bloque["var_abs"]
            var_pct  = bloque["var_pct"]
            tendencia = "▲" if var_abs >= 0 else "▼"
            color_var = POS_VALUE if var_abs >= 0 else NEG_VALUE

            # Lectura narrativa automática
            if var_pct < -10:
                lectura = "Atención: caída relevante. Revisar causa raíz."
            elif var_pct < 0:
                lectura = "Ligera baja. Monitorear."
            elif var_pct < 5:
                lectura = "Desempeño estable."
            elif var_pct < 15:
                lectura = "Crecimiento sólido — sostener estrategia."
            else:
                lectura = "Crecimiento fuerte — identificar driver."

            header = [bloque["label_a"], bloque["label_b"],
                      "Variación $", "Variación %", "Tend.", "Lectura"]
            row1 = [
                fmt_currency(actual),
                fmt_currency(anterior),
                fmt_currency(var_abs),
                fmt_pct(var_pct),
                tendencia,
                lectura,
            ]
            rows = [header, row1]

            cw = self.CONTENT_W
            col_widths = [cw*0.17, cw*0.17, cw*0.14, cw*0.10, cw*0.06, cw*0.36]

            neg_cells = []
            if var_abs < 0:
                neg_cells = [(1, 2), (1, 3)]

            tbl = self._build_rl_table(rows, col_widths,
                                       highlight_cols=[0],
                                       neg_cells=neg_cells,
                                       font_size=7)
            tbl.wrapOn(c, cw, 60)
            th = tbl._height
            tbl.drawOn(c, self.MARGIN, y - 18 - th)

            # Poner tendencia en color
            c.setFillColor(rl_color(color_var))
            c.setFont("Helvetica-Bold", 11)
            # (la flecha de tendencia ya está en la tabla, no necesitamos redibujarlo)

            if bloque["extra"]:
                c.setFillColor(GREY_RL)
                c.setFont("Helvetica-Oblique", 7)
                c.drawString(self.MARGIN, y - 20 - th - 6, bloque["extra"])
                y -= (th + 38)
            else:
                y -= (th + 30)

            if y < FOOTER_HEIGHT_PT + 60:
                break  # no cabe más en esta página

    # ------------------------------------------------------------------
    # Página 4: Histórico mensual
    # ------------------------------------------------------------------

    def _draw_page_historico(self, c):
        self._draw_header(c, subtitulo="Histórico Mensual")
        self._draw_footer(c)

        y = self._body_top()
        y = self._draw_section_title(c, "Histórico de Ventas Mensuales",
                                     "Barras apiladas por producto + Total", y)

        hist = self.proc.get_historico_mensual()
        if hist.empty:
            c.setFont("Helvetica", 10)
            c.drawString(self.MARGIN, y - 30, "Sin datos históricos disponibles.")
            return

        labels = hist["label"].tolist()
        # Separador entre años
        prev_year = None
        sep_idx = None
        for i, (ay, _) in enumerate(zip(hist["anio_num"], hist["mes"])):
            if prev_year is not None and ay != prev_year:
                sep_idx = i
            prev_year = ay

        series = {p: hist[p].tolist() if p in hist.columns else [0] * len(hist)
                  for p in PRODUCT_ORDER}
        total_vals = hist["Total"].tolist()

        y = self._draw_chart_title_bar(
            c, f"Ventas Netas Mensuales ($MXN miles sin IVA) — Total: {fmt_currency(sum(total_vals))}",
            y)

        chart_h = self.CONTENT_H * 0.72
        chart_png = make_stacked_bar_line(
            hist, labels, PRODUCT_ORDER,
            PRODUCT_COLORS, PRODUCT_DISPLAY_NAMES,
            total_vals, "Total Ventas",
            size_inches=(9.5, 3.5),
            separador_idx=sep_idx,
        )
        self._embed_png(c, chart_png, self.MARGIN, y - chart_h, self.CONTENT_W, chart_h)

    # ------------------------------------------------------------------
    # Páginas 4-7: Totales por Producto / Canal
    # ------------------------------------------------------------------

    def _draw_page_totales(self, c, group_by: str = "producto", mode: str = "semanal"):
        subtitle = (f"{'Por Producto' if group_by == 'producto' else 'Por Canal'} — "
                    f"{'Semanal' if mode == 'semanal' else 'Anual'}")
        self._draw_header(c, subtitulo=subtitle)
        self._draw_footer(c)

        y = self._body_top()
        y = self._draw_section_title(
            c,
            f"Ventas Totales {'Por Producto' if group_by == 'producto' else 'Por Canal'}",
            subtitle, y)

        # Tabla de KPIs
        y = self._draw_kpi_table(c, y, group_by=group_by, mode=mode)
        y -= 8

        # Gráfica Ventas $
        categories = PRODUCT_ORDER if group_by == "producto" else CANAL_ORDER
        color_map  = PRODUCT_COLORS if group_by == "producto" else CANAL_COLORS
        disp_names = PRODUCT_DISPLAY_NAMES if group_by == "producto" else {k: k for k in CANAL_ORDER}
        filtro     = None

        n_semanas = 12
        serie_v = self.proc.get_serie_semanal(n_semanas=n_semanas, group_by=group_by, filtro=filtro)
        serie_b = self.proc.get_serie_semanal_botellas(n_semanas=n_semanas, group_by=group_by, filtro=filtro)
        plan_df = self.proc.get_plan_semanal(n_semanas=n_semanas)
        semanas_labels = serie_v["label"].tolist() if not serie_v.empty else []

        # Año anterior (solo totales)
        ly, lyw = self.proc.anio - 1, self.proc.semana
        ly_serie = self.proc.get_serie_semanal(n_semanas=n_semanas)
        ly_totals = ly_serie["Total"].tolist() if "Total" in ly_serie.columns else []

        avail_h = y - FOOTER_HEIGHT_PT - self.MARGIN
        chart_h  = avail_h * 0.44

        if not serie_v.empty:
            plan_vals = plan_df["plan_venta_sin_impuestos"].tolist() if not plan_df.empty else []
            total_vals = serie_v["Total"].tolist() if "Total" in serie_v.columns else []
            series_dict = {}
            for cat in categories:
                if cat in serie_v.columns:
                    series_dict[cat] = serie_v[cat].tolist()

            y = self._draw_chart_title_bar(
                c, f"Ventas netas por semana ($MXN sin IVA) — Total: {fmt_currency(sum(total_vals))}",
                y)
            chart_png = make_combo_chart(
                semanas_labels, series_dict, color_map, disp_names,
                plan_vals, total_vals, ly_totals if len(ly_totals) == len(semanas_labels) else [],
                size_inches=(9.5, 2.8),
            )
            self._embed_png(c, chart_png, self.MARGIN, y - chart_h, self.CONTENT_W, chart_h)
            y -= chart_h + 8

        # Gráfica Botellas
        if not serie_b.empty:
            total_bot_vals = serie_b["Total"].tolist() if "Total" in serie_b.columns else []
            series_dict_b  = {cat: serie_b[cat].tolist() for cat in categories if cat in serie_b.columns}

            avail_h2 = y - FOOTER_HEIGHT_PT - self.MARGIN
            chart_h2  = avail_h2 * 0.85
            y = self._draw_chart_title_bar(
                c, f"Ventas volumen por semana (botellas) — Total: {fmt_int(sum(total_bot_vals))}",
                y)
            chart_png_b = make_combo_chart(
                semanas_labels, series_dict_b, color_map, disp_names,
                [], total_bot_vals, [],
                y_label="Botellas",
                size_inches=(9.5, 2.5),
            )
            self._embed_png(c, chart_png_b, self.MARGIN, y - chart_h2, self.CONTENT_W, chart_h2)

    def _draw_kpi_table(self, c, y: float, group_by: str = "producto", mode: str = "semanal") -> float:
        """Tabla de KPIs por grupo (producto o canal) para la semana/año actual."""
        proc = self.proc
        yw, ww = proc.anio, proc.semana
        py, pw = proc.anio - 1, proc.semana

        if mode == "semanal":
            df_cur  = proc._filter_period(yw, ww)
            df_prev = proc._filter_period(py, pw)
        else:
            df_cur  = proc._filter_ytd(yw, ww)
            df_prev = proc._filter_ytd(py, pw)

        group_col = "producto" if group_by == "producto" else "canal_norm"
        agg_cur  = df_cur.groupby(group_col)["venta_sin_impuestos"].sum()
        agg_prev = df_prev.groupby(group_col)["venta_sin_impuestos"].sum()

        cats = PRODUCT_ORDER if group_by == "producto" else CANAL_ORDER
        disp = PRODUCT_DISPLAY_NAMES if group_by == "producto" else {k: k for k in CANAL_ORDER}

        # Diseño empresarial de tabla comparativa (8 columnas):
        #   VALORES REALES a la izquierda | CATEGORÍA al centro | VARIACIONES a la derecha
        header = ["Año Ant.", "Plan", "Semana/Año Actual", "",
                  "Var vs Plan $", "Var vs Plan %", "Var vs Ant. $", "Var vs Ant. %"]
        rows   = [header]
        hi_rows = []
        neg_cells = []
        CAT_COL = 3  # índice de la columna de categoría (centro)

        plan_df = proc.dfp
        p_filter = plan_df[(plan_df["anio_num"] == yw) & (plan_df["semana_num"] == ww)]
        p_agg = p_filter.groupby(group_col)["plan_venta_sin_impuestos"].sum()

        total_cur = 0; total_prev = 0; total_plan = 0
        total_var_plan = 0; total_var_ant = 0

        for ri, cat in enumerate(cats):
            cv  = agg_cur.get(cat, 0)
            pv  = agg_prev.get(cat, 0)
            plv = p_agg.get(cat, 0)
            v_plan = cv - plv
            v_ant  = cv - pv
            p_plan = (v_plan / plv * 100) if plv > 0 else 0
            p_ant  = (v_ant  / pv  * 100) if pv  > 0 else 0

            total_cur  += cv; total_prev += pv; total_plan += plv
            total_var_plan += v_plan; total_var_ant += v_ant

            row_idx = ri + 1
            # reales (izq) | categoría (centro) | variaciones (der)
            r = [fmt_currency(pv), fmt_currency(plv), fmt_currency(cv),
                 disp.get(cat, cat)[:22],
                 fmt_currency(v_plan), fmt_pct(p_plan),
                 fmt_currency(v_ant),  fmt_pct(p_ant)]
            rows.append(r)

            if v_plan < 0:
                neg_cells += [(row_idx, 4), (row_idx, 5)]
            if v_ant < 0:
                neg_cells += [(row_idx, 6), (row_idx, 7)]

        # Fila total
        tv_plan = total_var_plan
        tp_plan = (tv_plan / total_plan * 100) if total_plan > 0 else 0
        tv_ant  = total_var_ant
        tp_ant  = (tv_ant  / total_prev * 100) if total_prev > 0 else 0
        tot_row_idx = len(rows)
        rows.append([fmt_currency(total_prev), fmt_currency(total_plan), fmt_currency(total_cur),
                     "Total",
                     fmt_currency(tv_plan), fmt_pct(tp_plan),
                     fmt_currency(tv_ant),  fmt_pct(tp_ant)])
        hi_rows.append(tot_row_idx)
        if tv_plan < 0: neg_cells += [(tot_row_idx, 4), (tot_row_idx, 5)]
        if tv_ant  < 0: neg_cells += [(tot_row_idx, 6), (tot_row_idx, 7)]

        cw = self.CONTENT_W
        # reales(3) | categoría(centro) | variaciones(4)
        col_widths = [cw * 0.11, cw * 0.10, cw * 0.13, cw * 0.22,
                      cw * 0.12, cw * 0.09, cw * 0.12, cw * 0.11]
        # Ajustar suma
        diff = cw - sum(col_widths)
        col_widths[-1] += diff

        tbl = self._build_rl_table(rows, col_widths,
                                    highlight_rows=hi_rows,
                                    highlight_cols=[2],   # columna "Semana/Año Actual"
                                    neg_cells=neg_cells,
                                    font_size=7,
                                    label_col=CAT_COL,
                                    label_align="CENTER",
                                    sep_before_cols=[CAT_COL, CAT_COL + 1])
        tbl.wrapOn(c, cw, 300)
        th = tbl._height
        tbl.drawOn(c, self.MARGIN, y - th)
        return y - th

    # ------------------------------------------------------------------
    # Páginas 8-19: SKU individual
    # ------------------------------------------------------------------

    def _draw_page_sku(self, c, producto: str, mode: str = "semanal"):
        disp = PRODUCT_DISPLAY_NAMES.get(producto, producto)
        subtitle = f"{disp} — {'Semanal' if mode == 'semanal' else 'Anual'}"
        self._draw_header(c, subtitulo=subtitle)
        self._draw_footer(c)

        y = self._body_top()
        y = self._draw_section_title(c, disp,
                                     f"Análisis {'Semanal' if mode == 'semanal' else 'Anual'}", y)

        # Tabla SKU
        sku_data = self.proc.get_tabla_sku(producto)
        y = self._draw_sku_detail_table(c, y, sku_data, mode=mode)
        y -= 8

        # Gráficas combo
        n_sem = 12
        serie_v = self.proc.get_serie_semanal(n_semanas=n_sem, group_by="producto", filtro=producto)
        serie_b = self.proc.get_serie_semanal_botellas(n_semanas=n_sem, group_by="producto", filtro=producto)
        plan_df = self.proc.get_plan_semanal(n_semanas=n_sem, filtro_producto=producto)
        semanas_labels = serie_v["label"].tolist() if not serie_v.empty else []
        plan_vals = plan_df["plan_venta_sin_impuestos"].tolist() if not plan_df.empty else []
        prod_color = PRODUCT_COLORS.get(producto, "#9B1C31")

        avail_h = y - FOOTER_HEIGHT_PT - self.MARGIN
        chart_h  = avail_h * 0.44

        if not serie_v.empty and "Total" in serie_v.columns:
            total_vals = serie_v["Total"].tolist()
            y = self._draw_chart_title_bar(
                c, f"Ventas netas {disp} por semana ($MXN sin IVA) — {fmt_currency(sum(total_vals))}", y)
            # Usa barras simples + línea plan (no dona)
            series_dict = {producto: total_vals}
            chart_png = make_combo_chart(
                semanas_labels, series_dict,
                {producto: prod_color}, {producto: disp},
                plan_vals, total_vals, [],
                size_inches=(9.5, 2.5),
            )
            self._embed_png(c, chart_png, self.MARGIN, y - chart_h, self.CONTENT_W, chart_h)
            y -= chart_h + 8

        if not serie_b.empty and "Total" in serie_b.columns:
            total_bot = serie_b["Total"].tolist()
            avail_h2  = y - FOOTER_HEIGHT_PT - self.MARGIN
            chart_h2  = avail_h2 * 0.85
            y = self._draw_chart_title_bar(
                c, f"Volumen {disp} por semana (botellas) — {fmt_int(sum(total_bot))}", y)
            series_dict_b = {producto: total_bot}
            chart_png_b   = make_combo_chart(
                semanas_labels, series_dict_b,
                {producto: prod_color}, {producto: disp},
                [], total_bot, [], y_label="Botellas",
                size_inches=(9.5, 2.5),
            )
            self._embed_png(c, chart_png_b, self.MARGIN, y - chart_h2, self.CONTENT_W, chart_h2)

    def _draw_sku_detail_table(self, c, y: float, sku_data: dict, mode: str = "semanal") -> float:
        """Tabla de detalle SKU: Semana Ant. | Plan | Año Ant. | Actual (resaltado) | Var vs Plan | Var vs Ant."""
        cur  = sku_data["semana_actual"]  if mode == "semanal" else sku_data["ytd"]
        prev = sku_data["semana_anterior"] if mode == "semanal" else sku_data["ytd_anio_anterior"]
        lasty= sku_data["anio_anterior"]
        plan = sku_data["plan"]

        def var(a_val, b_val):
            d = a_val - b_val
            p = (d / b_val * 100) if b_val != 0 else 0
            return d, p

        def _pp(d):
            """Formatea variación de un porcentaje en puntos porcentuales."""
            return f"{d:+.1f} pp"

        def _int_var(d):
            """Formatea variación de un conteo con signo y separador de miles."""
            return f"{int(round(d)):+,}"

        # Variaciones por métrica (vs Plan y vs Año Anterior)
        v_plan_d, v_plan_p = var(cur["ventas"], plan.get("ventas", 0))
        v_ant_d,  v_ant_p  = var(cur["ventas"], lasty["ventas"])
        m_plan_d, m_plan_p = var(cur["margen_pct"], plan.get("margen_pct", 0))
        m_ant_d,  m_ant_p  = var(cur["margen_pct"], lasty["margen_pct"])
        b_plan_d, b_plan_p = var(cur["botellas"], plan.get("botellas", 0))
        b_ant_d,  b_ant_p  = var(cur["botellas"], lasty["botellas"])
        c_plan_d, c_plan_p = var(cur["cajas"], plan.get("cajas", 0))
        c_ant_d,  c_ant_p  = var(cur["cajas"], lasty["cajas"])
        t_plan_d, t_plan_p = var(cur["ticket"], plan.get("ticket", 0))
        t_ant_d,  t_ant_p  = var(cur["ticket"], lasty["ticket"])

        header = ["Métrica", "Año Anterior", "Semana Anterior",
                  "Plan", "Actual (Resaltado)", "Var vs Plan $",
                  "Var vs Plan %", "Var vs Año Ant $", "Var vs Año Ant %"]

        rows = [header]
        metrics = [
            ("Ventas Netas $",   fmt_currency(lasty["ventas"]), fmt_currency(prev["ventas"]),
             fmt_currency(plan.get("ventas", 0)), fmt_currency(cur["ventas"]),
             fmt_currency(v_plan_d), fmt_pct(v_plan_p),
             fmt_currency(v_ant_d), fmt_pct(v_ant_p)),
            ("Margen %",         fmt_pct(lasty["margen_pct"]), fmt_pct(prev["margen_pct"]),
             fmt_pct(plan.get("margen_pct", 0)), fmt_pct(cur["margen_pct"]),
             _pp(m_plan_d), fmt_pct(m_plan_p),
             _pp(m_ant_d), fmt_pct(m_ant_p)),
            ("#Botellas",        fmt_int(lasty["botellas"]), fmt_int(prev["botellas"]),
             fmt_int(plan.get("botellas", 0)), fmt_int(cur["botellas"]),
             _int_var(b_plan_d), fmt_pct(b_plan_p),
             _int_var(b_ant_d), fmt_pct(b_ant_p)),
            ("Cajas 9L",         fmt_int(lasty["cajas"]), fmt_int(prev["cajas"]),
             fmt_int(plan.get("cajas", 0)), fmt_int(cur["cajas"]),
             _int_var(c_plan_d), fmt_pct(c_plan_p),
             _int_var(c_ant_d), fmt_pct(c_ant_p)),
            ("Ticket Promedio $", fmt_ticket(lasty["ticket"]), fmt_ticket(prev["ticket"]),
             fmt_ticket(plan.get("ticket", 0)), fmt_ticket(cur["ticket"]),
             fmt_ticket(t_plan_d), fmt_pct(t_plan_p),
             fmt_ticket(t_ant_d), fmt_pct(t_ant_p)),
        ]

        # Colorear en rojo las variaciones negativas (columnas 5-8) de cada métrica
        deltas = [
            (v_plan_d, v_ant_d), (m_plan_d, m_ant_d), (b_plan_d, b_ant_d),
            (c_plan_d, c_ant_d), (t_plan_d, t_ant_d),
        ]
        neg_cells = []
        for ri, m in enumerate(metrics, 1):
            rows.append(list(m))
            plan_d, ant_d = deltas[ri - 1]
            if plan_d < 0: neg_cells += [(ri, 5), (ri, 6)]
            if ant_d  < 0: neg_cells += [(ri, 7), (ri, 8)]

        cw = self.CONTENT_W
        col_widths = [cw * 0.16, cw * 0.10, cw * 0.11, cw * 0.10,
                      cw * 0.13, cw * 0.10, cw * 0.10, cw * 0.10, cw * 0.10]
        diff = cw - sum(col_widths)
        col_widths[-1] += diff

        tbl = self._build_rl_table(rows, col_widths,
                                    highlight_rows=[1],
                                    highlight_cols=[4],
                                    neg_cells=neg_cells,
                                    font_size=7)
        tbl.wrapOn(c, cw, 200)
        th = tbl._height
        tbl.drawOn(c, self.MARGIN, y - th)
        return y - th

    # ------------------------------------------------------------------
    # Páginas 20-31: Cliente individual
    # ------------------------------------------------------------------

    def _draw_page_cliente(self, c, cliente: str, mode: str = "semanal"):
        subtitle = f"{cliente[:25]} — {'Semanal' if mode == 'semanal' else 'Anual'}"
        self._draw_header(c, subtitulo=subtitle)
        self._draw_footer(c)

        y = self._body_top()
        y = self._draw_section_title(c, cliente[:40],
                                     f"Análisis {'Semanal' if mode == 'semanal' else 'Anual'}", y)

        proc = self.proc
        yw, ww = proc.anio, proc.semana

        if mode == "semanal":
            df_cli = proc._filter_period(yw, ww)
        else:
            df_cli = proc._filter_ytd(yw, ww)

        df_cli = df_cli[df_cli["cliente"] == cliente]

        # Tabla producto × KPI
        agg = df_cli.groupby("producto").agg(
            ventas=("venta_sin_impuestos", "sum"),
            botellas=("botellas", "sum"),
        ).reset_index()

        total_v = agg["ventas"].sum()
        header = ["Producto", "Ventas Netas $", "Botellas", "Participación %"]
        rows = [header]
        hi_rows = []
        for ri, (_, row) in enumerate(agg.iterrows(), 1):
            pct = (row["ventas"] / total_v * 100) if total_v > 0 else 0
            rows.append([
                PRODUCT_DISPLAY_NAMES.get(row["producto"], row["producto"]),
                fmt_currency(row["ventas"]),
                fmt_int(row["botellas"]),
                fmt_pct(pct),
            ])
        rows.append(["Total", fmt_currency(total_v), "—", "100%"])
        hi_rows.append(len(rows) - 1)

        cw = self.CONTENT_W * 0.5
        col_widths = [cw * 0.35, cw * 0.25, cw * 0.20, cw * 0.20]
        tbl = self._build_rl_table(rows, col_widths,
                                    highlight_rows=hi_rows, font_size=7)
        tbl.wrapOn(c, cw, 200)
        th = tbl._height
        tbl.drawOn(c, self.MARGIN, y - th)
        y -= th + 8

        # Gráfica de barras por producto (NO dona) para el cliente
        if not agg.empty:
            avail_h = y - FOOTER_HEIGHT_PT - self.MARGIN
            chart_h  = avail_h * 0.85

            agg_sorted = agg.copy()
            agg_sorted["producto_cat"] = pd.Categorical(
                agg_sorted["producto"], categories=PRODUCT_ORDER, ordered=True)
            agg_sorted = agg_sorted.sort_values("producto_cat")

            series_dict = {}
            for _, row in agg_sorted.iterrows():
                series_dict[row["producto"]] = [row["ventas"]]

            y = self._draw_chart_title_bar(
                c, f"Ventas {cliente[:20]} por Producto — {fmt_currency(total_v)}", y)
            chart_png = make_combo_chart(
                [cliente[:15]], series_dict,
                PRODUCT_COLORS,
                {p: PRODUCT_DISPLAY_NAMES.get(p, p) for p in PRODUCT_ORDER},
                [], [], [],
                size_inches=(9.5, 2.5),
            )
            self._embed_png(c, chart_png, self.MARGIN, y - chart_h, self.CONTENT_W, chart_h)


# ---------------------------------------------------------------------------
# Función de entrada
# ---------------------------------------------------------------------------

def generate_pdf(
    processor: LocoDataProcessor,
    output_path: str,
    logo_path: Optional[str] = None,
):
    """Genera el PDF completo y lo guarda en output_path."""
    gen = LocoReportePDF(processor, output_path, logo_path=logo_path)
    gen.generate()
