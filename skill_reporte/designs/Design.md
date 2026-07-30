# Design.md — Reporte "Ventas y Margen" · Loco Tequila

Documento de sistema de diseño para **replicar** el reporte semanal `Reporte_Loco_Semana_XX_AAAA.pdf`.
Pensado para ser consumido por una skill de generación de documentos/gráficas.

> ⚠️ **Nota sobre los HEX:** los valores de color son estimaciones leídas del PDF de referencia
> (Semana 30-2026). Si necesitas exactitud absoluta, muestrea un píxel del PDF original y
> sustituye el token correspondiente. La **estructura** (tablas, ejes, filas/columnas) sí es
> fiel al documento.

---

## 1. Identidad y meta

| Campo | Valor |
|---|---|
| Marca | Loco Tequila |
| Título del reporte | **Ventas y Margen** |
| Subtítulo | `De la Semana {NN}-{AAAA}` |
| Logo | "Loco" en blanco + subrayado "TEQUILA", esquina superior derecha |
| Idioma | Español (MX) |
| Moneda | Pesos MXN, formato `$1,889` (miles, sin decimales salvo Ticket Promedio) |
| Nota fija al pie de gráficas | `Las ventas no incluyen IVA, IEPS` |
| Numeración | Número de página abajo a la derecha |

---

## 2. Paleta de color (tokens)

### 2.1 Marca / estructura

| Token | HEX (aprox.) | Uso |
|---|---|---|
| `--brand-maroon` | `#6E1E28` | Banda de encabezado, títulos de sección, barras de título de gráficas |
| `--brand-maroon-deep` | `#5A1822` | Sombra / borde inferior de la banda |
| `--header-text` | `#FFFFFF` | Texto sobre banda maroon |
| `--section-title` | `#6E1E28` | Títulos "Ventas Totales", "Loco Blanco", etc. |
| `--section-subtitle` | `#8A8A8A` | Subtítulos "Por Producto" / "Por Canal" |
| `--page-bg` | `#FFFFFF` | Fondo de página |
| `--rule-line` | `#D9D9D9` | Líneas divisorias / borde inferior de página |

### 2.2 Colores de PRODUCTO (leyenda de dona y series apiladas)

Estos son los colores canónicos de las 6 SKU. Respetar SIEMPRE este orden y mapeo.

| Orden | Producto | Token | HEX (aprox.) |
|---|---|---|---|
| 1 | Loco Blanco | `--p-blanco` | `#9B1C31` (rojo vino / crimson) |
| 2 | Puro Corazón | `--p-corazon` | `#9A9A9A` (gris medio) |
| 3 | Loco Ámbar | `--p-ambar` | `#A96C43` (café/ámbar) |
| 4 | Loco 269 | `--p-269` | `#1F1F1F` (negro) |
| 5 | Loco Áureo | `--p-aureo` | `#1F6E6E` (teal/verde azulado) |
| 6 | Loco 200 | `--p-200` | `#F2C14E` (amarillo/dorado) |

### 2.3 Colores de CANAL (series apiladas en páginas "Por Canal")

| Canal | Token | HEX (aprox.) |
|---|---|---|
| Canal Tradicional y Moderno (Off Trade) | `--c-offtrade` | `#1F3B5C` (azul marino) |
| Centros de Consumo (On Trade) | `--c-ontrade` | `#7A1E2B` (guinda) |
| Venta Directa | `--c-directa` | `#E8A33D` (naranja/ámbar) |
| eCommerce | `--c-ecommerce` | `#5A5A5A` (gris oscuro) |
| Amigos y Familiares | `--c-amigos` | `#2E6E6E` (teal) |

### 2.4 Elementos de gráfica y estados

| Token | HEX (aprox.) | Uso |
|---|---|---|
| `--chart-plan-line` | `#E23B2E` | Línea roja "Plan de ventas / Plan venta" |
| `--chart-lastyear-area` | `#E7D6A6` | Área rellena "Año Pasado" (khaki claro) |
| `--chart-grid` | `#E2E2E2` | Cuadrícula horizontal / ejes |
| `--chart-label` | `#333333` | Etiquetas de dato sobre barras |
| `--highlight-cream` | `#FBF3DD` | Columna/fila resaltada ("Año Actual", "Ventas Netas", "Total") |
| `--pill-bg` | `#F6E2E2` | Píldora rosada de porcentaje en leyenda de dona |
| `--pill-text` | `#9B1C31` | Texto % dentro de la píldora |
| `--pos-value` | `#333333` | Variación positiva / neutra |
| `--neg-value` | `#E23B2E` | Variación negativa (rojo) — p.ej. `-97%` |

---

## 3. Tipografía

| Rol | Familia sugerida | Peso | Tamaño aprox. |
|---|---|---|---|
| Título reporte | Sans humanista (tipo "Poppins"/"Museo") | Bold | 30–34 pt |
| Subtítulo encabezado | Misma | Regular | 14 pt |
| Título de sección | Misma | Bold | 20–22 pt |
| Subtítulo de sección | Misma | Regular | 12 pt, gris |
| Encabezados de tabla | Sans | Bold | 7–8 pt |
| Cuerpo de tabla | Sans | Regular | 7–8 pt |
| Filas de total / resaltadas | Sans | Bold | 7–8 pt |
| Barra de título de gráfica | Sans, blanco sobre maroon | Bold | 9–10 pt |

Alineación numérica: **derecha** en todas las celdas de valor. Etiquetas de fila: **izquierda**.

---

## 4. Estructura de página

```
┌───────────────────────────────────────────────┐
│  BANDA MAROON  (Ventas y Margen / Semana)  LOGO │  ← --brand-maroon, alto ~90px
├───────────────────────────────────────────────┤
│  Título de sección           (Por Producto/Canal)│  ← --section-title
│                                                 │
│  [Leyenda dona]   [Tabla resumen]   (págs 1-2)  │
│  o                                              │
│  [Bloque de tablas SEMANAL/ANUAL]  (págs 4-31)  │
│                                                 │
│  [Barra maroon: "Ventas netas por ... $X"]      │
│  [Gráfica 1]                                    │
│  [Barra maroon: "Ventas volumen por ... N"]     │
│  [Gráfica 2]                                    │
├───────────────────────────────────────────────┤
│  línea gris                                  #N │
└───────────────────────────────────────────────┘
```

---

## 5. Esquemas de TABLA

Hay **5 tipos** de tabla. Todos comparten el orden de producto de §2.2.

### 5.1 Tabla Resumen (matriz Canal × Producto) — págs. 1, 2

- **Columnas (7 + total):** `Loco Blanco | Puro Corazón | Loco Ámbar | Loco 269 | Loco Áureo | Loco 200 | Total`
- **Filas (5 + total):**
  `Canal Tradicional`, `Canal Moderno`, `Centros de Consumo`, `Amigos y Familiares`, `Venta Directa`, **`Total`**
- Cada celda: valor `$`. La columna `Total` y la fila `Total` muestran `$valor (%)`.
- Fila `Total` y columna `Total` con fondo `--highlight-cream` y texto en negrita.

```
                 Blanco  Corazón  Ámbar  269   Áureo  200   Total
Canal Tradicional  $778   $274    $193   $6    $115   $63   $1,428 (36%)
Canal Moderno      $813   $218    $400   $64   $0     $0    $1,496 (37%)
Centros de Consumo $218   $216    $26    $21   $0     $13   $494  (12%)
Amigos y Familiares $0    $0      $0     $0    $0     $0    $0    (0%)
Venta Directa      $81    $201    $218   $0    $18    $66   $584  (15%)
Total ▓            $1,889 $909    $837   $91   $133   $142  $4,002 (100%)
                   (47%)  (23%)   (21%)  (2%)  (3%)   (4%)  (100%)
```

### 5.2 Tabla de detalle por cliente (bloques de canal) — pág. 1

Bloques: **Canal Tradicional**, **Canal Moderno**, **Venta Directa**, **Centros de Consumo**, **Familia y Amigos**, y un total combinado **Total Off Trade (Tradicional + Moderno)**.

- **Columnas:** los 6 productos + `Total` (con % de participación entre paréntesis).
- **Filas:** nombres de cliente (`LA EUROPEA MEXI...`, `VINOTECA MEXICO`, ...) truncados a ~15 car., más `Otros`, y cierre con:
  - `Ventas Netas 2026` (valores $)
  - `Participación %` (por columna)
- Fila de cierre con fondo `--highlight-cream`, negrita.

### 5.3 Tabla histórica mensual — pág. 3

- **Columnas:** 6 productos + `Total`.
- **Filas:** meses `Ene/25 … Dic/25` y `Ene/26 … {mes actual}/26`.
- Encima: dos bloques de encabezado `2025 (Total: $X)` y `2026 (Total: $Y)`.
- Acompaña gráfica de **barras apiladas por producto + línea "Total"** (roja) con separador vertical punteado entre años.

### 5.4 Tabla "Ventas Totales / {SKU} / {Cliente}" — SEMANAL y ANUAL (págs. 4-31)

Es la tabla central del reporte. Layout de **3 zonas horizontales**:

**Zona A — Valores absolutos** (4 sub-bloques, cada uno con `$` y `%`):
`Semana Año Ant.` | `Semana Anterior` | `Plan` | **`Año Actual`/`Semana Actual`** (resaltada `--highlight-cream`)

**Zona B — Etiqueta de fila** + rango de fechas en el encabezado:
`Semana {NN} - {AAAA}  /  Del {fecha} al {fecha}`

**Zona C — VARIACIONES VS** (3 sub-bloques, cada uno con `$` y `%`):
`Plan` | `Semana Anterior` | `Año Anterior`
- Variaciones negativas en `--neg-value` (rojo).

**Filas — versión "Por Producto":**
```
Loco Blanco
Loco Puro Corazón
Loco Ámbar
Loco 269
Loco Áureo
Ventas Netas Semanales / Anuales   ▓ (fila resaltada, negrita)
Margen %
#Botellas Vendidas
Cajas 9 Lts
Ticket Promedio (Pesos) $
```

**Filas — versión "Por Canal":**
```
Off Trade
On Trade
Venta Directa
Venta Ecommerce
Familia y Amigos
Ventas Netas Semanales / Anuales   ▓
Margen %
#Botellas Vendidas
Cajas 9 Lts
Ticket Promedio (Pesos) $
```

> Cada página SKU/cliente incluye **una tabla SEMANAL y una ANUAL** (dos páginas consecutivas).

### 5.5 Nota de celdas vacías

Cuando no hay dato se imprime `$0` / `0` / `0%` (nunca en blanco). Divisiones inválidas
aparecen literalmente como `$NaN` / `NaN%` en el original — replicar solo si se busca fidelidad exacta.

---

## 6. Especificación de GRÁFICAS

### 6.1 Dona (Resumen de ventas) — págs. 1, 2
- Tipo: **donut**, agujero ~55%.
- Segmentos = 6 productos, colores §2.2, en orden.
- Centro: `${Total}` grande + `Total de ventas`.
- Leyenda a la derecha: bullet de color · nombre · `$valor` · píldora rosada con `%`.

### 6.2 Barras apiladas + línea (Histórico mensual) — pág. 3
- Eje X: meses. Barras apiladas por **producto** (§2.2).
- Línea roja `--chart-plan-line` = `Total`, con etiqueta de dato por mes.
- Separador vertical punteado entre 2025 y 2026.
- Eje Y: 0 → 5000, paso 500.

### 6.3 Combo por semana/mes (páginas SKU y Canal) — págs. 4-31
Dos gráficas por página, dentro de barra de título maroon:
1. `Ventas netas por semana/mes ($) miles: ${total}`
2. `Ventas volumen por semana/mes (botellas): {total}`

Capas:
- **Área** color `--chart-lastyear-area` = serie `Año Pasado`.
- **Barras apiladas** por canal (§2.3) *o* por producto (§2.2) según la página.
- **Línea roja** `--chart-plan-line` = `Plan venta`.
- Etiquetas de dato numéricas encima de las barras.
- Leyenda inferior 1 (series): coincide con canales/productos + `Plan venta`.
- Leyenda inferior 2: `● Plan de ventas   ● Ventas Reales`.

---

## 7. Inventario de páginas (orden del PDF)

| Pág. | Contenido |
|---|---|
| 1 | Resumen Ventas **Anual** (dona + matriz + detalle por cliente) |
| 2 | Resumen Ventas **Semanal** |
| 3 | Histórico mensual (barras apiladas + línea) |
| 4–5 | Ventas Totales **Por Producto** (Semanal / Anual) |
| 6–7 | Ventas Totales **Por Canal** (Semanal / Anual) |
| 8–19 | Una SKU por par de páginas (Blanco, Corazón, Ámbar, 269, Áureo, 200) × (Semanal + Anual) |
| 20–31 | Clientes clave por par (Cava Sautto, La Europea, Palacio de Hierro, City Market, Vinoteca, La Castellana) |

---

## 8. Reglas de formato numérico

| Métrica | Formato | Ejemplo |
|---|---|---|
| Ventas ($ miles) | `$` + separador de miles, sin decimales | `$1,889` |
| Participación / variación | entero + `%` | `47%`, `-97%` |
| #Botellas Vendidas | entero | `2,829` |
| Cajas 9 Lts | entero | `206` |
| Ticket Promedio | `$` con 1 decimal | `$1.4` |
| Variación negativa | color rojo `--neg-value`, con signo `-` | `-$487` / `-92%` |

---

## 9. Checklist de replicación para la skill

1. Banda maroon `--brand-maroon` con título + subtítulo `De la Semana {NN}-{AAAA}` + logo blanco.
2. Respetar orden y color de las 6 SKU (§2.2) y de los 5 canales (§2.3) en TODA gráfica y tabla.
3. Resaltar en `--highlight-cream` la columna "Año/Semana Actual" y las filas de Total / Ventas Netas.
4. Variaciones negativas en rojo.
5. Cada SKU/cliente = par de páginas (Semanal + Anual) con las 2 gráficas combo.
6. Nota `Las ventas no incluyen IVA, IEPS` al pie de cada bloque de gráficas.
7. Numeración de página abajo-derecha.
8. Formatos numéricos de §8.
