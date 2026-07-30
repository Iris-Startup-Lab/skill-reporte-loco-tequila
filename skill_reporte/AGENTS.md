# AGENTS.md — Guía de Operación y Pruebas para Agentes IA y Usuarios

Este archivo contiene las instrucciones completas para ejecutar, probar y extender la skill **`reporte_loco_tequila`** de **Loco Tequila** utilizando diversos entornos de Inteligencia Artificial y agentes locales.

---

## 🎯 Propósito del Proyecto

Generar de forma autónoma los tres entregables ejecutivos del reporte de ventas y margen:
1. **PDF (~30 págs)**: Visualización directiva con paleta Maroon, gráficos vectoriales y logo institucional.
2. **XLSX (6-8 Hojas)**: Libro Excel analítico con condicionales, comparativos personalizados (WoW, MoM, YoY) y contexto de mercado.
3. **Dashboard HTML**: Dashboard interactivo responsivo con recálculo dinámico en tiempo real de KPIs y gráficas al aplicar filtros, exportación CSV con UTF-8 BOM y descarga de gráficas a imagen PNG.

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
  - **Claude 3.7 Sonnet / Claude 3.5 Sonnet**
  - **Claude 3.5 Opus**
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
- [ ] Abrir el Dashboard HTML generado y probar:
  - [ ] Selección de filtros (Año, Semana, Producto, Canal, Estado, Cliente).
  - [ ] Recálculo de KPIs superiores y redibujo de las 5 gráficas Chart.js.
  - [ ] Descargar CSV (verificar marca BOM UTF-8 en Excel).
  - [ ] Descargar imagen PNG de cualquier gráfica.
