"""
dashboard_generator.py
======================
Genera un dashboard HTML auto-contenido con:
  - Filtros interactivos reactivos (Año, Semana, Producto, Canal, Estado, Cliente)
  - Recálculo dinámico en tiempo real de KPIs y de las 5 gráficas Chart.js
  - Tabla filtrable con ordenamiento por columna y paginación
  - Descarga de CSV de datos filtrados con codificación UTF-8 BOM
  - Descarga de imágenes PNG para cada gráfica e independiente

Paleta: Design.md (brand-maroon #6E1E28, highlight-cream #FBF3DD, etc.)
Chart.js vía CDN (sin costo).
"""

import json
import os
import base64
from typing import Optional
import pandas as pd
import numpy as np

import design_tokens as dt
from design_tokens import (
    BRAND_MAROON, BRAND_MAROON_DEEP, HIGHLIGHT_CREAM, PAGE_BG, RULE_LINE,
    HEADER_TEXT, SECTION_SUBTITLE, NEG_VALUE, POS_VALUE,
    PRODUCT_ORDER, PRODUCT_DISPLAY_NAMES, PRODUCT_COLORS,
    CANAL_ORDER, CANAL_COLORS,
    CHART_PLAN_LINE, CHART_LASTYEAR_AREA, CHART_LASTYEAR_LINE, CHART_GRID,
    fmt_currency, fmt_int,
)
from data_processor import LocoDataProcessor
from logo_processor import get_logo_for_html


# ---------------------------------------------------------------------------
# Serialización segura de datos a JSON
# ---------------------------------------------------------------------------

class _SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if pd.isna(obj):
            return 0
        return super().default(obj)


def _to_json(obj) -> str:
    return json.dumps(obj, cls=_SafeEncoder, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Comparativo 8 Columnas (réplica de la tabla del PDF — pdf_generator._draw_kpi_table)
# ---------------------------------------------------------------------------

def _build_comparativo_8col(proc: LocoDataProcessor) -> dict:
    """Réplica en Python de la lógica EXACTA de
    pdf_generator.PDFReportGenerator._draw_kpi_table (no se modifica ese
    archivo, solo se reproduce su cruce de datos) para poder alimentar la
    nueva pestaña "Comparativo 8 Columnas" del dashboard con la misma fuente
    de verdad que usa el PDF (proc._filter_period/_filter_ytd + proc.dfp),
    en vez de recalcular desde DATA.tabla en JS.

    Estructura de salida:
        {"producto": {"semanal": [filas...], "anual": [filas...]},
         "canal":    {"semanal": [filas...], "anual": [filas...]}}

    Cada fila: categoria, actual, anio_anterior, plan (o None si la
    categoría no es comparable a Plan), var_plan_abs/var_plan_pct (o None),
    var_anio_abs (siempre numérico) y var_anio_pct (None = "N/D" cuando el
    año anterior no existe en absoluto en los datos, mismo criterio que
    _year_exists()/var() en get_resumen_ejecutivo()).
    """
    yw, ww = proc.anio, proc.semana
    py, pw = proc.anio - 1, proc.semana

    # Igual que vs_anio_anterior en get_resumen_ejecutivo(): si el año
    # anterior no existe en absoluto en los datos cargados, no hay base real
    # de comparación → var_anio_pct debe ser None ("N/D"), no un falso "+100%".
    year_b_ok = proc._year_exists(py)

    plan_df = proc.dfp
    if plan_df is not None and not plan_df.empty:
        p_filter = plan_df[(plan_df["anio_num"] == yw) & (plan_df["semana_num"] == ww)]
    else:
        p_filter = None

    groupings = [
        ("producto", PRODUCT_ORDER, "producto", PRODUCT_DISPLAY_NAMES),
        ("canal",    CANAL_ORDER,   "canal_norm", {k: k for k in CANAL_ORDER}),
    ]

    result = {}
    for key, cats, group_col, disp in groupings:
        result[key] = {}
        if p_filter is not None and not p_filter.empty:
            p_agg = p_filter.groupby(group_col)["plan_venta_sin_impuestos"].sum()
        else:
            p_agg = pd.Series(dtype=float)

        for mode in ("semanal", "anual"):
            if mode == "semanal":
                df_cur  = proc._filter_period(yw, ww)
                df_prev = proc._filter_period(py, pw)
            else:
                df_cur  = proc._filter_ytd(yw, ww)
                df_prev = proc._filter_ytd(py, pw)

            agg_cur  = df_cur.groupby(group_col)["venta_sin_impuestos"].sum()
            agg_prev = df_prev.groupby(group_col)["venta_sin_impuestos"].sum()

            rows = []
            total_cur = total_prev = total_plan = 0.0
            total_var_plan = total_var_anio = 0.0

            for cat in cats:
                cv = float(agg_cur.get(cat, 0) or 0)
                pv = float(agg_prev.get(cat, 0) or 0)

                # "Otros" es, por diseño (design_tokens.PRODUCT_ORDER/CANAL_ORDER),
                # el bucket dedicado a venta real sin Plan presupuestado
                # asociado (Agave/Servicios/KIT's/etc. para producto; canales
                # no catalogados para canal) — regla confirmada con el
                # cliente: su columna Plan y variaciones vs Plan son "N/A",
                # nunca un $0 inventado. Actual y Año Anterior sí son dinero
                # real y se muestran normalmente.
                es_comparable = (cat != "Otros")

                if es_comparable:
                    plv = float(p_agg.get(cat, 0) or 0)
                    v_plan_abs = cv - plv
                    v_plan_pct = (v_plan_abs / plv * 100) if plv > 0 else 0.0
                    total_plan += plv
                    total_var_plan += v_plan_abs
                else:
                    plv = None
                    v_plan_abs = None
                    v_plan_pct = None

                v_anio_abs = cv - pv
                if not year_b_ok:
                    v_anio_pct = None
                else:
                    v_anio_pct = (v_anio_abs / pv * 100) if pv != 0 else (100.0 if cv > 0 else 0.0)

                total_cur  += cv
                total_prev += pv
                total_var_anio += v_anio_abs

                rows.append({
                    "categoria":      disp.get(cat, cat),
                    "actual":         round(cv, 2),
                    "anio_anterior":  round(pv, 2),
                    "plan":           (round(plv, 2) if plv is not None else None),
                    "var_plan_abs":   (round(v_plan_abs, 2) if v_plan_abs is not None else None),
                    "var_plan_pct":   (round(v_plan_pct, 1) if v_plan_pct is not None else None),
                    "var_anio_abs":   round(v_anio_abs, 2),
                    "var_anio_pct":   (round(v_anio_pct, 1) if v_anio_pct is not None else None),
                })

            # Fila Total: el Plan del Total suma SOLO lo comparable (las
            # categorías "N/A" no aportan nada, ya que no fue presupuestado).
            tv_plan_pct = (total_var_plan / total_plan * 100) if total_plan > 0 else 0.0
            if not year_b_ok:
                tv_anio_pct = None
            else:
                tv_anio_pct = (total_var_anio / total_prev * 100) if total_prev != 0 else (100.0 if total_cur > 0 else 0.0)

            rows.append({
                "categoria":      "Total",
                "actual":         round(total_cur, 2),
                "anio_anterior":  round(total_prev, 2),
                "plan":           round(total_plan, 2),
                "var_plan_abs":   round(total_var_plan, 2),
                "var_plan_pct":   round(tv_plan_pct, 1),
                "var_anio_abs":   round(total_var_anio, 2),
                "var_anio_pct":   (round(tv_anio_pct, 1) if tv_anio_pct is not None else None),
            })

            result[key][mode] = rows

    return result


# ---------------------------------------------------------------------------
# Preparar datos para el dashboard
# ---------------------------------------------------------------------------

def _prepare_data(proc: LocoDataProcessor, contexto_mercado: Optional[dict] = None) -> dict:
    """Prepara todos los datasets que el dashboard necesita para filtrado reactivo."""
    df = proc.get_dataframe_dashboard()
    df = df.fillna(0)
    df["fecha"] = df["fecha"].astype(str)

    # Filtros disponibles
    semanas = sorted([int(s) for s in df["semana_num"].dropna().unique().tolist() if s > 0])
    anios   = sorted([int(a) for a in df["anio"].dropna().unique().tolist() if a > 0])
    productos = [PRODUCT_DISPLAY_NAMES.get(p, p) for p in PRODUCT_ORDER if p in df["producto"].unique()]
    canales   = [c for c in CANAL_ORDER if c in df["canal"].unique()]
    estados   = sorted([str(e) for e in df["estado"].dropna().unique().tolist() if str(e).strip()])
    clientes  = sorted([str(cl) for cl in df["cliente"].dropna().unique().tolist() if str(cl).strip()])

    # Agrupar tabla transaccional limpia para TODOS los registros del dataset
    # "comparable_plan" se agrega al groupby (feature: filtro global
    # "Comparables a Plan"/"No comparables con Plan") — es seguro porque es
    # 1:1 con producto_display/categoria_negocio (nunca fragmenta un grupo
    # que antes era una sola fila en dos), así sobrevive al reset_index() y
    # llega a cada registro de DATA.tabla para poder filtrarlo en JS.
    df_tabla = df.groupby(
        ["anio", "semana_num", "semana", "producto_display", "canal", "estado", "cliente",
         "comparable_plan"]
    ).agg(
        venta_sin_iva=("venta_sin_iva", "sum"),
        botellas=("botellas", "sum"),
        cajas_9l=("cajas_9l", "sum"),
        margen_pesos=("margen_pesos", "sum"),
    ).reset_index()

    df_tabla["margen_pct"] = (df_tabla["margen_pesos"] / df_tabla["venta_sin_iva"] * 100).fillna(0).round(1)

    tabla_records = df_tabla.to_dict(orient="records")
    for rec in tabla_records:
        rec["anio"] = int(rec["anio"])
        rec["semana_num"] = int(rec["semana_num"])
        rec["venta_sin_iva"] = round(float(rec["venta_sin_iva"]), 2)
        rec["botellas"] = round(float(rec["botellas"]), 2)
        rec["cajas_9l"] = round(float(rec["cajas_9l"]), 2)
        rec["margen_pesos"] = round(float(rec["margen_pesos"]), 2)
        rec["margen_pct"] = round(float(rec["margen_pct"]), 1)
        # bool(...) evita que json.dumps falle con numpy.bool_ (dtype nativo
        # de pandas tras el groupby de una columna booleana).
        rec["comparable_plan"] = bool(rec["comparable_plan"])
        for k, v in rec.items():
            if isinstance(v, float) and (v != v):
                rec[k] = 0

    # Plan semanal mapeado
    plan_map = {}
    if proc.dfp is not None and not proc.dfp.empty:
        dfp = proc.dfp
        grp_p = dfp.groupby(["anio_num", "semana_num"])["plan_venta_sin_impuestos"].sum().reset_index()
        for _, r in grp_p.iterrows():
            if pd.notna(r["anio_num"]) and pd.notna(r["semana_num"]):
                k_full = f"{int(r['anio_num'])}-W{int(r['semana_num']):02d}"
                k_sem  = f"W{int(r['semana_num']):02d}"
                val = float(r["plan_venta_sin_impuestos"])
                plan_map[k_full] = val
                plan_map[k_sem]  = plan_map.get(k_sem, 0) + val

    # Plan desglosado por producto y canal: permite que la línea de plan de las
    # gráficas respete los filtros de Producto/Canal. El plan de origen no trae
    # estado ni cliente, así que esos filtros no lo afectan.
    plan_detail = []
    if proc.dfp is not None and not proc.dfp.empty:
        dfp = proc.dfp
        needed = {"anio_num", "semana_num", "producto", "canal_norm",
                  "plan_venta_sin_impuestos"}
        if needed.issubset(set(dfp.columns)):
            grp_d = dfp.groupby(
                ["anio_num", "semana_num", "producto", "canal_norm"]
            )["plan_venta_sin_impuestos"].sum().reset_index()
            for _, r in grp_d.iterrows():
                if pd.isna(r["anio_num"]) or pd.isna(r["semana_num"]):
                    continue
                plan_detail.append({
                    "k": f"{int(r['anio_num'])}-W{int(r['semana_num']):02d}",
                    "p": PRODUCT_DISPLAY_NAMES.get(r["producto"], r["producto"]),
                    "c": r["canal_norm"],
                    "v": round(float(r["plan_venta_sin_impuestos"]), 2),
                })

    # Comparativo 8 Columnas (pestaña nueva) — misma fuente de verdad que el
    # PDF (_draw_kpi_table): se calcula en Python, no se recalcula en JS.
    comparativo_8col = _build_comparativo_8col(proc)

    # Resumen ejecutivo inicial
    resumen = proc.get_resumen_ejecutivo()

    # Oportunidades y riesgos: internos + contexto de mercado (si se proporcionó)
    oportunidades = proc.get_oportunidades_riesgos()
    if contexto_mercado and contexto_mercado.get("disponible"):
        # Quitar el placeholder interno de "contexto no disponible"
        oportunidades = [o for o in oportunidades
                         if "Contexto de mercado no disponible" not in o.get("hallazgo", "")]
        # Agregar los hallazgos reales del contexto de mercado (CRT/agave/NOM)
        oportunidades = oportunidades + contexto_mercado.get("hallazgos", [])

    return {
        "meta": {
            "semana": proc.semana,
            "anio": proc.anio,
            "semana_label": f"Semana {proc.semana:02d} · {proc.anio}",
        },
        "filtros": {
            "semanas": semanas,
            "anios": anios,
            "productos": productos,
            "canales": canales,
            "estados": estados,
            "clientes": clientes,
        },
        "kpis_initial": {
            "ventas_netas": float(resumen["actual"]["ventas_netas"]),
            "plan": float(resumen["plan"]["ventas_netas"]),
            "vs_plan_pct": float(resumen["vs_plan"]["pct"]),
            "vs_semana_ant_pct": float(resumen["vs_semana_anterior"]["pct"]),
            # "pct" puede ser None cuando no hay histórico del año anterior
            # cargado (ver var()/year_b en get_resumen_ejecutivo) — se pasa
            # como null al JS, que lo interpreta como "N/D".
            "vs_anio_ant_pct": (None if resumen["vs_anio_anterior"]["pct"] is None else float(resumen["vs_anio_anterior"]["pct"])),
            "ytd": float(resumen["ytd_actual"]["ventas_netas"]),
            "ytd_vs_ly_pct": (None if resumen["ytd_vs_ly"]["pct"] is None else float(resumen["ytd_vs_ly"]["pct"])),
            "botellas": float(resumen["actual"]["botellas"]),
            "margen_pct": float(resumen["actual"]["margen_pct"]),
            "ticket": float(resumen["actual"]["ticket_promedio"]),
        },
        "plan_map": plan_map,
        "plan_detail": plan_detail,
        "comparativo_8col": comparativo_8col,
        "tabla": tabla_records,
        "oportunidades": oportunidades,
        "product_colors": {PRODUCT_DISPLAY_NAMES.get(k, k): v for k, v in PRODUCT_COLORS.items()},
        "canal_colors": CANAL_COLORS,
    }


# ---------------------------------------------------------------------------
# Template HTML
# ---------------------------------------------------------------------------

def _build_html(data: dict, logo_svg: str = "") -> str:
    data_json = _to_json(data)

    maroon      = BRAND_MAROON
    maroon_deep = BRAND_MAROON_DEEP
    cream       = HIGHLIGHT_CREAM
    neg_color   = NEG_VALUE
    grid_color  = CHART_GRID
    subtitle_c  = SECTION_SUBTITLE

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Ventas — Loco Tequila</title>
  <meta name="description" content="Dashboard ejecutivo de ventas semanales Loco Tequila con filtros interactivos, recálculo dinámico y descarga de datos e imágenes.">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --brand-maroon:      {maroon};
      --brand-maroon-deep: {maroon_deep};
      --cream:             {cream};
      --neg:               {neg_color};
      --grid:              {grid_color};
      --sub:               {subtitle_c};
      --bg:                #F5F5F5;
      --card-bg:           #FFFFFF;
      --text:              #222222;
      --header-height:     86px;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Poppins', sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 13px;
    }}

    /* ── Header ──
       Sticky (no fixed) para no requerir padding-top compensatorio en
       body/main. z-index 500: por debajo del modal de gráfica ampliada
       (.chart-modal-overlay usa 999) y por encima del contenido normal
       (panel de filtros incluido, que no usa position sticky/fixed). */
    header {{
      position: sticky;
      top: 0;
      z-index: 500;
      background: linear-gradient(135deg, var(--brand-maroon) 0%, var(--brand-maroon-deep) 100%);
      color: #fff;
      padding: 18px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 3px 12px rgba(110,30,40,0.35);
    }}
    header h1 {{ font-size: 1.4rem; font-weight: 700; letter-spacing: 0.3px; }}
    header .subtitle {{ font-size: 0.78rem; opacity: 0.85; margin-top: 2px; }}
    .logo-area {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
    }}
    .logo-area img, .logo-area svg {{
      height: 50px;
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0 1px 3px rgba(0,0,0,0.3));
    }}
    .logo-fallback {{
      text-align: right;
      font-size: 1.6rem;
      font-weight: 900;
      letter-spacing: 2px;
      color: #fff;
    }}
    .logo-fallback span {{ display: block; font-size: 0.55rem; font-weight: 400; letter-spacing: 4px; opacity: 0.8; }}

    /* ── Filter panel (lateral colapsable) ──
       Antes era una barra horizontal (.filter-bar) arriba del contenido.
       Ahora es un panel <aside> a la izquierda dentro de .app-shell, con
       flujo normal (no sticky/fixed) para no competir en z-index con el
       header sticky (punto 6) — se desplaza junto con la página. */
    .app-shell {{ display: flex; align-items: flex-start; }}
    .content-wrap {{ flex: 1; min-width: 0; }}

    .filter-panel {{
      background: var(--card-bg);
      border-right: 3px solid var(--brand-maroon);
      width: 250px;
      flex-shrink: 0;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: width 0.22s ease, padding 0.22s ease;
      overflow: hidden;
    }}
    .filter-panel.collapsed {{
      width: 44px;
      padding: 14px 6px;
    }}
    .filter-panel.collapsed .filter-panel-body {{ display: none; }}
    .filter-panel.collapsed .filter-panel-title {{ display: none; }}

    .filter-panel-header {{ display: flex; align-items: center; gap: 8px; }}
    .filter-panel-title {{ font-size: 0.74rem; font-weight: 700; color: var(--brand-maroon); text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; }}
    .filter-toggle-btn {{
      background: var(--brand-maroon);
      color: #fff;
      border: none;
      border-radius: 6px;
      width: 30px;
      height: 30px;
      flex-shrink: 0;
      cursor: pointer;
      font-size: 0.95rem;
      transition: background 0.2s;
    }}
    .filter-toggle-btn:hover {{ background: var(--brand-maroon-deep); }}

    .filter-panel-body {{ display: flex; flex-direction: column; gap: 12px; }}
    .filter-panel label {{ font-size: 0.7rem; font-weight: 600; color: var(--sub); text-transform: uppercase; letter-spacing: 0.5px; }}
    .filter-panel select, .filter-panel input {{
      width: 100%;
      padding: 6px 10px;
      border: 1.5px solid #DDD;
      border-radius: 6px;
      font-size: 0.78rem;
      font-family: 'Poppins', sans-serif;
      background: #FAFAFA;
      transition: border-color 0.2s;
    }}
    .filter-panel select:focus, .filter-panel input:focus {{
      border-color: var(--brand-maroon);
      outline: none;
    }}
    .filter-group {{ display: flex; flex-direction: column; gap: 3px; }}
    .filter-btn-row {{ display: flex; flex-direction: column; gap: 8px; }}
    .btn {{
      padding: 7px 16px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-family: 'Poppins', sans-serif;
      font-size: 0.78rem;
      font-weight: 600;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}
    .btn-primary {{
      background: var(--brand-maroon);
      color: #fff;
    }}
    .btn-primary:hover {{ background: var(--brand-maroon-deep); transform: translateY(-1px); }}
    .btn-secondary {{
      background: var(--cream);
      color: var(--brand-maroon);
      border: 1.5px solid var(--brand-maroon);
    }}
    .btn-secondary:hover {{ background: #f0e6e8; }}

    .filter-status {{
      font-size: 0.72rem;
      color: var(--brand-maroon);
      font-weight: 600;
      background: #FBF3DD;
      padding: 6px 10px;
      border-radius: 10px;
      text-align: center;
    }}

    /* ── Segmented control (toggle Valores $ / % apilado) ── */
    .seg-control {{
      display: flex;
      background: rgba(255,255,255,0.15);
      border: 1px solid rgba(255,255,255,0.4);
      border-radius: 6px;
      overflow: hidden;
      flex-shrink: 0;
    }}
    .seg-btn {{
      background: transparent;
      color: #fff;
      border: none;
      padding: 4px 10px;
      font-family: 'Poppins', sans-serif;
      font-size: 0.68rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }}
    .seg-btn:hover {{ background: rgba(255,255,255,0.18); }}
    .seg-btn.active {{ background: #fff; color: var(--brand-maroon); }}

    /* ── Main layout ── */
    main {{ padding: 20px 32px; max-width: 1600px; margin: 0 auto; }}

    /* ── KPI cards (Sticky) ── */
    .kpi-sticky-container {{
      position: sticky;
      top: var(--header-height, 86px);
      z-index: 450;
      background: var(--bg);
      padding: 8px 0 14px 0;
      margin-top: -8px;
      margin-bottom: 20px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 0;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border-radius: 10px;
      padding: 16px 18px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
      border-left: 4px solid var(--brand-maroon);
      transition: transform 0.18s, box-shadow 0.18s;
    }}
    .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(110,30,40,0.14); }}
    .kpi-card .kpi-label {{ font-size: 0.68rem; color: var(--sub); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
    .kpi-card .kpi-value {{ font-size: 1.45rem; font-weight: 700; color: var(--brand-maroon); margin: 4px 0; }}
    .kpi-card .kpi-delta {{ font-size: 0.72rem; font-weight: 500; min-height: 1.1em; }}
    .kpi-card .kpi-delta.pos {{ color: #00B050; }}
    .kpi-card .kpi-delta.neg {{ color: var(--neg); }}

    /* ── Charts grid ── */
    .charts-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-bottom: 22px;
    }}
    .charts-grid.one-col {{ grid-template-columns: 1fr; }}
    .chart-card {{
      background: var(--card-bg);
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
      overflow: hidden;
    }}
    .chart-card .chart-title {{
      background: var(--brand-maroon);
      color: #fff;
      padding: 9px 16px;
      font-size: 0.78rem;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .chart-card .chart-note {{
      font-size: 0.62rem;
      opacity: 0.85;
      font-style: italic;
      display: block;
      margin-top: 1px;
    }}
    .chart-card .chart-body {{ padding: 14px; position: relative; background: #FFFFFF; }}

    .btn-chart-img {{
      background: rgba(255, 255, 255, 0.2);
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.4);
      border-radius: 4px;
      padding: 3px 9px;
      font-size: 0.68rem;
      font-family: 'Poppins', sans-serif;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }}
    .btn-chart-img:hover {{
      background: #ffffff;
      color: var(--brand-maroon);
      transform: translateY(-1px);
    }}
    .chart-actions {{ display: flex; gap: 6px; align-items: center; flex-shrink: 0; }}

    /* ── Modal de gráfica ampliada ── */
    .chart-modal-overlay {{
      position: fixed;
      inset: 0;
      background: rgba(30, 12, 15, 0.62);
      backdrop-filter: blur(2px);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
      z-index: 999;
    }}
    .chart-modal-overlay.open {{ display: flex; }}
    .chart-modal {{
      background: var(--card-bg);
      border-radius: 12px;
      box-shadow: 0 18px 50px rgba(0,0,0,0.38);
      width: 100%;
      max-width: 1280px;
      max-height: 92vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .chart-modal-head {{
      background: var(--brand-maroon);
      color: #fff;
      padding: 12px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      font-size: 0.92rem;
      font-weight: 600;
    }}
    .chart-modal-close {{
      background: rgba(255,255,255,0.18);
      color: #fff;
      border: 1px solid rgba(255,255,255,0.45);
      border-radius: 6px;
      padding: 5px 14px;
      font-family: 'Poppins', sans-serif;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }}
    .chart-modal-close:hover {{ background: #fff; color: var(--brand-maroon); }}
    .chart-modal-body {{
      padding: 18px;
      background: #FFFFFF;
      flex: 1;
      min-height: 0;
      position: relative;
    }}
    .chart-modal-canvas-wrap {{ position: relative; width: 100%; height: 72vh; }}

    /* ── Tabs (Dashboard General / Comparativo 8 Columnas) ── */
    .tab-nav {{
      display: flex;
      gap: 4px;
      padding: 0 32px;
      background: var(--card-bg);
      border-bottom: 2px solid var(--brand-maroon);
    }}
    .tab-btn {{
      background: transparent;
      border: none;
      padding: 12px 20px;
      font-family: 'Poppins', sans-serif;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--sub);
      cursor: pointer;
      border-bottom: 3px solid transparent;
      transition: color 0.2s, border-color 0.2s;
    }}
    .tab-btn:hover {{ color: var(--brand-maroon); }}
    .tab-btn.active {{ color: var(--brand-maroon); border-bottom-color: var(--brand-maroon); }}

    /* ── Comparativo 8 Columnas (réplica de la tabla del PDF) ── */
    .comp8-cat {{ text-align: center; }}
    .comp8-actual {{ background: var(--cream); font-weight: 700; }}
    .comp8-table thead th:first-child, .comp8-table tbody td:first-child {{ text-align: right; }}
    tr.comp8-total {{ background: #F0E6D8; font-weight: 700; }}
    tr.comp8-total td.comp8-actual {{ background: var(--cream); }}

    /* ── Table ── */
    .table-card {{
      background: var(--card-bg);
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
      margin-bottom: 22px;
      overflow: hidden;
    }}
    .table-header {{
      background: var(--brand-maroon);
      color: #fff;
      padding: 10px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.82rem;
      font-weight: 600;
    }}
    .table-wrapper {{ overflow-x: auto; max-height: 380px; overflow-y: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.75rem; }}
    thead th {{
      background: var(--cream);
      color: var(--brand-maroon);
      padding: 8px 10px;
      text-align: right;
      font-weight: 700;
      position: sticky;
      top: 0;
      cursor: pointer;
      user-select: none;
      border-bottom: 2px solid var(--brand-maroon);
      white-space: nowrap;
    }}
    thead th:first-child {{ text-align: left; }}
    thead th:hover {{ background: #f0e6e8; }}
    thead th .sort-icon {{ margin-left: 4px; opacity: 0.5; }}
    tbody tr {{ transition: background 0.12s; }}
    tbody tr:nth-child(even) {{ background: #FAFAFA; }}
    tbody tr:hover {{ background: var(--cream); }}
    tbody td {{ padding: 6px 10px; text-align: right; border-bottom: 1px solid #F0F0F0; }}
    tbody td:first-child {{ text-align: left; }}
    .neg-val {{ color: var(--neg); font-weight: 600; }}

    /* ── Opportunities ── */
    .opp-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .opp-card {{
      background: var(--card-bg);
      border-radius: 10px;
      padding: 14px 16px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
      border-top: 4px solid;
    }}
    .opp-card.riesgo {{ border-color: var(--neg); }}
    .opp-card.oportunidad {{ border-color: #00B050; }}
    .opp-card.informacion {{ border-color: #FFC000; }}
    .opp-tipo {{ font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px; }}
    .opp-tipo.riesgo {{ color: var(--neg); }}
    .opp-tipo.oportunidad {{ color: #00B050; }}
    .opp-tipo.informacion {{ color: #FFC000; }}
    .opp-hallazgo {{ font-size: 0.78rem; font-weight: 600; margin-bottom: 6px; }}
    .opp-impacto {{ font-size: 0.7rem; color: var(--sub); margin-bottom: 4px; }}
    .opp-rec {{ font-size: 0.72rem; border-top: 1px solid #EEE; padding-top: 6px; margin-top: 4px; }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 16px;
      font-size: 0.68rem;
      color: var(--sub);
      border-top: 1px solid #E8E8E8;
    }}

    /* ── Pagination ── */
    .pagination {{
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: flex-end;
      padding: 10px 18px;
      font-size: 0.75rem;
    }}
    .page-info {{ color: var(--sub); }}

    @media (max-width: 800px) {{
      .charts-grid {{ grid-template-columns: 1fr; }}
      header {{ flex-direction: column; gap: 8px; text-align: center; }}
      .app-shell {{ flex-direction: column; }}
      .filter-panel {{ width: 100%; border-right: none; border-bottom: 3px solid var(--brand-maroon); }}
      .filter-panel.collapsed {{ width: 100%; }}
      main {{ padding: 14px 16px; }}
    }}
  </style>
</head>
<body>

<header>
  <div>
    <h1>Dashboard · Ventas y Margen</h1>
    <div class="subtitle" id="headerSubtitle">Cargando...</div>
  </div>
  <div class="logo-area">
    {logo_svg if logo_svg else '<div class="logo-fallback">LOCO<span>TEQUILA</span></div>'}
  </div>
</header>

<div class="app-shell">
  <!-- Panel de filtros lateral colapsable (antes era .filter-bar horizontal).
       Misma funcionalidad exacta: mismos ids y listeners en los 6 selects
       y 4 botones — solo cambió el layout/CSS y el contenedor padre. -->
  <aside class="filter-panel" id="filterPanel">
    <div class="filter-panel-header">
      <button class="filter-toggle-btn" id="filterToggleBtn" onclick="toggleFilterPanel()"
              aria-expanded="true" aria-controls="filterPanelBody" title="Mostrar/ocultar filtros">☰</button>
      <span class="filter-panel-title">Filtros</span>
    </div>
    <div class="filter-panel-body" id="filterPanelBody">
      <div class="filter-group">
        <label>Año</label>
        <select id="fAnio" onchange="applyFilters()"><option value="all">Todos</option></select>
      </div>
      <div class="filter-group">
        <label>Semana</label>
        <select id="fSemana" onchange="applyFilters()"><option value="all">Todas</option></select>
      </div>
      <div class="filter-group">
        <label>Producto</label>
        <select id="fProducto" onchange="applyFilters()"><option value="all">Todos</option></select>
      </div>
      <div class="filter-group">
        <label>Canal</label>
        <select id="fCanal" onchange="applyFilters()"><option value="all">Todos</option></select>
      </div>
      <div class="filter-group">
        <label>Estado</label>
        <select id="fEstado" onchange="applyFilters()"><option value="all">Todos</option></select>
      </div>
      <div class="filter-group">
        <label>Cliente</label>
        <select id="fCliente" onchange="applyFilters()"><option value="all">Todos</option></select>
      </div>
      <div class="filter-group">
        <label>Comparables a Plan</label>
        <select id="fComparablePlan" onchange="applyFilters()">
          <option value="comparables">Comparables a Plan</option>
          <option value="no_comparables">No Comparables con Plan</option>
        </select>
      </div>
      <div class="filter-btn-row">
        <button class="btn btn-primary" onclick="applyFilters()">⚡ Aplicar</button>
        <button class="btn btn-secondary" onclick="resetFilters()">↺ Limpiar</button>
        <button class="btn btn-secondary" onclick="downloadCSV()">⬇ Descargar CSV</button>
        <button class="btn btn-secondary" onclick="downloadAllCharts()">📷 Descargar Gráficas</button>
      </div>
      <div class="filter-status" id="filterStatus">Mostrando todos los registros</div>
    </div>
  </aside>

  <div class="content-wrap">
  <nav class="tab-nav">
    <button class="tab-btn active" data-tab="general" onclick="switchTab('general')">Dashboard General</button>
    <button class="tab-btn" data-tab="comparativo8" onclick="switchTab('comparativo8')">Comparativo 8 Columnas</button>
  </nav>

  <section class="tab-content" id="tab-general">
  <main>
  <!-- KPIs (Sticky) -->
  <div class="kpi-sticky-container">
    <div class="kpi-grid" id="kpiGrid"></div>
  </div>

  <!-- Charts row 1 -->
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">
        <div>
          Ventas Netas Semanales ($MXN sin IVA)
          <span class="chart-note">Sin IVA ni IEPS · línea punteada = año anterior</span>
        </div>
        <div class="chart-actions">
          <button class="btn-chart-img" onclick="downloadChartImage('semanal', 'Ventas_Semanales_y_Plan')">📷 PNG</button>
          <button class="btn-chart-img" onclick="openChartModal('semanal')" title="Ver en grande">⛶ Ampliar</button>
        </div>
      </div>
      <div class="chart-body"><canvas id="chartSemanal" height="160"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">
        <div>
          Ventas por Producto por Semana
          <span class="chart-note">Barras apiladas sin IVA · líneas de plan y de año anterior</span>
        </div>
        <div class="chart-actions">
          <button class="btn-chart-img" onclick="downloadChartImage('producto', 'Ventas_Por_Producto')">📷 PNG</button>
          <button class="btn-chart-img" onclick="openChartModal('producto')" title="Ver en grande">⛶ Ampliar</button>
        </div>
      </div>
      <div class="chart-body"><canvas id="chartProducto" height="160"></canvas></div>
    </div>
  </div>

  <!-- Charts row 2 -->
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">
        <div>Ranking de Productos</div>
        <div class="chart-actions">
          <button class="btn-chart-img" onclick="downloadChartImage('ranking', 'Ranking_Productos')">📷 PNG</button>
          <button class="btn-chart-img" onclick="openChartModal('ranking')" title="Ver en grande">⛶ Ampliar</button>
        </div>
      </div>
      <div class="chart-body"><canvas id="chartRanking" height="130"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">
        <div>Top Regiones / Estados por Ventas</div>
        <div class="chart-actions">
          <button class="btn-chart-img" onclick="downloadChartImage('regional', 'Top_Regiones_Ventas')">📷 PNG</button>
          <button class="btn-chart-img" onclick="openChartModal('regional')" title="Ver en grande">⛶ Ampliar</button>
        </div>
      </div>
      <div class="chart-body"><canvas id="chartRegional" height="130"></canvas></div>
    </div>
  </div>

  <!-- Charts row 3: Canal -->
  <div class="charts-grid one-col">
    <div class="chart-card">
      <div class="chart-title">
        <div>
          Ventas por Canal por Semana
          <span class="chart-note">Sin IVA · total en miles arriba de cada barra</span>
        </div>
        <div class="chart-actions">
          <div class="seg-control" id="canalViewToggle">
            <button class="seg-btn active" data-mode="values" onclick="setCanalViewMode('values')">Valores ($)</button>
            <button class="seg-btn" data-mode="percent" onclick="setCanalViewMode('percent')">% (100% apilado)</button>
          </div>
          <button class="btn-chart-img" onclick="downloadChartImage('canal', 'Ventas_Por_Canal')">📷 PNG</button>
          <button class="btn-chart-img" onclick="openChartModal('canal')" title="Ver en grande">⛶ Ampliar</button>
        </div>
      </div>
      <div class="chart-body"><canvas id="chartCanal" height="110"></canvas></div>
    </div>
  </div>

  <!-- Tabla filtrable -->
  <div class="table-card">
    <div class="table-header">
      <span>Detalle de Ventas Filtradas</span>
      <span id="tableCount" style="font-size:0.72rem;opacity:0.8;"></span>
    </div>
    <div class="table-wrapper">
      <table id="mainTable">
        <thead>
          <tr>
            <th onclick="sortTable(0)">Semana <span class="sort-icon">⇅</span></th>
            <th onclick="sortTable(1)">Producto <span class="sort-icon">⇅</span></th>
            <th onclick="sortTable(2)">Canal <span class="sort-icon">⇅</span></th>
            <th onclick="sortTable(3)">Estado <span class="sort-icon">⇅</span></th>
            <th onclick="sortTable(4)">Cliente <span class="sort-icon">⇅</span></th>
            <th onclick="sortTable(5)">Ventas $ <span class="sort-icon">⇅</span></th>
            <th onclick="sortTable(6)">Botellas <span class="sort-icon">⇅</span></th>
            <th onclick="sortTable(7)">Margen % <span class="sort-icon">⇅</span></th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
    <div class="pagination">
      <span class="page-info" id="pageInfo"></span>
      <button class="btn btn-secondary" onclick="prevPage()">‹ Ant</button>
      <button class="btn btn-secondary" onclick="nextPage()">Sig ›</button>
    </div>
  </div>

  <!-- Oportunidades y Riesgos -->
  <div class="chart-card" style="margin-bottom:22px;">
    <div class="chart-title">Oportunidades y Riesgos Identificados</div>
    <div class="chart-body">
      <div class="opp-grid" id="oppGrid"></div>
    </div>
  </div>
  </main>
  </section>

  <!-- Pestaña: Comparativo 8 Columnas — réplica de la tabla del PDF
       (pdf_generator._draw_kpi_table), calculada en Python en
       DATA.comparativo_8col (misma fuente de verdad que el PDF: proc.dfp +
       proc._filter_period/_filter_ytd), NO recalculada desde DATA.tabla. -->
  <section class="tab-content" id="tab-comparativo8" hidden>
  <main>
  <!-- KPIs (repetidos a pedido del cliente en cada pestaña nueva, Sticky) -->
  <div class="kpi-sticky-container">
    <div class="kpi-grid" id="kpiGrid_comparativo8"></div>
  </div>

  <div class="table-card">
    <div class="table-header">
      <span>Comparativo 8 Columnas — Año Ant. · Plan · Actual · Var vs Plan · Var vs Año Ant.</span>
      <div class="seg-control" id="comparativo8ModeToggle">
        <button class="seg-btn active" data-mode="semanal" onclick="setComparativo8Mode('semanal')">Semanal</button>
        <button class="seg-btn" data-mode="anual" onclick="setComparativo8Mode('anual')">Anual (YTD)</button>
      </div>
    </div>
  </div>

  <div class="table-card">
    <div class="table-header"><span>Por Producto</span></div>
    <div class="table-wrapper" style="max-height:none;">
      <table class="comp8-table">
        <thead>
          <tr>
            <th>Año Ant.</th>
            <th>Plan</th>
            <th class="comp8-actual">Actual</th>
            <th class="comp8-cat">Categoría</th>
            <th>Var Plan $</th>
            <th>Var Plan %</th>
            <th>Var Año $</th>
            <th>Var Año %</th>
          </tr>
        </thead>
        <tbody id="comp8TableProducto"></tbody>
      </table>
    </div>
  </div>

  <div class="table-card">
    <div class="table-header"><span>Por Canal</span></div>
    <div class="table-wrapper" style="max-height:none;">
      <table class="comp8-table">
        <thead>
          <tr>
            <th>Año Ant.</th>
            <th>Plan</th>
            <th class="comp8-actual">Actual</th>
            <th class="comp8-cat">Categoría</th>
            <th>Var Plan $</th>
            <th>Var Plan %</th>
            <th>Var Año $</th>
            <th>Var Año %</th>
          </tr>
        </thead>
        <tbody id="comp8TableCanal"></tbody>
      </table>
    </div>
  </div>
  </main>
  </section>
  </div> <!-- /content-wrap -->
</div> <!-- /app-shell -->

<!-- Modal de gráfica ampliada -->
<div class="chart-modal-overlay" id="chartModalOverlay" onclick="handleModalBackdrop(event)"
     role="dialog" aria-modal="true" aria-labelledby="chartModalTitle">
  <div class="chart-modal">
    <div class="chart-modal-head">
      <span id="chartModalTitle">Gráfica</span>
      <button class="chart-modal-close" onclick="closeChartModal()" aria-label="Cerrar">✕ Cerrar</button>
    </div>
    <div class="chart-modal-body">
      <div class="chart-modal-canvas-wrap"><canvas id="chartModalCanvas"></canvas></div>
    </div>
  </div>
</div>

<footer>
  Loco Tequila · Dirección de Finanzas · Las ventas no incluyen IVA ni IEPS · Generado automáticamente
</footer>

<script>
// ── Datos embebidos ──────────────────────────────────────────────────────
const DATA = {data_json};

// ── Estado ───────────────────────────────────────────────────────────────
// Default inicial: solo comparables a Plan (mismo default que el <select>
// fComparablePlan, cuya primera <option> es "comparables"). Se recalcula de
// verdad en el primer applyFilters() disparado desde DOMContentLoaded.
let filteredTabla = DATA.tabla.filter(r => r.comparable_plan);
// Copia SIN el filtro "Comparables a Plan" aplicado (sí respeta los demás
// filtros: Año/Semana/Producto/Canal/Estado/Cliente) — la usa exclusivamente
// el Ranking de Productos, que por diseño nunca debe excluir por
// comparable_plan (debe mostrar siempre el mix completo de ventas).
let filteredTablaForRanking = [...DATA.tabla];
let sortCol = -1, sortAsc = true;
let page = 1;
const PAGE_SIZE = 50;
let charts = {{}};

// Fábricas de configuración: cada una devuelve un config NUEVO de Chart.js.
// Esto permite instanciar la misma gráfica dos veces (tarjeta + modal) sin que
// ambas instancias compartan los objetos dataset (Chart.js los muta).
let chartFactories = {{}};

const CHART_CANVAS = {{
  semanal:  'chartSemanal',
  producto: 'chartProducto',
  ranking:  'chartRanking',
  regional: 'chartRegional',
  canal:    'chartCanal',
}};

const CHART_TITLES = {{
  semanal:  'Ventas Netas Semanales ($MXN sin IVA)',
  producto: 'Ventas por Producto por Semana',
  ranking:  'Ranking de Productos',
  regional: 'Top Regiones / Estados por Ventas',
  canal:    'Ventas por Canal por Semana',
}};

let modalChart = null;
let modalChartKey = null;

// 'values' = barras apiladas por monto ($) · 'percent' = apiladas al 100%
// (cada canal como % del total de esa semana). Controlado por el toggle de
// la tarjeta "Ventas por Canal por Semana" (setCanalViewMode).
let canalViewMode = 'values';

// ── Plugin inline de Chart.js: datalabel del TOTAL apilado ────────────────
// Dibuja un texto arriba de cada barra apilada con el total de esa barra
// (no de cada segmento individual). Solo actúa sobre gráficas cuyas options
// declaren `plugins.stackedTotalLabels.enabled = true` (hoy solo la de
// Canal) para no afectar las demás gráficas apiladas del dashboard.
// Implementado 100% con la API nativa de Chart.js (afterDatasetsDraw +
// ctx.fillText) — sin librerías CDN adicionales, según el estándar del
// proyecto ("Standalone: un solo HTML sin dependencias externas más que
// Chart.js").
const stackedTotalLabelsPlugin = {{
  id: 'stackedTotalLabels',
  afterDatasetsDraw(chart) {{
    // OJO: `chart.options` es un objeto "resuelto" por Chart.js (proxy de
    // scriptable options) — leer una propiedad de función ahí (`formatter`)
    // hace que Chart.js la invoque solo con SU contexto interno antes de
    // devolverla, y esa auto-invocación revienta con "Cannot convert object
    // to primitive value" al intentar usar ese contexto como número. Hay que
    // leer la config cruda sin resolver desde `chart.config.options`.
    const cfg = chart.config.options.plugins && chart.config.options.plugins.stackedTotalLabels;
    if (!cfg || !cfg.enabled) return;
    const datasets = chart.data.datasets;
    if (!datasets || datasets.length === 0) return;
    const meta0 = chart.getDatasetMeta(0);
    if (!meta0 || !meta0.data) return;
    const {{ ctx, chartArea }} = chart;
    ctx.save();
    ctx.font = "600 10px 'Poppins', sans-serif";
    ctx.fillStyle = '#333333';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    meta0.data.forEach((_, i) => {{
      let total = 0;
      let topY = chartArea.bottom;
      datasets.forEach((ds, d) => {{
        const meta = chart.getDatasetMeta(d);
        if (meta.hidden) return;
        const val = ds.data[i];
        if (typeof val === 'number') total += val;
        const point = meta.data[i];
        // El punto más alto (menor y en pixeles) entre todos los segmentos
        // visibles de este índice es la cima real de la barra apilada,
        // sin importar el orden en que Chart.js apiló los datasets.
        if (point) topY = Math.min(topY, point.y);
      }});
      if (total === 0) return;
      const label = cfg.formatter ? cfg.formatter(total) : String(Math.round(total));
      const x = meta0.data[i].x;
      ctx.fillText(label, x, topY - 4);
    }});
    ctx.restore();
  }}
}};
Chart.register(stackedTotalLabelsPlugin);

// ── Panel de filtros: colapsar / expandir (persistido en localStorage) ────
function toggleFilterPanel(forceCollapsed) {{
  const panel = document.getElementById('filterPanel');
  const btn = document.getElementById('filterToggleBtn');
  const collapse = (typeof forceCollapsed === 'boolean')
    ? forceCollapsed
    : !panel.classList.contains('collapsed');
  panel.classList.toggle('collapsed', collapse);
  btn.setAttribute('aria-expanded', String(!collapse));
  try {{
    localStorage.setItem('locoTequilaFilterPanelCollapsed', collapse ? '1' : '0');
  }} catch (e) {{
    // localStorage puede fallar en modo privado/incógnito: no es crítico.
  }}
}}

function restoreFilterPanelState() {{
  let collapsed = false;
  try {{
    collapsed = localStorage.getItem('locoTequilaFilterPanelCollapsed') === '1';
  }} catch (e) {{
    // Si localStorage no está disponible, arranca expandido (default).
  }}
  toggleFilterPanel(collapsed);
}}

// ── Toggle Valores ($) / % apilado 100% de la gráfica de Canal ────────────
function setCanalViewMode(mode) {{
  canalViewMode = mode;
  document.querySelectorAll('#canalViewToggle .seg-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.mode === mode);
  }});
  renderChartsDynamic(filteredTabla);
}}

// ── Pestañas: Dashboard General / Comparativo 8 Columnas ─────────────────
function switchTab(name) {{
  document.querySelectorAll('.tab-content').forEach(el => {{
    el.hidden = (el.id !== 'tab-' + name);
  }});
  document.querySelectorAll('.tab-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.tab === name);
  }});
}}

// ── Comparativo 8 Columnas: Semanal / Anual (YTD) ─────────────────────────
// DATA.comparativo_8col ya viene calculado en Python (dashboard_generator.
// _build_comparativo_8col), con la misma fuente de verdad que el PDF
// (proc._filter_period/_filter_ytd + proc.dfp) — no depende de los filtros
// del panel lateral ni se recalcula aquí, solo se renderiza.
let comparativo8Mode = 'semanal';

function setComparativo8Mode(mode) {{
  comparativo8Mode = mode;
  document.querySelectorAll('#comparativo8ModeToggle .seg-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.mode === mode);
  }});
  renderComparativo8Col();
}}

function renderComparativo8Col() {{
  renderComparativo8Table('producto', 'comp8TableProducto');
  renderComparativo8Table('canal', 'comp8TableCanal');
}}

function renderComparativo8Table(groupKey, tbodyId) {{
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  const data = DATA.comparativo_8col || {{}};
  const rows = (data[groupKey] && data[groupKey][comparativo8Mode]) || [];

  // "N/A" = Plan no aplica (categoría "Otros" = venta real sin presupuesto
  // asociado: Agave/Servicios/KIT's/etc., o canal no catalogado). "N/D" =
  // variación sin base histórica real (año anterior no existe en los datos).
  const fmtOrNA = (v) => (v === null || v === undefined) ? 'N/A' : fmtCur(v);
  const fmtPctOrNA = (v) => (v === null || v === undefined) ? 'N/A' : `${{v >= 0 ? '+' : ''}}${{v.toFixed(1)}}%`;
  const fmtPctOrND = (v) => (v === null || v === undefined) ? 'N/D' : `${{v >= 0 ? '+' : ''}}${{v.toFixed(1)}}%`;
  const negCls = (v) => (typeof v === 'number' && v < 0) ? 'neg-val' : '';

  tbody.innerHTML = rows.map(r => {{
    const isTotal = r.categoria === 'Total';
    return `
      <tr class="${{isTotal ? 'comp8-total' : ''}}">
        <td>${{fmtCur(r.anio_anterior)}}</td>
        <td>${{fmtOrNA(r.plan)}}</td>
        <td class="comp8-actual">${{fmtCur(r.actual)}}</td>
        <td class="comp8-cat">${{r.categoria}}</td>
        <td class="${{negCls(r.var_plan_abs)}}">${{fmtOrNA(r.var_plan_abs)}}</td>
        <td class="${{negCls(r.var_plan_pct)}}">${{fmtPctOrNA(r.var_plan_pct)}}</td>
        <td class="${{negCls(r.var_anio_abs)}}">${{fmtCur(r.var_anio_abs)}}</td>
        <td class="${{negCls(r.var_anio_pct)}}">${{fmtPctOrND(r.var_anio_pct)}}</td>
      </tr>
    `;
  }}).join('');
}}

// ── Inicialización ───────────────────────────────────────────────────────
function updateStickyOffset() {{
  const hdr = document.querySelector('header');
  if (hdr) {{
    document.documentElement.style.setProperty('--header-height', hdr.offsetHeight + 'px');
  }}
}}
window.addEventListener('resize', updateStickyOffset);

document.addEventListener('DOMContentLoaded', () => {{
  updateStickyOffset();
  document.getElementById('headerSubtitle').textContent =
    `${{DATA.meta.semana_label}} · Dashboard Ejecutivo`;

  restoreFilterPanelState();
  populateFilters();
  // applyFilters() (no updateDashboard() directo) para que filteredTabla y
  // filteredTablaForRanking se calculen desde los valores reales de los
  // <select> (fComparablePlan arranca en "comparables" por su primera
  // <option>), en vez de depender del valor hardcodeado inicial de arriba.
  applyFilters();
  renderOportunidades(DATA.oportunidades);
  renderComparativo8Col();
}});

// ── Llenar Filtros Dropdown ───────────────────────────────────────────────
function populateFilters() {{
  const add = (id, items) => {{
    const sel = document.getElementById(id);
    items.forEach(v => {{
      const o = document.createElement('option');
      o.value = v; o.textContent = (id === 'fSemana') ? `W${{String(v).padStart(2,'0')}}` : v;
      sel.appendChild(o);
    }});
  }};
  add('fAnio',     DATA.filtros.anios);
  add('fSemana',   DATA.filtros.semanas);
  add('fProducto', DATA.filtros.productos);
  add('fCanal',    DATA.filtros.canales);
  add('fEstado',   DATA.filtros.estados);
  add('fCliente',  DATA.filtros.clientes || []);
}}

// ── Motor de Filtrado y Recálculo Dinámico ────────────────────────────────
// applyCompFilter=false omite la condición de "Comparables a Plan" (pero
// respeta los otros 6 filtros) — la usa el Ranking de Productos vía
// filteredTablaForRanking, que por diseño nunca se filtra por comparable_plan
// (debe mostrar siempre el mix completo de ventas).
function buildFilteredRecords(applyCompFilter) {{
  const anioVal     = document.getElementById('fAnio').value;
  const semanaVal   = document.getElementById('fSemana').value;
  const prodVal     = document.getElementById('fProducto').value;
  const canalVal    = document.getElementById('fCanal').value;
  const estadoVal   = document.getElementById('fEstado').value;
  const clienteVal  = document.getElementById('fCliente').value;
  const compVal     = document.getElementById('fComparablePlan').value;

  return DATA.tabla.filter(r => {{
    if (anioVal    !== 'all' && r.anio !== Number(anioVal)) return false;
    if (semanaVal  !== 'all' && r.semana_num !== Number(semanaVal.replace('W',''))) return false;
    if (prodVal    !== 'all' && r.producto_display !== prodVal) return false;
    if (canalVal   !== 'all' && r.canal !== canalVal) return false;
    if (estadoVal  !== 'all' && r.estado !== estadoVal) return false;
    if (clienteVal !== 'all' && r.cliente !== clienteVal) return false;
    if (applyCompFilter) {{
      // Filtro global "Comparables a Plan" / "No Comparables con Plan"
      // (default = comparables, confirmado con el cliente).
      if (compVal === 'comparables' && !r.comparable_plan) return false;
      if (compVal === 'no_comparables' && r.comparable_plan) return false;
    }}
    return true;
  }});
}}

function applyFilters() {{
  filteredTabla = buildFilteredRecords(true);
  filteredTablaForRanking = buildFilteredRecords(false);
  page = 1;
  updateDashboard();
}}

function resetFilters() {{
  ['fAnio','fSemana','fProducto','fCanal','fEstado','fCliente'].forEach(id => {{
    document.getElementById(id).value = 'all';
  }});
  // "Comparables a Plan" no tiene opción "Todos": su default (al cargar la
  // página y al limpiar filtros) es "comparables", confirmado con el cliente.
  document.getElementById('fComparablePlan').value = 'comparables';
  filteredTabla = buildFilteredRecords(true);
  filteredTablaForRanking = buildFilteredRecords(false);
  page = 1;
  updateDashboard();
}}

function updateDashboard() {{
  // Update status badge
  const total = DATA.tabla.length;
  const current = filteredTabla.length;
  const statusEl = document.getElementById('filterStatus');
  if (current === total) {{
    statusEl.textContent = `Mostrando todos los registros (${{total.toLocaleString()}})`;
  }} else {{
    statusEl.textContent = `Filtrados: ${{current.toLocaleString()}} de ${{total.toLocaleString()}} registros`;
  }}

  // 1. Recalcular KPIs dinámicos — se repiten en la pestaña "Dashboard
  // General" (#kpiGrid) y en "Comparativo 8 Columnas" (#kpiGrid_comparativo8),
  // a pedido explícito del cliente (mismas tarjetas al inicio de cada pestaña).
  renderKPIsDynamic(filteredTabla, 'kpiGrid');
  renderKPIsDynamic(filteredTabla, 'kpiGrid_comparativo8');

  // 2. Redibujar Gráficas dinámicas
  renderChartsDynamic(filteredTabla);

  // 3. Renderizar Tabla
  renderTable(filteredTabla);
}}

// ── Recálculo Dinámico de KPIs ────────────────────────────────────────────
// targetId: id del contenedor .kpi-grid a rellenar — permite reusar la misma
// función para el grid de la pestaña "Dashboard General" (kpiGrid, default)
// y el de "Comparativo 8 Columnas" (kpiGrid_comparativo8).
function renderKPIsDynamic(records, targetId = 'kpiGrid') {{
  const totalVentas = records.reduce((sum, r) => sum + (r.venta_sin_iva || 0), 0);
  const totalBotellas = records.reduce((sum, r) => sum + (r.botellas || 0), 0);
  // "# CAJAS DE 9L" (antes "# Botellas"): cajas_9l ya viene por registro
  // desde data_processor.py (prioriza "Cajas 9 lts" real del Excel del
  // cliente, o lo calcula si no existe). Pueden ser fraccionarias.
  const totalCajas9L = records.reduce((sum, r) => sum + (r.cajas_9l || 0), 0);
  const totalMargenPesos = records.reduce((sum, r) => sum + (r.margen_pesos || 0), 0);
  const margenPct = totalVentas > 0 ? (totalMargenPesos / totalVentas * 100) : 0;
  const ticket = totalBotellas > 0 ? (totalVentas / totalBotellas) : 0;

  // Plan para la selección actual
  let totalPlan = 0;
  const uniqueWeeks = [...new Set(records.map(r => `${{r.anio}}-W${{String(r.semana_num).padStart(2,'0')}}`))];
  uniqueWeeks.forEach(wKey => {{
    totalPlan += (DATA.plan_map[wKey] || 0);
  }});

  const vsPlanPct = totalPlan > 0 ? ((totalVentas - totalPlan) / totalPlan * 100) : 0;

  // ── Comparativas dinámicas ──────────────────────────────────────────────
  const anioSel  = document.getElementById('fAnio').value;
  const semSel   = document.getElementById('fSemana').value;

  let wowPct = DATA.kpis_initial.vs_semana_ant_pct;
  let yoyPct = DATA.kpis_initial.vs_anio_ant_pct;
  let ytdPct = DATA.kpis_initial.ytd_vs_ly_pct;
  let ytdVal = DATA.kpis_initial.ytd;

  // Si hay semana y año seleccionados, calcular WoW y YoY dinámicos
  if (semSel !== 'all' && anioSel !== 'all') {{
    const semNum = parseInt(semSel.replace('W',''));
    const anioNum = parseInt(anioSel);
    const prevSemNum = semNum > 1 ? semNum - 1 : 52;
    const prevAnioNum = semNum > 1 ? anioNum : anioNum - 1;

    const ventaActual = totalVentas;

    // Ventas semana anterior
    const recsPrevSem = DATA.tabla.filter(r => {{
      if (r.anio !== prevAnioNum || r.semana_num !== prevSemNum) return false;
      const p = document.getElementById('fProducto').value;
      const cv = document.getElementById('fCanal').value;
      const e = document.getElementById('fEstado').value;
      const cl = document.getElementById('fCliente').value.toLowerCase().trim();
      if (p  !== 'all' && r.producto_display !== p) return false;
      if (cv !== 'all' && r.canal !== cv) return false;
      if (e  !== 'all' && r.estado !== e) return false;
      if (cl && !(r.cliente && r.cliente.toLowerCase().includes(cl))) return false;
      return true;
    }});
    const ventaPrevSem = recsPrevSem.reduce((s, r) => s + (r.venta_sin_iva || 0), 0);
    const prevSemAnioExiste = DATA.tabla.some(r => r.anio === prevAnioNum);
    wowPct = !prevSemAnioExiste ? null
      : (ventaPrevSem !== 0 ? ((ventaActual - ventaPrevSem) / ventaPrevSem * 100) : (ventaActual > 0 ? 100 : 0));

    // Ventas misma semana año anterior (YoY)
    const recsPrevYY = DATA.tabla.filter(r => {{
      if (r.anio !== anioNum - 1 || r.semana_num !== semNum) return false;
      const p = document.getElementById('fProducto').value;
      const cv = document.getElementById('fCanal').value;
      const e = document.getElementById('fEstado').value;
      const cl = document.getElementById('fCliente').value.toLowerCase().trim();
      if (p  !== 'all' && r.producto_display !== p) return false;
      if (cv !== 'all' && r.canal !== cv) return false;
      if (e  !== 'all' && r.estado !== e) return false;
      if (cl && !(r.cliente && r.cliente.toLowerCase().includes(cl))) return false;
      return true;
    }});
    const ventaPrevYY = recsPrevYY.reduce((s, r) => s + (r.venta_sin_iva || 0), 0);
    const anioAntExiste = DATA.tabla.some(r => r.anio === anioNum - 1);
    yoyPct = !anioAntExiste ? null
      : (ventaPrevYY !== 0 ? ((ventaActual - ventaPrevYY) / ventaPrevYY * 100) : (ventaActual > 0 ? 100 : 0));
  }}

  // YTD: si hay año seleccionado, comparar acumulado vs año anterior
  if (anioSel !== 'all') {{
    const anioNum = parseInt(anioSel);
    const semMax = semSel !== 'all' ? parseInt(semSel.replace('W','')) : 999;
    const recsYTD    = DATA.tabla.filter(r => r.anio === anioNum && r.semana_num <= semMax);
    const recsYTD_LY = DATA.tabla.filter(r => r.anio === anioNum - 1 && r.semana_num <= semMax);
    const ytdCur = recsYTD.reduce((s, r) => s + (r.venta_sin_iva || 0), 0);
    const ytdLY  = recsYTD_LY.reduce((s, r) => s + (r.venta_sin_iva || 0), 0);
    const ytdAnioAntExiste = DATA.tabla.some(r => r.anio === anioNum - 1);
    ytdVal = ytdCur;
    ytdPct = !ytdAnioAntExiste ? null
      : (ytdLY !== 0 ? ((ytdCur - ytdLY) / ytdLY * 100) : (ytdCur > 0 ? 100 : 0));
  }}

  // "N/D" cuando no hay histórico del año anterior en los datos (en vez del
  // engañoso "+100%"/"0%" por división entre cero) — ver var()/year_b en
  // data_processor.py, mismo criterio aplicado aquí en el recálculo por filtro.
  const fmtDeltaPct = (pct) => (pct === null || pct === undefined || Number.isNaN(pct))
    ? 'N/D' : `${{pct >= 0 ? '+' : ''}}${{pct.toFixed(1)}}%`;

  const grid = document.getElementById(targetId);
  if (!grid) return;
  // Tarjetas monetarias "grandes" (Ventas Netas, Plan Est., YTD Acumuladas)
  // se muestran en miles vía fmtMiles (ej. "$1,234k") a pedido del cliente.
  // Los porcentajes NO cambian de formato. El Ticket Promedio usa fmtCur
  // (moneda completa sin decimales, ej. "$2,603") porque es un valor por
  // transacción, no un monto agregado "grande".
  const cards = [
    {{ label: 'WoW — vs Semana Anterior',        value: fmtDeltaPct(wowPct),  delta: wowPct, deltaLabel: '' }},
    {{ label: 'YoY — vs Misma Sem. Año Ant.',    value: fmtDeltaPct(yoyPct),  delta: yoyPct, deltaLabel: '' }},
    {{ label: 'YTD — vs Año Anterior (%)',        value: fmtDeltaPct(ytdPct),  delta: ytdPct, deltaLabel: '' }},
    {{ label: `YTD — Ventas Acumuladas`,          value: fmtMiles(ytdVal),                                       delta: null }},
    {{ label: 'Ventas Netas ($)',                 value: fmtMiles(totalVentas),  delta: vsPlanPct, deltaLabel: 'vs Plan' }},
    {{ label: 'Plan Est. ($)',                    value: fmtMiles(totalPlan),    delta: null }},
    {{ label: '# CAJAS DE 9L',                    value: totalCajas9L.toFixed(1), delta: null }},
    {{ label: 'Margen %',                         value: `${{margenPct.toFixed(1)}}%`, delta: null }},
    {{ label: 'Ticket Promedio',                  value: fmtCur(ticket),        delta: null }},
    {{ label: 'Registros',                        value: records.length.toLocaleString(), delta: null }},
  ];

  grid.innerHTML = cards.map(c => `
    <div class="kpi-card">
      <div class="kpi-label">${{c.label}}</div>
      <div class="kpi-value">${{c.value}}</div>
      ${{c.delta !== null
        ? `<div class="kpi-delta ${{c.delta >= 0 ? 'pos' : 'neg'}}">
             ${{c.delta >= 0 ? '▲' : '▼'}} ${{Math.abs(c.delta).toFixed(1)}}% ${{c.deltaLabel || ''}}
           </div>`
        : '<div class="kpi-delta">&nbsp;</div>'
      }}
    </div>
  `).join('');
}}


// ── Series de comparación (Año Anterior / Plan) ────────────────────────────

// Índice de ventas por clave "AAAA-Wnn" respetando los filtros NO temporales
// (Producto, Canal, Estado, Cliente). Base de la línea del año anterior.
function buildYearIndex() {{
  const p  = document.getElementById('fProducto').value;
  const cv = document.getElementById('fCanal').value;
  const e  = document.getElementById('fEstado').value;
  const cl = document.getElementById('fCliente').value;

  const idx = {{}};
  DATA.tabla.forEach(r => {{
    if (p  !== 'all' && r.producto_display !== p)  return;
    if (cv !== 'all' && r.canal            !== cv) return;
    if (e  !== 'all' && r.estado           !== e)  return;
    if (cl !== 'all' && r.cliente          !== cl) return;
    const k = `${{r.anio}}-W${{String(r.semana_num).padStart(2,'0')}}`;
    idx[k] = (idx[k] || 0) + (r.venta_sin_iva || 0);
  }});
  return idx;
}}

// Serie del año inmediatamente anterior, alineada a las etiquetas del eje X:
// "2026-W30" toma el valor de "2025-W30". Las semanas sin histórico quedan en
// null para que la línea se corte en lugar de caer a cero.
function lastYearSeries(weekLabels) {{
  const idx = buildYearIndex();
  return weekLabels.map(w => {{
    const m = /^(\\d{{4}})[-_ ]?W(\\d{{1,2}})/.exec(String(w));
    if (!m) return null;
    const k = `${{Number(m[1]) - 1}}-W${{String(m[2]).padStart(2,'0')}}`;
    return (k in idx) ? idx[k] : null;
  }});
}}

// Serie de plan alineada al eje X. Respeta los filtros de Producto y Canal;
// el plan de origen no trae Estado ni Cliente, por lo que esos no lo afectan.
function planSeries(weekLabels) {{
  const p  = document.getElementById('fProducto').value;
  const cv = document.getElementById('fCanal').value;
  const detail = DATA.plan_detail || [];

  if (detail.length === 0 || (p === 'all' && cv === 'all')) {{
    return weekLabels.map(w => DATA.plan_map[w] || 0);
  }}

  const idx = {{}};
  detail.forEach(d => {{
    if (p  !== 'all' && d.p !== p)  return;
    if (cv !== 'all' && d.c !== cv) return;
    idx[d.k] = (idx[d.k] || 0) + d.v;
  }});
  return weekLabels.map(w => idx[w] || 0);
}}

// Datasets de línea. Cada uno lleva su propio `stack` para que en gráficas
// apiladas no se sumen entre sí ni con las barras.
function planDataset(data) {{
  return {{
    label: 'Plan $',
    data: data,
    type: 'line',
    stack: 'plan',
    borderColor: '{CHART_PLAN_LINE}',
    backgroundColor: 'transparent',
    borderWidth: 2,
    pointRadius: 3,
    tension: 0.3,
    order: 1,
  }};
}}

function lastYearDataset(data) {{
  return {{
    label: 'Año Anterior $',
    data: data,
    type: 'line',
    stack: 'ly',
    borderColor: '{CHART_LASTYEAR_LINE}',
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderDash: [6, 4],
    pointRadius: 2,
    pointBackgroundColor: '{CHART_LASTYEAR_LINE}',
    tension: 0.3,
    spanGaps: false,
    order: 1,
  }};
}}

// ── Recálculo y Renderizado Dinámico de Gráficas ──────────────────────────
function renderChartsDynamic(records) {{
  // Extraer semanas únicas ordenadas
  const weekMap = {{}};
  records.forEach(r => {{
    const key = r.semana || `W${{String(r.semana_num).padStart(2,'0')}}`;
    if (!weekMap[key]) {{
      weekMap[key] = {{ semana_num: r.semana_num, total: 0, prods: {{}}, canales: {{}} }};
    }}
    weekMap[key].total += (r.venta_sin_iva || 0);

    const p = r.producto_display || 'Otro';
    weekMap[key].prods[p] = (weekMap[key].prods[p] || 0) + (r.venta_sin_iva || 0);

    const c = r.canal || 'Otro';
    weekMap[key].canales[c] = (weekMap[key].canales[c] || 0) + (r.venta_sin_iva || 0);
  }});

  const sortedWeeks = Object.keys(weekMap).sort((a, b) => {{
    const numA = parseInt(a.replace(/[^0-9]/g, '')) || 0;
    const numB = parseInt(b.replace(/[^0-9]/g, '')) || 0;
    return numA - numB;
  }});

  const totalesSem = sortedWeeks.map(w => weekMap[w].total);
  const planSem    = planSeries(sortedWeeks);
  const lySem      = lastYearSeries(sortedWeeks);
  const hasLY      = lySem.some(v => v !== null);
  // La línea de Plan solo tiene sentido cuando se está viendo el subconjunto
  // "Comparables a Plan": si el usuario eligió "No Comparables con Plan",
  // esa venta (Agave, Servicios, etc.) nunca estuvo contemplada en el Plan,
  // así que mostrar la línea sería comparar contra algo que no le aplica.
  const compFilterVal = document.getElementById('fComparablePlan').value;
  const showPlanLine  = compFilterVal !== 'no_comparables';

  // 1. Ventas Semanales + Plan + Año Anterior (línea gris)
  chartFactories.semanal = () => ({{
    type: 'bar',
    data: {{
      labels: sortedWeeks.slice(),
      datasets: [
        {{
          label: 'Ventas Netas $',
          data: totalesSem,
          backgroundColor: '{BRAND_MAROON}CC',
          borderColor: '{BRAND_MAROON}',
          borderWidth: 1,
          order: 2,
        }},
        ...(showPlanLine ? [planDataset(planSem)] : []),
        ...(hasLY ? [lastYearDataset(lySem)] : []),
      ]
    }},
    options: chartOptions('$MXN miles (sin IVA)', true),
  }});

  // 2. Ventas por Producto por Semana + Plan + Año Anterior (línea gris)
  const prodNames = DATA.filtros.productos;
  const prodSeries = prodNames.map(pName => ({{
    name: pName,
    data: sortedWeeks.map(w => weekMap[w].prods[pName] || 0),
  }}));
  chartFactories.producto = () => ({{
    type: 'bar',
    data: {{
      labels: sortedWeeks.slice(),
      datasets: [
        ...prodSeries.map(s => ({{
          label: s.name,
          data: s.data,
          backgroundColor: DATA.product_colors[s.name] || '#999',
          stack: 'prod',
          order: 2,
        }})),
        ...(showPlanLine ? [planDataset(planSem)] : []),
        ...(hasLY ? [lastYearDataset(lySem)] : []),
      ]
    }},
    options: chartOptions('$MXN miles (sin IVA)', false),
  }});

  // 3. Ranking de Productos
  // `producto_display` ya viene limpio desde Python (data_processor.py fuerza
  // "Otros" para toda venta real sin Plan asociado: Agave, Servicios, KIT's,
  // etc. — nunca "nan"), así que no hace falta ningún filtro extra aquí.
  // El bucket "Otros" es dinero real del negocio y SIEMPRE debe aparecer en
  // este ranking, con o sin el filtro "Comparables a Plan": es el mix
  // completo de ventas, no solo lo comparable contra presupuesto — por eso
  // usa `filteredTablaForRanking` (respeta Año/Semana/Producto/Canal/
  // Estado/Cliente, pero NUNCA excluye por `comparable_plan`) en vez de
  // `records`/`filteredTabla`.
  const prodTotals = {{}};
  filteredTablaForRanking.forEach(r => {{
    const p = r.producto_display || r.producto;
    prodTotals[p] = (prodTotals[p] || 0) + (r.venta_sin_iva || 0);
  }});
  const sortedProds = Object.entries(prodTotals).sort((a,b) => b[1] - a[1]);
  chartFactories.ranking = () => ({{
    type: 'bar',
    data: {{
      labels: sortedProds.map(p => p[0]),
      datasets: [{{
        label: 'Ventas Total',
        data: sortedProds.map(p => p[1]),
        backgroundColor: sortedProds.map(p => DATA.product_colors[p[0]] || '#999'),
        borderRadius: 4,
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => ' ' + fmtCur(ctx.raw) }} }},
      }},
      scales: {{
        x: {{
          ticks: {{ callback: v => fmtMillions(v), font: {{size: 10}} }},
          grid: {{ color: '{CHART_GRID}' }},
        }},
        y: {{ ticks: {{ font: {{size: 10}} }} }},
      }}
    }}
  }});

  // 4. Top Regiones / Estados
  // "Nacional" (venta sin desglose de estado real) y "Sin Estado" (vacío en
  // el Excel) no son regiones reales: se excluyen SOLO de esta gráfica
  // específica (no afecta filtros, tabla ni el resto del dashboard).
  const stateTotals = {{}};
  records.forEach(r => {{
    const s = r.estado || 'Sin Estado';
    if (s === 'Nacional' || s === 'Sin Estado') return;
    stateTotals[s] = (stateTotals[s] || 0) + (r.venta_sin_iva || 0);
  }});
  const sortedStates = Object.entries(stateTotals).sort((a,b) => b[1] - a[1]).slice(0, 12);
  chartFactories.regional = () => ({{
    type: 'bar',
    data: {{
      labels: sortedStates.map(s => s[0]),
      datasets: [{{
        label: 'Ventas Total',
        data: sortedStates.map(s => s[1]),
        backgroundColor: '{BRAND_MAROON}BB',
        borderRadius: 3,
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: ctx => ' ' + fmtCur(ctx.raw) }} }},
      }},
      scales: {{
        x: {{
          ticks: {{ callback: v => fmtMillions(v), font: {{size: 10}} }},
          grid: {{ color: '{CHART_GRID}' }},
        }},
        y: {{ ticks: {{ font: {{size: 9}} }} }},
      }}
    }}
  }});

  // 5. Ventas por Canal por Semana
  // Toggle "Valores ($)" / "% (100% apilado)" (canalViewMode, ver
  // setCanalViewMode arriba): en modo % cada canal se normaliza al % del
  // total de esa semana (0-100), en vez del monto absoluto.
  const canalNames = DATA.filtros.canales;
  let canalSeries = canalNames.map(cName => ({{
    name: cName,
    data: sortedWeeks.map(w => weekMap[w].canales[cName] || 0),
  }}));
  const isCanalPercent = canalViewMode === 'percent';
  if (isCanalPercent) {{
    const weekTotalsCanal = sortedWeeks.map(w =>
      canalNames.reduce((s, cName) => s + (weekMap[w].canales[cName] || 0), 0)
    );
    canalSeries = canalSeries.map(s => ({{
      name: s.name,
      data: s.data.map((v, i) => weekTotalsCanal[i] > 0 ? (v / weekTotalsCanal[i] * 100) : 0),
    }}));
  }}
  chartFactories.canal = () => {{
    const opts = chartOptions(
      isCanalPercent ? '% del total semanal' : '$MXN miles (sin IVA)', false
    );
    // Datalabel del TOTAL apilado (plugin stackedTotalLabels, ver arriba),
    // en miles y redondeado a 0 decimales — mismo criterio "en miles" que
    // pdf_generator.py usa para sus barras apiladas (f"{{v:.0f}}k").
    // En modo % cada barra ya suma ~100%, así que el label de total no
    // aporta información nueva: se oculta para mantener la gráfica limpia
    // (decisión de diseño).
    opts.plugins.stackedTotalLabels = {{
      enabled: !isCanalPercent,
      formatter: v => `${{Math.round(v / 1000).toLocaleString('es-MX')}}k`,
    }};
    if (isCanalPercent) {{
      opts.scales.y.max = 100;
      opts.scales.y.ticks.callback = v => `${{v}}%`;
      opts.plugins.tooltip.callbacks.label = ctx => ` ${{ctx.dataset.label}}: ${{ctx.raw.toFixed(1)}}%`;
    }}
    return {{
      type: 'bar',
      data: {{
        labels: sortedWeeks.slice(),
        datasets: canalSeries.map(s => ({{
          label: s.name,
          data: s.data,
          backgroundColor: DATA.canal_colors[s.name] || '#999',
          stack: 'canal',
        }})),
      }},
      options: opts,
    }};
  }};

  // Instanciar (o reinstanciar) las gráficas de las tarjetas
  Object.keys(CHART_CANVAS).forEach(key => {{
    if (charts[key]) charts[key].destroy();
    charts[key] = new Chart(document.getElementById(CHART_CANVAS[key]),
                            chartFactories[key]());
  }});

  // Si el modal está abierto, refrescarlo con los datos recién filtrados
  if (modalChartKey) renderModalChart(modalChartKey);
}}

function chartOptions(yLabel, showPlan) {{
  return {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ font: {{size: 10}}, boxWidth: 12 }} }},
      tooltip: {{
        // Las semanas sin histórico del año anterior van en null: no se listan
        filter: item => item.raw !== null && item.raw !== undefined,
        callbacks: {{
          label: ctx => ` ${{ctx.dataset.label}}: ${{fmtCur(ctx.raw)}}`
        }}
      }}
    }},
    scales: {{
      x: {{
        stacked: true,
        ticks: {{ font: {{size: 9}}, maxRotation: 40 }},
        grid: {{ display: false }},
      }},
      y: {{
        stacked: true,
        ticks: {{ callback: v => fmtMillions(v), font: {{size: 10}} }},
        grid: {{ color: '{CHART_GRID}' }},
        title: {{ display: true, text: yLabel, font: {{size: 10}} }},
      }}
    }}
  }};
}}

// ── Tabla Paginada y Ordenable ─────────────────────────────────────────────
function renderTable(data) {{
  const tbody = document.getElementById('tableBody');
  const start = (page - 1) * PAGE_SIZE;
  const slice = data.slice(start, start + PAGE_SIZE);

  tbody.innerHTML = slice.map(r => `
    <tr>
      <td>${{r.semana || 'W' + String(r.semana_num).padStart(2,'0')}}</td>
      <td>${{r.producto_display || r.producto}}</td>
      <td>${{r.canal}}</td>
      <td>${{r.estado}}</td>
      <td>${{r.cliente || '—'}}</td>
      <td>${{fmtCur(r.venta_sin_iva)}}</td>
      <td>${{fmtInt(r.botellas)}}</td>
      <td class="${{r.margen_pct < 0 ? 'neg-val' : ''}}">${{r.margen_pct.toFixed(1)}}%</td>
    </tr>
  `).join('');

  const total = data.length;
  const end   = Math.min(start + PAGE_SIZE, total);
  document.getElementById('tableCount').textContent = `${{total.toLocaleString()}} registros`;
  document.getElementById('pageInfo').textContent =
    total > 0 ? `${{start + 1}}–${{end}} de ${{total}}` : '0 registros';
}}

function sortTable(col) {{
  if (sortCol === col) sortAsc = !sortAsc;
  else {{ sortCol = col; sortAsc = true; }}
  const keys = ['semana','producto_display','canal','estado','cliente',
                 'venta_sin_iva','botellas','margen_pct'];
  const key = keys[col];
  filteredTabla.sort((a, b) => {{
    const va = a[key] ?? ''; const vb = b[key] ?? '';
    if (typeof va === 'number') return sortAsc ? va - vb : vb - va;
    return sortAsc ? String(va).localeCompare(String(vb))
                   : String(vb).localeCompare(String(va));
  }});
  page = 1;
  renderTable(filteredTabla);
}}

function prevPage() {{ if (page > 1) {{ page--; renderTable(filteredTabla); }} }}
function nextPage() {{
  const max = Math.ceil(filteredTabla.length / PAGE_SIZE);
  if (page < max) {{ page++; renderTable(filteredTabla); }}
}}

// ── Oportunidades y Riesgos ───────────────────────────────────────────────
function renderOportunidades(items) {{
  const grid = document.getElementById('oppGrid');
  if (!items || items.length === 0) {{
    grid.innerHTML = '<div style="font-size:0.75rem;color:#888;">Sin hallazgos registrados.</div>';
    return;
  }}
  grid.innerHTML = items.map(item => {{
    const cls = item.tipo.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');
    return `
      <div class="opp-card ${{cls}}">
        <div class="opp-tipo ${{cls}}">${{item.tipo}}</div>
        <div class="opp-hallazgo">${{item.hallazgo}}</div>
        <div class="opp-impacto">📊 Impacto: ${{item.impacto}}</div>
        <div class="opp-rec">💡 ${{item.recomendacion}}</div>
      </div>
    `;
  }}).join('');
}}

// ── Descarga de CSV Robusta (Con UTF-8 BOM para Excel) ────────────────────
function downloadCSV() {{
  if (!filteredTabla || filteredTabla.length === 0) {{
    alert('No hay datos para exportar con los filtros actuales.');
    return;
  }}

  const cols = ['semana','producto_display','canal','estado','cliente',
                'venta_sin_iva','botellas','margen_pesos','margen_pct'];
  const hdr  = ['Semana','Producto','Canal','Estado','Cliente',
                 'Venta Sin IVA','Botellas','Margen Pesos','Margen %'];

  let csv = '\\uFEFF' + hdr.join(',') + '\\n';
  filteredTabla.forEach(r => {{
    csv += cols.map(k => {{
      let v = r[k] ?? '';
      if (typeof v === 'number') return v;
      v = String(v).replace(/"/g, '""');
      return `"${{v}}"`;
    }}).join(',') + '\\n';
  }});

  const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url;

  const anio = document.getElementById('fAnio').value;
  const sem  = document.getElementById('fSemana').value;
  a.download = `loco_tequila_ventas_filtrado_${{anio !== 'all' ? anio : 'todos'}}_sem_${{sem !== 'all' ? sem : 'todas'}}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}}

// ── Descarga de Imágenes PNG de Gráficas ──────────────────────────────────
function downloadChartImage(chartKey, title) {{
  const chart = charts[chartKey];
  if (!chart || !chart.canvas) {{
    alert('La gráfica solicitada no está lista.');
    return;
  }}

  const canvas = chart.canvas;
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = canvas.width;
  tempCanvas.height = canvas.height;
  const ctx = tempCanvas.getContext('2d');

  // Fondo blanco sólido para evitar transparencia
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
  ctx.drawImage(canvas, 0, 0);

  const imageURI = tempCanvas.toDataURL('image/png', 1.0);
  const a = document.createElement('a');
  a.href = imageURI;
  a.download = `loco_tequila_${{title.toLowerCase().replace(/[^a-z0-9]/g, '_')}}.png`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}}

function downloadAllCharts() {{
  const chartKeys = [
    {{ key: 'semanal', title: 'Ventas_Semanales' }},
    {{ key: 'producto', title: 'Ventas_Por_Producto' }},
    {{ key: 'ranking', title: 'Ranking_Productos' }},
    {{ key: 'regional', title: 'Top_Regiones' }},
    {{ key: 'canal', title: 'Ventas_Por_Canal' }}
  ];
  let delay = 0;
  chartKeys.forEach(c => {{
    setTimeout(() => downloadChartImage(c.key, c.title), delay);
    delay += 300;
  }});
}}

// ── Modal: ver una gráfica ampliada ───────────────────────────────────────
function openChartModal(key) {{
  if (!chartFactories[key]) {{
    alert('La gráfica solicitada no está lista.');
    return;
  }}
  modalChartKey = key;
  document.getElementById('chartModalTitle').textContent = CHART_TITLES[key] || 'Gráfica';
  document.getElementById('chartModalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  renderModalChart(key);
}}

function renderModalChart(key) {{
  const factory = chartFactories[key];
  if (!factory) return;
  // La fábrica entrega datasets nuevos, así que la instancia del modal es
  // independiente de la de la tarjeta.
  const cfg = factory();
  cfg.options = Object.assign({{}}, cfg.options, {{
    responsive: true,
    maintainAspectRatio: false,
  }});
  if (modalChart) modalChart.destroy();
  modalChart = new Chart(document.getElementById('chartModalCanvas'), cfg);
}}

function closeChartModal() {{
  if (modalChart) {{ modalChart.destroy(); modalChart = null; }}
  modalChartKey = null;
  document.getElementById('chartModalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}}

function handleModalBackdrop(ev) {{
  if (ev.target === ev.currentTarget) closeChartModal();
}}

document.addEventListener('keydown', ev => {{
  if (ev.key === 'Escape' && modalChartKey) closeChartModal();
}});

// ── Helpers de Formato ────────────────────────────────────────────────────
function fmtCur(v) {{
  if (v == null || isNaN(v)) return '$0';
  return '$' + Math.round(v).toLocaleString('es-MX');
}}
function fmtInt(v) {{
  if (v == null || isNaN(v)) return '0';
  return Math.round(v).toLocaleString('es-MX');
}}
function fmtMillions(v) {{
  if (Math.abs(v) >= 1e6) return '$' + (v/1e6).toFixed(1) + 'M';
  if (Math.abs(v) >= 1e3) return '$' + (v/1e3).toFixed(0) + 'k';
  return '$' + Math.round(v);
}}
// Monto en miles de pesos, redondeado a 0 decimales (ej. "$1,234k" para
// $1,234,000) — formato pedido por el cliente para las tarjetas de KPI
// monetarias "grandes" (Ventas Netas, Plan Est., YTD Ventas Acumuladas).
function fmtMiles(v) {{
  if (v == null || isNaN(v)) return '$0k';
  return '$' + Math.round(v / 1000).toLocaleString('es-MX') + 'k';
}}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Función de entrada
# ---------------------------------------------------------------------------

def generate_dashboard(processor: LocoDataProcessor, output_path: str,
                       logo_path: Optional[str] = None,
                       contexto_mercado: Optional[dict] = None):
    """Genera el dashboard HTML y lo guarda en output_path."""
    print("[HTML] Preparando datos...")
    data = _prepare_data(processor, contexto_mercado=contexto_mercado)

    # Logo blanco inline para el header
    logo_svg = ""
    svg_source = logo_path
    if svg_source is None:
        candidate = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "Loco_Tequila_Logo.svg"
        )
        if os.path.exists(candidate):
            svg_source = candidate
    if svg_source:
        try:
            logo_svg = get_logo_for_html(svg_source, mode="inline")
        except Exception as e:
            print(f"[HTML] Logo no pudo cargarse: {e}")

    print("[HTML] Construyendo HTML...")
    html = _build_html(data, logo_svg=logo_svg)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML] Guardado: {output_path}")
