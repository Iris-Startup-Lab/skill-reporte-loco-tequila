# Resumen Ejecutivo: Storytelling with Data
**Autor**: Cole Nussbaumer Knaflic  
**Propósito**: Guía de referencia sobre principios de diseño de visualización de datos y comunicación directiva para la Skill de Reportes Ejecutivos.

---

## Capítulo 1: La Importancia del Contexto

Antes de construir cualquier gráfico o reporte, es fundamental responder tres preguntas clave:

1. **¿Quién? (Who)**: ¿Quién es la audiencia directiva? (CEO, CFO, Director de Ventas). Conocer sus prioridades y nivel de detalle necesario.
2. **¿Qué? (What)**: ¿Qué acción o decisión se necesita que la audiencia tome al ver los datos?
3. **¿Cómo? (How)**: ¿Qué datos y narrativa respaldan la sugerencia?

### Herramientas de Claridad
- **Prueba de los 3 Minutos**: Si no puedes explicar la conclusión principal de tu reporte en 3 minutos, la historia no está suficientemente clara.
- **La Gran Idea (Big Idea)**: Resumir el hallazgo principal en una sola frase estructurada en 3 partes: *articular el punto de vista, indicar lo que está en juego y la recomendación*.

---

## Capítulo 2: Elección de una Visualización Efectiva

No todos los tipos de gráficos son iguales. Se debe seleccionar la forma visual según el tipo de datos:

| Tipo de Visualización | Uso Recomendado | Reglas de Aplicación |
|---|---|---|
| **Texto Simple** | 1 o 2 métricas clave aisladas | Mostrar la cifra en fuente grande (ej. `$24.5M`) con una breve etiqueta explicativa. Evitar gráficos para números sueltos. |
| **Tablas** | Consulta de valores exactos por múltiples categorías | Líneas horizontales mínimas o ausentes. Destacar encabezados y filas de total con fondo tenue (`HIGHLIGHT_CREAM`). |
| **Mapa de Calor (Heatmap)** | Tablas con densidad de información | Aplicar gradiente cromático para dirigir la mirada a valores máximos/mínimos sin saturar. |
| **Gráfico de Líneas** | Tendencias y series de tiempo continuas | Ideal para ver evoluciones semanales o mensuales. |
| **Slopegraph** | Comparar 2 puntos en el tiempo entre múltiples categorías | Muestra cambios de posición o magnitud entre periodos (ej. 2025 vs 2026). |
| **Gráfico de Barras (Vertical / Horizontal)** | Comparaciones de categorías discretas | El cerebro humano procesa longitudes con alta precisión. Las barras deben iniciar SIEMPRE en eje 0. |
| **Barras Apiladas (Stacked Bars)** | Mostrar la composición del total por subcategorías | Excelente para ver la contribución de productos o canales a lo largo del tiempo. |

### Visualizaciones a EVITAR en Reportes Ejecutivos
- 🚫 **Pie Charts y Donas para Análisis de Tendencia**: Ineficientes para comparar ángulos y áreas. Se restringen solo a resúmenes de participación muy simples (máximo 5-6 segmentos).
- 🚫 **Gráficos 3D**: Distorsionan visualmente las proporciones reales.
- 🚫 **Ejes Y Secundarios con Escalas Distintas**: Confunden al lector y provocan falsas correlaciones.

---

## Capítulo 3: ¡El Desorden es tu Enemigo! (Decluttering)

El desorden gráfico aumenta la carga cognitiva de la audiencia. Se debe aplicar el principio de **Reducción del Desorden Visual**.

### Principios Gestalt de Percepción Visual
1. **Proximidad**: Colocar etiquetas pegadas a las series o barras para evitar leyendas lejanas.
2. **Similitud**: Usar el mismo color para elementos de la misma categoría a lo largo de todo el documento.
3. **Cerramiento (Enclosure)**: Usar sombreados o tarjetas claras para agrupar métricas relacionadas.
4. **Cierre (Closure)**: El cerebro completa formas; eliminar bordes pesados del gráfico.
5. **Continuidad**: Mantener alineaciones limpias a la izquierda para textos y a la derecha para cifras numéricas.
6. **Conexión**: Líneas continuas conectan mejor puntos en series de tiempo que símbolos aislados.

### Reglas Prácticas de Limpieza
- Eliminar bordes exteriores del gráfico.
- Usar líneas de cuadrícula (*gridlines*) ultra sutiles en gris claro (`#EBEBEB`) o eliminarlas.
- Usar espacio en blanco (*White space*) de forma activa para separar secciones y evitar sensación de saturación.

---

## Capítulo 4: Enfocar la Atención de la Audiencia

Aprovechar los **Atributos Pre-atencionales** para dirigir los ojos del ejecutivo a donde está la información importante en menos de un segundo:

- **Color Intencional**: Todo el reporte en escala de grises/tonos neutros, salvo el elemento de interés que se destaca con el color institucional (Maroon `#6E1E28`) o alertas (Rojo `#D9381E` / Verde `#2D8A4E`).
- **Tamaño y Peso**: Tipografía en negrita (`bold`) y mayor puntaje para totales y hallazgos críticos.
- **Posición**: Los ojos leen en patrón F/Z (de arriba a izquierda a abajo a derecha). Colocar los KPIs más importantes en la esquina superior izquierda.

---

## Capítulo 5: Pensar como un Diseñador

- **La forma sigue a la función**: Escoger el formato adecuado al objetivo.
- **Affordances (Pistas visuales)**:
  - Destacar lo crítico.
  - Eliminar distracciones innecesarias.
  - Crear una jerarquía visual clara (Título principal > Subtítulo > KPI > Tabla/Gráfico > Pie de página).
- **Accesibilidad**: Asegurar un alto contraste entre texto y fondo.

---

## Capítulo 6: Desmontando Visualizaciones de Ejemplo

Análisis paso a paso de gráficos corporativos mediocres transformados en piezas de comunicación ejecutiva limpia, eliminando ruido, re-estructurando ejes y aplicando jerarquía de color.

---

## Capítulo 7: Lecciones de Storytelling

Un reporte no es solo un conjunto de gráficos, es una historia de negocio estructurada:

1. **El Marco Narrativo**:
   - **Inicio**: Presentación de la situación actual y contexto del negocio.
   - **Nudo / Conflicto**: Desviaciones respecto al plan, riesgos o caídas en ventas/margen.
   - **Desenlace**: Hallazgos, oportunidades y recomendaciones de acción inmediata.
2. **Storyboarding**: Planificar la secuencia de páginas/diapositivas antes de escribir el código o los scripts de reporte.

---

## Capítulo 8: Integrándolo Todo

Caso de estudio integral donde se aplica el proceso de 6 pasos:
1. Entender el contexto.
2. Elegir la visualización adecuada.
3. Eliminar el desorden.
4. Enfocar la atención con atributos pre-atencionales.
5. Pensar como un diseñador.
6. Contar la historia.

---

## Capítulo 9: Casos de Estudio Reales

Ejemplos prácticos para distintos escenarios de negocio:
- Reportes financieros ejecutivos estáticos.
- Dashboards interactivos para análisis exploratorio.
- Presentaciones para junta directiva.

---

## Capítulo 10: Reflexiones Finales

Construcción de cultura de comunicación visual en equipos de analytics y finanzas. La meta es transformar datos en decisiones de negocio informadas y ágiles.
