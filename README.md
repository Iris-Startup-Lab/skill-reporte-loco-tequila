
# Skill: Generador de Reportes Ejecutivos Semanales (Loco Tequila)

<p align="left">
  <img src="imagenes/Loco_Tequila_Logo.svg" alt="Logo Loco Tequila" height="50" style="vertical-align: middle; margin-right: 15px;" />
  <img src="imagenes/LogoNuevo.png" alt="Logo Iris" height="50" style="vertical-align: middle;" />
</p>

------
Autor:

- Fernando Dorantes Nieto

------

Esta **Skill** proporciona un sistema agnóstico y automatizado para la generación de reportes ejecutivos de ventas y margen a partir de datos transaccionales y de planificación en formato CSV para **Loco Tequila**.

Produce tres entregables profesionales optimizados para la toma de decisiones directivas:

1. **Reporte PDF Ejecutivo (~30 páginas)**: Diseñado según principios de visualización directiva (*Storytelling with Data*), paleta de color institucional (Maroon), gráficos vectoriales de tendencia y logo institucional integrado.
2. **Libro Excel (XLSX, 6-8 Hojas Analíticas)**: Hojas analíticas con formato condicional, semáforos WoW/MoM/YoY/Plan, desglose por producto, cliente y región, hojas de comparativos personalizados y contexto de mercado.
3. **Dashboard HTML Interactivo**: Panel responsivo con recálculo dinámico en tiempo real de KPIs y de las 5 gráficas Chart.js al interactuar con filtros (Año, Semana, Producto, Canal, Estado, Cliente), descarga de datos filtrados en CSV con codificación UTF-8 BOM y descarga de imágenes PNG de gráficas.

---

## 🌟 Arquitectura Agnóstica y Estándar de Agent Skills

La skill cumple estrictamente con el estándar universal de **Agent Skills** (definido en `SKILL.md` y documentado para desarrolladores en `AGENTS.md`), permitiendo que cualquier agente de Inteligencia Artificial comprenda las instrucciones, argumentos y herramientas necesarias para ejecutar el pipeline de forma autónoma.

### 🤝 Protocolo de Bienvenida y Preguntas Iniciales (Máximo 2)

Cuando el usuario activa la Skill o interactúa con el agente:

1. **Presentación Automática**: El agente saluda y explica los 3 entregables (PDF, XLSX, Dashboard HTML).
2. **Pregunta 1: Fuente de Datos** (Solo si el usuario no ha adjuntado CSVs ni especificado ruta): Pregunta si usará datos propios o los de muestra (`data_for_test_and_simulation/`).
3. **Pregunta 2: Periodo / Semana Base a Comparar** (Solo si el usuario no indicó la semana y año base en su mensaje): Pregunta qué semana y año tomar como punto de evaluación (ej. Semana 30 de 2026).
4. **Mantenimiento del Estándar**: Verifica las columnas clave y genera automáticamente los 3 entregables con comparativos fijos (WoW, MoM, YoY, YTD, Rolling 52) y contexto de mercado tequilero (CRT, Agave, NOM-006).

---

## 🤖 Modelos e Integración por Entorno de IA

Esta skill está optimizada para ser probada y ejecutada localmente a través de diversos agentes e interfaces de IA:

### 1. OpenCode (CLI / IDE Agent)

- **Modelos soportados**:
  - **DeepSeek V4 Pro / DeepSeek V3 / R1**
  - **Kimi 3 / K2.7**
- **Operación**: OpenCode detecta `SKILL.md` y `AGENTS.md` para invocar comandos de Python mediante la consola interactiva en el ambiente Conda.

### 2. Antigravity (Google DeepMind Agentic IDE)

- **Modelos soportados**:
  - **Gemini 3.6 Flash** (Recomendado para alta velocidad, lógica agentica y precisión de código)
  - **Gemini 3.1 Pro / Ultra**
- **Operación**: Antigravity descubre automáticamente la skill en `.agents/skills/` o raíz de trabajo y utiliza herramientas como `search_web` para compilar indicadores del sector tequilero (CRT, agave, NOM-006).

### 3. Claude Desktop y Claude Code

- **Modelos soportados**:
  - **Claude Sonnet** (Recomendados)
  - **Claude Opus**
- **Operación en Claude Desktop**: Requiere servidor MCP Filesystem o Terminal para interactuar con los archivos locales.
- **Operación en Claude Code (CLI)**: Se ejecuta directamente desde la línea de comandos ejecutando instrucciones naturales vinculadas a `scripts/generate_report.py`.
- **Operación en Claude Desktop empresarial**: Empaquetar la carpeta de la skill a un zip y subir a la plataforma.

---

## 🚀 Requisitos e Instalación del Entorno Local (Conda)

Para la ejecución local de los scripts de generación y procesamiento gráfico, se requiere **Python 3.10+** y el ambiente Conda **`data_analytics_science`**.

### 1. Creación y Activación del Ambiente Conda

En PowerShell (Windows):

```powershell
# Iniciar hook de Conda en PowerShell
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression

# Activar el entorno 'data_analytics_science'
conda activate data_analytics_science
```

### 2. Instalación de Dependencias

```powershell
# Dependencias de renderizado vectorial nativo (requerido para el logo SVG/PNG)
conda install -c conda-forge cairo pycairo -y

# Dependencias de Python desde requirements.txt
pip install -r requirements.txt
```

---

## ⚙️ Modos de Uso y Comandos CLI

El orquestador principal es `scripts/generate_report.py`.

### 1. Generación de Reporte Semanal Completo

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 `
    --datos-dir data_for_test_and_simulation `
    --output-dir output
```

### 2. Generación por Artefacto Individual

```powershell
# Generar únicamente el PDF
python scripts/generate_report.py --semana 30 --anio 2026 --solo pdf

# Generar únicamente el Excel XLSX
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx

# Generar únicamente el Dashboard HTML
python scripts/generate_report.py --semana 30 --anio 2026 --solo html
```

### 3. Comparativos Custom (Semana vs Semana, Mes vs Mes, Año vs Año)

```powershell
# Comparar Semana 30 vs Semana 25 de 2026
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx `
    --modo-comparar semana --comparar-semana 25 --comparar-anio 2026

# Comparar Julio (Mes 7) vs Mayo (Mes 5) de 2026
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx `
    --modo-comparar mes --comparar-mes 5 --comparar-anio 2026

# Comparar Año 2026 vs Año 2025 (YTD)
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx `
    --modo-comparar anio --comparar-anio 2025
```

### 4. Integración de Contexto de Mercado (CRT, Agave, NOM-006)

```powershell
# 1. Ver queries sugeridas para búsqueda web
python scripts/generate_report.py --semana 30 --anio 2026 --mostrar-queries-mercado

# 2. Generar el archivo template de contexto
python scripts/generate_report.py --semana 30 --anio 2026 --generar-template-mercado

# 3. Llenar el template generado y ejecutar el reporte con contexto incluido
python scripts/generate_report.py --semana 30 --anio 2026 `
    --contexto-mercado output/template_contexto_mercado_S30_2026.txt
```

---

## 📁 Estructura del Proyecto

```
skill_reporte/
├── README.md                      <- Documentación principal del proyecto y setup (Este archivo)
├── AGENTS.md                      <- Instrucciones detalladas de prueba y operación para Agentes IA
├── SKILL.md                       <- Especificación estándar de la Skill para Agentes IA
├── requirements.txt               <- Lista de dependencias de Python
├── designs/
│   ├── Design.md                  <- Sistema de diseño (paleta maroon, tokens y layout)
│   └── storytelling_summary.md    <- Resumen por capítulos de Storytelling with Data
├── assets/
│   ├── Loco_Tequila_Logo.svg      <- Logo SVG original institucional
│   ├── Loco_Tequila_Logo_white.svg<- Logo SVG en versión blanca automatizada
│   └── Loco_Tequila_Logo_white.png<- Logo PNG renderizado de alta definición para PDF
├── data_for_test_and_simulation/  <- CSVs de datos de entrada (ventas y plan)
├── scripts/
│   ├── generate_report.py         <- CLI Orquestador Principal
│   ├── data_processor.py          <- Motor de cálculo de KPIs, agregaciones y comparativos
│   ├── logo_processor.py          <- Módulo de transformación y renderizado del logo
│   ├── pdf_generator.py           <- Generador de reporte PDF (~30 págs) con ReportLab
│   ├── xlsx_generator.py          <- Generador de libro Excel ejecutivo con openpyxl
│   ├── dashboard_generator.py     <- Generador de Dashboard HTML interactivo y responsivo
│   ├── design_tokens.py           <- Tokens de colores e identidades visuales
│   └── market_context.py          <- Módulo de procesamiento y plantillas de mercado
└── output/                        <- Carpeta donde se guardan los artefactos generados
```
