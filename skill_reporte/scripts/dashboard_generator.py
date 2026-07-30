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
    CHART_PLAN_LINE, CHART_LASTYEAR_AREA, CHART_GRID,
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
# Preparar datos para el dashboard
# ---------------------------------------------------------------------------

def _prepare_data(proc: LocoDataProcessor) -> dict:
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

    # Agrupar tabla transaccional limpia para TODOS los registros del dataset
    df_tabla = df.groupby(
        ["anio", "semana_num", "semana", "producto_display", "canal", "estado", "cliente"]
    ).agg(
        venta_sin_iva=("venta_sin_iva", "sum"),
        botellas=("botellas", "sum"),
        margen_pesos=("margen_pesos", "sum"),
    ).reset_index()

    df_tabla["margen_pct"] = (df_tabla["margen_pesos"] / df_tabla["venta_sin_iva"] * 100).fillna(0).round(1)

    tabla_records = df_tabla.to_dict(orient="records")
    for rec in tabla_records:
        rec["anio"] = int(rec["anio"])
        rec["semana_num"] = int(rec["semana_num"])
        rec["venta_sin_iva"] = round(float(rec["venta_sin_iva"]), 2)
        rec["botellas"] = round(float(rec["botellas"]), 2)
        rec["margen_pesos"] = round(float(rec["margen_pesos"]), 2)
        rec["margen_pct"] = round(float(rec["margen_pct"]), 1)
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

    # Resumen ejecutivo inicial
    resumen = proc.get_resumen_ejecutivo()

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
        },
        "kpis_initial": {
            "ventas_netas": float(resumen["actual"]["ventas_netas"]),
            "plan": float(resumen["plan"]["ventas_netas"]),
            "vs_plan_pct": float(resumen["vs_plan"]["pct"]),
            "vs_semana_ant_pct": float(resumen["vs_semana_anterior"]["pct"]),
            "vs_anio_ant_pct": float(resumen["vs_anio_anterior"]["pct"]),
            "ytd": float(resumen["ytd_actual"]["ventas_netas"]),
            "ytd_vs_ly_pct": float(resumen["ytd_vs_ly"]["pct"]),
            "botellas": float(resumen["actual"]["botellas"]),
            "margen_pct": float(resumen["actual"]["margen_pct"]),
            "ticket": float(resumen["actual"]["ticket_promedio"]),
        },
        "plan_map": plan_map,
        "tabla": tabla_records,
        "oportunidades": proc.get_oportunidades_riesgos(),
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
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Poppins', sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 13px;
    }}

    /* ── Header ── */
    header {{
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

    /* ── Filter bar ── */
    .filter-bar {{
      background: var(--card-bg);
      border-bottom: 3px solid var(--brand-maroon);
      padding: 12px 32px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }}
    .filter-bar label {{ font-size: 0.7rem; font-weight: 600; color: var(--sub); text-transform: uppercase; letter-spacing: 0.5px; }}
    .filter-bar select, .filter-bar input {{
      padding: 6px 10px;
      border: 1.5px solid #DDD;
      border-radius: 6px;
      font-size: 0.78rem;
      font-family: 'Poppins', sans-serif;
      background: #FAFAFA;
      transition: border-color 0.2s;
      min-width: 130px;
    }}
    .filter-bar select:focus, .filter-bar input:focus {{
      border-color: var(--brand-maroon);
      outline: none;
    }}
    .filter-group {{ display: flex; flex-direction: column; gap: 3px; }}
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
      margin-left: auto;
      font-size: 0.72rem;
      color: var(--brand-maroon);
      font-weight: 600;
      background: #FBF3DD;
      padding: 4px 10px;
      border-radius: 12px;
    }}

    /* ── Main layout ── */
    main {{ padding: 20px 32px; max-width: 1600px; margin: 0 auto; }}

    /* ── KPI cards ── */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
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
      .filter-bar {{ padding: 10px 16px; }}
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

<div class="filter-bar">
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
    <label>Buscar cliente</label>
    <input type="text" id="fCliente" placeholder="Nombre cliente..." oninput="applyFilters()">
  </div>
  <button class="btn btn-primary" onclick="applyFilters()">⚡ Aplicar</button>
  <button class="btn btn-secondary" onclick="resetFilters()">↺ Limpiar</button>
  <button class="btn btn-secondary" onclick="downloadCSV()">⬇ Descargar CSV</button>
  <button class="btn btn-secondary" onclick="downloadAllCharts()">📷 Descargar Gráficas</button>

  <div class="filter-status" id="filterStatus">Mostrando todos los registros</div>
</div>

<main>
  <!-- KPIs -->
  <div class="kpi-grid" id="kpiGrid"></div>

  <!-- Charts row 1 -->
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">
        <div>
          Ventas Netas Semanales ($MXN sin IVA)
          <span class="chart-note">Las ventas no incluyen IVA, IEPS</span>
        </div>
        <button class="btn-chart-img" onclick="downloadChartImage('semanal', 'Ventas_Semanales_y_Plan')">📷 PNG</button>
      </div>
      <div class="chart-body"><canvas id="chartSemanal" height="160"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">
        <div>
          Ventas por Producto por Semana
          <span class="chart-note">Barras apiladas sin IVA</span>
        </div>
        <button class="btn-chart-img" onclick="downloadChartImage('producto', 'Ventas_Por_Producto')">📷 PNG</button>
      </div>
      <div class="chart-body"><canvas id="chartProducto" height="160"></canvas></div>
    </div>
  </div>

  <!-- Charts row 2 -->
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">
        <div>Ranking de Productos</div>
        <button class="btn-chart-img" onclick="downloadChartImage('ranking', 'Ranking_Productos')">📷 PNG</button>
      </div>
      <div class="chart-body"><canvas id="chartRanking" height="130"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">
        <div>Top Regiones / Estados por Ventas</div>
        <button class="btn-chart-img" onclick="downloadChartImage('regional', 'Top_Regiones_Ventas')">📷 PNG</button>
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
          <span class="chart-note">Sin IVA</span>
        </div>
        <button class="btn-chart-img" onclick="downloadChartImage('canal', 'Ventas_Por_Canal')">📷 PNG</button>
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

<footer>
  Loco Tequila · Dirección de Finanzas · Las ventas no incluyen IVA ni IEPS · Generado automáticamente
</footer>

<script>
// ── Datos embebidos ──────────────────────────────────────────────────────
const DATA = {data_json};

// ── Estado ───────────────────────────────────────────────────────────────
let filteredTabla = [...DATA.tabla];
let sortCol = -1, sortAsc = true;
let page = 1;
const PAGE_SIZE = 50;
let charts = {{}};

// ── Inicialización ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {{
  document.getElementById('headerSubtitle').textContent =
    `${{DATA.meta.semana_label}} · Dashboard Ejecutivo`;

  populateFilters();
  updateDashboard();
  renderOportunidades(DATA.oportunidades);
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
}}

// ── Motor de Filtrado y Recálculo Dinámico ────────────────────────────────
function applyFilters() {{
  const anioVal     = document.getElementById('fAnio').value;
  const semanaVal   = document.getElementById('fSemana').value;
  const prodVal     = document.getElementById('fProducto').value;
  const canalVal    = document.getElementById('fCanal').value;
  const estadoVal   = document.getElementById('fEstado').value;
  const clienteVal  = document.getElementById('fCliente').value.toLowerCase().trim();

  filteredTabla = DATA.tabla.filter(r => {{
    if (anioVal    !== 'all' && r.anio !== Number(anioVal)) return false;
    if (semanaVal  !== 'all' && r.semana_num !== Number(semanaVal.replace('W',''))) return false;
    if (prodVal    !== 'all' && r.producto_display !== prodVal) return false;
    if (canalVal   !== 'all' && r.canal !== canalVal) return false;
    if (estadoVal  !== 'all' && r.estado !== estadoVal) return false;
    if (clienteVal && !(r.cliente && r.cliente.toLowerCase().includes(clienteVal))) return false;
    return true;
  }});

  page = 1;
  updateDashboard();
}}

function resetFilters() {{
  ['fAnio','fSemana','fProducto','fCanal','fEstado'].forEach(id => {{
    document.getElementById(id).value = 'all';
  }});
  document.getElementById('fCliente').value = '';
  filteredTabla = [...DATA.tabla];
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

  // 1. Recalcular KPIs dinámicos
  renderKPIsDynamic(filteredTabla);

  // 2. Redibujar Gráficas dinámicas
  renderChartsDynamic(filteredTabla);

  // 3. Renderizar Tabla
  renderTable(filteredTabla);
}}

// ── Recálculo Dinámico de KPIs ────────────────────────────────────────────
function renderKPIsDynamic(records) {{
  const totalVentas = records.reduce((sum, r) => sum + (r.venta_sin_iva || 0), 0);
  const totalBotellas = records.reduce((sum, r) => sum + (r.botellas || 0), 0);
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

  const grid = document.getElementById('kpiGrid');
  const cards = [
    {{ label: 'Ventas Netas ($)', value: fmtCur(totalVentas), delta: vsPlanPct, deltaLabel: 'vs Plan' }},
    {{ label: 'Plan Est. ($)', value: fmtCur(totalPlan), delta: null }},
    {{ label: '# Botellas', value: fmtInt(totalBotellas), delta: null }},
    {{ label: 'Margen %', value: `${{margenPct.toFixed(1)}}%`, delta: null }},
    {{ label: 'Ticket Promedio', value: `$${{ticket.toFixed(1)}}`, delta: null }},
    {{ label: 'Registros', value: records.length.toLocaleString(), delta: null }},
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
  const planSem = sortedWeeks.map(w => DATA.plan_map[w] || 0);

  // 1. Ventas Semanales + Plan
  if (charts.semanal) charts.semanal.destroy();
  charts.semanal = new Chart(document.getElementById('chartSemanal'), {{
    type: 'bar',
    data: {{
      labels: sortedWeeks,
      datasets: [
        {{
          label: 'Ventas Netas $',
          data: totalesSem,
          backgroundColor: '{BRAND_MAROON}CC',
          borderColor: '{BRAND_MAROON}',
          borderWidth: 1,
          order: 2,
        }},
        {{
          label: 'Plan $',
          data: planSem,
          type: 'line',
          borderColor: '{CHART_PLAN_LINE}',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.3,
          order: 1,
        }},
      ]
    }},
    options: chartOptions('$MXN miles (sin IVA)', true),
  }});

  // 2. Ventas por Producto por Semana
  if (charts.producto) charts.producto.destroy();
  const prodNames = DATA.filtros.productos;
  const prodDatasets = prodNames.map(pName => ({{
    label: pName,
    data: sortedWeeks.map(w => weekMap[w].prods[pName] || 0),
    backgroundColor: DATA.product_colors[pName] || '#999',
    stack: 'prod',
  }}));
  charts.producto = new Chart(document.getElementById('chartProducto'), {{
    type: 'bar',
    data: {{ labels: sortedWeeks, datasets: prodDatasets }},
    options: chartOptions('$MXN miles (sin IVA)', false),
  }});

  // 3. Ranking de Productos
  if (charts.ranking) charts.ranking.destroy();
  const prodTotals = {{}};
  records.forEach(r => {{
    const p = r.producto_display || r.producto;
    prodTotals[p] = (prodTotals[p] || 0) + (r.venta_sin_iva || 0);
  }});
  const sortedProds = Object.entries(prodTotals).sort((a,b) => b[1] - a[1]);
  charts.ranking = new Chart(document.getElementById('chartRanking'), {{
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
  if (charts.regional) charts.regional.destroy();
  const stateTotals = {{}};
  records.forEach(r => {{
    const s = r.estado || 'Sin Estado';
    stateTotals[s] = (stateTotals[s] || 0) + (r.venta_sin_iva || 0);
  }});
  const sortedStates = Object.entries(stateTotals).sort((a,b) => b[1] - a[1]).slice(0, 12);
  charts.regional = new Chart(document.getElementById('chartRegional'), {{
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
  if (charts.canal) charts.canal.destroy();
  const canalNames = DATA.filtros.canales;
  const canalDatasets = canalNames.map(cName => ({{
    label: cName,
    data: sortedWeeks.map(w => weekMap[w].canales[cName] || 0),
    backgroundColor: DATA.canal_colors[cName] || '#999',
    stack: 'canal',
  }}));
  charts.canal = new Chart(document.getElementById('chartCanal'), {{
    type: 'bar',
    data: {{ labels: sortedWeeks, datasets: canalDatasets }},
    options: chartOptions('$MXN miles (sin IVA)', false),
  }});
}}

function chartOptions(yLabel, showPlan) {{
  return {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ font: {{size: 10}}, boxWidth: 12 }} }},
      tooltip: {{
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
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Función de entrada
# ---------------------------------------------------------------------------

def generate_dashboard(processor: LocoDataProcessor, output_path: str,
                       logo_path: Optional[str] = None):
    """Genera el dashboard HTML y lo guarda en output_path."""
    print("[HTML] Preparando datos...")
    data = _prepare_data(processor)

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
