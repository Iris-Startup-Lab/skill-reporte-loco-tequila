# CLAUDE.md — Referencia Directa a AGENTS.md

> **DOCUMENTO PRINCIPAL Y FUENTE DE VERDAD:**
> Este repositorio utiliza **[`AGENTS.md`](./AGENTS.md)** como la **única fuente de verdad (Single Source of Truth - SSOT)** para todas las directrices de operación, reglas de interacción, arquitectura, entorno y pruebas de agentes de Inteligencia Artificial (incluyendo Claude Code y Claude Desktop).
>
> **Antes de realizar cualquier acción o ejecutar código, consulta obligatoriamente:**
> - 📘 **[`AGENTS.md`](./AGENTS.md)** — Reglas de interacción, entorno Conda, comandos de generación y checklist de verificación.
> - 📗 **[`SKILL.md`](./SKILL.md)** — Metodología de análisis, esquema de datos, pipeline de procesamiento y especificación de métricas.

---

## ⚡ Reglas Clave Resumidas (Ver detalle en AGENTS.md)

1. **Entorno Python Obligatorio**:
   - Activar siempre el entorno conda **`data_analytics_science`** antes de ejecutar scripts:
     ```powershell
     & "E:\Users\1167486\AppData\Local\anaconda3\Scripts\conda.exe" shell.powershell hook | Out-String | Invoke-Expression; conda activate data_analytics_science
     ```

2. **Interacción con el Usuario (Máximo 2 preguntas iniciales)**:
   - **Pregunta 1 (Datos)**: Solo si no se adjuntaron ni especificaron rutas de datos. Nunca asumir monitoreo de carpetas de uploads ni exigir nombres específicos de archivo.
   - **Pregunta 2 (Semana/Año base)**: Solo si no fue especificado por el usuario (default para muestra: Semana 30 de 2026).
   - **Entregables**: Siempre generar los 3 entregables (**PDF + XLSX + HTML**) en una sola corrida; no preguntar formatos salvo que el usuario use `--solo`.
   - **Contexto de mercado**: Obligatorio siempre (`--contexto-mercado`), recopilando previamente datos de CRT, agave y NOM-006.

3. **Comando de Ejecución Estándar**:
   ```powershell
   python scripts/generate_report.py --semana 30 --anio 2026 --datos-dir data_for_test_and_simulation --output-dir output
   ```

4. **Verificación y Checklist**:
   - Consultar la sección *Checklist de Verificación para Agentes* en [`AGENTS.md`](./AGENTS.md) al completar cualquier tarea o cambio.
