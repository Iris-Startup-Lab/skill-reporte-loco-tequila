# Metodología de cálculo — Reporte Loco Tequila

Documento técnico para Fernando (perfil data science). Cubre la lógica completa de
cálculo del sistema (`LocoDataProcessor` en `scripts/data_processor.py`), que
alimenta los tres entregables (PDF, XLSX, Dashboard HTML — estos dos últimos no se
modificaron en este cambio, pero comparten exactamente la misma capa de datos).

Contexto del cambio: el cliente final reportó que el PDF no explicaba qué estaba
calculando, y que al cargar una semana con datos de cliente que solo tiene 2026 (sin
histórico 2025), el reporte mostraba comparativas YTD/YoY con "cosas que no tienen
los datos del cliente" — en la práctica, un falso `+100%` de crecimiento por división
entre cero cuando el año de comparación no existe en absoluto en los datos cargados.
Este documento explica la causa raíz, el arreglo, y toda la lógica de cálculo
alrededor para que se pueda auditar de punta a punta.

Todas las referencias `archivo.py:línea` corresponden al estado del repo al momento
de escribir este documento — si el archivo se sigue editando, las líneas exactas se
recorren, pero el nombre de función/variable referenciado no debería cambiar.

---

## 1. Filtrado y limpieza de datos de entrada

`LocoDataProcessor._enrich()` (`scripts/data_processor.py:252` en adelante) es el
único punto de entrada que transforma el Excel crudo del cliente en el DataFrame
`self.df` que consume todo lo demás (KPIs, rankings, comparativos, dashboard).

### 1.1 Filtro de `Estatus` (`data_processor.py:259-274`)

- Si el archivo trae una columna `Estatus`/`Status`, se normaliza (`strip().lower()`).
- **Regla nueva:** si el valor `"vigente"` aparece en los datos, se usa **lista
  blanca** (`== "vigente"`) — esto excluye tanto filas `"Cancelado"` como una fila
  "fantasma" de totales de Excel (SKU/Categoría/Folio en blanco, pero con un monto de
  venta) que antes pasaba el filtro porque no era literalmente `"Cancelado"`.
- Si el archivo no usa esa terminología (datasets de muestra/prueba,
  `data_for_test_and_simulation/`), se conserva el filtro original (`!= "cancelado"`)
  para no romper esos datasets.
- **Verificado con datos reales:** el KPI de venta total ahora reconcilia
  exactamente con la suma de la matriz Canal × Producto (antes, la fila de totales
  inflaba el KPI general y aparecía como `"nan"`/`"Nacional"` en varias gráficas).

### 1.2 Salvaguarda adicional de SKU vacío (`data_processor.py:420-423`)

Por si alguna fila de totales se cuela sin que la regla de `Estatus` la detecte
(archivo sin columna `Estatus`, o con otra codificación), se marca `sku_vacio` cuando
`producto` normalizado es literalmente el string `"nan"`, y se excluye también de
`comparable_plan` (ver sección 2). Es una defensa en profundidad, no el mecanismo
principal.

---

## 2. Categorización de producto/canal y el bucket "Otros"

### 2.1 `categoria_negocio` y `comparable_plan` (`data_processor.py:406-434`)

- `categoria_negocio` se toma literal de la columna cruda `"Categoria"` del Excel del
  cliente (distinta de `categoria_o_linea`, que es la línea de producto
  Blanco/Ámbar/Áureo/etc.).
- `comparable_plan` es `True` **solo** si `categoria_negocio` normalizado ==
  `"producto (botellas)"` (constante `CATEGORIA_NEGOCIO_PRODUCTO`,
  `data_processor.py:39`) y el SKU no está vacío.
- Todo lo que **no** sea `comparable_plan` (Agave, Servicios, KIT's, Refacturación
  2025, Venta Activo, Transformación de Líquido, etc.) se re-etiqueta como
  `producto = "Otros"` (`data_processor.py:434`). Es venta real del negocio — no se
  descarta — pero al no tener SKU catalogado tampoco tiene Plan/presupuesto asociado,
  así que nunca se compara contra Plan y se agrupa en la categoría visual "Otros" en
  las tablas/gráficas por producto y canal (bug de "desaparición silenciosa"
  documentado en `to_do.md`, ya corregido).

### 2.2 Salvaguarda de SKUs/canales sin mapear (`data_processor.py:436-470`)

Aun dentro de `comparable_plan == True`, un SKU real que no matchea ningún alias
conocido en `EXPANDED_PRODUCT_MAPPING` (`data_processor.py:91`, típicamente un typo o
una variante nueva del cliente) también caería fuera de `PRODUCT_ORDER` y
desaparecería silenciosamente en cualquier `reindex(PRODUCT_ORDER)` (matriz
Canal×Producto, rankings, etc.). Se detecta con
`sin_mapear = df["comparable_plan"] & ~df["producto"].isin(PRODUCT_ORDER)`
(`data_processor.py:441`), se reagrupa como `"Otros"`, **y se imprime una advertencia
en consola** con el detalle (SKU, suma de venta, número de filas) para poder agregar
el alias correcto después:

```
[ADVERTENCIA] SKUs de producto sin mapear en EXPANDED_PRODUCT_MAPPING
(agrupados como 'Otros' para no perder la venta; agregar alias correcto):
```

Mismo mecanismo, en paralelo, para `canal_norm` no catalogado en `CANAL_ORDER`
(`data_processor.py:454-470`, alias conocidos en `CANAL_MAPPING`,
`design_tokens.py:82`). Confirmado en la corrida real de verificación (semana 34,
solo datos 2026): imprimió advertencias para los canales `Venta de Agave`,
`Loco USA`, `Operaciones`, `Administración` — ninguno de esos alias existe todavía en
`CANAL_MAPPING`, y quedaron agrupados en `"Otros"` sin perder el monto. Recomendación:
agregar esos alias a `CANAL_MAPPING` cuando se confirme con el cliente a qué canal
canónico corresponden (o si de plano son un canal nuevo que merece entrada propia).

---

## 3. Ventanas de comparación temporal y la regla "N/D" — el fix central

### 3.1 Causa raíz del bug reportado por el cliente

`get_resumen_ejecutivo()` (`data_processor.py:684-741`) construye todas las
comparativas estándar (WoW, YoY semanal, YTD vs LY) a través de una función interna
`var(a, b, ...)`. Antes del fix, esa función calculaba:

```python
p = (d / vb * 100) if vb != 0 else (100.0 if va > 0 else 0.0)
```

Cuando el año de comparación no existe **en absoluto** en los datos (`vb == 0` porque
no hay ninguna fila de ese año, no porque la venta real fuera cero), esto producía un
falso `+100%` — indistinguible, para el lector del PDF, de un crecimiento real del
100%. Con datos reales del cliente (solo 2026 cargado, sin 2025), esto se propagaba a
YoY semanal, YTD vs LY, y a `get_oportunidades_riesgos()` (que podía generar un
"hallazgo" de oportunidad completamente ficticio).

### 3.2 Fix aplicado

- Nuevo método `_year_exists(self, year)` (`data_processor.py:743-747`): `True` solo
  si hay al menos una fila real en `self.df` con `anio_num == year`.
- `var(a, b, key="ventas_netas", year_b=None)` (`data_processor.py:708-722`) recibe
  ahora un `year_b` opcional; si `year_b is not None and not self._year_exists(year_b)`,
  retorna `{"abs": d, "pct": None, "nd": True}` — **nunca** un porcentaje inventado.
  `"abs"` se mantiene siempre numérico (la diferencia real en pesos, que en este caso
  es simplemente la venta actual completa, ya que la venta del año inexistente es 0
  real) para no romper reconstrucciones tipo `anterior = actual - abs` en PDF/XLSX.
- Se aplica `year_b=ly` (año de comparación real, `anio - 1`) en las tres llamadas
  que comparan contra el año anterior: `vs_anio_anterior`, `mes_vs_ly`, `ytd_vs_ly`
  (`data_processor.py:735-740`). `vs_plan` y `vs_semana_anterior`/`mes_vs_anterior`
  **no** llevan `year_b` porque comparan contra Plan o contra la semana/mes inmediato
  anterior (que sí puede existir dentro del mismo año cargado), no contra "el año
  pasado".
- `get_rolling_52()` (`data_processor.py:1462+`) ya tenía su propio manejo: retorna
  `None` completo si hay menos de 40 semanas con datos, así que el bloque D del
  Semáforo de Comparativos simplemente no aparece cuando no hay suficiente histórico.
  No se modificó. **Nota de riesgo residual** (ver sección 6.3).

### 3.3 Consumidores del cambio — verificados

| Archivo | Punto | Tratamiento |
|---|---|---|
| `data_processor.py:1177-1191` | `get_oportunidades_riesgos()` | Guarda `ytd_var["pct"] is not None` antes de comparar con `>`/`<`. |
| `pdf_generator.py` (`_draw_page_comparativos`) | Página "Semáforo de Comparativos" | Rama `if var_pct is None: lectura = "N/D — sin histórico del año anterior..."`. |
| `design_tokens.py:149-160` (`fmt_pct`) | Formateo transversal | `None` → string `"N/D"` (antes producía `"0%"`). |
| `xlsx_generator.py` (`_sheet_resumen`, semáforos) | Hoja "Resumen Ejecutivo" | `pct_display = "N/D" if pct is None else f"{pct:+.1f}%"`. |
| `xlsx_generator.py:548-580` (`_write_comparison_block`) | Hoja "Comparativo Periodos" | `var_pct_val = "N/D" if var_pct is None else var_pct / 100`, con guarda de `number_format` solo si no es string. |
| `xlsx_generator.py` (Conclusiones y Próximos Pasos) | Hoja "Oportunidades y Riesgos" | `ytd_pct_txt = "N/D (sin histórico del año anterior)" if ytd_pct is None else ...`. |

Todos estos ya estaban corregidos y confirmados antes de esta tarea (corridas previas
del pipeline `--solo pdf`/`--solo xlsx` contra datos reales del cliente, sin errores).
Como parte de esta tarea se hizo una búsqueda exhaustiva de `["pct"]` en
`pdf_generator.py` y `xlsx_generator.py` para confirmar que no quedaba ningún otro
punto de consumo sin cubrir — se encontró un punto adicional, cubierto en la sección 6.1.

### 3.4 Qué significa cada ventana (resumen ejecutivo, ver también la nueva página del PDF)

- **WoW** — semana actual vs. semana inmediata anterior.
- **YoY Semanal** — semana actual vs. misma semana ISO del año anterior.
- **YTD vs LY** — acumulado semana 1→actual de este año vs. mismo corte del año anterior.
- **Rolling 52** — últimas 52 semanas con datos vs. las 52 previas a esas; requiere ≥40 semanas con datos, si no, el bloque completo se omite (no muestra "N/D", desaparece).

---

## 4. Cálculo de margen y volúmenes (cajas 9L)

### 4.1 Margen (`data_processor.py:495-517`)

Solo se recalcula si el archivo de ventas no trae `margen_pesos` (o si vino todo en
cero). Orden de prioridad:

1. **Costo real del archivo de ventas** — si `margen_pesos` ya viene poblado y no es
   todo cero, se usa tal cual, sin recalcular nada.
2. **Cruce con `COGS` del archivo de Plan/presupuesto** (`data_processor.py:497-509`):
   se construye `cogs_map` = costo unitario promedio por producto normalizado, tomado
   de `self.df_plan["COGS"]` (donde `COGS > 0`). Si un producto tiene ventas pero no
   aparece en `cogs_map` (no tiene fila de Plan con COGS), se usa un **fallback de
   $450/unidad** (`data_processor.py:512`, `.fillna(450.0)`) — un valor intermedio
   fijo, no calibrado por producto, para no dejar el margen en cero solo por falta de
   una fila puntual.
3. **Margen de referencia fijo del 60%** (`data_processor.py:515-517`) — solo si
   ni el archivo de ventas ni el de Plan tienen costo disponible en absoluto
   (`cogs_map` queda vacío).

### 4.2 Cajas de 9 litros (`data_processor.py:472-485`)

- Prioriza la columna real del cliente si el Excel ya la trae calculada (nombres
  aceptados: `"Cajas 9 lts"`, `"Cajas_9_lts"`, `"Cajas 9L"`, `"Cajas_9L"`, cualquier
  variante de mayúsculas/espacios).
- Si no existe esa columna (o viene vacía en alguna fila — `fillna`), se calcula como
  `botellas * ml_botella / 9000`, con `ml_botella` = 750 ml para la mayoría de SKUs y
  200 ml para `"Loco 200"` (`data_processor.py:474`, detectado por substring `"200"`
  en el nombre crudo del SKU).

### 4.3 Ticket promedio

Se redondea **siempre a la alza** (`math.ceil(ventas / botellas)`,
`data_processor.py:654`, y las variantes análogas en `_kpis`/`_plan_kpis`/por-SKU:
`data_processor.py:677, 1099, 1131`), nunca al más cercano ni truncado. Esto es
consistente en actuals y en Plan.

---

## 5. La tabla de "8 columnas" (`pdf_generator.py:1456`, `_draw_kpi_table`)

Aparece en las páginas de detalle por producto y por canal (modo `"semanal"` o
`"anual"`/YTD). Columnas, en orden:

1. Año Anterior ($)
2. Plan ($)
3. **Actual ($)** — resaltada
4. Categoría (nombre de producto o canal, columna central)
5. Var. vs Plan $
6. Var. vs Plan %
7. Var. vs Año Ant. $
8. Var. vs Año Ant. %

Con fila `Total` al cierre. Las columnas 7-8 están sujetas a la misma regla "N/D" de
la sección 3 cuando no hay histórico del año anterior cargado — importante: **esta
tabla no pasó por el mismo fix explícito de `var()` de `get_resumen_ejecutivo()`**;
construye sus valores a partir de las mismas fuentes (`self.df`/`get_matriz_...`), así
que hereda el comportamiento correcto siempre que use `fmt_pct`/las mismas funciones
de comparación ya corregidas — se verificó visualmente con datos reales (semana 34,
solo 2026) que no muestra falsos `100%` en esa columna.

---

## 6. Fuera de alcance / pendiente de esta tarea

### 6.1 `var()` duplicada en `get_comparativo_custom` — SÍ SE CORRIGIÓ

`get_comparativo_custom()` (`data_processor.py:1246+`, usada solo por el flujo
opcional de CLI `--modo-comparar`, que genera la hoja "Comparativo Custom" en el
XLSX vía `_sheet_comparativo_custom` — `xlsx_generator.py:1227`; **no** se usa en el
PDF, no se usa en el dashboard) tenía su **propia función `var()` independiente**
(antes en `data_processor.py:1273`, sin relación con la de `get_resumen_ejecutivo`),
con la misma división-entre-cero sin salvaguarda.

**Decisión:** aunque es un flujo poco usado (CLI opcional, no forma parte de la
generación estándar de reporte), se decidió aplicar el mismo tratamiento porque:
(a) el arreglo es acotado y de bajo riesgo (una guarda adicional antes de dividir),
y (b) deja abierta la misma confusión para el cliente si algún día se usa
`--modo-comparar` con un periodo B en un año sin histórico.

Cambio aplicado (`data_processor.py`, dentro de `get_comparativo_custom`):

```python
anio_b = periodo_b.get("anio")
year_b_ok = self._year_exists(anio_b) if anio_b is not None else True

def var(a_val, b_val):
    d = a_val - b_val
    if not year_b_ok:
        return {"abs": d, "pct": None}
    p = (d / b_val * 100) if b_val != 0 else (100.0 if a_val > 0 else 0.0)
    return {"abs": d, "pct": p}
```

Y su único consumidor, `xlsx_generator.py` (`_sheet_comparativo_custom`,
~línea 1276-1285), se ajustó para no tronar con `None / 100`:

```python
var_pct_val = "N/D" if var_pct is None else var_pct / 100
...
if var_pct is not None:
    ws.cell(row=ri, column=5).number_format = FMT_PCT1
```

**Límite de esta corrección (documentado, no arreglado):** dentro de la misma
`get_comparativo_custom()`, los desgloses `por_producto`, `por_canal` y `por_cliente`
(DataFrames, `data_processor.py:1280-1319` aprox.) calculan su `variacion_pct` con
`.replace([np.inf, -np.inf], 0).fillna(0)` — es decir, si el periodo B cae en un año
sin histórico, esas tablas mostrarían un **falso 0%** (no un crash, no un falso
100%, pero tampoco "N/D"). No se tocó porque son cálculos vectorizados sobre
DataFrame (no la función `var()` puntual que se pidió evaluar) y el riesgo de
romper algo al modificarlos en esta pasada se consideró mayor que el beneficio,
dado que es un flujo opcional y de bajo uso. **Recomendación a futuro:** aplicar el
mismo patrón `None`-si-`not year_b_ok` a esas tres columnas `variacion_pct` si se
detecta que `--modo-comparar` se usa con años sin histórico en la práctica.

### 6.2 Otros hallazgos relevantes durante la revisión

- El dashboard HTML (`scripts/dashboard_generator.py`) **no fue tocado** en esta
  tarea (otro agente trabajó en paralelo sobre ese archivo) y **no usa**
  `get_comparativo_custom` en absoluto — confirmado por búsqueda en el archivo.
- `xlsx_generator.py` no tiene ningún otro consumo de `["pct"]` fuera de los ya
  cubiertos en la tabla de la sección 3.3 y el de la sección 6.1.
- `pdf_generator.py` no tiene ningún consumo de `get_comparativo_custom` — la hoja
  "Comparativo Custom" solo existe en el XLSX.

### 6.3 Riesgo residual en `get_rolling_52` (identificado, no corregido — fuera de alcance de esta tarea)

`get_rolling_52()` (`data_processor.py:1503-1506`) calcula
`p = (d / vb * 100) if vb != 0 else 0.0` sin verificar si el año de comparación
existe. En teoría, si hay ≥40 semanas con datos en la ventana rolling actual pero el
año anterior (`y-1`) no tiene ninguna fila, `vb == 0` legítimamente y el bloque
mostraría un falso `0%` de variación en vez de "N/D". En la práctica esto es muy poco
probable: si hay ≥40 semanas de historia acumulada hacia atrás desde la semana
actual, casi siempre existe traslape real con el año anterior. Se documenta aquí
como hallazgo, consistente con la instrucción explícita de no modificar esta función
(ya evaluada y aceptada en una revisión previa).

---

## 7. Verificación realizada

Se corrió el pipeline completo contra tres escenarios:

1. `--semana 34 --anio 2026` con los archivos reales del cliente (solo 2026, sin
   histórico 2025) — `--solo pdf` y `--solo xlsx`: ambos generan sin error. El PDF
   muestra "N/D" en los bloques B y C del Semáforo de Comparativos (YoY Semanal y
   YTD vs LY), con la lectura narrativa "N/D — sin histórico del año anterior en los
   datos cargados". La hoja "Resumen Ejecutivo" del XLSX muestra el mismo "N/D" sin
   tronar.
2. `--semana 30 --anio 2026` con el dataset de muestra (`data_for_test_and_simulation/`,
   con histórico completo) — `--solo pdf`: las cuatro ventanas (WoW, YoY, YTD, Rolling
   52) muestran porcentajes reales (`-7%`, `+35%`, `+14%`, `+18%` en la corrida de
   verificación), confirmando que el caso normal no se rompió.
3. El PDF de ambos escenarios incluye la nueva última página "Notas Metodológicas"
   (ver `pdf_generator.py`, método `_draw_page_notas_metodologicas`), con
   paginación automática cuando el contenido no cabe en una sola página.
