"""
generate_proposal_html.py
=========================
Genera la versión HTML ejecutiva para personas no técnicas del documento
analisis_prescriptivos_propuestos.md, utilizando la identidad de marca y paleta
de colores de Design.md (brand maroon, highlight cream, tipografía moderna).

Salida:
  output/analisis_prescriptivos_propuestos.html
"""

import os
import sys

# Asegurar path para imports locales
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from logo_processor import get_logo_for_html

OUTPUT_DIR = os.path.join(os.path.dirname(_THIS_DIR), "output")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "analisis_prescriptivos_propuestos.html")


def build_html() -> str:
    logo_tag = get_logo_for_html(mode="img_tag")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Evolución Analítica Estratégica · Loco Tequila</title>
  <!-- Google Fonts: Poppins + Playfair Display -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --brand-maroon:       #6E1E28;
      --brand-maroon-deep:  #4A141A;
      --brand-maroon-light: #8E2B38;
      --highlight-cream:    #FBF3DD;
      --cream-soft:         #F7F2EA;
      --cream-border:       #E8DCBE;
      --bg:                 #F5F6F8;
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
      color: rgba(255, 255, 255, 0.85);
      font-weight: 300;
    }}
    .logo-area {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
    }}
    .logo-area img, .logo-area svg {{
      height: 48px;
      width: auto;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }}

    /* ── Barra de Navegación Rápida ── */
    .nav-bar {{
      position: sticky;
      top: 80px;
      z-index: 490;
      background: #FFFFFF;
      border-bottom: 2px solid var(--brand-maroon);
      padding: 0 36px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .nav-link {{
      display: inline-block;
      padding: 12px 16px;
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
      padding: 28px 32px;
      margin-bottom: 32px;
      box-shadow: 0 4px 14px rgba(0,0,0,0.04);
      position: relative;
    }}
    .hero-card h2 {{
      font-family: 'Playfair Display', serif;
      font-size: 1.7rem;
      color: var(--brand-maroon);
      margin-bottom: 10px;
      line-height: 1.3;
    }}
    .hero-card p {{
      font-size: 0.88rem;
      color: #444444;
      max-width: 950px;
      line-height: 1.7;
    }}
    .hero-pillars {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-top: 22px;
    }}
    .pillar-box {{
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 16px;
      border-top: 3px solid var(--brand-maroon);
    }}
    .pillar-title {{
      font-size: 0.76rem;
      font-weight: 700;
      color: var(--brand-maroon);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }}
    .pillar-desc {{
      font-size: 0.78rem;
      color: #555555;
      line-height: 1.4;
    }}

    /* ── Secciones y Tarjetas ── */
    .section {{
      margin-bottom: 44px;
      scroll-margin-top: 140px;
    }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 18px;
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

    /* ── Grids de Tarjetas de Diagnóstico ── */
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 18px;
      margin-bottom: 20px;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }}

    .card {{
      background: var(--card-bg);
      border-radius: 10px;
      border: 1px solid var(--border);
      padding: 20px 22px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(110,30,40,0.08);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }}
    .card-title {{
      font-size: 0.92rem;
      font-weight: 700;
      color: var(--brand-maroon);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .card-badge {{
      font-size: 0.65rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-high {{ background: var(--pos-green-bg); color: var(--pos-green); border: 1px solid rgba(0,176,80,0.3); }}
    .badge-mid  {{ background: var(--warn-yellow-bg); color: var(--warn-yellow); border: 1px solid rgba(212,136,6,0.3); }}
    .badge-info {{ background: var(--accent-blue-bg); color: var(--accent-blue); border: 1px solid rgba(31,59,92,0.3); }}
    .badge-ready {{ background: #E8F5E9; color: #2E7D32; font-weight: 700; }}

    .card-desc {{
      font-size: 0.81rem;
      color: #4A4A4A;
      line-height: 1.55;
      margin-bottom: 12px;
    }}

    .card-takeaway {{
      background: var(--cream-soft);
      border-left: 3px solid var(--brand-maroon);
      padding: 8px 12px;
      font-size: 0.75rem;
      color: #333;
      border-radius: 0 6px 6px 0;
      font-style: italic;
    }}

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
    .pyramid-level:hover {{ transform: scale(1.01); }}
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

    /* ── Callouts y Alertas ── */
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

    /* ── Footer ── */
    footer {{
      background: var(--brand-maroon-deep);
      color: #FFFFFF;
      text-align: center;
      padding: 24px;
      font-size: 0.74rem;
      opacity: 0.95;
    }}
    footer a {{ color: var(--highlight-cream); text-decoration: none; }}
  </style>
</head>
<body>

<!-- Header Sticky -->
<header>
  <div class="header-info">
    <div class="header-badge">Evolución de Inteligencia Comercial · Loco Tequila</div>
    <h1>De Reportes Descriptivos a Decisiones Prescriptivas</h1>
    <div class="subtitle">Guía Directiva y Comercial para Potenciar Margen, Retención de Clientes y Asignación de Producto</div>
  </div>
  <div class="logo-area">
    {logo_tag}
  </div>
</header>

<!-- Barra de Navegación Rápida -->
<nav class="nav-bar">
  <a class="nav-link" href="#evaluacion">0. Diagnóstico Actual</a>
  <a class="nav-link" href="#piramide">1. Pirámide de Valor</a>
  <a class="nav-link" href="#churn">2. Semáforo Anti-Churn B2B</a>
  <a class="nav-link" href="#diagnostico">3. Separador Ruido vs Cambio</a>
  <a class="nav-link" href="#prescriptivo">4. Asignación y Precios</a>
  <a class="nav-link" href="#roadmap">5. Hoja de Ruta (Semanas)</a>
  <a class="nav-link" href="#preguntas">6. Preguntas Directivas</a>
</nav>

<main class="container">

  <!-- Hero Card -->
  <section class="hero-card">
    <h2>¿Por qué evolucionar la analítica de Loco Tequila?</h2>
    <p>
      El sistema de reportes actual de Loco Tequila es <strong>extraordinariamente preciso en describir el pasado</strong>: sabemos exactamente cuánto vendimos, qué SKU aportó más dinero y cómo varió la semana contra el plan. Sin embargo, para una casa tequilera ultra-premium con producción artesanal limitada, el mayor retorno financiero no está en mirar el retrovisor, sino en <strong>anticipar qué clientes están por enfriarse, fijar el precio que maximiza margen sin destruir volumen y asignar botellas escasas a las cuentas más prestigiosas y rentables</strong>.
    </p>
    <div class="hero-pillars">
      <div class="pillar-box">
        <div class="pillar-title">1. Cuidar Cuentas Clave</div>
        <div class="pillar-desc">Detectar cuándo un restaurante o mayorista empieza a espaciar sus pedidos antes de que se pase a la competencia.</div>
      </div>
      <div class="pillar-box">
        <div class="pillar-title">2. Precios y Margen</div>
        <div class="pillar-desc">Identificar si podemos ajustar precios en canales clave sin perder cajas ni canibalizar otras líneas.</div>
      </div>
      <div class="pillar-box">
        <div class="pillar-title">3. Botellas Escasas</div>
        <div class="pillar-desc">Racionar matemáticamente las ediciones limitadas (Puro Corazón, Áureo) donde generan mayor impacto de marca.</div>
      </div>
    </div>
  </section>

  <!-- 0. Evaluación de la Skill -->
  <section class="section" id="evaluacion">
    <div class="section-header">
      <div class="section-num">0</div>
      <h2 class="section-title">Evaluación de Madurez de la Skill (Punto de Partida)</h2>
      <div class="section-subtitle">Revisión objetiva sobre los datos reales y de simulación</div>
    </div>

    <div class="grid-3">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Cobertura de Reportes</div>
          <span class="card-badge badge-high">Alta Madurez</span>
        </div>
        <div class="card-desc">
          Calcula automáticamente variaciones semanales (WoW), anuales (YoY), acumuladas (YTD) y Rolling 52. Matrices de canal, cliente y SKU perfectamente cuadradas.
        </div>
        <div class="card-takeaway">Nivel descriptivo 100% resuelto y confiable.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Motor de Datos Central</div>
          <span class="card-badge badge-high">Sólido</span>
        </div>
        <div class="card-desc">
          Una sola capa unificada (<code>LocoDataProcessor</code>) limpia y alimenta en paralelo los 3 entregables (PDF, Excel analítico y Dashboard interactivo).
        </div>
        <div class="card-takeaway">Garantiza una única fuente de verdad directiva.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Naturaleza de Datos</div>
          <span class="card-badge badge-info">Sell-In Puro</span>
        </div>
        <div class="card-desc">
          Los datos reflejan la facturación de Loco Tequila a sus clientes. Aún no se dispone de <em>sell-out</em> (ventas de la tienda al consumidor final) ni inventarios en distribuidor.
        </div>
        <div class="card-takeaway">Prioriza modelos de compra mayorista sobre machine learning complejo.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Dataset de Simulación</div>
          <span class="card-badge badge-high">59,778 Filas</span>
        </div>
        <div class="card-desc">
          239 semanas continuas (2022–2026), 37 clientes, 14 SKUs y 4 canales. Permite calibrar modelos de demanda y pruebas estadísticas robustas.
        </div>
        <div class="card-takeaway">Excelente base para calibración de métodos avanzados.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Datos Reales del Cliente</div>
          <span class="card-badge badge-mid">En Crecimiento</span>
        </div>
        <div class="card-desc">
          Archivo 2026 con ~500 operaciones iniciales. Aporta campos de oro: <code>Vendedor</code>, <code>Punto de Venta</code>, <code>CECO</code> y <code>Tipo Comprobante</code>.
        </div>
        <div class="card-takeaway">El valor aumentará exponencialmente conforme acumule semanas.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Estrategia Metodológica</div>
          <span class="card-badge badge-high">Pragmática</span>
        </div>
        <div class="card-desc">
          Con 37 cuentas clave, aplicar algoritmos de inteligencia artificial masivos sería imprudente. Se prioriza matemática probabilística B2B y semáforos de negocio.
        </div>
        <div class="card-takeaway">Evolución en fases: primero lo inmediato, luego lo sofisticado.</div>
      </div>
    </div>
  </section>

  <!-- 1. Pirámide de Valor -->
  <section class="section" id="piramide">
    <div class="section-header">
      <div class="section-num">1</div>
      <h2 class="section-title">La Escalera de Valor Analítico</h2>
      <div class="section-subtitle">El paso de saber qué pasó a saber qué decisión tomar</div>
    </div>

    <div class="pyramid-container">
      <div class="pyramid-level lvl-4">
        <div class="lvl-tag">NIVEL 4</div>
        <div class="lvl-content">
          <div class="lvl-title">Prescriptivo: ¿Qué decisión óptima debemos tomar hoy?</div>
          <div class="lvl-desc">Recomendación del siguiente mejor producto por cuenta (Next-Best-SKU), precio de margen máximo y asignación de botellas escasas a restaurantes Michelin / 50 Best.</div>
        </div>
      </div>

      <div class="pyramid-level lvl-3">
        <div class="lvl-tag">NIVEL 3</div>
        <div class="lvl-content">
          <div class="lvl-title">Predictivo: ¿Qué cliente está en riesgo y cuánto venderemos?</div>
          <div class="lvl-desc">Semáforo de cuentas en enfriamiento (alerta de pérdida de clientes), ciclo de recompra estimado y pronóstico de demanda a 12 semanas.</div>
        </div>
      </div>

      <div class="pyramid-level lvl-2">
        <div class="lvl-tag">NIVEL 2</div>
        <div class="lvl-content">
          <div class="lvl-title">Diagnóstico e Inferencia: ¿El cambio es real o es ruido?</div>
          <div class="lvl-desc">Separador de fluctuación estadística vs tendencia real; descomposición precisa de ventas en Efecto Precio, Efecto Volumen y Efecto Mezcla.</div>
        </div>
      </div>

      <div class="pyramid-level lvl-1">
        <div class="lvl-tag">NIVEL 1 (ACTUAL)</div>
        <div class="lvl-content">
          <div class="lvl-title">Descriptivo: ¿Qué vendimos y cómo varió contra el Plan?</div>
          <div class="lvl-desc">Entregables semanales consolidados: PDF directivo de 30 páginas, libro Excel analítico y Dashboard interactivo con filtros reactivos.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- 2. Semáforo Anti-Churn B2B -->
  <section class="section" id="churn">
    <div class="section-header">
      <div class="section-num">2</div>
      <h2 class="section-title">Eje 1: Prevención de Churn y Fidelización B2B</h2>
      <div class="section-subtitle">Cuidar las cuentas de centros de consumo y distribuidores</div>
    </div>

    <div class="callout">
      <strong>La realidad del Tequila Ultra-Premium:</strong> Un restaurante en Los Cabos o una vinoteca gourmet nunca llama para cancelar su cuenta; simplemente deja de pedir porque el sommelier rotó o una marca competidora ofreció incentivos. El objetivo es <em>detectar el silencio anormal</em> antes de que la relación se pierda.
    </div>

    <div class="traffic-box">
      <div class="traffic-card traffic-green">
        <div class="traffic-status">● Cuenta Activa y Saludable</div>
        <p style="font-size:0.77rem;color:#555;">La cuenta ordena dentro de su ventana de tiempo esperada (ej. cada 2 a 3 semanas). Su volumen y margen son consistentes con su historial.</p>
        <div class="traffic-action">Acción Comercial: Mantener atención de rutina y explorar venta cruzada (ofrecer Ámbar si solo compra Blanco).</div>
      </div>

      <div class="traffic-card traffic-yellow">
        <div class="traffic-status">▲ Cuenta en Enfriamiento (Alerta Preventiva)</div>
        <p style="font-size:0.77rem;color:#555;">El tiempo desde su última orden ya superó su ciclo promedio en un 50% (ej. si pedía cada 15 días, ya van 25 días sin orden).</p>
        <div class="traffic-action">Acción Comercial: Visita del Brand Ambassador, cata maridaje con Puro Corazón y reposición de exhibidores de barra.</div>
      </div>

      <div class="traffic-card traffic-red">
        <div class="traffic-status">■ Riesgo Crítico de Pérdida</div>
        <p style="font-size:0.77rem;color:#555;">Silencio transaccional anómalo prolongado. Alta probabilidad de que la marca haya sido retirada de la carta o sustituida.</p>
        <div class="traffic-action">Acción Comercial: Llamada directa del Director Comercial, revisión de condiciones de pago e incentivo especial de reactivación.</div>
      </div>
    </div>

    <div class="card" style="margin-top: 16px;">
      <div class="card-title">Índice de Salud de Cuenta B2B (Account Health Index - AHI)</div>
      <div class="card-desc" style="margin-top:6px;">
        Un semáforo único de 0 a 100 para cada cliente que evalúa cuatro pilares comerciales:
        <ul style="margin: 8px 0 0 20px; font-size:0.78rem; line-height: 1.6;">
          <li><strong>Puntualidad de Compra:</strong> ¿Está pidiendo a su ritmo habitual o está espaciando los pedidos?</li>
          <li><strong>Amplitud de Portafolio:</strong> Las cuentas que compran solo Loco Blanco tienen 3 veces más riesgo de irse que las que compran también Ámbar o Puro Corazón.</li>
          <li><strong>Calidad de Margen:</strong> Alerta si el margen bruto se está erosionando por otorgar descuentos excesivos.</li>
          <li><strong>Consistencia de Volumen:</strong> Tendencia de cajas de 9L en las últimas 8 semanas.</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- 3. Diagnóstico e Inferencia -->
  <section class="section" id="diagnostico">
    <div class="section-header">
      <div class="section-num">3</div>
      <h2 class="section-title">Eje 2: Diagnóstico Estadístico e Inferencia</h2>
      <div class="section-subtitle">Diferenciar el ruido semanal de los cambios comerciales reales</div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">1. El Separador de Ruido Semanal</div>
          <span class="card-badge badge-high">Fácil de Integrar</span>
        </div>
        <div class="card-desc">
          Hoy el reporte muestra: <em>"Ventas -2.5% vs semana anterior"</em>. Para la dirección, eso puede sonar a alarma. La estadística nos permite calcular una <strong>banda de fluctuación normal</strong>: si la caída está dentro de lo esperado para esa época del año, el sistema reporta <em>"Variación dentro del rango normal"</em>, evitando juntas de emergencia innecesarias.
        </div>
        <div class="card-takeaway">Tranquilidad directiva: solo atender lo que estadísticamente sea un cambio real.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">2. El Desarmador de Variaciones (Precio × Volumen × Mix)</div>
          <span class="card-badge badge-high">Gran Valor</span>
        </div>
        <div class="card-desc">
          Cuando las ventas cambian, la dirección necesita saber la causa raíz exacta:
          <ul style="margin: 8px 0 0 16px; font-size:0.78rem; line-height:1.5;">
            <li><strong>Efecto Precio:</strong> ¿Ganamos o perdimos porque cambió la lista de precios o los descuentos?</li>
            <li><strong>Efecto Volumen:</strong> ¿Se movieron más o menos cajas físicas?</li>
            <li><strong>Efecto Mezcla (Mix):</strong> ¿Nos compraron botellas más caras (Áureo/Corazón) o más baratas?</li>
          </ul>
        </div>
        <div class="card-takeaway">Explica en centavos por qué subió o bajó el ingreso neto.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">3. Elasticidad y Precios Óptimos</div>
          <span class="card-badge badge-mid">Estratégico</span>
        </div>
        <div class="card-desc">
          Responde preguntas críticas de fijación de precios: <em>¿Qué pasa si incrementamos 5% el precio de Loco Blanco en canal On-Trade? ¿Perderemos pedidos o los centros de consumo absorberán el ajuste? ¿Se pasarán a Puro Corazón o a Don Julio 1942?</em>
        </div>
        <div class="card-takeaway">Determina el precio que maximiza el margen neto en pesos, no solo las botellas vendidas.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">4. Medidor de Éxito de Eventos y Patrocinios</div>
          <span class="card-badge badge-info">Causal Impact</span>
        </div>
        <div class="card-desc">
          Aísla el retorno financiero real de una activación especial (ej. el lanzamiento de la <em>Edición Día de Muertos</em> o patrocinio de gala gastronómica), comparando el resultado de las plazas donde se activó contra plazas testigo que no tuvieron evento.
        </div>
        <div class="card-takeaway">Descubre si el evento generó ventas verdaderamente nuevas o solo adelantó compras.</div>
      </div>
    </div>
  </section>

  <!-- 4. Prescriptivo y Asignación -->
  <section class="section" id="prescriptivo">
    <div class="section-header">
      <div class="section-num">4</div>
      <h2 class="section-title">Eje 3: Asignación de Producto y Recomendaciones Comerciales</h2>
      <div class="section-subtitle">Optimizar la escasez y expandir el catálogo por cliente</div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Distribuidor Inteligente de Botellas Escasas</div>
          <span class="card-badge badge-high">Alta Relevancia</span>
        </div>
        <div class="card-desc">
          Para botellas de producción muy limitada (<em>Loco Áureo Elevación, Puro Corazón Edición Serpiente/Colibrí, Loco 269</em>), el producto no alcanza para todos. Un algoritmo matemático asigna las cuotas disponibles priorizando dos variables:
          <ul style="margin: 8px 0 0 16px; font-size:0.78rem; line-height:1.5;">
            <li><strong>Margen Neto Realizado:</strong> Cuentas con menor descuento comercial y mejor cumplimiento de pago.</li>
            <li><strong>Prestigio de Marca:</strong> Hoteles gran turismo y restaurantes de alta cocina donde la presencia de la botella genera deseo y valor de marca.</li>
          </ul>
        </div>
        <div class="card-takeaway">Evita que lotes exclusivos se malbaraten en canales de bajo prestigio.</div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Recomendador "Siguiente Mejor Producto" (Next-Best-SKU)</div>
          <span class="card-badge badge-high">Comercial</span>
        </div>
        <div class="card-desc">
          Analiza el patrón de compra de clientes similares para darle al vendedor la sugerencia exacta de venta cruzada:
          <em>"A este restaurante que lleva 3 meses comprando solo Loco Blanco, cuentas similares le compraron Loco Ámbar con 78% de probabilidad de éxito si se acompaña con cata guiada"</em>.
        </div>
        <div class="card-takeaway">Guía al equipo de ventas con recomendaciones basadas en datos, no en intuición.</div>
      </div>
    </div>
  </section>

  <!-- 5. Hoja de Ruta -->
  <section class="section" id="roadmap">
    <div class="section-header">
      <div class="section-num">5</div>
      <h2 class="section-title">Hoja de Ruta Priorizada (Paso a Paso)</h2>
      <div class="section-subtitle">Plan modular sin interrumpir los reportes actuales</div>
    </div>

    <div class="callout">
      <strong>Regla de Oro:</strong> Ninguna fase altera ni rompe los reportes que hoy ya funcionan. Cada módulo se suma como una pestaña nueva en Excel o una tarjeta interactiva en el Dashboard HTML.
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Fase</th>
            <th>Plazo</th>
            <th>Módulo de Negocio</th>
            <th>¿Qué verá la Dirección?</th>
            <th>Datos Necesarios</th>
            <th>Factibilidad</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="phase-badge">Fase 0</span></td>
            <td><strong>1 semana</strong></td>
            <td><strong>Separador de Ruido + Efecto Precio/Volumen</strong></td>
            <td>Banda de confianza en KPIs y semáforo que explica si la venta varió por precio o por volumen.</td>
            <td>Datos que ya tenemos ✅</td>
            <td><span class="card-badge badge-ready">Inmediata</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 1</span></td>
            <td><strong>2–3 sem</strong></td>
            <td><strong>Semáforo Anti-Churn B2B y Salud de Cuenta</strong></td>
            <td>Pestaña "Retención de Cuentas" en Excel y semáforo verde/amarillo/rojo en el Dashboard.</td>
            <td>Datos que ya tenemos ✅ (+Vendedor real)</td>
            <td><span class="card-badge badge-ready">Alta</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 2</span></td>
            <td><strong>3–4 sem</strong></td>
            <td><strong>Ciclos de Recompra y Permanencia</strong></td>
            <td>Tabla que proyecta cuántas semanas suelen pasar antes de que una cuenta vuelva a ordenar.</td>
            <td>Datos que ya tenemos ✅</td>
            <td><span class="card-badge badge-ready">Media-Alta</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 3</span></td>
            <td><strong>4–5 sem</strong></td>
            <td><strong>Valor Futuro Estimado por Cuenta (CLV)</strong></td>
            <td>Proyección de cuánto dinero comprará cada cliente clave en los próximos 3 meses.</td>
            <td>Datos que ya tenemos ✅</td>
            <td><span class="card-badge badge-ready">Media</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 4</span></td>
            <td><strong>5–7 sem</strong></td>
            <td><strong>Optimizador de Precios y Margen</strong></td>
            <td>Simulador para predecir si conviene subir precio en algún canal sin perder cajas.</td>
            <td>Requiere registrar cambios de listas</td>
            <td><span class="card-badge badge-mid">Estratégica</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 5</span></td>
            <td><strong>7–9 sem</strong></td>
            <td><strong>Pronóstico Jerárquico de Demanda a 12 semanas</strong></td>
            <td>Proyección coherente que suma igual a nivel vendedor, plaza y total nacional.</td>
            <td>Se afina al acumular semanas reales</td>
            <td><span class="card-badge badge-mid">Media</span></td>
          </tr>
          <tr>
            <td><span class="phase-badge">Fase 6</span></td>
            <td><strong>9–12 sem</strong></td>
            <td><strong>Simulador "What-If" Interactivo</strong></td>
            <td>Palancas deslizantes en el Dashboard HTML para mover precios y mix y ver el impacto en vivo.</td>
            <td>Depende de Fases 4 y 5</td>
            <td><span class="card-badge badge-info">Avanzada</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- 6. Preguntas Directivas -->
  <section class="section" id="preguntas">
    <div class="section-header">
      <div class="section-num">6</div>
      <h2 class="section-title">Preguntas Clave para el Comité Directivo</h2>
      <div class="section-subtitle">Definir prioridades para arrancar las primeras fases</div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">1. ¿Qué información comercial adicional se puede incorporar?</div>
        <div class="card-desc" style="margin-top:8px;">
          ¿Existen portales donde clientes como <em>La Europea</em> o <em>Liverpool</em> compartan sus inventarios en tienda (sell-out)? De ser así, podemos anticipar pedidos semanas antes de que ocurran.
        </div>
      </div>

      <div class="card">
        <div class="card-title">2. ¿Se dispone de la agenda de visitas de los vendedores?</div>
        <div class="card-desc" style="margin-top:8px;">
          Si conectamos el semáforo de riesgo con el vendedor asignado a cada cuenta, el sistema puede generar automáticamente la <strong>lista de visitas prioritarias de la semana</strong>.
        </div>
      </div>
    </div>
  </section>

</main>

<footer>
  Loco Tequila · Plan de Analítica Avanzada · Generado con el sistema de diseño institucional · Septiembre 2026
</footer>

</body>
</html>
"""
    return html


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_content = build_html()
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Documento HTML generado exitosamente:")
    print(f"     -> {OUTPUT_HTML}")
    print(f"     Tamanio: {len(html_content.encode('utf-8')) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
