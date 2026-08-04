# ----------------- Hoja: "Resumen ejecutivo"

He revisado las 6 hojas del workbook (incluida "Resumen Ejecutivo") y detecté charts + estilos en todas. No hice ningún cambio, es solo lectura/auditoría.

## 1. Descripción general (para que un agente la entienda como plantilla)

**Hoja 1 — Resumen Ejecutivo** (portada/dashboard, sin gráficos)

- Encabezado con título, subtítulo de corte y periodo comparado.
- Tabla KPI: filas = indicadores clave, columnas = Periodo actual | Periodo anterior | Variación % | Semáforo (texto) | Lectura (comentario narrativo).
- Bloque "Hallazgos Principales": lista numerada de insights, cada uno con línea de título en negrita + párrafo de detalle.
- Bloque "Notas Metodológicas": bullets pequeños en gris con supuestos, fuentes y reglas de depuración de datos.

**Hoja 2 — Comparativo Periodos** (Line + ColumnClustered)

- 3 bloques verticales: (a) Semana vs Semana con serie completa de todas las semanas del año + columna de promedio móvil de 4 semanas, (b) Mes vs Mes con meses cerrados, variación MoM y YoY mensual, más serie mensual año actual vs año anterior, (c) Acumulado del año (YTD) actual vs anterior.

**Hoja 3 — Análisis por Producto** (BarClustered + Line)

- Ranking de SKU con unidades/venta año actual vs anterior y variación %, con fila TOTAL.
- Tabla secundaria de venta por producto ordenada (para el gráfico de barras).
- Serie de tendencia semanal (últimas 12 semanas) de los productos top.
- Tabla de clasificación de tendencia (Ascendente/Estable/Descendente) por producto.

**Hoja 4 — Análisis por Cliente** (Pie + BarClustered)

- Bloque de concentración de cartera (top 5%, top 10%, # clientes activos, venta total base).
- Ranking top 20 clientes: venta, facturas, semanas activas, % del total y **% acumulado** (curva tipo Pareto).
- Tabla "Clientes en riesgo" (caída ≥ umbral vs año anterior).
- Tabla "Clientes en crecimiento" (incremento ≥ umbral vs año anterior).

**Hoja 5 — Análisis Regional** (BarClustered + Pie)

- Venta por Estado: unidades, venta año actual/anterior, % participación ambos años, variación en puntos porcentuales.
- Venta por Canal: mismas métricas para On Trade / Off Trade / Venta Directa / Venta Empleado.

**Hoja 6 — Oportunidades y Riesgos** (sin gráficos)

- Tabla: Hallazgo | Tipo (Riesgo / Oportunidad / Riesgo-Oportunidad) | Impacto estimado | Recomendación de acción.
- Bloque de fuentes de contexto de mercado (búsqueda web).
- Bloque "Conclusiones y próximos pasos" (lista numerada, texto narrativo).

## 2. Gráficos actuales y sugerencias

Encontrados: `Line`, `ColumnClustered`, `BarClustered` (x2), y **2 Pie charts** (en "Análisis por Cliente" para concentración de cartera, y en "Análisis Regional" para participación por canal).

Reemplazos sugeridos para los pie/donut:

- **Barra horizontal ordenada** (BarClustered horizontal) — ya la usan en otras hojas; es más fácil de leer que un pie cuando hay >4 categorías, y permite meter la etiqueta de % al final de la barra.
- **Gráfico de Pareto (barras + línea de % acumulado)** — la hoja de Cliente *ya calcula* el % acumulado por cliente (columna G), así que combinar barra de venta + línea acumulada aprovecha un dato que hoy no se grafica y comunica mejor "concentración" que un pie.
- **Treemap** — buena alternativa visual para concentración de cartera/canal cuando se quiere mostrar peso relativo sin eje.
- Si el canal solo tiene 2-4 categorías (como en Regional), un **donut** sigue siendo aceptable, pero una barra 100% apilada (stacked bar) comparando año actual vs anterior comunica mejor el cambio de mezcla que dos pies separados.

## 3. Coloreado

No existen reglas de **Conditional Formatting nativo de Excel** en ninguna de las 6 hojas (verificado programáticamente: 0 reglas de CF en todo el workbook). Todo el color que ven no son encabezados es **relleno/fuente fijo aplicado al momento de generar el archivo**, según umbrales de negocio decididos por el generador, por ejemplo:

- Semáforo de KPIs (Resumen Ejecutivo): rojo si la variación es una caída relevante, amarillo si es moderada.
- Clasificación de tendencia por producto: verde si "Ascendente", rojo si "Descendente", amarillo si "Estable".
- Variación % de clientes en riesgo: texto rojo.
- Columna "Tipo" en Oportunidades y Riesgos: fondo rojo = Riesgo, amarillo = Riesgo/Oportunidad, verde = Oportunidad.

Implicación para la skill: el agente debe **decidir el color explícitamente por celda según el umbral**, ya que no hay una fórmula de CF que se recalcule sola. Alternativa a considerar: migrar esta lógica a reglas de CF reales (basadas en fórmula) para que, si el reporte se regenera pisando solo los valores, los colores se actualicen automáticamente sin que el script tenga que recalcular el color cada vez.

## 4. Funciones/fórmulas presentes

Todas las hojas usan fórmulas simples, sin funciones de búsqueda:

- Variación %: `=(A-B)/B`
- División protegida: `=IFERROR(D7/C7,"n/a")` (precio promedio), `=IFERROR((D7-F7)/F7,"n/a")` (variación con protección ÷0)
- Totales: `=SUM(rango)`
- % del total: `=C15/$C$10`
- % acumulado (Pareto): `=SUM($C$15:C15)/$C$10` (referencia mixta que crece al copiar hacia abajo)
- Diferencia en puntos porcentuales: `=(F7-G7)`

No se usan `SUMIFS`, `VLOOKUP/XLOOKUP`, `INDEX/MATCH` ni `COUNTIFS` dentro del workbook. Los valores base agregados (unidades/venta por SKU, cliente, estado) están escritos como **valores estáticos**, no como fórmulas que jalen de una hoja de datos crudos — coherente con que las notas metodológicas indican que la fuente son archivos externos, no una hoja de transacciones dentro de este mismo workbook. Solo los ratios derivados dentro de cada hoja (variación %, % del total, % acumulado, precio promedio) son fórmulas.

# ----------------- Hoja: "Comparativo Periodos"

Confirmado: en esta hoja tampoco hay reglas de Conditional Formatting nativas — ya lo verifiqué antes a nivel de todo el workbook (0 reglas de CF en las 6 hojas). El color de las celdas de variación (`D9`, `D54:D56`, `D78` en rojo `#A6192E`; `C78` en mostaza `#8A6D00`) es relleno/fuente fijo aplicado al generar el archivo según el signo/magnitud de la variación, igual que en las demás hojas.

## Descripción general — Hoja: "Comparativo Periodos"

Hoja de series de tiempo comparativas, sin sección narrativa (a diferencia de Resumen Ejecutivo). Tres bloques verticales independientes, cada uno con su propia mini-tabla de resumen + su serie completa para graficar:

1. **Semana contra Semana (WoW)** — tabla resumen de 3 filas (semana previa cerrada, última semana cerrada, semana en curso/parcial) con Unidades, Venta y Facturas, más una fila de Variación % entre las dos semanas cerradas. Debajo, serie completa semana 1 a 30 con Venta y una columna de **Promedio móvil de 4 semanas** (para suavizar la serie en el gráfico de línea).
2. **Mes contra Mes (MoM)** — tabla resumen de 5 periodos (2 meses cerrados año actual, 1 mes del año anterior como referencia, mes en curso parcial año actual y su contraparte año anterior) con Unidades/Venta/Facturas, más 3 filas de variación (MoM, YoY mensual, parcial vs parcial). Debajo, serie mensual Ene-Dic con columnas "Venta año anterior" y "Venta año actual" lado a lado (para el gráfico de columnas).
3. **Acumulado del año (YTD)** — tabla de 2 filas (año anterior vs año actual) con Unidades, Venta, Facturas, Precio promedio/unidad calculado, y fila de Variación %.

Cada bloque de resumen incluye, en algunos casos, una nota metodológica en cursiva gris explicando una causa puntual detrás de una variación atípica (ej. un pedido grande que distorsiona una semana o un mes).

## Gráficos

- `Line`: se alimenta de la serie semanal (Venta + promedio móvil 4 semanas) del bloque 1.
- `ColumnClustered`: se alimenta de la serie mensual (Venta año anterior vs año actual) del bloque 2.

No hay pie/donut en esta hoja — los dos gráficos ya son de los tipos que recomiendo mantener (línea para tendencia semanal con suavizado, columnas agrupadas para comparación mensual año contra año). Si se quiere enriquecer:

- Añadir al **Line** una segunda serie con la venta semanal del año anterior (si se llega a incluir esa columna) para ver estacionalidad año contra año en la misma gráfica, en vez de solo el promedio móvil.
- Cambiar el **ColumnClustered** mensual por un **combo de columnas + línea de variación %** — ya existe la variación calculada en otras filas, así se ve el nivel y el cambio porcentual en un solo gráfico sin necesitar dos ejes separados en la tabla.

## Funciones/fórmulas presentes

- Variación %: `=(A-B)/B` — mismo patrón que en el resto del workbook (ej. `D9`, `D54:D56`, `C78`, `D78`).
- Precio promedio: `=D76/C76` (venta ÷ unidades, sin protección `IFERROR` en esta hoja, a diferencia de "Análisis por Producto" donde sí se usa).
- No hay `SUM`, `SUMIFS`, `VLOOKUP` ni funciones de fecha (`EOMONTH`, `TEXT`) en esta hoja — las series semanales y mensuales (Venta, Unidades, Facturas, Promedio móvil) están escritas como **valores estáticos**, calculadas fuera de Excel; solo las filas de variación % y el precio promedio YTD son fórmulas que referencian celdas de la misma hoja.

# ----------------- Hoja: "Analisis por Producto"

Confirmado también aquí: sin reglas de CF nativas (ya verificado a nivel workbook). El color es relleno/fuente fijo aplicado al generar el archivo, y noto un patrón nuevo: **no todas las variaciones se colorean**, solo las que superan cierto umbral de magnitud — ej. en `G7:G12`, las caídas grandes (`G7:G9`) están en rojo negrita, el crecimiento fuerte (`G11`) en verde negrita, pero variaciones chicas o "n/a" (`G10`, `G12`) quedan en negro/formato normal. Es decir, el generador aplica un **umbral de "relevancia"** antes de decidir si resalta la celda, no colorea todo por signo.

## Descripción general — Hoja "Análisis por Producto"

Hoja de ranking y tendencia por SKU, sin narrativa larga (solo una nota corta). Cuatro bloques:

1. **Ranking de productos YTD** — tabla por producto con Unidades y Venta (año actual y anterior), Variación % (coloreada solo si es relevante) y Precio promedio (año actual). Fila TOTAL con `SUM`.
2. **Nota metodológica corta** — una fila de texto explicando que el precio unitario es estable entre años (para descartar que la caída de venta sea por descuentos).
3. **Tabla secundaria de Venta 2026 por producto** — subconjunto simplificado (Producto + Venta), ordenado, que alimenta directamente al gráfico de barras (evita que el gráfico tenga que leer de la tabla principal con columnas de más).
4. **Tendencia últimas 12 semanas** — serie semanal (top 6 productos por venta) para el gráfico de línea, seguida de una **tabla de clasificación de tendencia** (Ascendente/Estable/Descendente) por producto, comparando la 1a. mitad vs la 2a. mitad de esas 12 semanas — esta sí está coloreada (verde/rojo/amarillo) en todas sus filas.

## Gráficos

- `BarClustered`: ranking de productos por venta (bloque 3).
- `Line`: tendencia semanal de los productos top (bloque 4).

Sin pie/donut en esta hoja — ambos tipos ya son apropiados. Sugerencias de mejora:

- El **BarClustered** de ranking podría ser **barra horizontal ordenada de mayor a menor** con dos series (año actual vs año anterior) en vez de una sola serie — hoy la tabla ya tiene ambos años pero el gráfico solo parece graficar uno; así se ve el cambio de mezcla de un vistazo.
- El **Line** de tendencia con 6 series simultáneas puede saturarse visualmente; una alternativa es un **sparkline por producto** dentro de la tabla de clasificación de tendencia (bloque 4), o un **small multiples** (una mini-gráfica de línea por producto) en vez de 6 líneas superpuestas en un solo gráfico.

## Funciones/fórmulas presentes

- Totales: `=SUM(C7:C20)` (unidades y venta totales).
- Variación % protegida: `=IFERROR((D7-F7)/F7,"n/a")` — con manejo explícito de división por cero (producto sin venta el año anterior).
- Precio promedio protegido: `=IFERROR(D7/C7,"n/a")`.
- No hay `VLOOKUP`, `SUMIFS`, ni funciones de texto/fecha. Igual que en las hojas anteriores, los valores base (unidades y venta por producto, y la serie semanal) están escritos como **valores estáticos**; solo Variación %, Precio promedio y los totales son fórmulas dentro de la hoja.

# ----------------- Hoja: "Analisis por Cliente"

Confirmado, sin CF nativo en esta hoja tampoco. Patrón de color estático encontrado:

- `C6:C7` (Top 5%/Top 10% concentración) en rojo — resaltado por ser nivel de riesgo alto, no por signo de variación.
- `E53:E67` (clientes en riesgo) en rojo, `E71:E82` (clientes en crecimiento) en verde — aquí el color es por **pertenencia a la tabla** (ya están pre-filtrados como "riesgo" o "crecimiento"), no por umbral fila a fila.
- `F15:G34` (% del total y % acumulado) sin color — son de apoyo, no de alerta.

## Descripción general — Hoja "Análisis por Cliente"

Hoja de concentración y segmentación de cartera. Cuatro bloques:

1. **Concentración de cartera** — 3 métricas sueltas: % de venta que representan los 5 clientes más grandes, % de los 10 más grandes (ambas resaltadas en rojo como señal de riesgo de concentración), y conteo de clientes activos en el periodo. Debajo, el total de venta de la base completa de clientes (denominador usado por las fórmulas de % de las demás tablas) y una nota de lectura en cursiva.
2. **Ranking Top 20 clientes** — Venta, Facturas, Semanas activas, % del total y **% acumulado** (curva de Pareto) por cliente. Tabla secundaria simplificada (Cliente + Venta + "Resto de clientes") que alimenta el gráfico de pie.
3. **Clientes en riesgo** — subconjunto filtrado (caída ≥ umbral vs periodo anterior, con piso de venta mínima para evitar ruido de cuentas chicas) con Venta actual/anterior, Variación %, y conteo de facturas "año anterior → año actual" en formato texto.
4. **Clientes en crecimiento** — mismo patrón que el bloque 3 pero para incrementos ≥ umbral.

## Gráficos

- `Pie`: concentración top 10 clientes vs "Resto de clientes" (bloque 2).
- `BarClustered`: ranking de clientes por venta (bloque 2).

Sugerencia de reemplazo del pie: dado que esta hoja **ya calcula el % acumulado** (columna G, curva de Pareto), lo más natural es un **gráfico de Pareto** (barras de venta por cliente + línea de % acumulado en eje secundario) en vez del pie — comunica la misma idea de concentración pero muestra el detalle de cada cliente, no solo top10-vs-resto. Alternativas: **barra horizontal ordenada** (consistente con el resto del workbook) o **treemap** si se quiere mantener la lectura visual de "peso" sin eje.

## Funciones/fórmulas presentes

- `% del total`: `=C15/$C$10` (referencia absoluta al denominador fijo).
- `% acumulado (Pareto)`: `=SUM($C$15:C15)/$C$10` — rango con ancla fija y límite variable, se arrastra hacia abajo para acumular.
- No hay `SUMIFS`, `COUNTIFS`, `VLOOKUP` ni fórmulas de fecha en esta hoja. Las métricas base (venta/facturas/semanas activas por cliente, listas de riesgo/crecimiento ya filtradas, concentración top5/top10, # clientes activos) están escritas como **valores estáticos** — el filtrado y ranking por cliente se hizo fuera de Excel; solo % del total y % acumulado son fórmulas dentro de la hoja.

# ----------------- Hoja: "Analisis Regional"

Confirmado: sin CF nativo (verificado a nivel workbook). Patrón de color estático en esta hoja:

- `H7:H17` (Variación en puntos porcentuales de participación **por Estado**) coloreada en **todas** sus filas: verde si ganó participación, rojo si perdió — aquí sí es por signo, sin umbral de magnitud.
- `H36:H40` (misma variación en pp pero **por Canal**) **no está coloreada** — queda en negro/formato normal, inconsistencia respecto al bloque de Estado que vale la pena que el agente replique tal cual o decida homogeneizar.

## Descripción general — Hoja "Análisis Regional"

Hoja de distribución geográfica y de canal, sin narrativa larga (solo una nota corta entre bloques). Dos bloques paralelos con la misma estructura de columnas:

1. **Venta por Estado** — por estado: Unidades y Venta año actual, Venta año anterior, % de Participación año actual, % de Participación año anterior, y Variación en puntos porcentuales de participación (no variación %, sino el cambio de peso relativo). Tabla secundaria simplificada (Estado + participación) que alimenta el pie. Nota de lectura en cursiva señalando el estado dominante y los de mayor ganancia/pérdida de participación.
2. **Venta por Canal** — misma estructura de columnas (Unidades, Venta actual, Venta anterior, % participación actual/anterior) aplicada a los canales de venta en vez de estados; aquí la columna de variación en pp no está coloreada.
Las ventas por canal se eliminarán de esta hoja y pasarán a la siguiente

## Gráficos

- `BarClustered`: venta/participación por estado (bloque 1).

## Funciones/fórmulas presentes

- `% Participación`: `=D7/SUM($D$7:$D$17)` (año actual, sin protección) y `=IFERROR(E7/SUM($E$7:$E$17),0)` (año anterior, con protección ÷0 y valor por defecto 0 en vez de "n/a").
- `Variación en puntos porcentuales`: `=(F7-G7)` — resta directa de dos %, no una división (distingue "cambio de peso" de "variación %").
- No hay `SUMIFS`, `VLOOKUP` ni fórmulas de fecha. Los valores base (unidades y venta por estado/canal, ambos años) están escritos como **valores estáticos**; solo % de participación y variación en pp son fórmulas dentro de la hoja — y usan `SUM` sobre un rango fijo como denominador, no una referencia a un total ya calculado en otra celda.

# ----------------- Hoja: "Analisis por Canal"

Esta será una nueva hoja
2. **Venta por Canal** — misma estructura de columnas (Unidades, Venta actual, Venta anterior, % participación actual/anterior) aplicada a los canales de venta en vez de estados; aquí la columna de variación en pp no está coloreada.

- `Pie`: participación por canal (bloque 2, 4 categorías).

Con solo 4 categorías el pie de canal es de los "menos malos", pero sigue siendo sugerible cambiarlo:

- **Barra horizontal 100% apilada** (una sola barra dividida en 4 segmentos) comparando año actual vs año anterior en dos barras — muestra el cambio de mezcla de canal mejor que dos pies o un solo pie estático.
- Para el bloque de Estado, ya usan `BarClustered`, que es correcto dado que hay 11 categorías (un pie con 11 rebanadas sería ilegible); podría mejorarse ordenando de mayor a menor y opcionalmente agregando la variación en pp como etiqueta de dato o barra secundaria.

## Funciones/fórmulas presentes

- `% Participación`: `=D7/SUM($D$7:$D$17)` (año actual, sin protección) y `=IFERROR(E7/SUM($E$7:$E$17),0)` (año anterior, con protección ÷0 y valor por defecto 0 en vez de "n/a").
- `Variación en puntos porcentuales`: `=(F7-G7)` — resta directa de dos %, no una división (distingue "cambio de peso" de "variación %").
- No hay `SUMIFS`, `VLOOKUP` ni fórmulas de fecha. Los valores base (unidades y venta por estado/canal, ambos años) están escritos como **valores estáticos**; solo % de participación y variación en pp son fórmulas dentro de la hoja — y usan `SUM` sobre un rango fijo como denominador, no una referencia a un total ya calculado en otra celda.

# ----------------- Hoja: "Oportunidades y Riesgos"

Ya tengo el detalle completo de esta hoja de una lectura anterior (styles incluidos). Sin gráficos y sin CF nativo, igual que el resto del workbook.

## Descripción general — Hoja "Oportunidades y Riesgos"

Hoja de síntesis cualitativa que cruza los hallazgos internos de venta con contexto de mercado externo (búsqueda web). Tres bloques, sin series de tiempo ni tablas numéricas de detalle:

1. **Tabla de Hallazgo / Tipo / Impacto estimado / Recomendación de acción** — cada fila es un insight (mezcla de riesgos y oportunidades) con: descripción del hallazgo (texto largo), clasificación categórica (Riesgo / Oportunidad / Riesgo-Oportunidad, coloreada), una calificación cualitativa de impacto en texto libre ("Alto", "Medio", "Sistémico", etc., sin escala numérica ni fórmula), y la recomendación de acción correspondiente.
2. **Fuentes de contexto de mercado** — bullets con las fuentes de la búsqueda web usada para enriquecer el análisis (medio + tema, sin URL en la celda).
3. **Conclusiones y próximos pasos** — lista numerada de acciones concretas con plazos, texto narrativo puro.

Es la única hoja donde el "Tipo" combina riesgo y oportunidad en una misma taxonomía de 3 valores, a diferencia de "Análisis por Cliente" donde riesgo/crecimiento son dos tablas separadas.

## Gráficos

No tiene gráficos. Dado que es una tabla cualitativa (texto largo en la mayoría de columnas), no es una hoja candidata natural para gráficos tradicionales. Si se quisiera visualizar:

- Un **mapa de calor 2x2** (Impacto vs. Urgencia/Plazo) tipo matriz de priorización, si se agregara una columna numérica de urgencia — más útil aquí que un pie/donut, que no aplicaría bien a datos mayormente de texto.
- Evitar pie/donut en esta hoja en cualquier escenario: no hay una métrica numérica proporcional que justifique una "parte del total".

## Coloreado

Confirmado antes: sin reglas de CF. El color es fijo por categoría, aplicado a **toda la fila de la columna "Tipo"** según el valor de texto:

- Fondo rojo (`#A6192E`) + texto blanco = "Riesgo".
- Fondo mostaza (`#8A6D00`) + texto blanco = "Riesgo / Oportunidad".
- Fondo verde (`#1E7145`) + texto blanco = "Oportunidad".

A diferencia de otras hojas (donde solo el texto cambia de color), aquí es **fondo de celda completo**, dando más peso visual a la etiqueta de clasificación.

## Funciones/fórmulas presentes

Ninguna. Es la única hoja del workbook 100% de valores estáticos (texto narrativo y clasificaciones), sin una sola fórmula — coherente con que no hay cifras que requieran cálculo, solo síntesis cualitativa derivada de las otras 5 hojas y de la búsqueda de contexto de mercado.
