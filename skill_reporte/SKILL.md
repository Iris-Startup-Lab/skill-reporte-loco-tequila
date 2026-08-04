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
| **PDF** | `Reporte_Loco_Semana_NN_AAAA.pdf` | ~40 páginas con paleta maroon, tablas y gráficas (incluye detalle Canal→Cliente→Producto y tabla de histórico mensual) |
| **XLSX** | `Reporte_Ejecutivo_Loco_Semana_NN_AAAA.xlsx` | **7 hojas** ejecutivas + contexto mercado (opcional) |
| **HTML** | `Dashboard_Loco_Semana_NN_AAAA.html` | Dashboard interactivo con filtros y descarga CSV/PNG |

---

## 🤖 Protocolo de Presentación y Guía del Agente

Al activarse esta Skill, el agente **DEBE** seguir este protocolo de interacción inicial con el usuario:

### Paso 1: Presentación e Identificación de Datos

El agente se presenta explicando claramente su función y los entregables que genera.

1. **Si el usuario YA adjuntó datos CSV o especificó una ruta (`--datos-dir`)**: El agente procede directamente a generar el reporte con dichos datos.
2. **Si el usuario NO ha adjuntado datos ni indicado ruta**: El agente realiza la **única** pregunta inicial (Paso 3).

> 🚫 **REGLA CRÍTICA DE SINTAXIS Y VOCABULARIO**:
> **NUNCA** uses frases como *"No veo archivos en tu carpeta de uploads"*, *"Tu carpeta de uploads está vacía"*, *"Sigo sin ver archivos en tu carpeta"*, ni asumas que existe un monitoreo automático en segundo plano. El agente NO busca ni monitorea carpetas de uploads en segundo plano; simplemente procesa los archivos adjuntos en el chat o la ruta indicada por el usuario.

### Paso 2: CSVs Requeridos y Esquema Esperado

La skill lee **exactamente 2 CSVs** de la carpeta `--datos-dir` (o adjuntados por el usuario):

| Archivo | Rol | ¿Obligatorio? |
| --- | --- | --- |
| `loco_actuals_enriquecido.csv` | Ventas reales (actuals) | **Sí** |
| `loco_actual_vs_plan_semanal.csv` | Plan/presupuesto vs real semanal | Opcional (sin él, no hay comparativos vs Plan) |

#### Ejemplo de Dataset de Ventas Reales — `loco_actuals_enriquecido.csv`

Encabezado real (20 columnas). Las columnas **clave** que consume el reporte son
`semana de venta`, `fecha de venta`, `SKU/producto`, `cliente`, `canal_reporte`,
`region_o_estado`, `venta_sin_impuestos`, `botellas`, `cajas_9L`, `margen_pesos` y `anio`:

```csv
semana de venta,fecha de venta,SKU/producto,unidades_de_venta,categoria_o_linea,cliente,canal,region_o_estado,precio_unitario,venta_con_impuestos,venta_sin_impuestos,anio,ml_botella,botellas,litros,cajas_9L,margen_pct,margen_pesos,sub_canal,canal_reporte
2026-W30,2026-07-20,Loco Ámbar,30,Ámbar,La Europea,Off Trade,Jalisco,1256.08,66876.00,45000.00,2026,750,30,22.5,2.5,0.6,27000.00,Tradicional,Off Trade
2026-W30,2026-07-21,Loco 269,25,Blanco,Bodegas Alianza,On Trade,CDMX,1450.00,72500.00,62000.00,2026,750,25,18.75,2.083,0.5,31000.00,Directo,On Trade
```

#### Ejemplo de Dataset de Presupuesto/Plan — `loco_actual_vs_plan_semanal.csv`

Encabezado real (21 columnas). Las columnas **clave** son `anio`, `semana de venta`,
`SKU/producto`, `canal_reporte`, `plan_botellas`, `plan_cajas_9L`, `plan_venta_sin_impuestos`
y `plan_margen_pesos`:

```csv
anio,semana de venta,fecha_lunes,SKU/producto,canal,canal_reporte,plan_unidades,plan_botellas,plan_cajas_9L,plan_venta_sin_impuestos,plan_venta_con_impuestos,plan_margen_pesos,actual_unidades,actual_botellas,actual_cajas_9L,actual_venta_sin,actual_venta_con,actual_margen,var_vs_plan_$,var_vs_plan_%,cumplimiento_%
2026,2026-W30,2026-07-20,Loco 269,Off Trade,Off Trade,77,77,6.43,113846.49,202054.76,72861.76,74,74,6.17,107835.88,191387.11,69014.96,-6010.61,-5.3,94.7
```

### Paso 3: Preguntas de Aclaración Iniciales (MÁXIMO 2 PREGUNTAS)

El agente solo puede realizar **hasta 2 preguntas de aclaración** antes de generar los reportes, y únicamente si dicha información no fue incluida por el usuario en su mensaje inicial:

#### 1. Pregunta 1: Fuente de Datos (solo si no se adjuntaron datos ni ruta)

Si el usuario **no** ha adjuntado archivos CSV ni ha especificado una ruta de datos:
> *"¿Con qué datos genero el reporte?*
>
> 1. *Tus **datos propios CSV** (puedes adjuntarlos aquí en el chat o indicarme la ruta de la carpeta).*
> 2. *Los **datos de muestra incluidos** (`data_for_test_and_simulation/` — Semana 30 de 2026).*

#### 2. Pregunta 2: Periodo / Semana Base a Comparar (solo si el usuario no especificó semana y año)

Si el usuario **no** especificó en su mensaje el número de semana y año base a evaluar:
> *"¿Qué **semana y año base** deseas evaluar y comparar en el reporte? (Ejemplo: Semana 30 de 2026)."*

*Nota*: Si el usuario elige la opción 2 (datos de muestra) y no especifica semana ni año, se toma por defecto la **Semana 30 de 2026** (`--semana 30 --anio 2026`). Si el usuario proporciona toda la información en su mensaje inicial (datos + semana/año), el agente realiza **0 preguntas** y ejecuta de inmediato.

Una vez respondidas las preguntas necesarias, el agente **genera directamente los 3 entregables sin más interrupciones**.

### Reglas de comportamiento del agente (IMPORTANTE)

1. **Siempre genera los 3 formatos** (PDF + XLSX + HTML) en una sola corrida.
   **Nunca** preguntes qué formato quiere el usuario ni uses `--solo` salvo
   petición explícita del usuario.
2. **Nunca** preguntes por comparativos adicionales / custom. Los 4 comparativos
   fijos (ver §Ventanas Comparativas) ya vienen incluidos automáticamente y son
   los únicos que se reportan. **No uses** `--modo-comparar` salvo que el usuario
   lo pida explícitamente con palabras.
3. **No** hagas preguntas de contexto innecesarias (imágenes, logos, colores,
   temas, etc.). Todo eso ya está resuelto por defecto.
4. **El contexto de mercado (CRT/agave/NOM) es SIEMPRE OBLIGATORIO.** En CADA
   reporte, antes de generar el archivo final, el agente **debe** buscar en la
   web y llenar el contexto de mercado (ver §Contexto de Mercado Externo). No es
   opcional y **no** se pregunta al usuario: se ejecuta siempre de forma
   automática. Solo si la búsqueda web falla por completo se genera el reporte
   con el placeholder de contexto.

---

## Ventanas Comparativas por Defecto (las 4 que SIEMPRE se reportan)

El XLSX incluye **siempre y automáticamente** las siguientes 4 ventanas
comparativas en la Hoja "Comparativo Periodos". El agente **no pregunta nada**
y **no necesita parámetros adicionales** para generarlas:

| Bloque | Ventana | Descripción |
| --- | --- | --- |
| **A** | Semana anterior | Semana seleccionada vs **la semana inmediata anterior** |
| **B** | Misma semana año anterior | Semana seleccionada vs **la misma semana del año anterior** |
| **C** | Acumulado YTD vs año anterior | **Acumulado** S01–SNN del año en curso vs el **mismo acumulado** hasta esa semana del año anterior |
| **D** | Rolling 52 semanas | Últimas 52 semanas vs las mismas 52 del año anterior (**solo si hay ≥ 40 semanas con datos**) |

Estas 4 ventanas corresponden exactamente a lo que el negocio requiere comparar y
**son las únicas** comparaciones que se incluyen por defecto. Además, la hoja
incluye la **serie semanal completa del año** (con columna de año anterior +
promedio móvil de 4 semanas) y una gráfica de líneas.

> **Nota:** El agente **no** debe ofrecer ni solicitar comparativos adicionales.
> Solo si el usuario, por iniciativa propia, pide una comparación distinta
> (ej. "compárame la semana 30 con la 25"), el agente usa `--modo-comparar`.

---

## Cómo invocar (comandos básicos)

```powershell
# Activar entorno Conda:
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression
conda activate data_analytics_science

# Reporte completo (los 3 formatos) — ESTE es el uso por defecto:
python scripts/generate_report.py --semana 30 --anio 2026 `
    --datos-dir data_for_test_and_simulation `
    --output-dir output

# --solo SOLO se usa si el usuario lo pide explícitamente (no preguntar por esto):
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

### Flujo OBLIGATORIO de contexto de mercado (ejecutar SIEMPRE)

⚠️ **Este flujo se ejecuta en CADA reporte, sin excepción y sin preguntar.** El
contexto de mercado se busca **ANTES** de generar los archivos, y la generación
final se hace **en una sola corrida** pasando `--contexto-mercado`. Nunca generes
el reporte "primero" y el contexto "después": el orden correcto es buscar → llenar
el .txt → generar todo con `--contexto-mercado`.

**Paso 1 — Ver las queries sugeridas:**

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 `
    --mostrar-queries-mercado
```

**Paso 2 — Buscar en web** (el agente usa su herramienta de búsqueda web / `search_web` / `WebSearch`).
Debe buscar, como mínimo, estos temas del año del reporte:

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
**Obligatorio** incluir al menos 2 líneas con el formato estructurado (así se
extraen automáticamente como hallazgos de Riesgo/Oportunidad):

```
RIESGO: Precio del agave subio 15% en Q2-2026, comprimiendo margen estimado
OPORTUNIDAD: Exportaciones a EE.UU. crecen 8% YoY, canal export a impulsar
```

**Paso 5 — Generar el reporte completo CON contexto** (los 3 formatos en una sola corrida):

```powershell
python scripts/generate_report.py --semana 30 --anio 2026 `
    --datos-dir data_for_test_and_simulation `
    --contexto-mercado output/template_contexto_mercado_S30_2026.txt
```

Esto agrega la hoja "Contexto Mercado" al XLSX (y la sección correspondiente al
PDF) con los hallazgos estructurados.

> **Fallback:** solo si la búsqueda web no está disponible o falla por completo,
> genera el reporte sin `--contexto-mercado`. En ese caso la hoja "Contexto
> Mercado" muestra el placeholder. Esto es la excepción, no la norma.

### Instrucción al agente (SIEMPRE, en todos los reportes)

En **todos** los reportes el agente debe, sin preguntar:

1. Ejecutar `--mostrar-queries-mercado` para obtener las queries
2. Usar su herramienta de búsqueda web para buscar cada query
3. Resumir los hallazgos en el formato RIESGO:/OPORTUNIDAD:
4. Escribir el resumen en un archivo .txt (usar `--generar-template-mercado` como base)
5. Generar el reporte completo pasando `--contexto-mercado <archivo>`

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
│   ├── loco_actuals_enriquecido.csv        <- INPUT obligatorio (ventas reales)
│   └── loco_actual_vs_plan_semanal.csv     <- INPUT opcional (plan vs real)
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
| Comparativos WoW, MoM, YoY, YTD | ✅ Hoja 2 XLSX: 4 bloques por defecto (WoW, YoY semanal, YTD vs LY, Rolling 52) + serie anual completa |
| Patrones por producto (ranking 8-12 sem.) | ✅ Hoja 3 XLSX: ranking YTD + tendencia 12 sem + tabla Ascendente/Estable/Descendente |
| Patrones por cliente (concentración, riesgo) | ✅ Hoja 4 XLSX: top 5%/10% cartera + Pareto + Clientes en Riesgo + Clientes en Crecimiento |
| Análisis regional por estado | ✅ Hoja 5 XLSX: ventas estado año actual vs anterior + variación pp coloreada |
| Análisis por canal de distribución | ✅ Hoja 6 XLSX: nueva hoja separada con barra apilada 100% |
| Oportunidades y riesgos (internos) | ✅ Hoja 7 XLSX (automático, fondo completo en columna Tipo) |
| Contexto de mercado (CRT, agave, NOM) | ✅ Hoja 8 XLSX (requiere búsqueda web) |
| Conclusiones y Próximos Pasos | ✅ Hoja 7 XLSX (5 puntos) |
| Semáforo WoW/YoY/YTD/Plan + Lectura | ✅ Hoja 1 XLSX (columna narrativa automática) |
| Comparativo custom dos periodos | ✅ Hoja extra XLSX (con --modo-comparar) |

---

## Principios de visualización

- **Sin donas para análisis de tendencia** — solo en resumen (págs 1-2 PDF)
- **Mix de producto (resumen PDF):** el gráfico se elige según el número de
  productos con venta:
  - **≤ 3 productos → dona** clásica, con el total al **centro**.
  - **> 3 productos → treemap de Voronoi** (áreas proporcionales a la venta),
    con el total **arriba** del gráfico. Es más legible que una dona con muchas
    categorías. Lo implementan `make_voronoi_chart()` / `_voronoi_treemap_cells()`
    en `pdf_generator.py` (power diagram + relajación de Balzer/Lloyd, sin
    dependencias extra).
- **Barras agrupadas/apiladas + línea** para tendencias semanales y comparativos
- **Barras horizontales** para rankings (productos, clientes, regiones)
- **Combo chart** (área año pasado + barras + línea plan) para páginas SKU/canal

---

## 🔧 Notas Técnicas y Solución de Problemas

### Ejes de las gráficas en Excel (se dibujan automáticamente)

Las gráficas del XLSX **ya muestran sus ejes de forma automática** al abrir el
archivo. **No** es necesario aplicar manualmente "Diseño de gráfico → Diseño
rápido → Diseño 3" (ese parche fue retirado).

- **Causa raíz que se corrigió:** openpyxl (3.1.x) crea *ambos* ejes con
  `axPos="l"` (los dos a la izquierda) y sin el elemento `<c:delete>`. Con ambos
  ejes a la izquierda Excel no puede dibujar el eje horizontal de categorías y
  solo se veían las líneas de cuadrícula.
- **Solución:** la función `_fix_chart_axes()` en `xlsx_generator.py` se aplica a
  toda gráfica (vía `_add_chart_with_note`) y fija:
  - `delete = False` en ambos ejes → `<c:delete val="0"/>` (eje visible);
  - posición correcta según orientación: gráficas verticales `catAx="b"` /
    `valAx="l"`; gráficas de barras horizontales `catAx="l"` / `valAx="b"`;
  - `tickLblPos="nextTo"` y `majorTickMark="out"`.

> Si al agregar una gráfica nueva no se ven los ejes, asegúrate de insertarla con
> `_add_chart_with_note(...)` (que aplica el fix) y **no** con `ws.add_chart(...)`
> directamente.

### Formato de moneda en Excel

Todas las variables monetarias del XLSX se muestran con signo `$` al inicio y
separador de miles con comas (`"$"#,##0`; el ticket promedio con 1 decimal,
`"$"#,##0.0`). Los conteos (botellas, cajas) usan `#,##0` **sin** `$`; los
porcentajes usan formato `%` y las variaciones muestran el signo (`+/-`).

### Comparativas del Resumen Ejecutivo (todas las métricas)

La tabla "KPIs Clave" de la Hoja 1 y las tablas de detalle por SKU del PDF
incluyen las comparativas **de todas las métricas**, no solo de Ventas Netas:
`Valor · Plan · Var vs Plan · Var vs Plan % · Año Anterior · Var vs Año Ant. ·
Var vs Año Ant. %` para Ventas Netas, # Botellas, Cajas 9L, Margen % (variación
en puntos porcentuales, `pp`) y Ticket Promedio.

### Hoja "Contexto Mercado" (siempre presente)

La hoja **siempre se genera**:

- **Con** `--contexto-mercado <archivo.txt>` → trae el contexto real (resumen,
  hallazgos Riesgo/Oportunidad y fuentes). **Este es el flujo obligatorio** (ver
  §Contexto de Mercado Externo): el agente busca en web y llena el `.txt` en cada
  reporte.
- **Sin** ese parámetro → la hoja muestra un *placeholder* indicando que falta el
  contexto. Esto es solo el fallback cuando la búsqueda web no está disponible.

> ⚠️ Si ves el placeholder en la hoja de contexto, significa que el reporte se
> generó **sin** `--contexto-mercado`. Repite el flujo obligatorio: buscar en web →
> llenar el `.txt` → regenerar pasando `--contexto-mercado`.

### Páginas nuevas del PDF: Canal → Cliente → Producto

Tras la hoja de resumen (la que trae el Voronoi/dona) se genera el detalle
**Canal → Cliente → Producto**, en dos bloques: uno **Anual (YTD)** justo después
del resumen anual y otro **Semanal** justo después del resumen semanal. Cada
bloque tiene una sección por canal (Off Trade → Tradicional / Moderno + Total Off
Trade, más On Trade, Venta Directa y Familia y Amigos) con una tabla clientes ×
productos (top 10 + fila "Otros"), columna Total con %, y filas de "Ventas Netas"
y "Participación %". La paginación es automática (`_draw_pages_canal_cliente_producto`
en `pdf_generator.py`, apoyada en `get_cliente_producto_por_canal()`): las tablas
largas se parten entre páginas repitiendo el encabezado.

### Página nueva del PDF: Histórico Mensual — Tabla por Producto

Justo **después** de la gráfica de histórico mensual se agrega una hoja con la
**misma información en tabla**: meses en filas × productos en columnas + Total
(`_draw_page_historico_tabla`, reutiliza `get_historico_mensual()`, mismas
etiquetas de mes que la gráfica).

### Tablas comparativas de 8 columnas: categoría al centro

Las tablas comparativas de **8 columnas** ("Ventas Totales Por Producto" y
"…Por Canal", `_draw_kpi_table`) usan el diseño empresarial con la **categoría al
centro**: valores **reales a la izquierda** (Año Ant. · Plan · Actual resaltado),
**categoría al centro** y **variaciones a la derecha** (vs Plan y vs Año Ant.),
con separadores verticales entre grupos. Las demás tablas (incluida la de detalle
SKU, de 9 columnas) **no cambian**. `_build_rl_table` admite `label_col`,
`label_align` y `sep_before_cols` para este layout.

### Dashboard HTML

- **Oportunidades y Riesgos:** cuando se genera con `--contexto-mercado`, el HTML
  **fusiona los hallazgos de mercado** (CRT/agave/NOM) en la sección y **elimina**
  la tarjeta placeholder "Contexto de mercado no disponible". El contexto se carga
  una sola vez en `generate_report.py` y se pasa tanto a XLSX como a HTML.
- **Filtro Cliente:** es un **listado desplegable** (`<select>`, ordenado
  alfabéticamente) como los demás filtros, no una búsqueda por texto.

---

## Dependencias Python

```powershell
pip install reportlab svglib matplotlib openpyxl chardet pandas numpy
```
