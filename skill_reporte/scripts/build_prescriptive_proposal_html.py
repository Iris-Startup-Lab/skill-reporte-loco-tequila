"""
Generador del documento HTML interactivo y enriquecido:
'output/analisis_prescriptivos_propuestos.html'
Para el Comité Directivo y Comercial de Loco Tequila.
Incluye visualizaciones interactivas con Chart.js, simulador What-If y casos de negocio.
"""

import os
import base64

def generate_prescriptive_html(output_path: str = "output/analisis_prescriptivos_propuestos.html"):
    # Cargar logo en base64 (PNG liviano ~18KB)
    logo_path = "assets/Loco_Tequila_Logo_white.png"
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Evolución Analítica Estratégica · Loco Tequila</title>
  <!-- Google Fonts: Poppins + Playfair Display -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <!-- Chart.js 4.4 Standalone CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

  <style>
    :root {{
      --brand-maroon:       #6E1E28;
      --brand-maroon-deep:  #4A141A;
      --brand-maroon-light: #8E2B38;
      --highlight-cream:    #FBF3DD;
      --cream-soft:         #F7F2EA;
      --cream-border:       #E8DCBE;
      --bg:                 #F4F5F7;
      --card-bg:            #FFFFFF;
      --text:               #222222;
      --text-muted:         #666666;
      --border:             #E2E8F0;
      --pos-green:          #00B050;
      --pos-green-bg:       #EBF8F1;
      --warn-yellow:        #D48806;
      --warn-yellow-bg:     #FEF7E8;
      --neg-red:            #C00000;
      --neg-red-bg:         #FDE8E8;
      --accent-blue:        #1F3B5C;
      --accent-blue-bg:     #EBF2FA;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: 'Poppins', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      font-size: 14px;
    }}

    /* ── Header Institucional Sticky ── */
    header {{
      position: sticky;
      top: 0;
      z-index: 500;
      background: linear-gradient(135deg, var(--brand-maroon) 0%, var(--brand-maroon-deep) 100%);
      color: #fff;
      padding: 16px 36px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 16px rgba(74, 20, 26, 0.35);
    }}
    .header-info {{ display: flex; flex-direction: column; gap: 3px; }}
    .header-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(251, 243, 221, 0.2);
      color: var(--highlight-cream);
      font-size: 0.68rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      padding: 3px 10px;
      border-radius: 20px;
      width: fit-content;
      border: 1px solid rgba(251, 243, 221, 0.35);
    }}
    header h1 {{
      font-family: 'Playfair Display', serif;
      font-size: 1.45rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #FFFFFF;
    }}
    header .subtitle {{
      font-size: 0.78rem;
      color: rgba(255, 255, 255, 0.88);
      font-weight: 300;
    }}
    .logo-area img {{
      height: 46px;
      width: auto;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }}

    /* ── Barra de Navegación Rápida ── */
    .nav-bar {{
      position: sticky;
      top: 79px;
      z-index: 490;
      background: #FFFFFF;
      border-bottom: 2px solid var(--brand-maroon);
      padding: 0 36px;
      display: flex;
      gap: 6px;
      overflow-x: auto;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .nav-link {{
      display: inline-block;
      padding: 11px 15px;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.76rem;
      font-weight: 600;
      white-space: nowrap;
      border-bottom: 3px solid transparent;
      transition: all 0.2s;
    }}
    .nav-link:hover {{
      color: var(--brand-maroon);
      border-bottom-color: var(--brand-maroon);
      background: rgba(110, 30, 40, 0.03);
    }}

    /* ── Contenedor Principal ── */
    .container {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 32px 24px 80px 24px;
    }}

    /* ── Hero Banner ── */
    .hero-card {{
      background: linear-gradient(135deg, #FFFFFF 0%, #FAF7F2 100%);
      border: 1px solid var(--cream-border);
      border-left: 6px solid var(--brand-maroon);
      border-radius: 12px;
      padding: 26px 30px;
      margin-bottom: 32px;
      box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }}
    .hero-card h2 {{
      font-family: 'Playfair Display', serif;
      font-size: 1.65rem;
      color: var(--brand-maroon);
      margin-bottom: 10px;
      line-height: 1.3;
    }}
    .hero-card p {{
      font-size: 0.88rem;
      color: #444444;
      max-width: 1050px;
      line-height: 1.7;
    }}
    .hero-pillars {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
      margin-top: 20px;
    }}
    .pillar-box {{
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 16px;
      border-top: 3px solid var(--brand-maroon);
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }}
    .pillar-title {{
      font-size: 0.76rem;
      font-weight: 700;
      color: var(--brand-maroon);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .pillar-desc {{
      font-size: 0.78rem;
      color: #555555;
      line-height: 1.45;
    }}

    /* ── Secciones y Tarjetas ── */
    .section {{
      margin-bottom: 50px;
      scroll-margin-top: 140px;
    }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;
      border-bottom: 2px solid #E2E8F0;
      padding-bottom: 8px;
    }}
    .section-num {{
      background: var(--brand-maroon);
      color: #fff;
      font-weight: 700;
      font-size: 0.82rem;
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      flex-shrink: 0;
    }}
    .section-title {{
      font-family: 'Playfair Display', serif;
      font-size: 1.35rem;
      color: var(--brand-maroon);
      font-weight: 700;
    }}
    .section-subtitle {{
      font-size: 0.76rem;
      color: var(--text-muted);
      font-weight: 400;
      margin-left: auto;
    }}

    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
      gap: 22px;
      margin-bottom: 20px;
    }}
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
      margin-bottom: 20px;
    }}

    .card {{
      background: var(--card-bg);
      border-radius: 10px;
      border: 1px solid var(--border);
      padding: 22px 24px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.04);
      display: flex;
      flex-direction: column;
    }}
    .card-title {{
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--brand-maroon);
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }}
    .card-badge {{
      font-size: 0.65rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-high  {{ background: var(--pos-green-bg); color: var(--pos-green); border: 1px solid rgba(0,176,80,0.3); }}
    .badge-mid   {{ background: var(--warn-yellow-bg); color: var(--warn-yellow); border: 1px solid rgba(212,136,6,0.3); }}
    .badge-ready {{ background: #E8F5E9; color: #2E7D32; font-weight: 700; }}

    .card-desc {{
      font-size: 0.82rem;
      color: #4A4A4A;
      line-height: 1.55;
      margin-bottom: 14px;
    }}
    .card-takeaway {{
      background: var(--cream-soft);
      border-left: 3px solid var(--brand-maroon);
      padding: 10px 14px;
      font-size: 0.77rem;
      color: #333;
      border-radius: 0 6px 6px 0;
      font-style: italic;
      margin-top: auto;
    }}

    /* ── Gráficos Ilustrativos ── */
    .chart-box {{
      background: #FFFFFF;
      border-radius: 10px;
      border: 1px solid var(--border);
      padding: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      position: relative;
    }}
    .chart-box-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 14px;
    }}
    .chart-box-title {{
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--brand-maroon);
    }}
    .chart-box-sub {{
      font-size: 0.72rem;
      color: var(--text-muted);
    }}
    .chart-canvas-wrap {{
      position: relative;
      height: 280px;
      width: 100%;
    }}

    /* ── Comparativa Antes vs Después ── */
    .compare-container {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 14px;
    }}
    .compare-card {{
      border-radius: 8px;
      padding: 14px 16px;
      font-size: 0.78rem;
      line-height: 1.5;
    }}
    .compare-before {{
      background: #F8F9FA;
      border-left: 4px solid #A0AEC0;
      color: #4A5568;
    }}
    .compare-after {{
      background: #FAF5F5;
      border-left: 4px solid var(--brand-maroon);
      color: #2D3748;
    }}
    .compare-label {{
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }}
    .compare-before .compare-label {{ color: #718096; }}
    .compare-after .compare-label {{ color: var(--brand-maroon); }}

    /* ── Pirámide Visual ── */
    .pyramid-container {{
      background: #FFFFFF;
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .pyramid-level {{
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 14px 18px;
      margin-bottom: 10px;
      border-radius: 8px;
      transition: all 0.2s;
    }}
    .pyramid-level:hover {{ transform: scale(1.008); }}
    .lvl-4 {{ background: #5A1822; color: #FFFFFF; border-left: 6px solid #D4AF37; }}
    .lvl-3 {{ background: #7A222D; color: #FFFFFF; border-left: 6px solid #E23B2E; }}
    .lvl-2 {{ background: #A03B47; color: #FFFFFF; border-left: 6px solid #FBF3DD; }}
    .lvl-1 {{ background: #EDE5DF; color: #222222; border-left: 6px solid var(--brand-maroon); }}

    .lvl-tag {{
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      padding: 4px 10px;
      border-radius: 4px;
      min-width: 110px;
      text-align: center;
    }}
    .lvl-4 .lvl-tag {{ background: rgba(255,255,255,0.25); color: #fff; }}
    .lvl-3 .lvl-tag {{ background: rgba(255,255,255,0.2); color: #fff; }}
    .lvl-2 .lvl-tag {{ background: rgba(255,255,255,0.2); color: #fff; }}
    .lvl-1 .lvl-tag {{ background: var(--brand-maroon); color: #fff; }}

    .lvl-content {{ flex: 1; }}
    .lvl-title {{ font-size: 0.88rem; font-weight: 700; margin-bottom: 2px; }}
    .lvl-desc {{ font-size: 0.76rem; opacity: 0.9; }}

    /* ── Semáforo de Churn ── */
    .traffic-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin: 18px 0;
    }}
    .traffic-card {{
      border-radius: 10px;
      padding: 16px 18px;
      border: 1px solid var(--border);
    }}
    .traffic-green {{
      background: #F4FAF6;
      border-top: 4px solid var(--pos-green);
    }}
    .traffic-yellow {{
      background: #FDF9F0;
      border-top: 4px solid var(--warn-yellow);
    }}
    .traffic-red {{
      background: #FDF4F4;
      border-top: 4px solid var(--neg-red);
    }}
    .traffic-status {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.84rem;
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .traffic-green .traffic-status {{ color: var(--pos-green); }}
    .traffic-yellow .traffic-status {{ color: var(--warn-yellow); }}
    .traffic-red .traffic-status {{ color: var(--neg-red); }}
    .traffic-action {{
      margin-top: 10px;
      padding-top: 8px;
      border-top: 1px dashed rgba(0,0,0,0.1);
      font-size: 0.74rem;
      font-weight: 600;
      color: #333;
    }}

    /* ── Simulador What-If Interactivo ── */
    .simulator-container {{
      background: linear-gradient(145deg, #FFFFFF 0%, #FCF9F7 100%);
      border: 2px solid var(--brand-maroon);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 6px 20px rgba(110,30,40,0.08);
      margin: 24px 0;
    }}
    .sim-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 10px;
    }}
    .sim-badge {{
      background: var(--brand-maroon);
      color: #fff;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .sim-grid {{
      display: grid;
      grid-template-columns: 1fr 1.35fr;
      gap: 24px;
    }}
    .sim-controls {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .sim-control-group {{
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
    }}
    .sim-control-label {{
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
      font-weight: 600;
      margin-bottom: 6px;
      color: #333;
    }}
    .sim-slider {{
      width: 100%;
      accent-color: var(--brand-maroon);
      cursor: pointer;
    }}
    .sim-results-cards {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 16px;
    }}
    .sim-kpi-card {{
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      text-align: center;
    }}
    .sim-kpi-label {{
      font-size: 0.66rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
    }}
    .sim-kpi-val {{
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--brand-maroon);
      margin: 2px 0;
    }}
    .sim-kpi-delta {{
      font-size: 0.7rem;
      font-weight: 600;
      color: var(--pos-green);
    }}

    /* ── Tablas Ejecutivas ── */
    .table-wrap {{
      background: #FFFFFF;
      border-radius: 10px;
      border: 1px solid var(--border);
      overflow-x: auto;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      margin-bottom: 20px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.78rem;
    }}
    thead th {{
      background: var(--brand-maroon);
      color: #FFFFFF;
      padding: 11px 14px;
      text-align: left;
      font-weight: 600;
      letter-spacing: 0.3px;
    }}
    tbody td {{
      padding: 11px 14px;
      border-bottom: 1px solid #EDF2F7;
      color: #333333;
    }}
    tbody tr:nth-child(even) {{ background: #FAFAFA; }}
    tbody tr:hover {{ background: var(--cream-soft); }}
    .phase-badge {{
      display: inline-block;
      font-weight: 700;
      font-size: 0.7rem;
      padding: 3px 8px;
      border-radius: 4px;
      background: var(--highlight-cream);
      color: var(--brand-maroon);
      border: 1px solid #E2D3AB;
    }}

    /* ── Callouts y Footer ── */
    .callout {{
      background: var(--highlight-cream);
      border-left: 4px solid var(--brand-maroon);
      border-radius: 0 8px 8px 0;
      padding: 16px 20px;
      margin: 18px 0;
      font-size: 0.82rem;
      color: #3B2A1A;
    }}
    .callout strong {{ color: var(--brand-maroon); }}

    footer {{
      background: var(--brand-maroon-deep);
      color: #FFFFFF;
      text-align: center;
      padding: 24px;
      font-size: 0.75rem;
      opacity: 0.95;
    }}
  </style>
</head>
<body>

<!-- Header Sticky -->
<header>
  <div class="header-info">
    <div class="header-badge">Evolución de Inteligencia Comercial · Loco Tequila</div>
    <h1>De Reportes Descriptivos a Decisiones Prescriptivas</h1>
    <div class="subtitle">Estrategia Interactiva para Potenciar Margen, Retención de Cuentas B2B y Optimización de Precios</div>
  </div>
  <div class="logo-area">
    <img src="{logo_b64}" alt="Loco Tequila Logo">
  </div>
</header>

<!-- Barra de Navegación Rápida -->
<nav class="nav-bar">
  <a class="nav-link" href="#diagnostico-madurez">0. Diagnóstico Actual</a>
  <a class="nav-link" href="#piramide-valor">1. Pirámide de Valor</a>
  <a class="nav-link" href="#eje-inferencial">2. Efecto Precio × Volumen × Mix</a>
  <a class="nav-link" href="#eje-churn">3. Retención B2B & Churn</a>
  <a class="nav-link" href="#eje-pricing">4. Precios & Margen Óptimo</a>
  <a class="nav-link" href="#what-if">5. Simulador What-If</a>
  <a class="nav-link" href="#roadmap">6. Hoja de Ruta</a>
  <a class="nav-link" href="#preguntas">7. Preguntas Directivas</a>
</nav>

<main class="container">

  <!-- Hero Card -->
  <section class="hero-card">
    <h2>¿Por qué evolucionar la analítica de Loco Tequila?</h2>
    <p>
      El sistema de reportes actual de Loco Tequila es <strong>extraordinariamente sólido en describir el pasado</strong>: sabemos exactamente cuánto vendimos, qué SKU aportó más dinero y cómo varió la semana contra el plan. Sin embargo, para una casa tequilera ultra-premium con producción artesanal limitada, el mayor retorno financiero no está en mirar el retrovisor, sino en <strong>anticipar qué clientes están por enfriarse, fijar el precio que maximiza margen sin destruir volumen y asignar botellas escasas a las cuentas más prestigiosas y rentables</strong>.
    </p>
    <div class="hero-pillars">
      <div class="pillar-box">
        <div class="pillar-title">🛡️ 1. Cuidar Cuentas Clave</div>
        <div class="pillar-desc">Detectar cuándo una cuenta On-Trade o cadena mayorista espacia sus órdenes antes de que deje de comprar por completo.</div>
      </div>
      <div class="pillar-box">
        <div class="pillar-title">🔍 2. Descomponer Crecimiento</div>
        <div class="pillar-desc">Separar si una subida en ventas viene de vender más botellas (volumen), de subir precios o de una mejor mezcla hacia Puro Corazón/Áureo.</div>
      </div>
      <div class="pillar-box">
        <div class="pillar-title">💎 3. Asignación Estratégica</div>
        <div class="pillar-desc">Programar la entrega de ediciones limitadas finitas donde generen mayor valor de marca y margen neto por litro.</div>
      </div>
      <div class="pillar-box">
        <div class="pillar-title">🎯 4. Simulación Prescriptiva</div>
        <div class="pillar-desc">Modelar escenarios en vivo con palancas deslizantes antes de autorizar listas de precios o cuotas comerciales.</div>
      </div>
    </div>
  </section>

  <!-- 0. Diagnóstico Actual -->
  <section class="section" id="diagnostico-madurez">
    <div class="section-header">
      <div class="section-num">0</div>
      <h2 class="section-title">Diagnóstico de Madurez Analítica (Punto de Partida)</h2>
      <div class="section-subtitle">Evaluación técnica y operativa de la información existente</div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Dimensión</th>
            <th>Nivel Actual</th>
            <th>Diagnóstico Técnico</th>
            <th>Impacto en el Negocio</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Cobertura Descriptiva</strong></td>
            <td><span class="card-badge badge-ready">Madurez Alta</span></td>
            <td>WoW, YoY, YTD, Rolling 52, matrices Canal→Cliente→Producto, comparativo 8 columnas, contexto CRT/agave/NOM.</td>
            <td>La dirección tiene visibilidad total del cumplimiento del presupuesto y ventas históricas.</td>
          </tr>
          <tr>
            <td><strong>Motor de Procesamiento</strong></td>
            <td><span class="card-badge badge-ready">Sólido & Centralizado</span></td>
            <td><code>LocoDataProcessor</code> unifica limpieza, mapeos, márgenes y regla N/D para alimentar PDF, XLSX y HTML.</td>
            <td>Una sola fuente de verdad sin discrepancias entre áreas.</td>
          </tr>
          <tr>
            <td><strong>Naturaleza de los Datos</strong></td>
            <td><span class="card-badge badge-mid">Sell-In Transaccional</span></td>
            <td>Registra facturas emitidas a distribuidores y centros de consumo. No hay sell-out directo de tienda ni inventarios.</td>
            <td>Se debe inferir el consumo del cliente final mediante la frecuencia de reposición de órdenes.</td>
          </tr>
          <tr>
            <td><strong>Dataset Simulado vs Real</strong></td>
            <td><span class="card-badge badge-high">Transición Activa</span></td>
            <td>Simulación: 59,778 filas, 37 clientes, 14 SKUs, 2022–2026. Data Real Cliente: 22,064 filas en Plan y ~500 en Actuals 2026.</td>
            <td>Los algoritmos se prueban con el histórico simulado y se activan gradualmente con la data real acumulada.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="callout">
      <strong>Conclusión Diagnóstica:</strong> La plataforma actual domina el <em>Nivel 1 (Descriptivo)</em>. La transición más rentable consiste en implementar métodos inferenciales y de retención que funcionen <strong>de inmediato con los datos que ya poseemos</strong> (remuestreo bootstrap, descomposición P×V×M, semáforo RFM y supervivencia Kaplan-Meier), posponiendo modelos complejos de ML hasta acumular 12 meses de historia real continua.
    </div>
  </section>

  <!-- 1. Pirámide de Valor -->
  <section class="section" id="piramide-valor">
    <div class="section-header">
      <div class="section-num">1</div>
      <h2 class="section-title">Pirámide de Evolución Analítica</h2>
      <div class="section-subtitle">De responder "¿Qué pasó?" a prescribir "¿Qué decisión tomar?"</div>
    </div>

    <div class="pyramid-container">
      <div class="pyramid-level lvl-4">
        <div class="lvl-tag">Nivel 4 · Futuro</div>
        <div class="lvl-content">
          <div class="lvl-title">Analítica Prescriptiva · "¿Qué acción debemos tomar?"</div>
          <div class="lvl-desc">Optimizador de precios por canal, asignación lineal de barricas limitadas, recomendador Next-Best-SKU y simulador What-If.</div>
        </div>
      </div>
      <div class="pyramid-level lvl-3">
        <div class="lvl-tag">Nivel 3 · Próximo</div>
        <div class="lvl-content">
          <div class="lvl-title">Analítica Predictiva · "¿Qué pasará si no actuamos?"</div>
          <div class="lvl-desc">Semáforo de enfriamiento de cuentas (Churn B2B), valor futuro proyectado del cliente (CLV) y pronóstico de demanda a 12 semanas.</div>
        </div>
      </div>
      <div class="pyramid-level lvl-2">
        <div class="lvl-tag">Nivel 2 · Inmediato</div>
        <div class="lvl-content">
          <div class="lvl-title">Analítica Inferencial / Diagnóstica · "¿Por qué ocurrió y es estadísticamente real?"</div>
          <div class="lvl-desc">Descomposición Precio × Volumen × Mix, bandas de confianza bootstrap (separar ruido de tendencia real) y elasticidad precio.</div>
        </div>
      </div>
      <div class="pyramid-level lvl-1">
        <div class="lvl-tag">Nivel 1 · Actual</div>
        <div class="lvl-content">
          <div class="lvl-title">Analítica Descriptiva (Completada con Éxito)</div>
          <div class="lvl-desc">Reporte PDF ejecutivo, Libro XLSX de 8 hojas con comparativo de 8 columnas y Dashboard HTML interactivo con filtros en tiempo real.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- 2. Eje Inferencial: Descomposición PVM -->
  <section class="section" id="eje-inferencial">
    <div class="section-header">
      <div class="section-num">2</div>
      <h2 class="section-title">Eje Inferencial: Descomposición Precio × Volumen × Mix</h2>
      <div class="section-subtitle">Entender la verdadera anatomía de las variaciones de venta</div>
    </div>

    <div class="grid-2">
      <!-- Explicación Conceptual -->
      <div class="card">
        <div class="card-title">
          <span>La Trampa de Mirar Solo la Venta Bruta</span>
          <span class="card-badge badge-ready">Quick Win · Fase 0</span>
        </div>
        <div class="card-desc">
          Cuando una semana reporta un incremento de <strong>+$450,000 MXN</strong>, la dirección puede asumir que el mercado está creciendo con fuerza. Sin embargo, matemáticamente ese aumento puede esconder una contracción peligrosa en clientes y botellas.
        </div>
        <div class="card-desc">
          La <strong>Descomposición Logarítmica P×V×M</strong> separa exactamente los 3 motores:
          <ul style="margin: 8px 0 8px 20px; line-height: 1.6;">
            <li><strong>Efecto Volumen:</strong> ¿Se vendieron más o menos cajas físicas? (-$120,000 en el ejemplo).</li>
            <li><strong>Efecto Precio:</strong> ¿Cuánto aportó la subida de precios de lista? (+$380,000).</li>
            <li><strong>Efecto Mix:</strong> ¿Los clientes compraron productos más caros (Puro Corazón/Áureo vs Blanco)? (+$190,000).</li>
          </ul>
        </div>
        <div class="card-takeaway">
          <strong>Conclusión Directiva:</strong> La venta subió por precio y mezcla premium, pero el volumen físico cayó. La acción comercial debe enfocarse en reactivar la rotación en botellas sin bajar los precios.
        </div>

        <div class="compare-container">
          <div class="compare-card compare-before">
            <div class="compare-label">Reporte Descriptivo Actual</div>
            "Ventas subieron +10.7% vs año anterior. Meta semanal cumplida."
          </div>
          <div class="compare-card compare-after">
            <div class="compare-label">Diagnóstico Inferencial Propuesto</div>
            "Ventas +10.7%, pero volumen cayó -2.8%. Crecimiento sostenido por alza de precios (+9%) y mix premium (+4.5%). Riesgo de saturación en canal On-Trade."
          </div>
        </div>
      </div>

      <!-- Gráfico Waterfall Interactivo -->
      <div class="chart-box">
        <div class="chart-box-header">
          <div>
            <div class="chart-box-title">Ejemplo Interactivo: Desglose de Variación de Ventas</div>
            <div class="chart-box-sub">Descomposición de +$450k netos entre 2025 y 2026 ($MXN)</div>
          </div>
          <span class="card-badge badge-high">+10.7% Neto</span>
        </div>
        <div class="chart-canvas-wrap">
          <canvas id="chartPVM"></canvas>
        </div>
      </div>
    </div>
  </section>

  <!-- 3. Eje Churn: Semáforo y Supervivencia B2B -->
  <section class="section" id="eje-churn">
    <div class="section-header">
      <div class="section-num">3</div>
      <h2 class="section-title">Eje Predictivo: Sistema Inteligente Anti-Churn B2B</h2>
      <div class="section-subtitle">Anticipar la fuga de centros de consumo y mayoristas antes de que ocurra</div>
    </div>

    <p style="margin-bottom: 20px; font-size: 0.85rem; color: #444;">
      En el segmento de destilados de lujo, un restaurante de alta gama o una vinoteca nunca avisa que dejará de comprar: simplemente <strong>espacia sus pedidos</strong>, agota el inventario en trastienda y es captado silenciosamente por marcas rivales (Clase Azul, Don Julio 1942, Casa Dragones).
    </p>

    <!-- Semáforo Dinámico -->
    <div class="traffic-box">
      <div class="traffic-card traffic-green">
        <div class="traffic-status">🟢 Activo Estable (P_Alive &ge; 80%)</div>
        <p style="font-size:0.77rem; color:#444;">El cliente compra dentro de su intervalo normal de rotación (ej. cada 2 a 3 semanas).</p>
        <div class="traffic-action">Acción Comercial: Mantener servicio de excelencia y ofrecer tasting de nuevas ediciones.</div>
      </div>
      <div class="traffic-card traffic-yellow">
        <div class="traffic-status">🟡 En Enfriamiento (50% &le; P_Alive &lt; 80%)</div>
        <p style="font-size:0.77rem; color:#444;">El cliente ha demorado más de 1.5 veces su ciclo típico de recompra (ej. lleva 6 semanas sin pedir).</p>
        <div class="traffic-action">Acción Comercial: Llamada del Brand Ambassador y capacitación a sommeliers/bartenders.</div>
      </div>
      <div class="traffic-card traffic-red">
        <div class="traffic-status">🔴 Riesgo Crítico (P_Alive &lt; 50%)</div>
        <p style="font-size:0.77rem; color:#444;">Intervalo anormalmente prolongado. Muy alta probabilidad de haber sido sustituido en la carta.</p>
        <div class="traffic-action">Acción Comercial: Visita urgente del Director Comercial con paquete de apoyo promocional.</div>
      </div>
    </div>

    <!-- Gráficos de Churn: Dispersión de Clientes + Supervivencia -->
    <div class="grid-2" style="margin-top: 24px;">
      <!-- Matriz de Cuentas B2B -->
      <div class="chart-box">
        <div class="chart-box-header">
          <div>
            <div class="chart-box-title">Matriz de Salud de Cartera B2B (Muestra Simulada)</div>
            <div class="chart-box-sub">Facturación Anual ($k) vs Semanas de Inactividad (Tamaño = Cajas 9L)</div>
          </div>
          <span class="card-badge badge-mid">37 Clientes</span>
        </div>
        <div class="chart-canvas-wrap">
          <canvas id="chartChurnScatter"></canvas>
        </div>
      </div>

      <!-- Curva de Supervivencia Kaplan-Meier -->
      <div class="chart-box">
        <div class="chart-box-header">
          <div>
            <div class="chart-box-title">Curva de Supervivencia de Recompra (Kaplan-Meier)</div>
            <div class="chart-box-sub">Probabilidad de volver a ordenar según semanas transcurridas</div>
          </div>
          <span class="card-badge badge-ready">Ciclos de Vida</span>
        </div>
        <div class="chart-canvas-wrap">
          <canvas id="chartSurvival"></canvas>
        </div>
      </div>
    </div>
  </section>

  <!-- 4. Eje Pricing & Asignación -->
  <section class="section" id="eje-pricing">
    <div class="section-header">
      <div class="section-num">4</div>
      <h2 class="section-title">Eje Prescriptivo: Optimización de Precios & Asignación de Lotes</h2>
      <div class="section-subtitle">Maximizar margen total sin destruir la demanda de cajas</div>
    </div>

    <div class="grid-2">
      <!-- Gráfico de Elasticidad y Margen Óptimo -->
      <div class="chart-box">
        <div class="chart-box-header">
          <div>
            <div class="chart-box-title">Simulación de Elasticidad: Curva de Margen Óptimo</div>
            <div class="chart-box-sub">Búsqueda del punto de equilibrio entre precio unitario y margen neto total</div>
          </div>
          <span class="card-badge badge-high">Sweet Spot: $1,650</span>
        </div>
        <div class="chart-canvas-wrap">
          <canvas id="chartPricing"></canvas>
        </div>
      </div>

      <!-- Asignación de Ediciones Limitadas -->
      <div class="card">
        <div class="card-title">
          <span>Asignación Óptima de Lotes Finitos</span>
          <span class="card-badge badge-ready">Prescriptivo · Fase 4</span>
        </div>
        <div class="card-desc">
          Para botellas de alta exclusividad (como <strong>Loco Áureo Elevación</strong> o la <strong>Edición Serpiente</strong>, donde solo existen 1,200 botellas anuales), el modelo matemático asigna las piezas resolviendo un problema de programación lineal:
        </div>
        <div style="background:#FAF7F2; padding:12px; border-radius:8px; font-size:0.78rem; margin-bottom:12px; border:1px solid #EAE0D0;">
          <strong>Criterios del Algoritmo de Reparto:</strong>
          <ol style="margin-left: 20px; margin-top: 6px; line-height: 1.5;">
            <li><strong>Score de Prestigio del Cliente:</strong> Presencia en cartas Michelin / 5 Diamantes / Tiendas insignia.</li>
            <li><strong>Margen Neto por Botella:</strong> Venta directa vs mayorista con descuento.</li>
            <li><strong>Venta Cruzada Condicionada:</strong> Asignar 1 caja de edición limitada solo si la cuenta compra 4 cajas de Loco Blanco.</li>
          </ol>
        </div>
        <div class="card-takeaway">
          <strong>Resultado:</strong> Se elimina la disputa comercial entre vendedores y se garantiza que el stock escaso construya marca y maximice el beneficio de la compañía.
        </div>
      </div>
    </div>
  </section>

  <!-- 5. Simulador What-If Interactivo -->
  <section class="section" id="what-if">
    <div class="section-header">
      <div class="section-num">5</div>
      <h2 class="section-title">Simulador "What-If" Interactivo Directivo</h2>
      <div class="section-subtitle">Experimente con las palancas comerciales y observe el impacto financiero proyectado en vivo</div>
    </div>

    <div class="simulator-container">
      <div class="sim-header">
        <div>
          <strong style="color:var(--brand-maroon); font-size:0.95rem;">Simulador de Escenarios Comerciales</strong>
          <div style="font-size:0.74rem; color:#666;">Ajuste las palancas de la izquierda para evaluar el impacto en Margen y Utilidad Anual</div>
        </div>
        <span class="sim-badge">En Vivo</span>
      </div>

      <div class="sim-grid">
        <!-- Controles Deslizantes -->
        <div class="sim-controls">
          <div class="sim-control-group">
            <div class="sim-control-label">
              <span>Ajuste de Precio Promedio:</span>
              <strong id="valPrecio" style="color:var(--brand-maroon);">+0%</strong>
            </div>
            <input type="range" id="sliderPrecio" class="sim-slider" min="-10" max="25" step="1" value="0" oninput="updateSimulation()">
            <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:#888; margin-top:2px;">
              <span>-10% (Descuento)</span>
              <span>Base (0%)</span>
              <span>+25% (Premium)</span>
            </div>
          </div>

          <div class="sim-control-group">
            <div class="sim-control-label">
              <span>Mix de Gama Alta (Puro Corazón & Áureo):</span>
              <strong id="valMix" style="color:var(--brand-maroon);">35%</strong>
            </div>
            <input type="range" id="sliderMix" class="sim-slider" min="20" max="60" step="1" value="35" oninput="updateSimulation()">
            <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:#888; margin-top:2px;">
              <span>20% (Foco Blanco)</span>
              <span>35% (Actual)</span>
              <span>60% (Ultra-Luxury)</span>
            </div>
          </div>

          <div class="sim-control-group">
            <div class="sim-control-label">
              <span>Retención de Cuentas B2B (Anti-Churn):</span>
              <strong id="valRetencion" style="color:var(--brand-maroon);">82%</strong>
            </div>
            <input type="range" id="sliderRetencion" class="sim-slider" min="70" max="98" step="1" value="82" oninput="updateSimulation()">
            <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:#888; margin-top:2px;">
              <span>70% (Fuga)</span>
              <span>82% (Base)</span>
              <span>98% (Excelente)</span>
            </div>
          </div>
        </div>

        <!-- Resultados Dinámicos y Gráfico -->
        <div>
          <div class="sim-results-cards">
            <div class="sim-kpi-card">
              <div class="sim-kpi-label">Ventas Netas Proyectadas</div>
              <div class="sim-kpi-val" id="kpiSimVentas">$42.8M</div>
              <div class="sim-kpi-delta" id="deltaSimVentas">+0.0%</div>
            </div>
            <div class="sim-kpi-card">
              <div class="sim-kpi-label">Margen Bruto Total</div>
              <div class="sim-kpi-val" id="kpiSimMargen">$27.8M</div>
              <div class="sim-kpi-delta" id="deltaSimMargen">65.0%</div>
            </div>
            <div class="sim-kpi-card" style="background:var(--highlight-cream); border-color:#E2D3AB;">
              <div class="sim-kpi-label">Beneficio Incremental</div>
              <div class="sim-kpi-val" id="kpiSimUtilidad" style="color:var(--brand-maroon);">$0.0M</div>
              <div class="sim-kpi-delta" id="deltaSimUtilidad" style="color:var(--brand-maroon);">vs Escenario Base</div>
            </div>
          </div>

          <div style="position:relative; height: 180px; width: 100%;">
            <canvas id="chartSimComparison"></canvas>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- 6. Hoja de Ruta Priorizada -->
  <section class="section" id="roadmap">
    <div class="section-header">
      <div class="section-num">6</div>
      <h2 class="section-title">Hoja de Ruta de Implementación Técnica</h2>
      <div class="section-subtitle">Fases autónomas y acumulativas sin alterar los reportes actuales</div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Fase</th>
            <th>Plazo</th>
            <th>Módulo Analítico</th>
            <th>Entregable Concreto</th>
            <th>Datos Necesarios</th>
            <th>Impacto Comercial</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="phase-badge">Fase 0</span></td>
            <td><strong>1 sem</strong></td>
            <td><strong>Significancia Bootstrap + Descomposición P×V×M</strong></td>
            <td>Bandas de confianza en KPIs y desglose automático de si el crecimiento vino de precio, volumen o mix.</td>
            <td>Datos que ya tenemos ✅</td>
            <td><span class="card-badge badge-ready">Inmediato</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 1</span></td>
            <td><strong>2–3 sem</strong></td>
            <td><strong>Semáforo de Retención y Churn B2B</strong></td>
            <td>Nueva pestaña en Excel con cuentas en riesgo verde/amarillo/rojo y tareas asignadas al vendedor.</td>
            <td>Datos que ya tenemos ✅ (+ Vendedor)</td>
            <td><span class="card-badge badge-high">Muy Alto</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 2</span></td>
            <td><strong>3–4 sem</strong></td>
            <td><strong>Curvas de Supervivencia y Recompra</strong></td>
            <td>Modelo Kaplan-Meier para estimar semanas límite de compra antes de que una cuenta se considere perdida.</td>
            <td>Datos que ya tenemos ✅</td>
            <td><span class="card-badge badge-mid">Alto</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 3</span></td>
            <td><strong>4–5 sem</strong></td>
            <td><strong>Valor de Vida del Cliente (CLV con BG/NBD)</strong></td>
            <td>Proyección de cuánto dinero comprará cada cuenta en los siguientes 3 meses para priorizar visitas.</td>
            <td>Datos que ya tenemos ✅</td>
            <td><span class="card-badge badge-mid">Medio-Alto</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 4</span></td>
            <td><strong>5–7 sem</strong></td>
            <td><strong>Optimizador de Precios y Margen Máximo</strong></td>
            <td>Simulador para predecir si conviene subir precios en On-Trade o Mayoristas sin perder volumen crítico.</td>
            <td>Historial de listas de precios</td>
            <td><span class="card-badge badge-high">Estratégico</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 5</span></td>
            <td><strong>7–9 sem</strong></td>
            <td><strong>Pronóstico Jerárquico de Demanda a 12 semanas</strong></td>
            <td>Proyección reconciliada que cuadra matemáticamente por vendedor, plaza y total nacional.</td>
            <td>Acumulación de historia real</td>
            <td><span class="card-badge badge-mid">Operativo</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 6</span></td>
            <td><strong>9–12 sem</strong></td>
            <td><strong>Simulador "What-If" Completo en Dashboard HTML</strong></td>
            <td>Módulo interactivo en el dashboard oficial para evaluar escenarios de precios y mix en reuniones de comité.</td>
            <td>Integración de Fases 4 y 5</td>
            <td><span class="card-badge badge-ready">Directivo</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- 7. Preguntas Directivas -->
  <section class="section" id="preguntas">
    <div class="section-header">
      <div class="section-num">7</div>
      <h2 class="section-title">Preguntas Clave para el Comité Directivo</h2>
      <div class="section-subtitle">Decisiones de negocio para enfocar los primeros módulos</div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">1. ¿Se dispone de información de sell-out o inventario en tienda?</div>
        <div class="card-desc">
          Si cuentas como <em>La Europea</em> o <em>Liverpool</em> comparten portales con sus niveles de inventario en anaquel, podemos anticipar quiebres de stock 2 o 3 semanas antes de que ellos mismos generen la orden de compra.
        </div>
      </div>

      <div class="card">
        <div class="card-title">2. ¿Cómo se articula hoy la agenda del equipo comercial?</div>
        <div class="card-desc">
          Al integrar el campo de <code>Vendedor</code> de la facturación real con el Semáforo de Churn, el sistema puede enviar cada lunes una <strong>lista priorizada de visitas comerciales</strong> con las cuentas en amarillo que requieren intervención.
        </div>
      </div>
    </div>
  </section>

</main>

<footer>
  Loco Tequila · Propuesta de Analítica Inferencial, Predictiva y Prescriptiva · Sistema de Diseño Oficial · Septiembre 2026
</footer>

<!-- ── Scripts de Gráficos Chart.js & Lógica del Simulador ── -->
<script>
  // Paleta institucional compartida
  const MAROON = '#6E1E28';
  const MAROON_LIGHT = '#8E2B38';
  const MAROON_DEEP = '#4A141A';
  const CREAM = '#FBF3DD';
  const GREEN = '#00B050';
  const YELLOW = '#D48806';
  const RED = '#C00000';
  const BLUE = '#1F3B5C';

  // 1. Gráfico PVM (Waterfall simulado con barras)
  const ctxPVM = document.getElementById('chartPVM').getContext('2d');
  new Chart(ctxPVM, {{
    type: 'bar',
    data: {{
      labels: ['Base 2025', 'Efecto Volumen', 'Efecto Precio', 'Efecto Mix Premium', 'Venta 2026'],
      datasets: [{{
        label: 'Aporte ($MXN)',
        data: [4200000, -120000, 380000, 190000, 4650000],
        backgroundColor: [
          '#A0AEC0',
          RED,
          GREEN,
          GREEN,
          MAROON
        ],
        borderRadius: 6
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: function(c) {{
              let v = c.raw;
              let prefix = v > 0 ? '+$' : '-$';
              return (v >= 0 ? '+' : '') + '$' + Math.abs(v).toLocaleString('es-MX') + ' MXN';
            }}
          }}
        }}
      }},
      scales: {{
        y: {{
          ticks: {{
            callback: (val) => '$' + (val / 1000000).toFixed(1) + 'M'
          }}
        }}
      }}
    }}
  }});

  // 2. Gráfico Churn Scatter
  const ctxChurn = document.getElementById('chartChurnScatter').getContext('2d');
  new Chart(ctxChurn, {{
    type: 'scatter',
    data: {{
      datasets: [
        {{
          label: 'Activo Estable',
          data: [
            {{ x: 1.5, y: 3200, r: 14, name: 'La Europea' }},
            {{ x: 2.0, y: 2800, r: 12, name: "Grupo Anderson's" }},
            {{ x: 2.8, y: 2400, r: 10, name: 'Bodegas Alianza' }},
            {{ x: 3.2, y: 1900, r: 9,  name: 'Vinoteca Norte' }},
            {{ x: 1.8, y: 1600, r: 8,  name: 'Hotel Four Seasons' }}
          ],
          backgroundColor: 'rgba(0, 176, 80, 0.75)',
          borderColor: GREEN
        }},
        {{
          label: 'En Enfriamiento',
          data: [
            {{ x: 6.2, y: 2100, r: 11, name: 'Hotel Resort Cancún' }},
            {{ x: 5.5, y: 1450, r: 8,  name: 'Mayorista Bajío' }},
            {{ x: 7.0, y: 1100, r: 7,  name: 'Grupo Sonora Grill' }}
          ],
          backgroundColor: 'rgba(212, 136, 6, 0.8)',
          borderColor: YELLOW
        }},
        {{
          label: 'Riesgo Crítico',
          data: [
            {{ x: 10.5, y: 2600, r: 12, name: 'Cadena Departamental Norte' }},
            {{ x: 12.0, y: 1300, r: 8,  name: 'Distribuidor Occidente' }},
            {{ x: 13.5, y: 850,  r: 6,  name: 'Restaurante Polanco' }}
          ],
          backgroundColor: 'rgba(192, 0, 0, 0.8)',
          borderColor: RED
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'top' }},
        tooltip: {{
          callbacks: {{
            label: function(ctx) {{
              let raw = ctx.raw;
              return `${{raw.name}}: ${{raw.x}} sem sin comprar · $${{raw.y}}k anuales`;
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          title: {{ display: true, text: 'Semanas sin Compra (Recency)' }},
          min: 0,
          max: 15
        }},
        y: {{
          title: {{ display: true, text: 'Facturación Anualizada ($k MXN)' }},
          min: 0,
          max: 3800
        }}
      }}
    }}
  }});

  // 3. Gráfico Kaplan-Meier Supervivencia
  const ctxSurv = document.getElementById('chartSurvival').getContext('2d');
  new Chart(ctxSurv, {{
    type: 'line',
    data: {{
      labels: ['Sem 0', 'Sem 2', 'Sem 4', 'Sem 6', 'Sem 8', 'Sem 10', 'Sem 12'],
      datasets: [
        {{
          label: 'Canal On-Trade (Restaurantes/Hoteles)',
          data: [100, 88, 68, 38, 20, 10, 4],
          borderColor: MAROON,
          backgroundColor: 'rgba(110, 30, 40, 0.08)',
          fill: true,
          tension: 0.3,
          borderWidth: 2.5
        }},
        {{
          label: 'Canal Off-Trade (Especializadas/Mayoristas)',
          data: [100, 94, 85, 65, 45, 28, 15],
          borderColor: BLUE,
          borderDash: [5, 5],
          tension: 0.3,
          borderWidth: 2
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'top' }},
        tooltip: {{
          callbacks: {{
            label: (c) => `${{c.dataset.label}}: ${{c.raw}}% de probabilidad de recompra`
          }}
        }}
      }},
      scales: {{
        y: {{
          min: 0,
          max: 100,
          ticks: {{ callback: (v) => v + '%' }},
          title: {{ display: true, text: 'Probabilidad de Recompra (%)' }}
        }}
      }}
    }}
  }});

  // 4. Gráfico Pricing & Elasticidad
  const ctxPrice = document.getElementById('chartPricing').getContext('2d');
  new Chart(ctxPrice, {{
    type: 'line',
    data: {{
      labels: ['$1,200', '$1,350', '$1,500', '$1,650 (Óptimo)', '$1,800', '$1,950', '$2,100'],
      datasets: [
        {{
          label: 'Margen Bruto Total Proyectado ($M)',
          data: [21.5, 24.2, 26.8, 28.5, 27.2, 24.6, 21.0],
          borderColor: MAROON,
          backgroundColor: 'rgba(110,30,40,0.12)',
          fill: true,
          yAxisID: 'yMargen',
          tension: 0.35,
          borderWidth: 3,
          pointRadius: [3, 3, 3, 7, 3, 3, 3],
          pointBackgroundColor: [MAROON, MAROON, MAROON, '#D4AF37', MAROON, MAROON, MAROON]
        }},
        {{
          label: 'Demanda Estimada (Cajas 9L)',
          data: [4200, 3900, 3550, 3180, 2650, 2100, 1600],
          borderColor: '#718096',
          borderDash: [4, 4],
          yAxisID: 'yVol',
          tension: 0.3,
          borderWidth: 1.8
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'top' }}
      }},
      scales: {{
        yMargen: {{
          type: 'linear',
          position: 'left',
          title: {{ display: true, text: 'Margen Total ($M MXN)' }},
          ticks: {{ callback: (v) => '$' + v + 'M' }}
        }},
        yVol: {{
          type: 'linear',
          position: 'right',
          grid: {{ drawOnChartArea: false }},
          title: {{ display: true, text: 'Cajas 9L' }}
        }}
      }}
    }}
  }});

  // 5. Simulador What-If Interactivo
  let simChart = null;
  const BASE_VENTAS = 42800000;
  const BASE_MARGEN_PCT = 0.65;

  function initSimChart() {{
    const ctx = document.getElementById('chartSimComparison').getContext('2d');
    simChart = new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: ['Ventas Netas ($M)', 'Margen Bruto ($M)'],
        datasets: [
          {{
            label: 'Escenario Base',
            data: [42.8, 27.82],
            backgroundColor: '#CBD5E0',
            borderRadius: 6
          }},
          {{
            label: 'Escenario Simulado',
            data: [42.8, 27.82],
            backgroundColor: MAROON,
            borderRadius: 6
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'top' }}
        }},
        scales: {{
          y: {{
            beginAtZero: true,
            ticks: {{ callback: (v) => '$' + v + 'M' }}
          }}
        }}
      }}
    }});
  }}

  function updateSimulation() {{
    const pAdj = parseFloat(document.getElementById('sliderPrecio').value);
    const mixVal = parseFloat(document.getElementById('sliderMix').value);
    const retVal = parseFloat(document.getElementById('sliderRetencion').value);

    // Text labels
    document.getElementById('valPrecio').innerText = (pAdj >= 0 ? '+' : '') + pAdj + '%';
    document.getElementById('valMix').innerText = mixVal + '%';
    document.getElementById('valRetencion').innerText = retVal + '%';

    // Modelación simplificada de elasticidad (elasticidad = -1.15)
    const elasticidad = -1.15;
    const factorVolumen = 1 + (pAdj / 100 * elasticidad);
    const factorPrecio = 1 + (pAdj / 100);

    // Efecto mix: pasar de 35% base a mixVal añade margen
    const factorMixMargen = 1 + ((mixVal - 35) / 100 * 0.28);

    // Efecto retención: pasar de 82% base a retVal
    const factorRetencion = 1 + ((retVal - 82) / 100 * 0.45);

    const ventasSim = BASE_VENTAS * factorPrecio * factorVolumen * factorRetencion;
    const margenPctSim = Math.min(0.82, Math.max(0.50, BASE_MARGEN_PCT * factorMixMargen + (pAdj * 0.003)));
    const margenSim = ventasSim * margenPctSim;

    const baseMargen = BASE_VENTAS * BASE_MARGEN_PCT;
    const utilidadDelta = margenSim - baseMargen;

    // Actualizar KPIs
    document.getElementById('kpiSimVentas').innerText = '$' + (ventasSim / 1000000).toFixed(1) + 'M';
    const deltaV = ((ventasSim / BASE_VENTAS - 1) * 100).toFixed(1);
    document.getElementById('deltaSimVentas').innerText = (deltaV >= 0 ? '+' : '') + deltaV + '%';
    document.getElementById('deltaSimVentas').style.color = deltaV >= 0 ? GREEN : RED;

    document.getElementById('kpiSimMargen').innerText = '$' + (margenSim / 1000000).toFixed(1) + 'M';
    document.getElementById('deltaSimMargen').innerText = (margenPctSim * 100).toFixed(1) + '% margen';

    const utilM = (utilidadDelta / 1000000).toFixed(2);
    document.getElementById('kpiSimUtilidad').innerText = (utilidadDelta >= 0 ? '+$' : '-$') + Math.abs(utilM) + 'M';
    document.getElementById('kpiSimUtilidad').style.color = utilidadDelta >= 0 ? MAROON : RED;

    // Actualizar gráfico
    if (simChart) {{
      simChart.data.datasets[1].data = [
        parseFloat((ventasSim / 1000000).toFixed(2)),
        parseFloat((margenSim / 1000000).toFixed(2))
      ];
      simChart.update();
    }}
  }}

  // Inicializar al cargar
  window.addEventListener('DOMContentLoaded', () => {{
    initSimChart();
    updateSimulation();
  }});
</script>

</body>
</html>
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] Documento HTML prescriptivo generado en: {output_path} ({len(html_content)} bytes)")

if __name__ == "__main__":
    generate_prescriptive_html()
