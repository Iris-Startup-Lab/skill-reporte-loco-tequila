# TO-DO: Productos que "desaparecen" en los reportes

**Reportado por:** cliente, vía Fernando (2026-09-07 aprox.)
**Síntoma:** a veces el reporte no presenta datos de cierto(s) producto(s).
**Ejecutar:** mañana.

---

## 1. Causa raíz encontrada (confirmada leyendo el código)

`PRODUCT_ORDER` en [scripts/design_tokens.py:32-39](scripts/design_tokens.py#L32-L39) es una lista **fija** de solo 6 SKUs canónicos:
`Loco Blanco, Puro Corazon, Loco Ambar, Loco 269, Loco Aureo, Loco 200`.

El SKU crudo del cliente se homologa contra `EXPANDED_PRODUCT_MAPPING` en
[scripts/data_processor.py:82-120](scripts/data_processor.py#L82-L120). La función de mapeo
(línea 127) hace:

```python
return EXPANDED_PRODUCT_MAPPING.get(s, s)
```

Si el SKU **no está** en ese diccionario, se regresa tal cual (sin mapear) — hasta aquí no
se pierde el dato. El problema viene después: **todas** las tablas/pivotes de producto
(`get_matriz_canal_producto`, `get_detalle_clientes`, `get_historico_mensual`, y las
equivalentes en `pdf_generator.py` / `xlsx_generator.py`) hacen:

```python
piv = piv.reindex(columns=PRODUCT_ORDER, fill_value=0)
```

`reindex` con `columns=PRODUCT_ORDER` **descarta silenciosamente cualquier columna
(producto) que no esté en esa lista de 6**. No hay warning, no hay log, el dato
simplemente no aparece en ninguna tabla ni gráfica por producto.

### Evidencia con datos reales del cliente (semana 34, 488 filas vigentes)

SKUs presentes en el archivo que **no están** en `EXPANDED_PRODUCT_MAPPING` y por lo tanto
se caen de todos los desgloses por producto:

| SKU crudo | Filas |
| --- | --- |
| `Agave` | 28 |
| `Servicios de Personalizaciones` | 8 |
| `Kit de Juego Backamoon` | 3 |
| `Servicios de Catering` / `catering` | 6 |
| `Membresía Loco Hierofante` | 2 |
| `Venta de Tiguan` | 1 |
| `Kit Relojera` | 1 |
| `Kit Maleta de Piel` | 1 |
| `Loco USA` | 1 |
| `Transformación Liquido` | 1 |
| `Loco Áureo 2026` | 5 |

≈ 57 de 488 filas vigentes (~12%) no aparecen en ninguna tabla/gráfica por producto.

### Bug secundario (inconsistencia de totales)

El KPI de "Venta total" del Resumen Ejecutivo se calcula en
[scripts/data_processor.py:551](scripts/data_processor.py#L551) con:

```python
ventas = df["venta_sin_impuestos"].sum()
```

Esto suma **todo** el DataFrame filtrado, incluyendo los SKUs no catalogados de la tabla
arriba. Pero la matriz Canal × Producto (`get_matriz_canal_producto`,
[scripts/data_processor.py:667](scripts/data_processor.py#L667)) calcula su `Total` **después**
de descartar esos mismos SKUs. Resultado: el total del Resumen Ejecutivo **no cuadra**
con la suma de la tabla de productos/canales — el cliente puede notar que "falta dinero"
en el desglose aunque el total general sí lo incluya.

---

## 2. Qué se debe decidir (no es solo un fix de código)

Antes de tocar código, confirmar con el cliente/negocio:

- [ ] ¿`Agave`, `Kits`, `Servicios`, `Membresías`, `Venta de Tiguan` son ventas reales del
      negocio que deben reportarse en alguna categoría ("Otros"), o son ruido/errores de
      captura que **sí** se deben omitir del reporte completo (incluyendo el KPI total)?
- [ ] ¿`Loco Áureo 2026` es un SKU nuevo real (variante 2026 del Áureo) que debería
      mapearse a `Loco Aureo`, o es un producto distinto?

La petición original ("que se omitan si el producto no existe en la base de datos") sugiere
la opción A: omitir consistentemente en **todo** el reporte (incluyendo KPIs), no solo en
las tablas por producto. Pero hay que confirmarlo porque cambia el monto de "venta total"
que ve el cliente.

---

## 3. Plan de fix propuesto

1. **Detectar y loggear SKUs no mapeados** en `transform_client_data.py` o al inicio de
   `data_processor.py` (donde se aplica `EXPANDED_PRODUCT_MAPPING`): imprimir/loggear la
   lista de SKUs crudos que no matchean el diccionario, con su suma de venta y # de filas,
   antes de cualquier reindex. Esto evita que el problema vuelva a pasar en silencio con el
   próximo archivo del cliente.

2. **Decidir una sola regla y aplicarla en todos lados** (no solo en el reindex de
   productos):
   - Opción A (omitir del reporte, incluyendo KPI): filtrar `df = df[df["producto"].isin(PRODUCT_ORDER)]`
     **una sola vez**, justo después de cargar/homologar los datos en
     `LocoDataProcessor.__init__` (o donde se lea el CSV enriquecido), antes de que `_kpis`,
     `get_matriz_canal_producto`, etc. lo usen. Así el KPI total y las tablas por producto
     quedan consistentes entre sí, y `reindex(columns=PRODUCT_ORDER)` deja de "esconder"
     nada porque ya no hay productos fuera de la lista.
   - Opción B (bucket "Otros"): en vez de filtrar, mapear todo lo no reconocido a un
     producto sintético `"Otros"` y decidir si se agrega a `PRODUCT_ORDER`/`PRODUCT_COLORS`
     o se muestra aparte. Requiere más cambios de diseño (colores, tablas, ancho de columnas
     en PDF/XLSX).
   - **Recomendación**: empezar con Opción A (más simple, es lo que pidió el cliente),
     dejar Opción B documentada para si el negocio decide que sí quiere ver "Otros".

3. **Archivos a tocar** (una vez decidida la regla):
   - `scripts/data_processor.py`: agregar el filtro/omite en la carga de `self.df` (cerca de
     donde se aplica `map_producto`/`EXPANDED_PRODUCT_MAPPING`), para que sea la única fuente
     de verdad y no haya que repetir la lógica en cada método.
   - Confirmar que `pdf_generator.py` y `xlsx_generator.py` no vuelven a leer el CSV crudo
     por su cuenta (si solo consumen los DataFrames ya filtrados de `data_processor.py`, no
     necesitan cambios).
   - Agregar el log de SKUs omitidos en algún lugar visible (consola al generar el reporte,
     o una sección/nota en el propio PDF/XLSX de "Notas Metodológicas" — ya existe ese bloque
     en la hoja "Resumen Ejecutivo", ver [descripcion_de_las_hojas_de_calculo.md](descripcion_de_las_hojas_de_calculo.md)).

4. **Regresión / prueba**: usar
   [datos_reales_cliente/Reportes de ventas 2026 semana 34 OK.xlsx](datos_reales_cliente/Reportes%20de%20ventas%202026%20semana%2034%20OK.xlsx)
   como caso de prueba real (ya tiene los 11 SKUs no catalogados de la tabla de arriba) y
   verificar que, tras el fix:
   - El log/consola muestre exactamente qué SKUs se omitieron y cuánta venta representan.
   - El KPI "Venta total" del Resumen Ejecutivo cuadre con la suma de la matriz Canal × Producto.
   - Ningún producto de `PRODUCT_ORDER` desaparezca cuando sí tiene datos (no romper el caso normal).

5. Revisar también si `Loco Áureo 2026` debe agregarse a `EXPANDED_PRODUCT_MAPPING` como
   alias de `"Loco Aureo"` (parece un typo/variante de nombre, no un producto nuevo) —
   si es así, ese uno **no** se debe omitir, se debe mapear.

---

# REGISTRO DE CAMBIOS — 2026-09-10

Sesión de cambios pedidos por el cliente (vía Fernando). Resuelve el bug de arriba
("productos que desaparecen") y agrega varios cambios menores/mayores al HTML y PDF.
Ver [metodologia_reporte.md](metodologia_reporte.md) para el detalle técnico completo
de la lógica de cálculo.

## Causa raíz confirmada del bug de arriba (con datos reales)

Se confirmó con `datos_reales_cliente/Reportes de ventas 2026 semana 34 OK.xlsx` que:
- El Excel del cliente trae una fila de **Total general** al final de la hoja (SKU,
  Folio y Categoria en blanco, Venta = suma de toda la hoja, `Estatus` vacío — ni
  "Vigente" ni "Cancelado"). Esa fila fantasma es la causa de **tres** bugs a la vez:
  el KPI de venta total mal cuadrado, la barra `"nan"` (la más alta) en Ranking de
  Productos, y la barra `"Nacional"` en Top Regiones.
- La columna cruda **`Categoria`** del Excel (que el sistema ignoraba por completo)
  ya trae la señal correcta: `"Producto (Botellas)"` (venta real de tequila) vs.
  `"Agave"`, `"Servicios"`, `"KIT's"`, `"Refacturacion 2025"`, `"Venta Activo"`,
  `"Transformacion de Liquido"` — exactamente los mismos SKUs "perdidos" que ya
  documentaba este archivo.

## CAMBIOS MENORES — Datos Generales
1. **Totales de Excel mal leídos** → arreglado. `scripts/data_processor.py`: el filtro
   de `Estatus` pasó de lista negra (`!= "cancelado"`) a lista blanca (`== "vigente"`)
   cuando ese valor existe en los datos — excluye canceladas **y** la fila fantasma de
   totales. Fallback al filtro original si el archivo no usa esa terminología (no
   rompe datasets de muestra).

## CAMBIOS MENORES — Reporte HTML
1. **Ranking de Productos con "nan"** → arreglado (causa raíz de arriba). Ya no puede
   salir "nan"; el bucket `"Otros"` (Agave/Servicios/etc., dinero real) sigue
   apareciendo a propósito — ya no es un bug, es la categoría real del negocio.
2. **Barra "Nacional" en Top Regiones** → arreglado. Se excluye `"Nacional"`/`"Sin
   Estado"` específicamente en esa gráfica (`chartFactories.regional`).
3. **Ventas por Canal por Semana**: agregados datalabels en miles (redondeado a 0
   decimales) arriba de cada barra apilada (plugin de Chart.js inline, sin dependencia
   externa), y un toggle "Valores ($)" / "% apilado 100%".
4. **Tarjetas de valores en miles**: Ventas Netas, Plan Est. y YTD Acumuladas ahora en
   miles (`fmtMiles`, formato `"$1,234k"`). Ticket Promedio se redondea siempre **a la
   alza** (`math.ceil`, en `data_processor.py`) y se muestra como moneda entera.
   "# Botellas" renombrada a **"# CAJAS DE 9L"**, usando la columna real del cliente
   (`Cajas 9 lts`) cuando existe, o el cálculo `botellas × ml_botella / 9000` si no.
5. **Script de pruebas manuales replicable**: `scripts/exportar_datos_validacion.py`
   (nuevo) — reusa `LocoDataProcessor` (misma fuente de verdad que PDF/XLSX/HTML, no
   reinventa la limpieza) para exportar CSVs listos para Tableau/Power BI desde
   cualquier archivo futuro, con checks de reconciliación automáticos. Ver
   [pruebas_manuales/LEEME_validacion.md](pruebas_manuales/LEEME_validacion.md) para
   la explicación de la lógica y cómo interpretar cada check.

## CAMBIOS MAYORES — Reporte HTML
1. **Filtro "Con Agave"/"Sin Agave" vs Plan**: implementado como filtro **"Comparables
   a Plan" / "No Comparables con Plan"**, agrupando por ahora TODAS las categorías sin
   Plan asociado (Agave, Servicios, Refacturación, Venta Activo, Transformación de
   Liquido — no solo Agave), a petición explícita de Fernando mientras el cliente
   confirma el alcance final. Default = "Comparables a Plan". Aislar solo "Agave" más
   adelante es un cambio de una línea (`comparable_plan` en `data_processor.py`).
   Las gráficas con línea de Plan siempre excluyen lo no comparable (estructural: el
   Plan del cliente nunca tuvo presupuesto de Agave/Servicios/etc.).
2. **Filtros como panel colapsable a la izquierda**: implementado (`<aside
   class="filter-panel">`, botón para expandir/colapsar, persistencia en
   localStorage).
3. **Banda roja fija**: implementado (`position: sticky` en el header).
4. **Pestañas + tabla comparativa de 8 columnas**: implementado — nueva pestaña
   "Comparativo 8 Columnas" que replica la tabla del PDF (`_draw_kpi_table`): Año
   Ant. | Plan | Actual | Categoría (centro) | Var vs Plan $/% | Var vs Año Ant. $/%,
   por producto y por canal, semanal/anual. Las tarjetas de KPI se repiten al inicio
   de cada pestaña.

## CAMBIOS MAYORES — Reporte PDF
1. **PDF confuso / YTD sin explicación**: causa raíz encontrada — cuando el archivo
   del cliente solo tiene un año de datos (ej. solo 2026), las variaciones YoY/YTD
   dividían entre cero y mostraban un falso `"+100%"` en vez de indicar que no hay
   base de comparación. Arreglado en `LocoDataProcessor.get_resumen_ejecutivo()` (y en
   `get_comparativo_custom`): ahora esas variaciones muestran `"N/D"` en PDF, XLSX y
   HTML cuando el año de comparación no existe en los datos cargados.
2. **Nueva página final "Notas Metodológicas"** en el PDF (`_draw_page_
   notas_metodologicas`), explicando en lenguaje ejecutivo las ventanas de
   comparación, qué significa "N/D", la tabla de 8 columnas, la regla de margen de
   referencia (60%) y la conversión a cajas de 9L.
3. **`metodologia_reporte.md`** (nuevo, raíz del proyecto): explicación técnica
   completa con referencias `archivo.py:línea` para que Fernando la evalúe.

## Corrección adicional — SKILL.md / AGENTS.md pedían un nombre de archivo exacto

Detectado por Fernando: el agente le decía al usuario que "adjunte
`loco_actuals_enriquecido.csv`" como si ese nombre exacto fuera obligatorio — pero ese
es solo el nombre del dataset de muestra interno; los archivos reales del cliente
nunca se llaman así ni traen esos encabezados (confirmado hoy con el Excel real).
`data_processor.py` ya detecta el rol del archivo por palabras clave en el nombre y
reconoce columnas por contenido, no por nombre exacto. Se corrigió `SKILL.md` (nueva
sección "Paso 2: Qué Debe Contener el Archivo del Cliente" — describe columnas/
contenido esperado con ejemplos reales, no nombres de archivo) y `AGENTS.md` (regla
explícita de no pedir renombrar archivos), para que ningún agente vuelva a repetir
ese error.

## Corrección adicional — la skill arrancaba muy seca (sin presentarse)

Detectado por Fernando (captura de pantalla): al activar `/reporte-loco-tequila` sin
datos adjuntos, el agente iba directo a "No hay archivos adjuntos... necesito una
cosa antes de arrancar", sin explicar qué hace la skill. Se agregó en `SKILL.md`
("Paso 1: Presentación e Identificación de Datos") una plantilla obligatoria de
presentación (propósito + 3 entregables + comparativos automáticos) que el agente
debe usar en el **mismo mensaje** antes de la(s) pregunta(s) — la presentación no
cuenta como una de las 2 preguntas permitidas.

## Corrección adicional — "Uncaught TypeError: Cannot convert object to primitive value" al abrir el Dashboard HTML

Detectado por Fernando al abrir el HTML. No se reproducía con el JS aislado ni con un
Chart.js simulado; se diagnosticó cargando el Dashboard real en un Chromium headless
(Playwright) con la consola instrumentada, lo que dio el stack trace exacto.

**Causa:** el plugin `stackedTotalLabelsPlugin` (datalabels en miles de "Ventas por
Canal por Semana", agregado en esta misma sesión) leía su configuración con
`chart.options.plugins.stackedTotalLabels` — pero `chart.options` en Chart.js es un
objeto **ya resuelto** (proxy de "scriptable options"): al acceder a la propiedad
`formatter` (una función), Chart.js la **auto-ejecuta con su propio contexto interno**
antes de devolverla. Nuestro `formatter` recibía entonces ese objeto de contexto en
vez del total numérico esperado, y `v / 1000` no podía convertir el objeto a número
→ exactamente el error reportado.

**Fix** (`scripts/dashboard_generator.py`, plugin `stackedTotalLabelsPlugin`): leer la
configuración cruda sin resolver desde `chart.config.options.plugins.stackedTotalLabels`
en vez de `chart.options.plugins...`. Verificado con Chart.js real en Chromium headless
(carga inicial + cambio de pestañas + toggle % del canal) contra datos reales del
cliente y el dataset de muestra: sin errores de consola.

**Nota aparte (no es bug, solo fragilidad de red)**: el Dashboard carga Chart.js desde
`cdn.jsdelivr.net`. Si el navegador de quien abre el HTML no tiene salida a internet o
un proxy/firewall bloquea ese dominio, las gráficas no cargan (`Chart is not defined`)
aunque el resto del dashboard funcione. No se tocó en esta sesión — evaluar si conviene
seguir dependiendo de un CDN externo para un reporte pensado como "standalone".

## Corrección adicional — Línea de "Plan $" seguía apareciendo en "No Comparables con Plan"

**Reporte del usuario**: en el filtro "Comparables a Plan" del Dashboard, al
seleccionar "No Comparables con Plan" la línea roja de Plan seguía dibujándose sobre
las gráficas "Ventas Semanales" y "Ventas por Producto por Semana" (screenshot
adjunto). La idea es que esa línea solo aparezca cuando el filtro está en
"Comparables a Plan".

**Causa**: `chartFactories.semanal` y `chartFactories.producto`
(`scripts/dashboard_generator.py`) agregaban `planDataset(planSem)` de forma
incondicional, sin revisar el valor del `<select id="fComparablePlan">`.

**Fix**: se lee `document.getElementById('fComparablePlan').value` dentro de
`renderChartsDynamic()` y se calcula `showPlanLine = compFilterVal !== 'no_comparables'`;
ambos charts ahora incluyen `planDataset(...)` solo si `showPlanLine` es verdadero
(spread condicional `...(showPlanLine ? [planDataset(planSem)] : [])`). El modal de
gráfica ampliada y la descarga de imágenes reutilizan la misma `chartFactories[key]()`,
así que heredan el fix sin cambios adicionales.

**Verificado** con Chromium headless (Playwright) sobre datos reales del cliente:
con "Comparables a Plan" ambos charts muestran el dataset `"Plan $"`; al cambiar a
"No Comparables con Plan" desaparece de los dos; al regresar a "Comparables a Plan"
reaparece. Sin errores de consola en ningún estado.

## Pendiente / fuera de alcance de esta sesión
- Confirmar con el cliente si "No Comparables con Plan" debe quedarse como un solo
  bucket (Agave + Servicios + Refacturación + Venta Activo + Transformación de
  Liquido) o separarse — Fernando ya envió la pregunta, en espera de respuesta.
- Se encontraron y arreglaron de paso dos gaps de mapeo reales (no relacionados a la
  categorización de negocio): SKU `"Loco 269 ml"` sin alias en
  `EXPANDED_PRODUCT_MAPPING`, y canal `"Venta Directa Off Trade"` sin alias en
  `CANAL_MAPPING` — ambos ya agregados.
- El dataset de muestra (`data_for_test_and_simulation/`) también tenía SKUs sin
  mapear (`"Puro Corazon Ed. Lim Serp"`, `"Puro Corazon Ed. Lim Colibri"`, ~$7.7M) que
  antes desaparecían silenciosamente de las tablas por producto — detectados por el
  nuevo log de advertencia, quedan agrupados en `"Otros"` por ahora; pendiente decidir
  si son variantes reales de Puro Corazón que merecen su propio alias.
- `get_rolling_52()` ya tenía su propio manejo seguro (retorna `None` si hay menos de
  40 semanas con datos) — no se tocó.
