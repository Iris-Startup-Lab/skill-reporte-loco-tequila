# AGENTS.md — Guía de Operación y Pruebas para Agentes IA y Usuarios

Este archivo contiene las instrucciones completas para ejecutar, probar y extender la skill **`reporte_loco_tequila`** de **Loco Tequila** utilizando diversos entornos de Inteligencia Artificial y agentes locales.

---

## 🎯 Propósito del Proyecto

Generar de forma autónoma los tres entregables ejecutivos del reporte de ventas y margen:

1. **PDF (~30 págs)**: Visualización directiva con paleta Maroon, gráficos vectoriales y logo institucional.
2. **XLSX (6-8 Hojas)**: Libro Excel analítico con condicionales, comparativos personalizados (WoW, MoM, YoY) y contexto de mercado.
3. **Dashboard HTML**: Dashboard interactivo responsivo con recálculo dinámico en tiempo real de KPIs y gráficas al aplicar filtros, exportación CSV con UTF-8 BOM y descarga de gráficas a imagen PNG.

---

## 🚦 Reglas de Interacción del Agente (OBLIGATORIAS)

Para evitar preguntas innecesarias, el agente debe seguir estas reglas al activar la skill (MÁXIMO 2 PREGUNTAS INICIALES EN TOTAL):

1. **Pregunta 1: Fuente de Datos (solo si no se adjuntaron datos ni ruta)**:
   - Si el usuario **ya adjuntó archivos CSV** en el chat o **especificó una ruta de datos**, procede directamente con esos datos.
   - Si el usuario **no ha adjuntado datos ni indicado ruta**, haz únicamente esta pregunta:
     *"¿Prefieres adjuntar/indicar la ruta de tus **datos propios CSV** o generar el reporte con los **datos de muestra** (`data_for_test_and_simulation/`)?"*
   - 🚫 **REGLA CRÍTICA DE SINTAXIS**: NUNCA menciones frases como *"No veo archivos en tu carpeta de uploads"*, *"Tu carpeta de uploads está vacía"*, ni asumas que existe un monitoreo automático de carpetas. El agente no busca ni monitorea carpetas de uploads en segundo plano; simplemente procesa lo que el usuario adjunta en el chat o la ruta que indica.
2. **Pregunta 2: Periodo / Semana Base a Comparar (solo si el usuario no especificó semana y año)**:
   - Si el usuario **ya especificó la semana y año base** en su instrucción (ej. *"Genera el reporte de la semana 30 de 2026"*), usa esos valores sin preguntar.
   - Si el usuario **NO especificó la semana ni el año base** a analizar, pregunta:
     *"¿Qué **semana y año base** deseas evaluar y comparar en el reporte? (Ejemplo: Semana 30 de 2026)"*
   - *Nota*: Si el usuario elige usar datos de muestra y no indica semana/año, usa por defecto la **Semana 30 de 2026** (`--semana 30 --anio 2026`).
3. **Siempre genera los 3 formatos** (PDF + XLSX + HTML) en una corrida. **Nunca** preguntes qué formato quiere; no uses `--solo` salvo petición explícita.
4. **Comparativos fijos, sin preguntar**: el reporte SIEMPRE incluye estas 4 comparaciones automáticas contra la semana base elegida:
   - Semana seleccionada **vs semana inmediata anterior**.
   - Semana seleccionada **vs misma semana del año anterior**.
   - **Acumulado (YTD)** del año en curso hasta la semana seleccionada **vs el mismo acumulado del año anterior**.
   - **Rolling 52 semanas** vs las mismas 52 del año anterior.
   No ofrezcas ni pidas comparativos adicionales; usa `--modo-comparar` solo si el usuario lo pide con palabras.
5. **No hagas preguntas de contexto irrelevantes** (imágenes, logos, colores, temas). Todo está resuelto por defecto.
6. El **contexto de mercado** (CRT/agave/NOM) es **SIEMPRE OBLIGATORIO**: en cada reporte, antes de generar, busca en la web (CRT, precio agave, NOM-006, exportaciones), llena el `.txt` con líneas `RIESGO:` / `OPORTUNIDAD:` y genera con `--contexto-mercado`. Solo si la búsqueda web falla por completo se genera sin él (placeholder).

---

## 🐍 Configuración del Entorno Conda

Todos los comandos requieren ejecutarse dentro del entorno de Python **`data_analytics_science`**.

### Activación en PowerShell (Windows)

```powershell
# 1. Cargar el hook de Conda
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression

# 2. Activar el ambiente de trabajo
conda activate data_analytics_science
```

### Instalación de Dependencias (si se prueba en un nuevo ambiente)

```powershell
# Dependencias gráficas nativas (Cairo para SVG -> PNG del logo)
conda install -c conda-forge cairo pycairo -y

# Requerimientos de Python
pip install -r requirements.txt
```

---

## 🤖 Guía de Ejecución por Entorno de IA y Modelo

### 1. OpenCode (CLI / IDE Agent)

- **Modelos recomendados**:
  - **DeepSeek V3 / R1 / V4 Pro**
  - **Kimi 3 / K1.5**
- **Instrucciones para OpenCode**:
  1. Abrir la carpeta del proyecto en OpenCode.
  2. Al recibir una instrucción como *"Genera el reporte de la semana 30 de 2026"*, el agente detectará automáticamente `SKILL.md` y `AGENTS.md`.
  3. Ejecutar la llamada activando el entorno conda antes de invocar Python:

     ```powershell
     & "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science; python scripts/generate_report.py --semana 30 --anio 2026
     ```

---

### 2. Antigravity (Google DeepMind Agentic IDE)

- **Modelos recomendados**:
  - **Gemini 3.6 Flash** (Predeterminado para alta velocidad y precisión de código)
  - **Gemini 3.1 Pro / Ultra**
- **Instrucciones para Antigravity**:
  1. Antigravity descubre automáticamente las skills en la raíz de trabajo o en `.agents/skills/`.
  2. El agente procesará las peticiones del usuario, pudiendo usar la herramienta `search_web` para consultar información externa del mercado tequilero (CRT, agave, NOM-006) y estructurarla en el reporte.
  3. Al ejecutar comandos en la terminal de Antigravity, anteponer la activación de Conda.

---

### 3. Claude Desktop y Claude Code

- **Modelos recomendados**:
  - **Claude Sonnet**
  - **Claude Opus**
- **Configuración en Claude Desktop**:
  - Configurar los servidores MCP (Model Context Protocol) correspondientes:
    - `@modelcontextprotocol/server-filesystem`
    - `@modelcontextprotocol/server-powershell` / terminal commands.
  - Cargar `SKILL.md` en el sistema o espacio de conocimiento (*Project Knowledge*).
- **Configuración en Claude Code (CLI)**:
  - Abrir la terminal en la raíz del proyecto y lanzar `claude`.
  - Ejemplo de prompt:
    > *"Analiza la semana 30 de 2026 comparándola contra la semana 25 y genera el libro de Excel"*
  - Claude Code ejecutará:

    ```powershell
    python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx --modo-comparar semana --comparar-semana 25 --comparar-anio 2026
    ```

---

## ⚡ Comandos Rápidos de Prueba

### Generar todos los entregables (Semana 30, 2026)

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 --datos-dir data_for_test_and_simulation --output-dir output
```

### Generar solo el Dashboard HTML interactivo

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 --solo html
```

### Generar solo el Reporte PDF

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 --solo pdf
```

### Generar solo el Libro XLSX de Excel

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx
```

### Probar Comparativo Custom (ej. Julio vs Mayo 2026)

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx --modo-comparar mes --comparar-mes 5 --comparar-anio 2026
```

### Probar Contexto de Mercado (CRT / Agave / NOM-006)

```powershell
# 1. Ver queries
python scripts/generate_report.py --semana 30 --anio 2026 --mostrar-queries-mercado

# 2. Generar template
python scripts/generate_report.py --semana 30 --anio 2026 --generar-template-mercado

# 3. Correr reporte con contexto
python scripts/generate_report.py --semana 30 --anio 2026 --contexto-mercado output/template_contexto_mercado_S30_2026.txt
```

---

## 🔍 Checklist de Verificación para Agentes

Al finalizar cualquier modificación en el código:

- [ ] Ejecutar el orquestador principal con `--solo html`, `--solo pdf` y `--solo xlsx`.
- [ ] Verificar que no existan excepciones de codificación `cp1252` o `UnicodeDecodeError` en Windows.
- [ ] **Contexto de mercado (OBLIGATORIO):** generar SIEMPRE con `--contexto-mercado`. Tras generar, abrir la hoja "Contexto Mercado" del XLSX y confirmar que trae datos reales (resumen + hallazgos Riesgo/Oportunidad + fuentes) y **no** el placeholder "…no disponible…". Si aparece el placeholder, se olvidó la búsqueda web: repetir el flujo (buscar → llenar `.txt` → regenerar con `--contexto-mercado`).
- [ ] **Gráficas del XLSX:** al abrir el archivo, las gráficas deben mostrar sus ejes automáticamente (no debe hacer falta aplicar "Diseño 3" a mano). Si agregaste una gráfica nueva, insértala con `_add_chart_with_note(...)` para que `_fix_chart_axes()` corrija `axPos`/`delete`.
- [ ] **Resumen Ejecutivo / detalle SKU:** confirmar que las comparativas (Var vs Plan / Var vs Año Ant.) estén llenas para **todas** las métricas (Ventas, Botellas, Cajas, Margen %, Ticket), no solo Ventas Netas.
- [ ] **Formato de moneda en XLSX:** los importes muestran `$` con separador de miles; los conteos no llevan `$`.
- [ ] **Mix de producto (resumen PDF):** con ≤3 productos debe salir la **dona** (total al centro); con >3, el **treemap de Voronoi** (total arriba). Verificar que las áreas se vean proporcionales y las etiquetas legibles.
- [ ] **PDF — Canal→Cliente→Producto:** el detalle **Anual** va justo tras el resumen anual y el **Semanal** tras el resumen semanal. Confirmar que Tradicional + Moderno = Total Off Trade y que las tablas largas se parten repitiendo encabezado.
- [ ] **PDF — Histórico Mensual tabla:** la tabla mensual por producto va **después** de la gráfica de histórico mensual, con las mismas etiquetas de mes.
- [ ] **PDF — Tablas comparativas de 8 columnas:** la categoría va al **centro**, reales a la izquierda y variaciones a la derecha. Las demás tablas (incl. detalle SKU de 9 columnas) no deben cambiar.
- [ ] Abrir el Dashboard HTML generado y probar:
  - [ ] Selección de filtros (Año, Semana, Producto, Canal, Estado, Cliente). **Cliente es un desplegable** (`<select>`), no búsqueda por texto.
  - [ ] **Oportunidades y Riesgos:** con `--contexto-mercado`, deben aparecer los hallazgos de mercado (CRT/agave/NOM) y **no** la tarjeta "Contexto de mercado no disponible".
  - [ ] Recálculo de KPIs superiores y redibujo de las 5 gráficas Chart.js.
  - [ ] Descargar CSV (verificar marca BOM UTF-8 en Excel).
  - [ ] Descargar imagen PNG de cualquier gráfica.
