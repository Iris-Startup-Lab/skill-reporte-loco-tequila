# Cómo validar manualmente cualquier archivo futuro (Tableau / Power BI / etc.)

Reemplaza al notebook `Pruebas_limpieza_analisis_de_datos_descriptivos.ipynb`
con un script reutilizable: **`scripts/exportar_datos_validacion.py`**.

## Por qué así (mi lógica)

El notebook limpiaba los datos con su propia copia de la lógica (renombrar
columnas, quitar filas sin `folio_fiscal`, etc.). El riesgo de tener una
segunda ruta de limpieza es que **diverja silenciosamente** de la lógica real
del reporte — que es exactamente la familia de bugs que arreglamos esta
sesión (una fila de "Total" del Excel que se contaba en un lado y no en
otro, un SKU que se perdía en una tabla pero no en otra, etc.).

Por eso el script nuevo **no reimplementa la limpieza**: instancia
`LocoDataProcessor` (la misma clase que usan `pdf_generator.py`,
`xlsx_generator.py` y `dashboard_generator.py`) y exporta tal cual el
resultado. Lo que ves en Tableau es **exactamente** lo que alimenta los 3
entregables — no una aproximación.

## Uso (para cualquier archivo nuevo del cliente, no solo el de esta semana)

```powershell
& "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression
conda activate data_analytics_science

python scripts/exportar_datos_validacion.py `
    --datos-dir datos_reales_cliente `
    --semana 34 --anio 2026 `
    --output-dir pruebas_manuales/validacion_S34_2026
```

`--datos-dir` puede apuntar a cualquier carpeta con un Excel/CSV de ventas
(y opcionalmente uno de plan/presupuesto) — no tiene que llamarse igual que
los archivos de ejemplo, `LocoDataProcessor` ya detecta cuál es cuál por
nombre de archivo.

## Qué se genera

| Archivo | Contenido |
| --- | --- |
| `ventas_enriquecido.csv` | Una fila = una venta, con **todas** las columnas derivadas: `producto`, `categoria_o_linea` (línea Blanco/Ámbar/Áureo), `categoria_negocio` (la columna cruda "Categoria" del Excel), `comparable_plan` (True/False), `canal_norm`, `region_o_estado`, `botellas`, `cajas_9L`, `margen_pesos`, `margen_pct`, `venta_sin_impuestos`, `venta_con_impuestos`, etc. |
| `plan_enriquecido.csv` | El presupuesto/Plan enriquecido, mismo criterio. |
| `resumen_checks.csv` | Las reconciliaciones automáticas (ver abajo). |
| `productos_sin_mapear_detalle.csv` | Solo aparece si hay SKUs reales sin alias — el detalle fila por fila para decidir si hace falta agregarlos a `EXPANDED_PRODUCT_MAPPING`. |

Los tres CSV llevan BOM UTF-8 (`utf-8-sig`), así que tildes y "ñ" se ven bien
en Excel/Tableau en Windows sin configurar nada.

## Qué significa cada check en `resumen_checks.csv`

- **filas_crudas_en_archivo_original** vs **filas_vigentes_tras_filtro_estatus**:
  cuántas filas traía el Excel original vs cuántas quedaron después de
  quedarnos solo con `Estatus == "Vigente"`. La diferencia debería
  explicarse **solo** por canceladas + la típica fila de "Total" al final
  de la hoja. Si la diferencia es mucho mayor, algo más se está cayendo y
  hay que investigar.
- **venta_total_general** vs **venta_total_suma_por_producto** /
  **reconciliacion_total_OK**: el total general de venta debe coincidir
  centavo a centavo con la suma de la venta agrupada por producto
  (incluyendo el bucket "Otros"). Si `reconciliacion_total_OK` sale `False`,
  hay una fuga de datos en el pipeline — repórtamelo, no debería pasar tras
  los cambios de esta sesión.
- **venta_por_categoria_negocio::\<categoría\>**: el desglose real por la
  columna "Categoria" del Excel (Producto (Botellas), Agave, Servicios,
  etc.) — para que confirmes a ojo que los montos por categoría de negocio
  tienen sentido, y para armar la gráfica de validación que quieras en
  Tableau (ej. una dona de "Producto real vs Otros").
- **filas_producto_sin_mapear_en_Otros** / **venta_producto_sin_mapear_en_Otros**:
  filas que SÍ son "Producto (Botellas)" (un tequila real) pero cuyo SKU no
  matcheó ningún alias conocido, así que cayeron en "Otros" por seguridad
  (no se pierden, pero tampoco se ven como el producto que en realidad son).
  Si este número no es cero, hay que agregar el alias correcto a
  `EXPANDED_PRODUCT_MAPPING` en `scripts/data_processor.py` — revisa
  `productos_sin_mapear_detalle.csv` para ver cuáles SKUs son.
- **filas_canal_agrupadas_en_Otros** / **venta_canal_agrupada_en_Otros**: lo
  mismo pero para el canal comercial (columna "Canal / Reporte") — puede ser
  un canal interno legítimamente distinto (Agave/Servicios ya vienen con su
  propio canal interno) o un typo de un canal real que falte mapear en
  `CANAL_MAPPING` (`scripts/design_tokens.py`).

## Qué NO valida este script

No re-verifica reglas de negocio (ej. si el margen de 60% de referencia es
razonable, o si un cliente debería estar en "Moderno" vs "Tradicional") —
eso sigue siendo criterio tuyo/del cliente. Solo garantiza que los números
que ves son consistentes internamente y que ninguna venta se perdió
silenciosamente en el camino.

Ver también `metodologia_reporte.md` (raíz del proyecto) para la explicación
completa de cómo se calcula cada parte del reporte (WoW/YoY/YTD, tabla de 8
columnas, regla "N/D", etc.).
