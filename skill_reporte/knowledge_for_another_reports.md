# Guía Maestra de Replicación: Sistema Tripartito de Reportes Ejecutivos
## Blueprint de Arquitectura para Migrar o Replicar el Reporte con Otra Marca

> Este documento resume los principios de diseño, la estructura modular y los puntos clave necesarios para tomar esta arquitectura de reportes ejecutivos (PDF + XLSX + Dashboard HTML) y desplegarla exitosamente para **cualquier otra marca o industria**, manteniendo el estándar de calidad directiva.

---

## 1. Filosofía y Arquitectura del Sistema

El éxito de este sistema radica en el **desacoplamiento estricto** entre cuatro capas independientes:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           1. FUENTE DE DATOS                            │
│           CSVs / Excel / ERP / Plan de Ventas / Presupuesto             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  2. CAPA DE NORMALIZACIÓN Y NEGOCIO                     │
│    data_processor.py: Limpieza, homologación canónica, KPIs temporales   │
│           (WoW, MoM, YoY, YTD, Rolling 52 semanas, Var vs Plan)         │
└──────────────┬───────────────────────────────────────────┬──────────────┘
               │                                           │
               ▼                                           ▼
┌──────────────────────────────┐           ┌──────────────────────────────┐
│  3. TOKENS DE DISEÑO Y MARCA │           │ 4. INTELIGENCIA DE MERCADO   │
│  design_tokens.py            │           │ market_context.py            │
│  logo_processor.py           │           │ Web search + Riesgos/Oport.  │
└──────────────┬───────────────┘           └──────────────┬───────────────┘
               │                                          │
               └─────────────────────┬────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    5. MOTORES DE RENDERIZADO TRIPARTITO                 │
│  ┌───────────────────────┬──────────────────────┬────────────────────┐  │
│  │   pdf_generator.py    │  xlsx_generator.py   │dashboard_generator │  │
│  │   ReportLab directivo │  openpyxl analítico  │HTML/JS interactivo │  │
│  └───────────────────────┴──────────────────────┴────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   6. ORQUESTADOR Y OPERACIÓN AGÉNTICA                   │
│   generate_report.py: CLI unificado + AGENTS.md (reglas de interacción) │
└─────────────────────────────────────────────────────────────────────────┘
```

El principio fundamental es la **entrega tripartita simultánea**:
1. **PDF Directivo (~25-35 págs)**: Pensado para el C-Level / Consejo; visual, estricto en jerarquía tipográfica, márgenes y páginas temáticas auto-contenidas.
2. **Excel Analítico (6-8 Hojas)**: Pensado para Finanzas y Control de Gestión; fórmulas nativas, semáforos, tablas dinámicas y gráficas con ejes legibles.
3. **Dashboard Web HTML**: Pensado para el equipo comercial y operativo; interactivo, sin backend (standalone), recálculo de KPIs en tiempo real, responsive y exportable.

---

## 2. Los Puntos Principales a Adaptar para una Nueva Marca

Cuando vayas a crear el reporte de una nueva marca (asumiendo que ya tienes su manual de identidad visual, logo y datos de venta), debes trabajar sobre estos **6 bloques fundamentales**:

---

### Bloque A: Tokens de Diseño y Paleta de Identidad (`design_tokens.py`)

Es la **fuente única de verdad** de colores, fuentes y medidas. Ningún color hexadecimal debe escribirse "quemado" (hardcoded) en los generadores.

Puntos a definir en el nuevo archivo:
1. **Colores Institucionales de Marca**:
   - `BRAND_PRIMARY`: Color dominante (ej. Maroon en Loco, Azul Marino en ginebras, Verde Oliva en destilados botánicos, Negro/Oro en marcas Ultra-Premium).
   - `BRAND_DEEP`: Versión más oscura para gradientes y sombras.
   - `HEADER_TEXT`: Color de texto en bandas principales (usualmente `#FFFFFF`).
2. **Paleta Semántica Universal**:
   - `POS_VALUE`: Verde o Neutro oscuro (`#333333`) para variaciones positivas.
   - `NEG_VALUE`: Rojo institucional (`#E23B2E`) para desviaciones negativas o bajo presupuesto.
   - `HIGHLIGHT_CREAM`: Tinte suave de contraste para columnas/filas resaltadas (`#FBF3DD` o tintes acordes a la nueva marca).
   - `CHART_PLAN_LINE`: Color contrastante para la línea de presupuesto/meta (ej. rojo o dorado).
3. **Paleta Específica por SKU / Submarca (`PRODUCT_COLORS`)**:
   - Cada producto del portafolio debe tener un color **fijo, distinguible y coherente** con su etiqueta o botella.
   - **Regla de oro**: El mismo producto debe verse del mismo color en el treemap del PDF, en las series de Chart.js del Dashboard y en las columnas de Excel.
4. **Paleta y Orden de Canales Comerciales (`CANAL_COLORS` y `CANAL_ORDER`)**:
   - Definir los canales estándar de la marca (ej. On-Premise, Off-Premise tradicional, Autoservicio/Moderno, E-Commerce, Duty Free, Venta Directa).
5. **Tipografía y Formateadores**:
   - Nombre de familia para gráficas vectoriales (`FONT_FAMILY`).
   - Helpers de formato adaptados a la moneda y región:
     - `fmt_currency(val)`: Formato monetario (ej. `$1,889,000`).
     - `fmt_pct(val)`: Porcentaje con signo (`+12.5%` o `-3.2%`).
     - `fmt_int(val)`: Conteo entero con separador de miles.
     - `fmt_ticket(val)`: Ticket o precio medio ponderado por unidad.

---

### Bloque B: Normalización de Datos y Catálogo Canónico (`data_processor.py`)

Los datos crudos de ventas suelen llegar de distintas fuentes (ERP, mayoristas, distribuidores, tickets de retail) con nombres inconsistentes, faltas de ortografía o códigos no estandarizados.

Puntos a configurar:
1. **Diccionario de Homologación de Productos (`PRODUCT_MAPPING`)**:
   - Mapear todas las variantes textuales que aparecen en los CSVs hacia el nombre canónico de catálogo.
   - Ejemplo: `"Vap Blanco 2 copas"`, `"LOCO BLANCO 750"`, `"Loco Blanco 750ml"` $\rightarrow$ `"Loco Blanco"`.
2. **Diccionario de Homologación de Canales (`CANAL_MAPPING`)**:
   - Mapear variantes locales de sucursales o equipos a los canales directivos.
   - Ejemplo: `"VD Mty"`, `"Venta Directa Puebla"` $\rightarrow$ `"Venta Directa"`.
3. **Conversión de Unidades Físicas a Equivalencias de Industria**:
   - En destilados: Botellas $\rightarrow$ Litros $\rightarrow$ Cajas de 9 Litros equivalentes (`cajas_9L`).
   - En vino: Cajas de 12 botellas o 9L.
   - En cerveza: Hectolitros o cartones.
   - En retail/FMCG: Paquetes, bultos o cajas físicas.
4. **Motores de Cálculo Temporal Automáticos**:
   - Asegurar que el procesador calcule automáticamente para la semana base seleccionada:
     - **WoW**: Semana actual vs semana anterior ($N$ vs $N-1$).
     - **YoY**: Semana actual vs misma semana del año anterior.
     - **YTD**: Acumulado del año corriente (Semana 1 a $N$) vs acumulado del año anterior (Semana 1 a $N$).
     - **Rolling 52**: Últimas 52 semanas consecutivas vs las 52 semanas previas.
     - **Plan**: Cumplimiento y variación contra presupuesto mensual o semanal.

---

### Bloque C: Identidad Vectorial y Logo (`logo_processor.py`)

El reporte ejecutivo requiere que el logo se integre en alta resolución tanto en fondos claros (Excel/Dashboard) como en fondos oscuros de marca (cabeceras ReportLab en el PDF).

Puntos clave:
1. **Insumo Ideal**: Archivo vectorial **SVG**.
2. **Generación Automática de Versión Blanca/Negativa**:
   - El script debe tomar el SVG original y generar o transformar automáticamente los atributos `fill` y `stroke` a `#FFFFFF` para la cabecera maroon/oscura.
3. **Conversión Vectorial a Raster para ReportLab**:
   - Usar `cairosvg` o `pycairo` si está disponible, o `reportlab.graphics.shapes` para renderizar el logo sin pérdida de nitidez.
   - Incluir siempre un **fallback textual elegante** si no existe archivo de imagen (ej. texto estilizado con letra condensada y espaciado de letras).

---

### Bloque D: Contexto Externo y Fuentes del Mercado (`market_context.py`)

Un reporte financiero de nivel directivo no analiza las ventas en el vacío; las contrasta con el entorno macro y del sector.

Puntos a adaptar para la nueva marca:
1. **Organismos Reguladores e Instituciones de Referencia**:
   - En Tequila: Consejo Regulador del Tequila (CRT), Cámara Nacional de la Industria Tequilera (CNIT), precio del Agave Tequilana Weber, NOM-006-SCFI.
   - En Mezcal: COMERCAM / Consejo del Mezcal, precio del Agave Espadín/Silvestre, NOM-070.
   - En Vinos: OIV, Consetur, vendimias, clima, cosechas y tipo de cambio.
   - En Alimentos / Retail: ANTAD, INEGI, inflación de canasta básica, tarifas arancelarias.
2. **Plantilla de Análisis Estructurado**:
   - El sistema debe soportar un archivo de texto con estructura obligatoria de pares:
     - `RIESGO: [Descripción del impacto potencial en costo o volumen]`
     - `OPORTUNIDAD: [Estrategia accionable ante la coyuntura del mercado]`
     - `FUENTE: [Cita formal]`
3. **Flujo de Ingesta Inteligente**:
   - El agente de IA busca en la web las noticias más recientes de la categoría, completa el template y lo inyecta en los 3 entregables (sección destacada en PDF, hoja dedicada en Excel, tarjetas en Dashboard).

---

### Bloque E: Parametrización de los Motores de Salida

#### 1. Reporte PDF (`pdf_generator.py` con ReportLab)
- **Heurística de Gráficas de Portada**:
  - Si la marca tiene **$\le$ 3-4 productos clave**: Utilizar gráfica de **Dona** con etiqueta total al centro y tarjetas de desglose.
  - Si la marca tiene **$>$ 4 productos**: Cambiar automáticamente a **Treemap de Voronoi / Rectangular** o Barras Horizontales para evitar colisiones de etiquetas.
- **Estructura de Bloques Auto-contenidos**:
  - Cada página debe tener su cabecera de marca, título de sección, tabla comparativa (Real vs Plan vs Año Ant.) y gráfica de barras/línea.
  - Páginas de resumen general $\rightarrow$ Desglose por Canal $\rightarrow$ Fichas individuales por SKU $\rightarrow$ Fichas individuales por Cliente Top.

#### 2. Libro Excel (`xlsx_generator.py` con openpyxl)
- **Estructura de Pestañas**:
  1. *Resumen Ejecutivo* (KPI cards + semáforo de cumplimiento).
  2. *Comparativo Temporal* (WoW, MoM, YoY, YTD).
  3. *Por Producto* (Ranking, volumen, precio unitario).
  4. *Por Cliente* (Pareto, concentración de venta).
  5. *Regional / Territorial* (Ventas por estado o zona).
  6. *Oportunidades y Contexto de Mercado*.
- **Reglas de Estilo**:
  - Celdas numéricas siempre con formato numérico de Excel (no strings), alineación derecha.
  - Textos alineación izquierda.
  - Ejes de gráficas de openpyxl siempre normalizados mediante `_fix_chart_axes` para evitar que Excel oculte los nombres de categorías.

#### 3. Dashboard Web Interactivo (`dashboard_generator.py`)
- **Arquitectura Standalone**: Generar un archivo HTML único con los datos embebidos en JSON (`window.REPORT_DATA = {...}`).
- **Componentes Clave**:
  - Barra de filtros reactivos: Año, Semana, Canal, Producto, Cliente (mediante `<select>` ordenado alfabéticamente).
  - Recálculo dinámico en el cliente: al cambiar un filtro, todos los KPIs superiores y las 5 gráficas de Chart.js deben recalcularse al vuelo.
  - Modal para ampliar gráficos (`⛶ Ampliar`) con vista expandida.
  - Botón de descarga de imagen PNG de cada gráfica.
  - Botón de exportación a CSV con **marca BOM UTF-8** para compatibilidad inmediata con Excel en español.

---

### Bloque F: Reglas de Orquestación y Agentes (`generate_report.py` y `AGENTS.md`)

Para que el reporte pueda ser operado tanto por un humano desde consola como por cualquier modelo de IA (Claude, Gemini, DeepSeek, ChatGPT):
1. **Regla de Máximo 2 Preguntas Iniciales**:
   - Pregunta 1: Fuente de datos (¿CSV propio o muestra?).
   - Pregunta 2: Periodo a evaluar (Semana y Año base).
2. **Generación Sin Fricciones**:
   - Los 3 formatos (PDF + XLSX + HTML) se generan en una sola corrida sin preguntar.
   - Las 4 comparaciones temporales (WoW, YoY, YTD, Rolling) son fijas y no negociables.
3. **Prevención de Fallos en Windows**:
   - Envolver `sys.stdout` y `sys.stderr` en UTF-8 al inicio del script para evitar excepciones `cp1252` o `UnicodeEncodeError`.

---

## 3. Checklist Paso a Paso para Crear el Reporte de una Marca Nueva

Sigue este orden de implementación cuando inicies un nuevo proyecto de reporting:

```markdown
[ ] FASE 1: INSUMOS DE MARCA
    [ ] 1.1 Obtener logo en SVG y paleta corporativa oficial (Hexadecimales).
    [ ] 1.2 Identificar catálogo de SKUs y colores representativos de cada producto.
    [ ] 1.3 Obtener archivos de ventas históricos (mínimo 1 año para YoY, ideal 2 para Rolling 52) y archivo de Plan/Budget.

[ ] FASE 2: CONFIGURACIÓN DE TOKENS (scripts/design_tokens.py)
    [ ] 2.1 Sustituir BRAND_PRIMARY, BRAND_DEEP y neutros por los de la nueva marca.
    [ ] 2.2 Reemplazar diccionarios PRODUCT_COLORS, PRODUCT_ORDER y PRODUCT_DISPLAY_NAMES.
    [ ] 2.3 Reemplazar CANAL_COLORS y CANAL_ORDER.
    [ ] 2.4 Ajustar divisas y símbolos numéricos (MXN, USD, EUR, etc.).

[ ] FASE 3: MAPEO Y TRANSFORMACIÓN DE DATOS (scripts/data_processor.py)
    [ ] 3.1 Construir el diccionario EXPANDED_PRODUCT_MAPPING con las variantes reales de la nueva marca.
    [ ] 3.2 Construir el diccionario CANAL_MAPPING con los canales de distribución del cliente.
    [ ] 3.3 Validar la fórmula de conversión a unidades estándar (cajas, litros, botellas).
    [ ] 3.4 Probar data_processor.py de forma aislada y confirmar que los DataFrames agregados cuadren al centavo.

[ ] FASE 4: CONTEXTO DE INDUSTRIA (scripts/market_context.py)
    [ ] 4.1 Definir las 3-5 entidades o fuentes regulatorias del sector de la marca.
    [ ] 4.2 Configurar las queries de búsqueda web automatizadas (tendencias de precios de materias primas, aranceles, consumo).
    [ ] 4.3 Redactar el template con hallazgos de RIESGO y OPORTUNIDAD.

[ ] FASE 5: AJUSTES EN GENERADORES (PDF, XLSX, HTML)
    [ ] 5.1 PDF: Ajustar alturas de cabecera y títulos según la longitud de nombres de los nuevos SKUs.
    [ ] 5.2 PDF: Si el catálogo supera 4 SKUs, asegurar treemap o barras horizontales en lugar de dona en portada.
    [ ] 5.3 XLSX: Verificar que los encabezados de columnas reflejen las métricas del nuevo negocio.
    [ ] 5.4 HTML: Verificar que los estilos CSS tomen las variables de color del nuevo design_tokens.py.

[ ] FASE 6: CONTROL DE CALIDAD Y PRUEBAS
    [ ] 6.1 Ejecutar corrida completa: python scripts/generate_report.py --semana X --anio Y.
    [ ] 6.2 Validar que el PDF abra correctamente y no tenga textos encimados ni desbordamientos de página.
    [ ] 6.3 Validar que el Excel abra sin alertas de "archivo dañado" y que las gráficas muestren sus etiquetas de eje X.
    [ ] 6.4 Validar que el HTML filtre en vivo y exporte CSV con tildes y caracteres especiales intactos.
```

---

## 4. Errores Comunes y Lecciones Aprendidas (Evitar a toda costa)

1. **El bug de los ejes mudos en openpyxl (Excel)**:
   - Al crear gráficos nativos en Excel con openpyxl, por defecto los ejes X pueden desaparecer o mostrarse vacíos en versiones de Microsoft 365. Se debe forzar explícitamente el borrado de la etiqueta `delete` en el XML del gráfico (`chart.x_axis.delete = False`) y fijar su posición (`axPos = 'b'`).
2. **Corte de series temporales (Rolling 52 / Año Anterior)**:
   - En el primer año de datos (ej. semana 1 a 52), la serie comparativa del año anterior no existe. La gráfica **debe cortar la línea** (valores `None` o `NaN`), nunca dejarla caer a cero `$0`, ya que distorsiona la escala e induce a errores de lectura directiva.
3. **Codificación de texto en Windows**:
   - Los nombres de clientes y productos en español suelen incluir tildes (`á`, `é`, `í`, `ó`, `ú`) y `ñ`. Todo archivo CSV generado debe anteponer `\ufeff` (UTF-8 BOM); de lo contrario, Excel en Windows los abrirá con caracteres corruptos.
4. **Colisión visual en gráficas de dona**:
   - Las gráficas de pastel o dona solo toleran hasta 3 o 4 categorías. Para portafolios con 5 a 15 SKUs, sustituir siempre por treemaps o barras horizontales con etiquetas limpias.

---

## 5. Estructura Recomendada para el Nuevo Repositorio de Marca

```
reporte_nombre_marca/
├── assets/
│   ├── Logo_Marca.svg              # Logo original de la marca
│   └── Logo_Marca_white.svg        # Versión negativa en blanco
├── data/
│   ├── actuals_historico.csv       # Ventas reales históricas
│   └── plan_ventas_semanal.csv     # Presupuesto / Plan
├── designs/
│   └── Design.md                   # Especificación tipográfica y paleta
├── output/                         # Carpeta donde se depositan los 3 entregables
├── scripts/
│   ├── __init__.py
│   ├── design_tokens.py            # Tokens de diseño y paletas de la marca
│   ├── data_processor.py           # Ingesta, limpieza y cálculos temporales
│   ├── logo_processor.py           # Adaptación y renderizado de logos
│   ├── market_context.py           # Consultas y resumen de coyuntura de mercado
│   ├── pdf_generator.py            # Motor ReportLab
│   ├── xlsx_generator.py           # Motor openpyxl
│   ├── dashboard_generator.py      # Motor HTML/CSS/Chart.js interactivo
│   └── generate_report.py          # CLI Orquestador
├── AGENTS.md                       # Reglas de interacción para asistentes IA
├── requirements.txt                # Dependencias (pandas, reportlab, openpyxl, cairosvg, etc.)
└── knowledge_for_another_reports.md# Esta guía de arquitectura
```

---
*Con este documento, cualquier ingeniero de datos, diseñador o agente de IA cuenta con el mapa de ruta exacto para adaptar el motor a cualquier portafolio comercial en cuestión de horas.*
