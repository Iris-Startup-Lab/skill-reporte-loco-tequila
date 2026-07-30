---
name: reporte_loco_tequila
description: >
  Genera el reporte semanal ejecutivo de Loco Tequila en tres formatos:
  PDF (reporte visual con paleta maroon), XLSX (6-8 hojas analiticas) y
  Dashboard HTML (interactivo, filtrable, descargable). Soporta comparaciones
  custom entre semanas, meses o años, y busqueda web de contexto de mercado
  (CRT, precio agave, NOM-006).
  Palabras clave: reporte, loco tequila, ventas, semanal, semana, pdf, xlsx,
  dashboard, html, finanzas, analisis, tequila, comparar, contexto mercado,
  CRT, agave, NOM, wow, mom, yoy, ytd.
---

# Skill: Reporte Semanal Loco Tequila

## Propósito

Genera automáticamente los tres entregables del reporte semanal de ventas y margen de **Loco Tequila**:

| Entregable | Archivo | Descripción |
| --- | --- | --- |
| **PDF** | `Reporte_Loco_Semana_NN_AAAA.pdf` | ~30 páginas con paleta maroon, tablas y gráficas |
| **XLSX** | `Reporte_Ejecutivo_Loco_Semana_NN_AAAA.xlsx` | 6-8 hojas ejecutivas: base + comparativo custom + contexto mercado |
| **HTML** | `Dashboard_Loco_Semana_NN_AAAA.html` | Dashboard interactivo con filtros y descarga CSV |

---

## 🤖 Protocolo de Presentación y Guía del Agente

Al activarse esta Skill, el agente **DEBE** seguir este protocolo de interacción inicial con el usuario:

### Paso 1: Presentación Inicial

El agente se presenta explicando claramente su función y los entregables que genera:

### Paso 2: Detección Inteligente de CSVs y Ejemplo de Dataset

El agente comprueba automáticamente si existen archivos CSV en el directorio actual o en la ruta especificada:

1. **Detección por Nombre/Columnas**: Busca archivos que contengan ventas reales (`actuals`, `ventas`, `enriquecido`) o presupuesto (`plan`, `presupuesto`). No exige un nombre estricto.
2. **Muestra del Dataset de Ejemplo**: Si el usuario no está seguro del formato o nombre de su archivo, el agente le muestra una muestra del dataset esperado:

#### Ejemplo de Dataset de Ventas Reales (CSV)

```csv
semana de venta,fecha de venta,SKU/producto,cliente,canal_reporte,region_o_estado,venta_sin_impuestos,botellas,margen_pesos,anio
2026-W30,2026-07-20,Loco Blanco,La Europea,On-Premise,Jalisco,45000,30,22500,2026
2026-W30,2026-07-21,Puro Corazon,Bodegas Alianza,Retail,CDMX,62000,25,31000,2026
```

#### Ejemplo de Dataset de Presupuesto/Plan (CSV)

```csv
semana de venta,SKU/producto,canal_reporte,plan_venta_sin_impuestos,plan_botellas,anio
2026-W30,Loco Blanco,On-Premise,50000,35,2026
```

### Paso 3: Manejo de Archivos Faltantes o Dudas

Si no se detectan CSVs nuevos o el usuario no los tiene listos:
> *"No he detectado un CSV con el formato exacto. Puedo:*
>
> 1. *Usar un CSV de tu carpeta que contenga las columnas de ventas.*
> 2. *Procesar los **datos de simulación incluidos** (`data_for_test_and_simulation/` - Semana 30 de 2026).*
>
> *¿Qué prefieres utilizar?"*

El agente presenta opciones claras para orientar al usuario sobre qué hacer a continuación:

- **Opción A (Reporte Completo)**: Generar los 3 entregables (PDF + XLSX + HTML) de la semana seleccionada.
- **Opción B (Formato Específico)**: Generar únicamente el PDF, el Excel o el Dashboard interactivo.
- **Opción C (Comparativo de Periodos)**: Comparar semanas (ej. Semana 30 vs 25), meses (ej. Julio vs Mayo) o años (YTD 2026 vs 2025).
- **Opción D (Contexto de Mercado)**: Buscar en la web noticias e indicadores del sector (CRT, precio de agave, norma NOM-006) e incluirlos en el reporte.

---

## Cómo invocar (comandos básicos)

```powershell
# Activar entorno Conda:
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression
conda activate data_analytics_science

# Reporte completo semana actual:
python scripts/generate_report.py --semana 30 --anio 2026 `
    --datos-dir data_for_test_and_simulation `
    --output-dir output

# Solo un formato:
python scripts/generate_report.py --semana 30 --anio 2026 --solo pdf
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx
python scripts/generate_report.py --semana 30 --anio 2026 --solo html
```

---

## Comparaciones entre periodos

El usuario puede pedir comparar semanas, meses o años. El agente debe traducir
la pregunta a los parámetros correctos:

### Comparar dos semanas

```powershell
# "Compara la semana 30 con la semana 25 de 2026"
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx `
    --modo-comparar semana --comparar-semana 25 --comparar-anio 2026
```

### Comparar dos meses

```powershell
# "Compara julio contra mayo de 2026"
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx `
    --modo-comparar mes --comparar-mes 5 --comparar-anio 2026
# (mes actual = 7 julio, comparar-mes = 5 mayo)
```

### Comparar dos años

```powershell
# "Compara 2026 contra 2025 en ventas acumuladas"
python scripts/generate_report.py --semana 30 --anio 2026 --solo xlsx `
    --modo-comparar anio --comparar-anio 2025
```

> **Nota para el agente:** Al detectar una pregunta de comparación, identificar:
>
> 1. El modo: ¿es semana vs semana, mes vs mes, año vs año?
> 2. El periodo A (el más reciente / el de la semana del reporte)
> 3. El periodo B (el de comparación)
> 4. Ejecutar el comando XLSX con --modo-comparar y los parámetros correctos

### Ejemplos de preguntas conversacionales → comando

| Pregunta del usuario | Comando resultante |
| --- | --- |
| "¿Cómo fue la semana 30 vs la 25?" | `--modo-comparar semana --comparar-semana 25` |
| "Compara junio con mayo" | `--modo-comparar mes --comparar-mes 5` |
| "¿Cómo van las ventas YTD vs el año pasado?" | `--modo-comparar anio --comparar-anio 2025` |
| "¿Cuánto creció Loco Blanco esta semana vs la anterior?" | `--modo-comparar semana --comparar-semana 29` |

---

## Contexto de Mercado Externo

### ¿Qué es CRT / Agave / NOM?

| Término | Significado | Por qué importa para el reporte |
| --- | --- | --- |
| **CRT** | Consejo Regulador del Tequila — publica estadísticas mensuales de producción y exportaciones | Permite saber si la caída/crecimiento de Loco es interna o de todo el mercado |
| **Precio del Agave** | Precio por tonelada del agave azul Weber (materia prima del tequila) | Cuando sube, el margen de la empresa se comprime aunque las ventas crezcan |
| **NOM-006** | Norma Oficial Mexicana que regula qué puede llamarse "Tequila" | Cambios en categorías, etiquetado o zonas de producción afectan estrategia de producto |

### Flujo para incluir contexto de mercado

El agente debe seguir este flujo cuando el usuario pide contexto de mercado:

**Paso 1 — Ver las queries sugeridas:**

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 `
    --mostrar-queries-mercado
```

**Paso 2 — Buscar en web** (el agente usa su herramienta search_web):

```
Buscar: "CRT Consejo Regulador Tequila estadisticas produccion exportacion 2026"
Buscar: "precio agave azul tequila Mexico 2026 tonelada"
Buscar: "NOM-006 tequila cambios regulacion 2026"
Buscar: "exportaciones tequila Estados Unidos Europa 2026"
```

**Paso 3 — Generar el template de contexto:**

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 `
    --generar-template-mercado
# Genera: output/template_contexto_mercado_S30_2026.txt
```

**Paso 4 — El agente llena el template** con el resumen de lo encontrado en web.
Puede usar el formato estructurado:

```
RIESGO: Precio del agave subio 15% en Q2-2026, comprimiendo margen estimado
OPORTUNIDAD: Exportaciones a EE.UU. crecen 8% YoY, canal export a impulsar
```

**Paso 5 — Generar el reporte con contexto:**

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 `
    --contexto-mercado output/template_contexto_mercado_S30_2026.txt
```

Esto agrega una hoja "Contexto Mercado" al XLSX con los hallazgos estructurados.

### Instrucción al agente para búsqueda automática

Cuando el usuario pida *"incluye contexto de mercado"* o *"¿cómo está el sector?"*,
el agente debe:

1. Ejecutar `--mostrar-queries-mercado` para obtener las queries
2. Usar `search_web` para buscar cada query
3. Resumir los hallazgos en el formato RIESGO:/OPORTUNIDAD:
4. Escribir el resumen en un archivo .txt
5. Pasar `--contexto-mercado <archivo>` al generate_report.py

---

## Parámetros completos del CLI

| Parámetro | Requerido | Default | Descripción |
| --- | --- | --- | --- |
| `--semana` | ✅ | — | Semana ISO (1–53) del reporte principal |
| `--anio` | ✅ | — | Año del reporte (ej. 2026) |
| `--datos-dir` | ❌ | `data_for_test_and_simulation` | Carpeta con los CSVs |
| `--output-dir` | ❌ | `output` | Carpeta de salida |
| `--logo` | ❌ | `assets/Loco_Tequila_Logo.svg` | Ruta al logo |
| `--solo` | ❌ | (todos) | `pdf` \| `xlsx` \| `html` |
| `--top-clientes` | ❌ | `6` | Número de clientes top |
| `--modo-comparar` | ❌ | — | `semana` \| `mes` \| `anio` |
| `--comparar-semana` | ❌ | — | Semana B (con `--modo-comparar semana`) |
| `--comparar-mes` | ❌ | — | Mes B 1-12 (con `--modo-comparar mes`) |
| `--comparar-anio` | ❌ | — | Año B (con cualquier `--modo-comparar`) |
| `--contexto-mercado` | ❌ | — | Ruta a .txt con contexto CRT/agave/NOM |
| `--generar-template-mercado` | ❌ | — | Crea el template de contexto y sale |
| `--mostrar-queries-mercado` | ❌ | — | Muestra queries de búsqueda web y sale |

---

## Estructura de archivos

```
skill_reporte/
├── SKILL.md                               <- Este archivo
├── previous_prompt.txt                    <- Prompt original del agente financiero
├── requirements.txt                       <- Dependencias Python
├── designs/
│   ├── Design.md                          <- Sistema de diseño (paleta, layout)
│   └── storytelling_summary.md            <- Resumen por capítulos de Storytelling with Data
├── assets/
│   ├── Loco_Tequila_Logo.svg
├── data_for_test_and_simulation/
│   ├── loco_actuals_enriquecido.csv
│   ├── loco_actual_vs_plan_semanal.csv
│   └── loco_plan.csv
├── scripts/
│   ├── generate_report.py     <- Orquestador CLI (ENTRADA PRINCIPAL)
│   ├── data_processor.py      <- Carga, limpia, calcula KPIs y comparativos
│   ├── pdf_generator.py       <- PDF ~30 pags (ReportLab + matplotlib)
│   ├── xlsx_generator.py      <- XLSX 6-8 hojas (openpyxl)
│   ├── dashboard_generator.py <- HTML filtrable (Chart.js CDN)
│   ├── market_context.py      <- Contexto CRT/agave/NOM
│   └── design_tokens.py       <- Paleta maroon, SKUs, canales
└── output/                    <- Archivos generados (creada automáticamente)
```

---

## Qué analiza el reporte (conforme al previous_prompt.txt)

| Sección del prompt original | Cobertura |
| --- | --- |
| Comparativos WoW, MoM, YoY, YTD | ✅ Hoja 2 XLSX + cálculos automáticos |
| Patrones por producto (ranking 8-12 sem.) | ✅ Hoja 3 XLSX + págs 8-19 PDF |
| Patrones por cliente (concentración, riesgo) | ✅ Hoja 4 XLSX + págs 20-31 PDF |
| Análisis regional por estado y canal | ✅ Hoja 5 XLSX |
| Oportunidades y riesgos (internos) | ✅ Hoja 6 XLSX (automático) |
| Contexto de mercado (CRT, agave, NOM) | ✅ Hoja 8 XLSX (requiere búsqueda web) |
| Conclusiones y Próximos Pasos | ✅ Hoja 6 XLSX (5 puntos) |
| Semáforo WoW/MoM/YoY/Plan | ✅ Hoja 1 XLSX |
| Comparativo custom dos periodos | ✅ Hoja 7 XLSX (con --modo-comparar) |

---

## Principios de visualización

- **Sin donas para análisis de tendencia** — solo en resumen (págs 1-2 PDF)
- **Barras agrupadas/apiladas + línea** para tendencias semanales y comparativos
- **Barras horizontales** para rankings (productos, clientes, regiones)
- **Combo chart** (área año pasado + barras + línea plan) para páginas SKU/canal

---

## Dependencias Python

```powershell
pip install reportlab svglib matplotlib openpyxl chardet pandas numpy
```
