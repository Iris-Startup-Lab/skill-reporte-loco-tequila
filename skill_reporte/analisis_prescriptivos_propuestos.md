# Plan Estratégico de Analítica Avanzada: Modelos Inferenciales, Predictivos y Prescriptivos para Loco Tequila

**Documento Técnico y de Negocio**
**Skill:** `reporte_loco_tequila`
**Actualizado:** Septiembre 2026

> Este documento evalúa la madurez analítica de la skill y propone una hoja de ruta
> para incorporar análisis **inferenciales, predictivos y prescriptivos** (más allá de
> lo descriptivo), ordenada por **factibilidad real con los datos disponibles** — no por
> ambición metodológica. Los números de la evaluación provienen de una revisión del
> código (`scripts/data_processor.py`, `scripts/generate_report.py`) y de los datasets
> en `data_for_test_and_simulation/` y `datos_reales_cliente/`.

---

## 0. Evaluación de la skill (punto de partida)

| Dimensión | Estado | Comentario |
| --- | --- | --- |
| Cobertura descriptiva | **Alta** | WoW, YoY, YTD, Rolling 52, matrices Canal→Cliente→Producto, Semáforo, contexto CRT/agave/NOM. |
| Motor de datos | **Sólido** | `LocoDataProcessor` centraliza limpieza, mapeos, márgenes, cajas 9L y la regla `N/D`. Una sola capa alimenta PDF/XLSX/HTML. |
| Calidad de datos | **Limitada** | Es *sell-in* transaccional. No hay sell-out/depletions, contratos, inventario, lead-times, motivo de baja ni competencia. |
| Dataset de muestra | **Viable para estadística** | 59,778 filas · 37 clientes · 14 SKUs · 4 canales · 2022–2026 (239 semanas). Concentración top-5 = 41%, HHI = 550. |
| Datos reales del cliente | **Insuficiente aún** | 500 filas en 2026 (sin histórico → comparativos `N/D`). Aporta campos ricos: `Vendedor`, `Punto de Venta`, `CECO`, `RFC`, `Tipo Comprobante`, `Moneda`. |
| Riesgo metodológico | **Medio** | Solo 37 cuentas → riesgo de overfitting en ML de churn; la data real aún no tiene profundidad temporal. |

**Conclusión:** la skill es madura en lo descriptivo (Nivel 1). Casi todo el valor no
descriptivo depende de (a) **acumular historia semanal** y (b) **enriquecer fuentes**.
Por eso el plan prioriza métodos que funcionan **con los datos actuales** (inferencia,
RFM, supervivencia) y deja los modelos costosos (ML de churn, causal impact, optimización
de inventario) para cuando exista la base de datos necesaria.

```
        ▲
Nivel 4 │                              [PRESCRIPTIVO]
        │       Next-Best-SKU, Precio Óptimo, Asignación de Inventario, What-If
        ├─────────────────────────────────────────────────────────────
Nivel 3 │                      [PREDICTIVO]
        │          Churn B2B, CLV (BG/NBD), Pronóstico de Demanda
        ├─────────────────────────────────────────────────────────────
Nivel 2 │                              [DIAGNÓSTICO / INFERENCIAL]
        │      Significancia bootstrap, Precio×Volumen×Mix, Elasticidad
        ├─────────────────────────────────────────────────────────────
Nivel 1 │ [ACTUAL]                     [DESCRIPTIVO]
        │         KPIs Semanales, Comparativos 8 Col, Tableros HTML/PDF/XLSX
        └─────────────────────────────────────────────────────────────►
                                                               Tiempo / Valor
```

El siguiente paso consiste en transicionar desde responder *"¿Qué vendimos y cuánto varió
vs Plan?"* hacia responder:
1. **Inferencial / diagnóstico:** *"¿El cambio es real o ruido, y de dónde viene (precio, volumen o mix)?"*
2. **Predictivo:** *"¿Qué cuentas están en riesgo de abandono y cuál es su valor futuro?"*
3. **Prescriptivo:** *"¿Qué SKU ofrecer a cada cliente, a qué precio y cómo asignar producto limitado para maximizar margen?"*

---

## 1. Eje A — Inferencial / Diagnóstico  ·  *(alto valor, baja barrera)*

Responde *"¿el cambio es real o ruido, y de dónde viene?"*. Todo se construye sobre
`LocoDataProcessor` (`scripts/data_processor.py`), sin fuentes externas.

### A.1 Significancia de la variación WoW / YoY
Hoy el reporte muestra una variación puntual sin decir si está dentro del ruido normal de
la serie. Con 239 semanas de muestra se puede estimar una banda de confianza.

- **Método:** *block bootstrap* semanal (remuestreo por bloques para preservar
  autocorrelación) sobre la serie de ventas; IC al 90/95%.
- **Salida:** KPI con intervalo — p. ej. `+3.2% [-1.1%, +7.5%]` → "variación no
  significativa" cuando cruza cero.
- **Integra en:** Hoja "Resumen Ejecutivo" (XLSX) y Semáforo del PDF.

### A.2 Descomposición ventas = Precio × Volumen × Mix
Descomposición logarítmica de la variación para atribuirla a sus componentes:

$$\Delta \ln V = \underbrace{\Delta \ln P}_{\text{precio}} + \underbrace{\Delta \ln Q}_{\text{volumen}} + \underbrace{\Delta \text{mix}}_{\text{canasta}}$$

- **Salida:** por SKU y por canal, cuánto de la caída/crecimiento vino de precio, de
  volumen o de cambio de mezcla.

### A.3 Tendencia y estacionalidad
- **Método:** STL (separar tendencia / estacionalidad / residuo) + test de tendencia
  **Mann-Kendall** por SKU y canal.
- **Salida:** clasificación *Ascendente / Estable / Descendente* con p-value, en lugar de
  comparar dos puntos.

### A.4 Contrastes por grupos y concentración de cartera
- **Kruskal-Wallis** (no paramétrico) de ticket y margen % entre canales y regiones, con
  corrección **Benjamini-Hochberg**.
- **HHI / Gini / Pareto** para medir concentración de cartera (ya hay `Pareto` básico; se
  formaliza el índice).

### A.5 Elasticidad precio (propia y cruzada)
- **Modelo:** $\ln(Q_{ijt}) = \alpha + \beta_1 \ln(P_{ijt}) + \sum_{k \ne j} \gamma_k \ln(P_{ikt}) + \delta\,\text{Canal}_i + \sum \theta_m \text{Mes}_m + \varepsilon_{ijt}$
- $\beta_1$ = elasticidad propia; $\gamma_k$ = canibalización cruzada.
- **Cautela:** posible endogeneidad de precio → documentar supuestos y usar variables
  instrumentales si el negocio aporta cambios de lista exógenos.

---

## 2. Eje B — Predictivo: Churn y Retención B2B

Responde *"¿qué cuenta se está enfriando y por qué?"*. En licores ultra-premium el churn
rara vez se notifica: se manifiesta como **enfriamiento gradual** (espaciamiento de
órdenes), pérdida de presencia en carta (On-Trade) o reemplazo por competencia
(Clase Azul, Don Julio 1942, Casa Dragones).

### B.1 RFM dinámico
- **Recency:** semanas desde la última compra por cuenta.
- **Frequency:** número de órdenes / semanas activas.
- **Monetary:** venta y margen acumulados.
- Se comparan contra la mediana histórica de cada cuenta (no contra un umbral global).

### B.2 BG/NBD + Gamma-Gamma (Buy-Till-You-Die)
- **Objetivo:** $P(\text{Alive})$ y valor monetario futuro esperado a 8/12 semanas.
- **Librería:** `lifetimes`. Adecuado para datos *sparse* y pocas cuentas — requiere menos
  volumen que un clasificador supervisado.
- **Segmentación:**
  - **Activo Estable** ($P(\text{Alive}) \ge 0.80$).
  - **En Enfriamiento** ($0.50 \le P < 0.80$): intervalo desde la última orden $> \mu + 1.5\sigma$ de su ciclo.
  - **Riesgo Crítico** ($P < 0.50$): intervención inmediata del equipo comercial.

### B.3 Análisis de supervivencia
- **Kaplan-Meier** del tiempo entre recompras por segmento (canal / gama).
- **Cox / AFT** con covariables: mix de SKUs, canal, ticket, margen, región, **vendedor**
  (disponible en la data real). Salida interpretable: *hazard ratios* de churn.
- **Ventaja:** maneja censura (cuentas aún activas) correctamente.

### B.4 Account Health Index (AHI, 0–100)
$$\text{AHI}_i = w_1 Z_{\text{Recency}} + w_2 Z_{\text{Breadth}} + w_3 Z_{\text{Margin}} + w_4 Z_{\text{Volume}}$$

- **Recency:** ratio intervalo actual / mediana histórica.
- **Breadth:** ¿solo Blanco o ya incorporó Ámbar/Áureo/Puro Corazón?
- **Margin:** estabilidad de margen bruto % (detecta erosión por sobre-descuento).
- **Volume:** tendencia de cajas 9L en rolling de 8 semanas.

### B.5 Clasificador de churn (solo cuando haya ≥12–18 meses reales)
- **Modelo:** Regresión Logística o LightGBM con **validación temporal walk-forward**
  (nunca k-fold aleatorio) y calibración de probabilidades.
- **Precaución:** con 37 cuentas no hay potencia estadística; mientras tanto, usar
  AHI + supervivencia + BG/NBD.

### B.6 Acciones prescriptivas anti-churn
- **On-Trade:** visita de Brand Ambassador, capacitación a sommeliers/bartenders, catas
  con Puro Corazón, reposición de POP.
- **Off-Trade:** incentivo escalonado por volumen en SKUs de rotación (Blanco 750 ml)
  condicionado a una caja de gama alta (Áureo/Ámbar).
- **Asignación:** cruzar AHI con `Vendedor` / `Punto de Venta` para generar una lista de
  tareas priorizada.

---

## 3. Eje C — Prescriptivo

Responde *"¿qué hago, a quién y a qué precio?"*.

### C.1 Mix de producto y Next-Best-SKU
- **Reglas de asociación** (support / confidence / lift) sobre el historial de canasta.
- **Propensión logística** para recomendar a cada cuenta mono-compra el siguiente SKU.
- **Salida:** "canastas de éxito" por tipología de cuenta (hotel de playa vs. cantina urbana).

### C.2 Optimización de precio
- Usar la elasticidad del Eje A.5 para simular el precio que **maximiza margen** (no
  ingresos) por canal, con restricción de no romper el volumen de cajas 9L.

### C.3 Asignación de producto de disponibilidad finita
- **Programación lineal** (`PuLP` / `scipy.optimize`) para ediciones limitadas
  (Áureo Elevación, 269, ediciones Día de Muertos):
  $$\max \sum_i \sum_j \text{MargenNeto}_{ij} \cdot X_{ij}$$
  sujeto a inventario por SKU, compromisos contractuales y score de prestigio del cliente.
- **Requisito:** el negocio debe exponer inventario/compromisos.

### C.4 Simulador "What-If" en el Dashboard HTML
- Controles deslizantes de precio, mix y días de cobertura que recalculan KPIs en vivo
  usando las elasticidades estimadas. Extiende `scripts/dashboard_generator.py`.

### C.5 Causal Impact (cuando haya historia)
- Series de tiempo estructurales bayesianas (*BSTS / CausalImpact*) con contrafactual
  sintético por canal/territorio para medir el efecto incremental de lanzamientos o
  activaciones.

---

## 4. Hoja de Ruta Priorizada

| Fase | Plazo | Módulo analítico | Entregable técnico | Datos que ya tenemos | Riesgo |
| --- | --- | --- | --- | --- | --- |
| **0. Quick Win** | 1 sem | Significancia bootstrap + descomposición Precio×Volumen×Mix | `scripts/estadistica_inferencial.py` + banda de confianza en XLSX/PDF | ✅ Sí | Bajo |
| **1. Anti-Churn** | 2–3 sem | RFM dinámico + AHI + semáforo | Hoja "Churn & Retención" (XLSX) + tarjeta en Dashboard HTML | ✅ Sí (+`Vendedor` real) | Bajo |
| **2. Supervivencia** | 3–4 sem | Kaplan-Meier + Cox | `scripts/survival.py` + tabla de hazard ratios | ✅ Sí | Medio |
| **3. CLV** | 4–5 sem | BG/NBD + Gamma-Gamma | `scripts/clv.py` — $P(\text{Alive})$ y valor futuro a 12 sem | ✅ Sí (`lifetimes`) | Medio |
| **4. Pricing** | 5–7 sem | Elasticidad + margen óptimo | `scripts/pricing_optimizer.py` | Requiere variación de precios | Alto |
| **5. Forecast** | 7–9 sem | Pronóstico jerárquico 12 sem (reconciliado) | Extiende el pipeline para proyectar en PDF/XLSX | Muestra ✅ / real requiere historia | Medio |
| **6. What-If** | 9–12 sem | Simulador interactivo | Sliders en Dashboard HTML | Depende de Fases 4–5 | Medio |

> **Principio de secuencia:** cada fase debe ser **autónoma y sumativa** — la Fase 1 no
> depende de las demás, y ninguna rompe los 4 comparativos fijos que hoy son obligatorios.

---

## 5. Integración Técnica

- **Una sola capa de datos:** las nuevas métricas se calculan en `data_processor.py` (o
  módulos importados que devuelvan DataFrames) y se consumen desde `xlsx_generator.py`,
  `pdf_generator.py` y `dashboard_generator.py` sin duplicar lógica.
- **Sin romper el flujo por defecto:** agregar hojas nuevas (p. ej. **"Churn &
  Retención"**, **"Inferencia"**) y secciones opcionales en el PDF. Los 4 comparativos
  fijos siguen intactos.
- **CLI:** banderas opcionales `--analitica-avanzada` (o `--churn` / `--pricing`) que
  activen los módulos; por defecto el reporte se mantiene igual.
- **Dependencias a validar en el env `data_analytics_science`:** `lifetimes`, `scipy`,
  `statsmodels`, `lifelines`, `scikit-learn` → agregar a `requirements.txt` solo tras
  confirmar que están instaladas.

---

## 6. Rigor Estadístico Obligatorio

- **Validación temporal** (walk-forward) en todo modelo predictivo — nunca aleatoria.
- **Corrección por múltiples pruebas** (Benjamini-Hochberg) al comparar muchos SKUs/canales.
- **Reportar efecto + intervalo**, no solo p-value; cuidar la potencia dado N=37 cuentas.
- **Censura** correcta en supervivencia; **estacionalidad y anulaciones** (`Estatus`) en
  toda serie.
- **Documentar** supuestos y límites en `metodologia_reporte.md` (extender las Notas
  Metodológicas que ya existen en el PDF).

---

## 7. Requerimientos de Datos y Enriquecimiento

1. **Sell-In (actual):** `loco_actuals_enriquecido.csv` / reportes del cliente.
2. **Sell-Out / Depletions (deseable):** ventas del distribuidor al punto de consumo
   final — permite anticipar quiebres de anaquel.
3. **Inventario y lead-times (necesario para Fase C.3):** disponibilidad por SKU y
   compromisos contractuales.
4. **Trade Marketing (opcional):** cartas/restaurantes donde Loco es *house pour*.
5. **Datos de visitas del `Vendedor` (deseable):** convierte el score de churn en tarea
   comercial accionable.
6. **Series históricas del CRT:** molienda de agave, inventario de barricas y precio
   spot de agave para los modelos con factores exógenos.

---

## 8. Preguntas Abiertas para Calibrar el Plan

1. ¿Existe data de **sell-out**, **inventario** y **visitas del vendedor**?
2. ¿Desde cuándo se acumula **historia semanal real**? (define cuándo habilitar ML de
   churn, causal impact y forecast con datos propios y no de muestra).
