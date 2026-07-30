"""
xlsx_generator.py
=================
Genera el archivo Excel ejecutivo con 6 hojas analíticas.
Usa openpyxl con formato profesional: paleta maroon, condicionales, gráficas.

Hojas:
  1. Resumen Ejecutivo  — KPIs + semáforo + 5 hallazgos
  2. Comparativo        — WoW / MoM / YoY / YTD
  3. Por Producto       — ranking + tendencia 12 semanas
  4. Por Cliente        — concentración + tendencia
  5. Regional           — ventas por estado
  6. Oportunidades      — hallazgos, tipo, impacto, recomendación
"""

import os
from typing import Optional, List, Dict
import pandas as pd
import numpy as np

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import DataBarRule

import design_tokens as dt
from design_tokens import (
    BRAND_MAROON, HIGHLIGHT_CREAM, NEG_VALUE, POS_VALUE,
    SECTION_SUBTITLE, RULE_LINE, PAGE_BG,
    PRODUCT_ORDER, PRODUCT_DISPLAY_NAMES, PRODUCT_COLORS,
    CANAL_ORDER, CANAL_COLORS,
    fmt_currency, fmt_pct, fmt_int, fmt_ticket,
)
from data_processor import LocoDataProcessor


# ---------------------------------------------------------------------------
# Helpers de estilo
# ---------------------------------------------------------------------------

def _fill(hex_color: str) -> PatternFill:
    c = hex_color.lstrip("#")
    return PatternFill("solid", fgColor=c)


def _font(bold=False, color="000000", size=9, italic=False) -> Font:
    c = color.lstrip("#")
    return Font(bold=bold, color=c, size=size, italic=italic, name="Calibri")


def _align(h="left", v="center", wrap=False) -> Alignment:
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)


def _border_thin() -> Border:
    s = Side(style="thin", color="D9D9D9")
    return Border(left=s, right=s, top=s, bottom=s)


def _border_medium() -> Border:
    s = Side(style="medium", color="6E1E28")
    return Border(bottom=s)


FILL_MAROON  = _fill(BRAND_MAROON)
FILL_CREAM   = _fill(HIGHLIGHT_CREAM)
FILL_WHITE   = _fill("FFFFFF")
FILL_HEADER2 = _fill("F2F2F2")

FONT_HEADER  = _font(bold=True, color="FFFFFF", size=9)
FONT_TITLE   = _font(bold=True, color=BRAND_MAROON, size=14)
FONT_SECTION = _font(bold=True, color=BRAND_MAROON, size=11)
FONT_BODY    = _font(size=9)
FONT_BOLD    = _font(bold=True, size=9)
FONT_TOTAL   = _font(bold=True, color=BRAND_MAROON, size=9)
FONT_NEG     = _font(bold=True, color=NEG_VALUE, size=9)
FONT_SUB     = _font(italic=True, color=SECTION_SUBTITLE, size=8)

BORDER = _border_thin()

FMT_CURRENCY = '#,##0'
FMT_PCT      = '0%'
FMT_PCT1     = '0.0%'
FMT_INT      = '#,##0'
FMT_DECIMAL  = '#,##0.0'

TRAFFIC_GREEN  = "00B050"
TRAFFIC_YELLOW = "FFC000"
TRAFFIC_RED    = "FF0000"


def _set_col_width(ws, col_letter: str, width: float):
    ws.column_dimensions[col_letter].width = width


def _header_row(ws, row_idx: int, values: list, start_col: int = 1):
    """Escribe una fila de encabezado con estilo maroon."""
    for ci, val in enumerate(values, start_col):
        cell = ws.cell(row=row_idx, column=ci, value=val)
        cell.fill   = FILL_MAROON
        cell.font   = FONT_HEADER
        cell.alignment = _align("center")
        cell.border = BORDER


def _data_row(ws, row_idx: int, values: list, start_col: int = 1,
              bold=False, cream=False, neg_cols: list = None):
    """Escribe una fila de datos con estilo alternado."""
    fill = FILL_CREAM if cream else (_fill("F9F9F9") if row_idx % 2 == 0 else FILL_WHITE)
    for ci, val in enumerate(values, start_col):
        cell = ws.cell(row=row_idx, column=ci, value=val)
        cell.fill   = fill
        cell.font   = FONT_BOLD if bold else FONT_BODY
        cell.border = BORDER
        # Alineación: primera columna izquierda, resto derecha
        if ci == start_col:
            cell.alignment = _align("left")
        else:
            cell.alignment = _align("right")
        # Negativos en rojo
        if neg_cols and ci in neg_cols and isinstance(val, (int, float)) and val < 0:
            cell.font = FONT_NEG


def _traffic_light(ws, row_idx: int, col_idx: int, value: float, thresholds=(-5, 5)):
    """Semáforo: rojo < low, amarillo entre, verde > high."""
    cell = ws.cell(row=row_idx, column=col_idx)
    low, high = thresholds
    if isinstance(value, (int, float)):
        if value < low:
            color = TRAFFIC_RED
            emoji = "🔴"
        elif value > high:
            color = TRAFFIC_GREEN
            emoji = "🟢"
        else:
            color = TRAFFIC_YELLOW
            emoji = "🟡"
        cell.value = f"{emoji} {value:+.1f}%"
        cell.font  = _font(bold=True, color=color, size=9)
    cell.alignment = _align("center")


# ---------------------------------------------------------------------------
# Generador principal
# ---------------------------------------------------------------------------

class LocoReporteXLSX:
    """
    Genera el reporte Excel ejecutivo de Loco Tequila con 6 hojas analíticas.
    """

    def __init__(self, processor: LocoDataProcessor, output_path: str):
        self.proc        = processor
        self.output_path = output_path
        self.wb          = Workbook()
        self.wb.remove(self.wb.active)  # eliminar hoja vacía por defecto

    # ------------------------------------------------------------------
    # Generador principal
    # ------------------------------------------------------------------

    def generate(self):
        self._sheet_resumen()
        self._sheet_comparativo()
        self._sheet_productos()
        self._sheet_clientes()
        self._sheet_regional()
        self._sheet_oportunidades()
        self.wb.save(self.output_path)
        print(f"[XLSX] Guardado: {self.output_path}")

    # ------------------------------------------------------------------
    # Hoja 1: Resumen Ejecutivo
    # ------------------------------------------------------------------

    def _sheet_resumen(self):
        ws = self.wb.create_sheet("Resumen Ejecutivo")
        ws.sheet_view.showGridLines = False

        r = self.proc.get_resumen_ejecutivo()
        sem = self.proc.semana
        anio = self.proc.anio

        # --- Título ---
        ws.merge_cells("A1:I1")
        ws["A1"] = f"Reporte Ejecutivo — Semana {sem:02d} · {anio}"
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = _align("left")
        ws["A1"].fill = _fill("FFF8F0")

        ws.merge_cells("A2:I2")
        ws["A2"] = f"Loco Tequila · Ventas y Margen · {anio}-W{sem:02d}"
        ws["A2"].font = FONT_SUB
        ws["A2"].fill = _fill("FFF8F0")

        # --- KPI Cards (fila 4-11) ---
        ws.merge_cells("A4:B4")
        ws["A4"] = "KPIs Clave — Semana Actual"
        ws["A4"].font = FONT_SECTION
        ws["A4"].fill = FILL_CREAM

        kpi_headers = ["Métrica", "Valor", "Plan", "Var vs Plan", "Año Anterior", "Var vs Año Ant."]
        _header_row(ws, 5, kpi_headers, start_col=1)

        cur  = r["actual"]
        plan = r["plan"]
        vp   = r["vs_plan"]
        ly   = r["vs_anio_anterior"]
        prev = r["vs_semana_anterior"]

        # Definir métricas
        kpis = [
            ("Ventas Netas (sin IVA)",
             cur["ventas_netas"], plan["ventas_netas"],
             vp["abs"], vp["pct"],
             cur["ventas_netas"] - ly["abs"], ly["pct"]),
            ("# Botellas Vendidas",
             cur["botellas"], plan.get("botellas", 0),
             None, None, None, None),
            ("Cajas 9 Litros",
             cur["cajas_9l"], plan.get("cajas_9l", 0),
             None, None, None, None),
            ("Margen % Estimado",
             cur["margen_pct"] / 100, None,
             None, None, None, None),
            ("Ticket Promedio $",
             cur["ticket_promedio"], None,
             None, None, None, None),
        ]

        neg_c = [4, 6]
        for ri, (met, val, plan_v, var_abs, var_pct, ant_val, ant_pct) in enumerate(kpis, 6):
            row_vals = [
                met,
                val,
                plan_v if plan_v else "—",
                var_abs if var_abs is not None else "—",
                f"{var_pct:+.1f}%" if var_pct is not None else "—",
                ant_val if ant_val is not None else "—",
                f"{ant_pct:+.1f}%" if ant_pct is not None else "—",
            ]
            cream = (ri % 2 == 0)
            _data_row(ws, ri, row_vals[:6], bold=(ri == 6), cream=(ri == 6))

            # Formatear celdas numéricas
            cell_val = ws.cell(row=ri, column=2)
            if met == "Margen % Estimado":
                cell_val.number_format = FMT_PCT1
            elif met == "Ticket Promedio $":
                cell_val.number_format = FMT_DECIMAL
                cell_val.value = val
            elif "Botellas" in met or "Cajas" in met:
                cell_val.number_format = FMT_INT
            else:
                cell_val.number_format = FMT_CURRENCY

        # --- Semáforos ---
        ws.merge_cells("A13:B13")
        ws["A13"] = "Semáforo de Desempeño"
        ws["A13"].font = FONT_SECTION
        ws["A13"].fill = FILL_CREAM

        semaforos = [
            ("WoW (vs semana anterior)",  r["vs_semana_anterior"]["pct"]),
            ("MoM (vs mes anterior)",     r["mes_vs_anterior"]["pct"]),
            ("MoM vs Año Anterior",       r["mes_vs_ly"]["pct"]),
            ("YTD vs Año Anterior",       r["ytd_vs_ly"]["pct"]),
            ("vs Plan Semanal",           r["vs_plan"]["pct"]),
        ]
        _header_row(ws, 14, ["Indicador", "Variación", "Estado"], start_col=1)
        for ri, (label, pct) in enumerate(semaforos, 15):
            ws.cell(row=ri, column=1, value=label).font = FONT_BODY
            ws.cell(row=ri, column=1).alignment = _align("left")
            ws.cell(row=ri, column=2, value=f"{pct:+.1f}%").alignment = _align("right")
            ws.cell(row=ri, column=2).font = FONT_BODY
            _traffic_light(ws, ri, 3, pct)
            for ci in range(1, 4):
                ws.cell(row=ri, column=ci).border = BORDER

        # --- 5 Hallazgos principales ---
        ws.merge_cells("A21:F21")
        ws["A21"] = "Hallazgos Principales"
        ws["A21"].font = FONT_SECTION
        ws["A21"].fill = FILL_CREAM

        hallazgos = self.proc.get_oportunidades_riesgos()
        _header_row(ws, 22, ["#", "Hallazgo", "Tipo", "Impacto", "Recomendación"], start_col=1)
        for ri, h in enumerate(hallazgos[:5], 23):
            tipo_color = TRAFFIC_RED if h["tipo"] == "Riesgo" else (
                TRAFFIC_GREEN if h["tipo"] == "Oportunidad" else TRAFFIC_YELLOW)
            vals = [ri - 22, h["hallazgo"], h["tipo"], h["impacto"], h["recomendacion"]]
            _data_row(ws, ri, vals)
            ws.cell(row=ri, column=3).font = _font(bold=True, color=tipo_color, size=9)

        # Anchos de columna
        widths = [30, 14, 12, 14, 12, 14]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    # ------------------------------------------------------------------
    # Hoja 2: Comparativo WoW / MoM / YoY / YTD
    # ------------------------------------------------------------------

    def _sheet_comparativo(self):
        ws = self.wb.create_sheet("Comparativo Periodos")
        ws.sheet_view.showGridLines = False

        r = self.proc.get_resumen_ejecutivo()

        ws.merge_cells("A1:G1")
        ws["A1"] = "Comparativo de Periodos — Ventas sin IVA (MXN)"
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = _align("left")
        ws["A1"].fill = _fill("FFF8F0")

        # Tabla WoW
        self._write_comparison_block(ws, start_row=3, title="Semana a Semana (WoW)",
                                      actual=r["actual"]["ventas_netas"],
                                      anterior=r["actual"]["ventas_netas"] - r["vs_semana_anterior"]["abs"],
                                      var_abs=r["vs_semana_anterior"]["abs"],
                                      var_pct=r["vs_semana_anterior"]["pct"],
                                      labels=["Semana Actual", "Semana Anterior"])
        self._write_comparison_block(ws, start_row=9, title="Mes a Mes (MoM)",
                                      actual=r["mes_actual"]["ventas_netas"],
                                      anterior=r["mes_actual"]["ventas_netas"] - r["mes_vs_anterior"]["abs"],
                                      var_abs=r["mes_vs_anterior"]["abs"],
                                      var_pct=r["mes_vs_anterior"]["pct"],
                                      labels=["Mes Actual", "Mes Anterior"])
        self._write_comparison_block(ws, start_row=15, title="Mes vs Año Anterior (YoY Mensual)",
                                      actual=r["mes_actual"]["ventas_netas"],
                                      anterior=r["mes_actual"]["ventas_netas"] - r["mes_vs_ly"]["abs"],
                                      var_abs=r["mes_vs_ly"]["abs"],
                                      var_pct=r["mes_vs_ly"]["pct"],
                                      labels=["Mes Actual", "Mismo Mes Año Ant."])
        self._write_comparison_block(ws, start_row=21, title="Acumulado del Año (YTD)",
                                      actual=r["ytd_actual"]["ventas_netas"],
                                      anterior=r["ytd_actual"]["ventas_netas"] - r["ytd_vs_ly"]["abs"],
                                      var_abs=r["ytd_vs_ly"]["abs"],
                                      var_pct=r["ytd_vs_ly"]["pct"],
                                      labels=["YTD Actual", "YTD Año Anterior"])

        # Tabla 12 semanas rolling
        row = 27
        ws.merge_cells(f"A{row}:G{row}")
        ws[f"A{row}"] = "Últimas 12 Semanas — Ventas Semanales"
        ws[f"A{row}"].font = FONT_SECTION
        ws[f"A{row}"].fill = FILL_CREAM

        serie = self.proc.get_serie_semanal(n_semanas=12)
        plan  = self.proc.get_plan_semanal(n_semanas=12)
        cols_hdr = ["Semana", "Ventas Netas $", "Plan $", "Var vs Plan $", "Var vs Plan %"]
        _header_row(ws, row + 1, cols_hdr, start_col=1)

        plan_dict = {}
        if not plan.empty:
            plan_dict = dict(zip(plan["label"], plan["plan_venta_sin_impuestos"]))

        for ri, (_, srow) in enumerate(serie.iterrows(), row + 2):
            lbl   = srow.get("label", "")
            venta = float(srow.get("Total", 0))
            plan_v = plan_dict.get(lbl, 0)
            var_abs = venta - plan_v
            var_pct = (var_abs / plan_v * 100) if plan_v > 0 else 0
            cream = (lbl == f"W{self.proc.semana:02d}")
            _data_row(ws, ri, [lbl, venta, plan_v, var_abs, var_pct / 100],
                      cream=cream, neg_cols=[4])
            for ci, fmt in [(2, FMT_CURRENCY), (3, FMT_CURRENCY),
                             (4, FMT_CURRENCY), (5, FMT_PCT1)]:
                ws.cell(row=ri, column=ci).number_format = fmt

        # Anchos
        for i, w in enumerate([14, 18, 18, 18, 15], 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    def _write_comparison_block(self, ws, start_row: int, title: str,
                                  actual: float, anterior: float,
                                  var_abs: float, var_pct: float,
                                  labels: list):
        ws.merge_cells(f"A{start_row}:G{start_row}")
        ws[f"A{start_row}"] = title
        ws[f"A{start_row}"].font = FONT_SECTION
        ws[f"A{start_row}"].fill = FILL_CREAM

        _header_row(ws, start_row + 1,
                    [labels[0], labels[1], "Variación $", "Variación %", "Crecimiento"],
                    start_col=1)

        vals = [actual, anterior, var_abs, var_pct / 100,
                "▲" if var_abs >= 0 else "▼"]
        _data_row(ws, start_row + 2, vals, cream=True, neg_cols=[3])

        for ci, fmt in [(1, FMT_CURRENCY), (2, FMT_CURRENCY),
                         (3, FMT_CURRENCY), (4, FMT_PCT1)]:
            ws.cell(row=start_row + 2, column=ci).number_format = fmt

        crec_cell = ws.cell(row=start_row + 2, column=5)
        crec_cell.font = _font(bold=True,
                                color=TRAFFIC_GREEN if var_abs >= 0 else TRAFFIC_RED,
                                size=11)
        crec_cell.alignment = _align("center")

    # ------------------------------------------------------------------
    # Hoja 3: Por Producto
    # ------------------------------------------------------------------

    def _sheet_productos(self):
        ws = self.wb.create_sheet("Por Producto")
        ws.sheet_view.showGridLines = False

        ws.merge_cells("A1:H1")
        ws["A1"] = "Análisis por Producto — Ranking y Tendencia"
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = _align("left")
        ws["A1"].fill = _fill("FFF8F0")

        # Ranking anual
        ranking = self.proc.get_ranking_productos(mode="anual")
        ws.merge_cells("A3:H3")
        ws["A3"] = "Ranking por Volumen de Ventas (YTD)"
        ws["A3"].font = FONT_SECTION
        ws["A3"].fill = FILL_CREAM

        cols = ["Producto", "Ventas Netas $", "Botellas", "Cajas 9L",
                "Margen $", "Margen %", "Participación %"]
        _header_row(ws, 4, cols, start_col=1)

        for ri, (_, row) in enumerate(ranking.iterrows(), 5):
            cream = (ri == 5)  # top 1 resaltado
            vals = [
                PRODUCT_DISPLAY_NAMES.get(row["producto"], row["producto"]),
                row["ventas"],
                row["botellas"],
                row["cajas"],
                row["margen"],
                row["margen_pct"] / 100,
                row["participacion_pct"] / 100,
            ]
            _data_row(ws, ri, vals, cream=cream)
            fmts = [None, FMT_CURRENCY, FMT_INT, FMT_INT, FMT_CURRENCY, FMT_PCT1, FMT_PCT1]
            for ci, fmt in enumerate(fmts, 1):
                if fmt:
                    ws.cell(row=ri, column=ci).number_format = fmt

        # Fila total
        tot_row = len(ranking) + 5
        total_vals = ["Total",
                      ranking["ventas"].sum(),
                      ranking["botellas"].sum(),
                      ranking["cajas"].sum(),
                      ranking["margen"].sum(), "—", "100%"]
        _data_row(ws, tot_row, total_vals, bold=True, cream=True)
        ws.cell(row=tot_row, column=2).number_format = FMT_CURRENCY
        ws.cell(row=tot_row, column=3).number_format = FMT_INT

        # Tabla tendencia 12 semanas
        row_start = tot_row + 3
        ws.merge_cells(f"A{row_start}:M{row_start}")
        ws[f"A{row_start}"] = "Tendencia Semanal por Producto (últimas 12 semanas)"
        ws[f"A{row_start}"].font = FONT_SECTION
        ws[f"A{row_start}"].fill = FILL_CREAM

        serie = self.proc.get_serie_semanal(n_semanas=12)
        if not serie.empty:
            hdr = ["Semana"] + [PRODUCT_DISPLAY_NAMES.get(p, p) for p in PRODUCT_ORDER if p in serie.columns] + ["Total"]
            _header_row(ws, row_start + 1, hdr)
            for ri, (_, srow) in enumerate(serie.iterrows(), row_start + 2):
                vals = [srow.get("label", "")]
                for p in PRODUCT_ORDER:
                    if p in srow.index:
                        vals.append(float(srow[p]))
                vals.append(float(srow.get("Total", 0)))
                cream = (srow.get("label", "") == f"W{self.proc.semana:02d}")
                _data_row(ws, ri, vals, cream=cream)
                for ci in range(2, len(vals) + 1):
                    ws.cell(row=ri, column=ci).number_format = FMT_CURRENCY

            # Gráfica de líneas (barras agrupadas en Excel para tendencia)
            chart_row_start = row_start + 2
            chart_row_end   = chart_row_start + len(serie) - 1
            n_prods = len([p for p in PRODUCT_ORDER if p in serie.columns])

            chart = BarChart()
            chart.type = "col"
            chart.grouping = "stacked"
            chart.overlap = 100
            chart.title  = "Tendencia Semanal por Producto"
            chart.y_axis.title = "$MXN (sin IVA)"
            chart.x_axis.title = "Semana"
            chart.style = 10
            chart.width = 24
            chart.height = 12

            cats = Reference(ws, min_col=1, min_row=chart_row_start, max_row=chart_row_end)
            for ci in range(2, 2 + n_prods):
                data = Reference(ws, min_col=ci, min_row=row_start + 1, max_row=chart_row_end)
                series_obj = BarChart()
                series_obj.add_data(data, titles_from_data=True)
                chart.append(series_obj.series[0])

            chart.set_categories(cats)
            ws.add_chart(chart, f"A{chart_row_end + 3}")

        # Anchos
        for i, w in enumerate([20, 16, 12, 12, 16, 12, 14], 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    # ------------------------------------------------------------------
    # Hoja 4: Por Cliente
    # ------------------------------------------------------------------

    def _sheet_clientes(self):
        ws = self.wb.create_sheet("Por Cliente")
        ws.sheet_view.showGridLines = False

        ws.merge_cells("A1:H1")
        ws["A1"] = "Análisis por Cliente — Concentración y Tendencia"
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = _align("left")
        ws["A1"].fill = _fill("FFF8F0")

        top_clientes = self.proc.get_top_clientes(mode="anual")
        det_df = self.proc.get_detalle_clientes(top_clientes, mode="anual")

        ws.merge_cells("A3:H3")
        ws["A3"] = f"Top {len(top_clientes)} Clientes — Ventas YTD por Producto"
        ws["A3"].font = FONT_SECTION
        ws["A3"].fill = FILL_CREAM

        cols = ["Cliente"] + [PRODUCT_DISPLAY_NAMES.get(p, p) for p in PRODUCT_ORDER] + ["Total $", "Part %"]
        _header_row(ws, 4, cols)

        total_global = det_df["Total"].sum() if not det_df.empty else 1

        for ri, (idx, row) in enumerate(det_df.iterrows(), 5):
            tv   = row["Total"]
            pct  = tv / total_global * 100 if total_global > 0 else 0
            vals = [str(idx)[:30]] + [row[p] for p in PRODUCT_ORDER if p in row.index] + [tv, pct / 100]
            _data_row(ws, ri, vals)
            for ci in range(2, len(PRODUCT_ORDER) + 2):
                ws.cell(row=ri, column=ci).number_format = FMT_CURRENCY
            ws.cell(row=ri, column=len(PRODUCT_ORDER) + 2).number_format = FMT_CURRENCY
            ws.cell(row=ri, column=len(PRODUCT_ORDER) + 3).number_format = FMT_PCT1

        # Fila total
        tot_r = 5 + len(det_df)
        total_row = ["Total"] + [det_df[p].sum() if p in det_df.columns else 0 for p in PRODUCT_ORDER] + [total_global, 1.0]
        _data_row(ws, tot_r, total_row, bold=True, cream=True)
        for ci in range(2, len(PRODUCT_ORDER) + 3):
            ws.cell(row=tot_r, column=ci).number_format = FMT_CURRENCY
        ws.cell(row=tot_r, column=len(PRODUCT_ORDER) + 3).number_format = FMT_PCT1

        # Concentración
        conc_row = tot_r + 3
        ws.merge_cells(f"A{conc_row}:D{conc_row}")
        ws[f"A{conc_row}"] = "Concentración de Ingresos (Top Clientes)"
        ws[f"A{conc_row}"].font = FONT_SECTION
        ws[f"A{conc_row}"].fill = FILL_CREAM

        pct_top = det_df["Total"].sum() / total_global * 100 if not det_df.empty else 0
        ws.cell(row=conc_row + 1, column=1, value="% del ingreso total en top clientes")
        ws.cell(row=conc_row + 1, column=2, value=pct_top / 100).number_format = FMT_PCT1
        ws.cell(row=conc_row + 1, column=2).font = _font(bold=True, color=BRAND_MAROON, size=12)

        # Anchos
        ws.column_dimensions["A"].width = 30
        for i in range(2, len(PRODUCT_ORDER) + 4):
            ws.column_dimensions[get_column_letter(i)].width = 14

    # ------------------------------------------------------------------
    # Hoja 5: Regional
    # ------------------------------------------------------------------

    def _sheet_regional(self):
        ws = self.wb.create_sheet("Regional")
        ws.sheet_view.showGridLines = False

        ws.merge_cells("A1:F1")
        ws["A1"] = "Análisis Regional — Ventas por Estado"
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = _align("left")
        ws["A1"].fill = _fill("FFF8F0")

        df_reg = self.proc.get_analisis_regional(mode="anual")

        ws.merge_cells("A3:F3")
        ws["A3"] = "Ranking de Estados — YTD"
        ws["A3"].font = FONT_SECTION
        ws["A3"].fill = FILL_CREAM

        _header_row(ws, 4, ["#", "Estado / Región", "Ventas Netas $", "Botellas", "Participación %"])

        total_v = df_reg["ventas"].sum()
        for ri, (_, row) in enumerate(df_reg.iterrows(), 5):
            pct_v = row["ventas"] / total_v if total_v > 0 else 0
            _data_row(ws, ri, [ri - 4, row["region_o_estado"],
                                row["ventas"], row["botellas"], pct_v])
            ws.cell(row=ri, column=3).number_format = FMT_CURRENCY
            ws.cell(row=ri, column=4).number_format = FMT_INT
            ws.cell(row=ri, column=5).number_format = FMT_PCT1

        # Formateo condicional (data bar) en ventas
        last_row = 4 + len(df_reg)
        ws.conditional_formatting.add(
            f"C5:C{last_row}",
            DataBarRule(start_type="min", end_type="max",
                        color=BRAND_MAROON.lstrip("#"))
        )

        # Gráfica barras horizontales (top 15)
        chart = BarChart()
        chart.type = "bar"  # horizontal
        chart.title = "Top Regiones — Ventas Netas ($MXN)"
        chart.y_axis.title = "Estado"
        chart.x_axis.title = "$MXN sin IVA"
        chart.width = 22
        chart.height = 14
        chart.style = 10

        n_rows = min(15, len(df_reg))
        data  = Reference(ws, min_col=3, min_row=4, max_row=4 + n_rows)
        cats  = Reference(ws, min_col=2, min_row=5, max_row=4 + n_rows)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        ws.add_chart(chart, f"G3")

        for i, w in enumerate([5, 28, 18, 12, 14], 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    # ------------------------------------------------------------------
    # Hoja 6: Oportunidades y Riesgos
    # ------------------------------------------------------------------

    def _sheet_oportunidades(self):
        ws = self.wb.create_sheet("Oportunidades y Riesgos")
        ws.sheet_view.showGridLines = False

        ws.merge_cells("A1:E1")
        ws["A1"] = "Oportunidades y Riesgos Identificados"
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = _align("left")
        ws["A1"].fill = _fill("FFF8F0")

        ws.merge_cells("A2:E2")
        ws["A2"] = (f"Análisis automatizado · Semana {self.proc.semana:02d} · {self.proc.anio} "
                    "— Complementar con contexto de mercado")
        ws["A2"].font = FONT_SUB

        _header_row(ws, 4, ["#", "Hallazgo", "Tipo", "Impacto Estimado", "Recomendación de Acción"])

        items = self.proc.get_oportunidades_riesgos()
        for ri, item in enumerate(items, 5):
            tipo_color = TRAFFIC_RED if item["tipo"] == "Riesgo" else (
                TRAFFIC_GREEN if item["tipo"] == "Oportunidad" else TRAFFIC_YELLOW)
            vals = [ri - 4, item["hallazgo"], item["tipo"], item["impacto"], item["recomendacion"]]
            _data_row(ws, ri, vals)
            ws.cell(row=ri, column=3).font = _font(bold=True, color=tipo_color, size=9)
            for ci in range(1, 6):
                ws.cell(row=ri, column=ci).alignment = _align("left", wrap=True)

        # Conclusiones
        conc_row = 5 + len(items) + 2
        ws.merge_cells(f"A{conc_row}:E{conc_row}")
        ws[f"A{conc_row}"] = "Conclusiones y Próximos Pasos"
        ws[f"A{conc_row}"].font = FONT_SECTION
        ws[f"A{conc_row}"].fill = FILL_CREAM

        resumen = self.proc.get_resumen_ejecutivo()
        wow_pct = resumen["vs_semana_anterior"]["pct"]
        ytd_pct = resumen["ytd_vs_ly"]["pct"]
        plan_pct = resumen["vs_plan"]["pct"]

        pasos = [
            f"1. WoW: {wow_pct:+.1f}% — {'Mantener ritmo' if wow_pct > 0 else 'Investigar causa de caída'}",
            f"2. YTD vs Año Ant.: {ytd_pct:+.1f}% — {'Sostener estrategia actual' if ytd_pct > 0 else 'Revisar mix de producto y canal'}",
            f"3. Cumplimiento de plan: {plan_pct:+.1f}% — {'OK' if plan_pct > -5 else 'Requiere plan de recuperación urgente'}",
            "4. Monitorear concentración de clientes — diversificar cartera si top 3 > 50%.",
            "5. Validar datos de mercado (CRT, exportaciones, precio agave) para contexto externo.",
        ]
        for i, paso in enumerate(pasos, conc_row + 1):
            ws.merge_cells(f"A{i}:E{i}")
            ws[f"A{i}"] = paso
            ws[f"A{i}"].font = FONT_BODY
            ws[f"A{i}"].alignment = _align("left", wrap=True)
            ws.row_dimensions[i].height = 20

        # Anchos
        widths = [5, 40, 16, 24, 45]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    # ------------------------------------------------------------------
    # Hoja 7 (opcional): Comparativo Custom entre dos periodos
    # ------------------------------------------------------------------

    def _sheet_comparativo_custom(self, comp: Dict):
        """
        Hoja generada solo cuando se pasa --comparar-*.
        Muestra lado a lado los dos periodos con variaciones.
        """
        ws = self.wb.create_sheet("Comparativo Custom")
        ws.sheet_view.showGridLines = False

        label_a = comp["labels"]["a"]
        label_b = comp["labels"]["b"]

        ws.merge_cells("A1:G1")
        ws["A1"] = f"Comparativo: {label_a}  vs  {label_b}"
        ws["A1"].font = FONT_TITLE
        ws["A1"].alignment = _align("left")
        ws["A1"].fill = _fill("FFF8F0")

        # --- KPIs comparativos ---
        ws.merge_cells("A3:G3")
        ws["A3"] = "KPIs Generales"
        ws["A3"].font = FONT_SECTION
        ws["A3"].fill = FILL_CREAM

        _header_row(ws, 4, ["Metrica", label_a, label_b,
                              "Variacion $", "Variacion %", "Tendencia"])

        metricas = [
            ("Ventas Netas $",
             comp["kpis_a"]["ventas_netas"],
             comp["kpis_b"]["ventas_netas"],
             comp["variacion"]["ventas_netas"]["abs"],
             comp["variacion"]["ventas_netas"]["pct"]),
            ("# Botellas",
             comp["kpis_a"]["botellas"],
             comp["kpis_b"]["botellas"],
             comp["variacion"]["botellas"]["abs"],
             comp["variacion"]["botellas"]["pct"]),
            ("Margen %",
             comp["kpis_a"]["margen_pct"],
             comp["kpis_b"]["margen_pct"],
             comp["variacion"]["margen_pct"]["abs"],
             comp["variacion"]["margen_pct"]["pct"]),
            ("Ticket Promedio $",
             comp["kpis_a"]["ticket_promedio"],
             comp["kpis_b"]["ticket_promedio"],
             comp["variacion"]["ticket_promedio"]["abs"],
             comp["variacion"]["ticket_promedio"]["pct"]),
        ]

        for ri, (met, va, vb, var_abs, var_pct) in enumerate(metricas, 5):
            cream = (ri == 5)
            tendencia = "mejora" if var_abs >= 0 else "baja"
            tend_color = TRAFFIC_GREEN if var_abs >= 0 else TRAFFIC_RED
            _data_row(ws, ri, [met, va, vb, var_abs, var_pct / 100, tendencia],
                      cream=cream, neg_cols=[4])
            ws.cell(row=ri, column=2).number_format = FMT_CURRENCY
            ws.cell(row=ri, column=3).number_format = FMT_CURRENCY
            ws.cell(row=ri, column=4).number_format = FMT_CURRENCY
            ws.cell(row=ri, column=5).number_format = FMT_PCT1
            ws.cell(row=ri, column=6).font = _font(bold=True, color=tend_color, size=9)

        # --- Por Producto ---
        row = 11
        ws.merge_cells(f"A{row}:G{row}")
        ws[f"A{row}"] = "Comparativo por Producto"
        ws[f"A{row}"].font = FONT_SECTION
        ws[f"A{row}"].fill = FILL_CREAM

        por_prod = comp.get("por_producto")
        if por_prod is not None and not por_prod.empty:
            _header_row(ws, row + 1, ["Producto", label_a, label_b,
                                       "Variacion $", "Variacion %"])
            for ri2, (idx, prow) in enumerate(por_prod.iterrows(), row + 2):
                va = prow.get("periodo_a", 0)
                vb = prow.get("periodo_b", 0)
                vd = prow.get("variacion_abs", 0)
                vp = prow.get("variacion_pct", 0)
                prod_display = PRODUCT_DISPLAY_NAMES.get(idx, idx)
                _data_row(ws, ri2, [prod_display, va, vb, vd, vp / 100],
                          neg_cols=[4])
                for ci, fmt in [(2, FMT_CURRENCY), (3, FMT_CURRENCY),
                                 (4, FMT_CURRENCY), (5, FMT_PCT1)]:
                    ws.cell(row=ri2, column=ci).number_format = fmt

            # Grafica de barras agrupadas
            last_prod_row = row + 1 + len(por_prod)
            chart = BarChart()
            chart.type = "col"
            chart.grouping = "clustered"
            chart.title = f"Ventas por Producto: {label_a} vs {label_b}"
            chart.y_axis.title = "$MXN sin IVA"
            chart.width = 22
            chart.height = 12
            chart.style = 10

            data_ref = Reference(ws, min_col=2, max_col=3,
                                  min_row=row + 1, max_row=last_prod_row)
            cats_ref = Reference(ws, min_col=1,
                                  min_row=row + 2, max_row=last_prod_row)
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)
            ws.add_chart(chart, f"G{row}")
            next_section = last_prod_row + 16
        else:
            next_section = row + 4

        # --- Por Canal ---
        row2 = next_section
        ws.merge_cells(f"A{row2}:G{row2}")
        ws[f"A{row2}"] = "Comparativo por Canal"
        ws[f"A{row2}"].font = FONT_SECTION
        ws[f"A{row2}"].fill = FILL_CREAM

        por_canal = comp.get("por_canal")
        if por_canal is not None and not por_canal.empty:
            _header_row(ws, row2 + 1, ["Canal", label_a, label_b,
                                         "Variacion $", "Variacion %"])
            for ri3, (idx, crow) in enumerate(por_canal.iterrows(), row2 + 2):
                va = crow.get("periodo_a", 0)
                vb = crow.get("periodo_b", 0)
                vd = crow.get("variacion_abs", 0)
                vp = crow.get("variacion_pct", 0)
                _data_row(ws, ri3, [idx, va, vb, vd, vp / 100], neg_cols=[4])
                for ci, fmt in [(2, FMT_CURRENCY), (3, FMT_CURRENCY),
                                 (4, FMT_CURRENCY), (5, FMT_PCT1)]:
                    ws.cell(row=ri3, column=ci).number_format = fmt

        # Anchos
        for i, w in enumerate([22, 18, 18, 16, 14, 14], 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    # ------------------------------------------------------------------
    # Hoja 8 (opcional): Contexto de mercado externo
    # ------------------------------------------------------------------

    def _sheet_contexto_mercado(self, contexto: Dict):
        """Hoja con el contexto de mercado (CRT, agave, NOM) buscado por el agente."""
        ws = self.wb.create_sheet("Contexto Mercado")
        ws.sheet_view.showGridLines = False

        ws.merge_cells("A1:E1")
        ws["A1"] = "Contexto de Mercado Externo"
        ws["A1"].font = FONT_TITLE
        ws["A1"].fill = _fill("FFF8F0")

        if not contexto.get("disponible", False):
            ws.merge_cells("A3:E3")
            ws["A3"] = contexto.get("resumen", "Sin contexto de mercado disponible.")
            ws["A3"].font = FONT_SUB
            ws["A3"].alignment = _align("left", wrap=True)
            ws.row_dimensions[3].height = 40
            ws.merge_cells("A5:E5")
            ws["A5"] = ("Para incluir contexto de mercado, solicitar al agente: "
                        "'busca estadisticas CRT, precio agave y cambios NOM-006 "
                        "para la semana {semana} de {anio} y agrega el contexto al reporte'")
            ws["A5"].font = _font(italic=True, color=SECTION_SUBTITLE, size=9)
            ws["A5"].alignment = _align("left", wrap=True)
            ws.row_dimensions[5].height = 40
        else:
            # Resumen general
            ws.merge_cells("A3:E5")
            ws["A3"] = contexto["resumen"][:2000]
            ws["A3"].alignment = _align("left", wrap=True)
            ws["A3"].font = FONT_BODY
            ws.row_dimensions[3].height = 80

            # Hallazgos del mercado
            row = 7
            ws.merge_cells(f"A{row}:E{row}")
            ws[f"A{row}"] = "Hallazgos de Mercado"
            ws[f"A{row}"].font = FONT_SECTION
            ws[f"A{row}"].fill = FILL_CREAM

            _header_row(ws, row + 1, ["#", "Hallazgo", "Tipo", "Impacto", "Recomendacion"])
            for ri, h in enumerate(contexto.get("hallazgos", []), row + 2):
                tipo_color = TRAFFIC_RED if h["tipo"] == "Riesgo" else (
                    TRAFFIC_GREEN if h["tipo"] == "Oportunidad" else TRAFFIC_YELLOW)
                _data_row(ws, ri, [ri - (row + 1), h["hallazgo"], h["tipo"],
                                    h["impacto"], h["recomendacion"]])
                ws.cell(row=ri, column=3).font = _font(bold=True, color=tipo_color, size=9)

            # Fuentes
            if contexto.get("fuentes"):
                src_row = row + 2 + len(contexto["hallazgos"]) + 2
                ws.cell(row=src_row, column=1, value="Fuentes consultadas:").font = FONT_SECTION
                for i, fuente in enumerate(contexto["fuentes"], src_row + 1):
                    ws.cell(row=i, column=1, value=fuente).font = FONT_SUB

        for i, w in enumerate([5, 45, 14, 24, 40], 1):
            ws.column_dimensions[get_column_letter(i)].width = w


# ---------------------------------------------------------------------------
# Funcion de entrada
# ---------------------------------------------------------------------------

def generate_xlsx(
    processor: LocoDataProcessor,
    output_path: str,
    comparativo_custom: Optional[Dict] = None,
    contexto_mercado: Optional[Dict] = None,
):
    """
    Genera el XLSX ejecutivo y lo guarda en output_path.

    Params opcionales:
      comparativo_custom : resultado de proc.get_comparativo_custom(...)
      contexto_mercado   : resultado de market_context.load_market_context(...)
    """
    gen = LocoReporteXLSX(processor, output_path)

    # Hojas base siempre
    gen._sheet_resumen()
    gen._sheet_comparativo()
    gen._sheet_productos()
    gen._sheet_clientes()
    gen._sheet_regional()
    gen._sheet_oportunidades()

    # Hojas opcionales
    if comparativo_custom:
        gen._sheet_comparativo_custom(comparativo_custom)

    if contexto_mercado:
        gen._sheet_contexto_mercado(contexto_mercado)
    else:
        # Siempre incluir hoja de contexto, aunque sea el placeholder
        gen._sheet_contexto_mercado({"disponible": False,
                                      "resumen": "", "fuentes": [], "hallazgos": []})

    gen.wb.save(output_path)
    print(f"[XLSX] Guardado: {output_path}")
