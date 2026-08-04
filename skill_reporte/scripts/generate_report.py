"""
generate_report.py
==================
Orquestador principal -- genera PDF, XLSX y dashboard HTML del reporte
semanal de Loco Tequila.

Uso:
  python scripts/generate_report.py --semana 30 --anio 2026
      --datos-dir data_for_test_and_simulation
      --output-dir output

Argumentos opcionales:
  --logo    : ruta al logo SVG/PNG (default: assets/Loco_Tequila_Logo.svg)
  --solo    : pdf | xlsx | html  (genera solo uno de los tres)
  --top-clientes : numero de clientes top en PDF/XLSX (default 6)
"""

import argparse
import os
import sys
import time
from datetime import datetime

# Forzar UTF-8 en stdout/stderr para evitar errores cp1252 en Windows
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Asegurar que el directorio scripts/ sea importable
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from data_processor import LocoDataProcessor
from pdf_generator import generate_pdf
from xlsx_generator import generate_xlsx
from dashboard_generator import generate_dashboard
from market_context import load_market_context, create_template, get_search_queries


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

BANNER = """
===========================================================
  LOCO TEQUILA -- Generador de Reporte Semanal
  PDF | XLSX | Dashboard HTML
===========================================================
"""


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------

def _validate_week(semana: int, anio: int):
    if not (1 <= semana <= 53):
        raise ValueError(f"Semana inválida: {semana}. Debe estar entre 1 y 53.")
    if not (2020 <= anio <= 2035):
        raise ValueError(f"Año inválido: {anio}.")


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(BANNER)

    parser = argparse.ArgumentParser(
        description="Genera reporte semanal de Loco Tequila (PDF + XLSX + HTML).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--semana",       type=int, required=True,
                        help="Numero de semana ISO (1-53)")
    parser.add_argument("--anio",         type=int, required=True,
                        help="Anio del reporte (ej. 2026)")
    parser.add_argument("--datos-dir",    type=str,
                        default="data_for_test_and_simulation",
                        help="Carpeta con los CSVs de entrada")
    parser.add_argument("--output-dir",   type=str,
                        default="output",
                        help="Carpeta de salida para los archivos generados")
    parser.add_argument("--logo",         type=str,
                        default=None,
                        help="Ruta al logo SVG/PNG (opcional)")
    parser.add_argument("--solo",         type=str,
                        choices=["pdf", "xlsx", "html"],
                        default=None,
                        help="Genera solo uno de los tres artefactos")
    parser.add_argument("--top-clientes", type=int, default=6,
                        help="Numero de clientes top a incluir (default: 6)")

    # --- Comparativo custom ---
    parser.add_argument("--modo-comparar", type=str,
                        choices=["semana", "mes", "anio"],
                        default=None,
                        help="Modo de comparacion custom: semana | mes | anio")
    parser.add_argument("--comparar-semana", type=int, default=None,
                        help="Semana B para comparar (requiere --modo-comparar semana)")
    parser.add_argument("--comparar-mes",    type=int, default=None,
                        help="Mes B para comparar 1-12 (requiere --modo-comparar mes)")
    parser.add_argument("--comparar-anio",   type=int, default=None,
                        help="Anio B para comparar (requerido con --modo-comparar)")

    # --- Contexto de mercado ---
    parser.add_argument("--contexto-mercado", type=str, default=None,
                        help="Ruta a archivo .txt con contexto CRT/agave/NOM buscado por el agente")
    parser.add_argument("--generar-template-mercado", action="store_true",
                        help="Genera un archivo template de contexto de mercado y sale")
    parser.add_argument("--mostrar-queries-mercado", action="store_true",
                        help="Muestra las queries de busqueda web sugeridas para el contexto")

    args = parser.parse_args()

    # --- Helpers especiales (no requieren carga de datos) ---
    if args.mostrar_queries_mercado:
        print("\nQueries sugeridas para busqueda web de contexto de mercado:")
        for q in get_search_queries(args.anio):
            print(f"  - {q}")
        print()
        return

    if args.generar_template_mercado:
        tpl_path = os.path.join(
            os.path.dirname(_THIS_DIR), "output",
            f"template_contexto_mercado_S{args.semana:02d}_{args.anio}.txt"
        )
        os.makedirs(os.path.dirname(tpl_path), exist_ok=True)
        create_template(tpl_path, args.semana, args.anio)
        print(f"[OK] Template generado: {tpl_path}")
        print("Completa el archivo y usa --contexto-mercado para incluirlo en el reporte.")
        return

    # Resolver rutas relativas al directorio raíz del proyecto
    project_root = os.path.dirname(_THIS_DIR)
    datos_dir    = os.path.join(project_root, args.datos_dir) \
                   if not os.path.isabs(args.datos_dir) else args.datos_dir
    output_dir   = os.path.join(project_root, args.output_dir) \
                   if not os.path.isabs(args.output_dir) else args.output_dir

    # Logo: buscar en assets/ si no se especifica
    logo_path = args.logo
    if logo_path is None:
        candidate = os.path.join(project_root, "assets", "Loco_Tequila_Logo.svg")
        if os.path.exists(candidate):
            logo_path = candidate

    # Validaciones
    _validate_week(args.semana, args.anio)

    if not os.path.isdir(datos_dir):
        print(f"[ERROR] Carpeta de datos no encontrada: {datos_dir}")
        sys.exit(1)

    _ensure_dir(output_dir)

    semana_pad = f"{args.semana:02d}"
    suffix     = f"Semana_{semana_pad}_{args.anio}"

    pdf_path  = os.path.join(output_dir, f"Reporte_Loco_{suffix}.pdf")
    xlsx_path = os.path.join(output_dir, f"Reporte_Ejecutivo_Loco_{suffix}.xlsx")
    html_path = os.path.join(output_dir, f"Dashboard_Loco_{suffix}.html")

    # ── Carga de datos ──────────────────────────────────────────────────
    print(f"[INFO] Cargando datos desde: {datos_dir}")
    t0 = time.time()
    try:
        proc = LocoDataProcessor(
            datos_dir    = datos_dir,
            semana       = args.semana,
            anio         = args.anio,
            n_top_clientes = args.top_clientes,
        )
    except Exception as e:
        print(f"[ERROR] Al cargar datos: {e}")
        raise

    elapsed = time.time() - t0
    print(f"[OK] Datos cargados en {elapsed:.1f}s | {len(proc.df):,} registros actuals | {len(proc.dfp):,} registros plan\n")

    # Contexto de mercado (compartido por XLSX y HTML)
    ctx_mercado = load_market_context(filepath=args.contexto_mercado)

    results = {}

    # ── PDF ─────────────────────────────────────────────────────────────
    if args.solo in (None, "pdf"):
        print("[PDF] Generando PDF...")
        t1 = time.time()
        try:
            generate_pdf(proc, pdf_path, logo_path=logo_path)
            elapsed1 = time.time() - t1
            size_mb  = os.path.getsize(pdf_path) / 1_048_576
            print(f"   [OK] PDF listo en {elapsed1:.1f}s | {size_mb:.1f} MB")
            results["pdf"] = pdf_path
        except Exception as e:
            print(f"   [ERROR] Generando PDF: {e}")
            import traceback; traceback.print_exc()

    # ── XLSX ─────────────────────────────────────────────────────────────
    if args.solo in (None, "xlsx"):
        print("\n[XLSX] Generando XLSX...")
        t2 = time.time()
        try:
            # Comparativo custom
            comp_custom = None
            if args.modo_comparar:
                modo = args.modo_comparar
                periodo_a = {"anio": args.anio}
                periodo_b = {"anio": args.comparar_anio or args.anio}
                if modo == "semana":
                    periodo_a["semana"] = args.semana
                    if args.comparar_semana is None:
                        print("   [WARN] --comparar-semana no especificado, omitiendo comparativo custom.")
                    else:
                        periodo_b["semana"] = args.comparar_semana
                        comp_custom = proc.get_comparativo_custom(modo, periodo_a, periodo_b)
                elif modo == "mes":
                    # Mes del semana actual
                    cur_mes = proc._filter_period(args.anio, args.semana)["mes"].mode()
                    periodo_a["mes"] = int(cur_mes.iloc[0]) if len(cur_mes) > 0 else 1
                    if args.comparar_mes is None:
                        print("   [WARN] --comparar-mes no especificado, omitiendo comparativo custom.")
                    else:
                        periodo_b["mes"] = args.comparar_mes
                        comp_custom = proc.get_comparativo_custom(modo, periodo_a, periodo_b)
                elif modo == "anio":
                    if args.comparar_anio is None:
                        print("   [WARN] --comparar-anio no especificado, omitiendo comparativo custom.")
                    else:
                        comp_custom = proc.get_comparativo_custom(modo, periodo_a, periodo_b)

            generate_xlsx(proc, xlsx_path,
                          comparativo_custom=comp_custom,
                          contexto_mercado=ctx_mercado)
            elapsed2 = time.time() - t2
            size_kb  = os.path.getsize(xlsx_path) / 1024
            print(f"   [OK] XLSX listo en {elapsed2:.1f}s | {size_kb:.0f} KB")
            results["xlsx"] = xlsx_path
        except Exception as e:
            print(f"   [ERROR] Generando XLSX: {e}")
            import traceback; traceback.print_exc()

    # ── HTML ─────────────────────────────────────────────────────────────
    if args.solo in (None, "html"):
        print("\n[HTML] Generando Dashboard HTML...")
        t3 = time.time()
        try:
            generate_dashboard(proc, html_path, contexto_mercado=ctx_mercado)
            elapsed3 = time.time() - t3
            size_kb  = os.path.getsize(html_path) / 1024
            print(f"   [OK] HTML listo en {elapsed3:.1f}s | {size_kb:.0f} KB")
            results["html"] = html_path
        except Exception as e:
            print(f"   [ERROR] Generando Dashboard HTML: {e}")
            import traceback; traceback.print_exc()

    # ── Resumen ───────────────────────────────────────────────────────────
    total_time = time.time() - t0
    print(f"\n{'='*58}")
    print(f"  Reporte Semana {args.semana:02d}-{args.anio} -- Completado en {total_time:.1f}s")
    print(f"{'='*58}")
    for kind, path in results.items():
        print(f"  {kind.upper():5s}  ->  {path}")
    print(f"{'='*58}\n")


if __name__ == "__main__":
    main()
