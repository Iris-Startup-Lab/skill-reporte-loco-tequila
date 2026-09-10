"""
exportar_datos_validacion.py
=============================
Exporta los datos YA ENRIQUECIDOS por LocoDataProcessor -- los mismos que
consumen pdf_generator.py, xlsx_generator.py y dashboard_generator.py -- a
CSVs planos para pruebas manuales y validacion visual en Tableau/Power BI/
el editor de graficos que prefieras.

Por que reusa LocoDataProcessor en vez de limpiar los datos otra vez (como
en el notebook pruebas_manuales/Pruebas_limpieza_analisis_de_datos_
descriptivos.ipynb): si la exportacion de validacion tuviera su propia
logica de limpieza, podria "divergir" silenciosamente de la logica real del
reporte (justo el tipo de bug que motivo esta sesion de cambios: dos rutas
de codigo calculando el mismo numero de formas distintas). Aqui se garantiza
que lo que ves en Tableau es EXACTAMENTE lo que alimenta el PDF/XLSX/HTML.

Uso (cualquier archivo futuro de ventas/plan, no solo el de esta semana):
  python scripts/exportar_datos_validacion.py ^
      --datos-dir datos_reales_cliente ^
      --semana 34 --anio 2026 ^
      --output-dir pruebas_manuales/validacion_S34_2026

Genera en --output-dir:
  - ventas_enriquecido.csv   : self.df completo (una fila = una venta), con
                               todas las columnas derivadas (producto,
                               categoria_o_linea, categoria_negocio,
                               comparable_plan, canal_norm, region_o_estado,
                               botellas, cajas_9L, margen_pesos, margen_pct,
                               venta_sin_impuestos, venta_con_impuestos, etc.)
  - plan_enriquecido.csv     : self.dfp completo (presupuesto), si existe.
  - resumen_checks.csv       : reconciliaciones automaticas (ver mas abajo)
                               y el detalle de SKUs/canales sin mapear que
                               se agruparon en "Otros" (para que decidas si
                               falta agregar un alias en EXPANDED_PRODUCT_
                               MAPPING/CANAL_MAPPING).

Los tres CSV se escriben con encoding utf-8-sig (BOM) para que Excel/Tableau
en Windows respeten tildes/enies sin corromper el texto.

Que checks corre y por que (mi logica, para que la evalues):
  1. filas_crudas_vs_vigentes: cuantas filas trafan el archivo original vs
     cuantas quedaron tras el filtro de Estatus=="Vigente" (o el fallback
     != "Cancelado" si el archivo no usa esa palabra). La diferencia deberia
     explicarse solo por canceladas + filas de "Total" de Excel -- si la
     diferencia es mucho mayor a lo esperado, algo mas se esta cayendo.
  2. venta_total_general vs venta_total_por_producto (suma del groupby por
     "producto", que ya incluye el bucket "Otros"): deben coincidir al
     centavo. Si no coinciden, hay una fuga de datos en algun punto del
     pipeline (avisa, no deberia pasar tras los fixes de esta sesion).
  3. venta_por_categoria_negocio: el desglose real Producto (Botellas) vs
     Agave/Servicios/etc. -- para que confirmes visualmente en Tableau que
     los montos por categoria tienen sentido de negocio.
  4. productos_sin_mapear / canales_sin_mapear: filas que cayeron en "Otros"
     por typo o variante nueva de SKU/canal (no por ser una categoria de
     negocio distinta) -- esto es lo que hoy se imprime como advertencia en
     consola al correr generate_report.py; aqui queda tambien en CSV para
     que no se pierda si nadie vio la consola.
"""

import argparse
import os
import sys

import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from data_processor import LocoDataProcessor


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def exportar(datos_dir: str, semana: int, anio: int, output_dir: str):
    _ensure_dir(output_dir)

    n_crudas = 0
    proc = LocoDataProcessor(datos_dir=datos_dir, semana=semana, anio=anio)
    if proc.df_actuals is not None:
        n_crudas = len(proc.df_actuals)

    # ------------------------------------------------------------------
    # 1. Exports enriquecidos completos (misma fuente de verdad que el
    #    reporte real -- no se recalcula nada aqui).
    # ------------------------------------------------------------------
    ventas_path = os.path.join(output_dir, "ventas_enriquecido.csv")
    proc.df.to_csv(ventas_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Ventas enriquecidas -> {ventas_path} ({len(proc.df)} filas)")

    plan_path = os.path.join(output_dir, "plan_enriquecido.csv")
    if proc.dfp is not None and not proc.dfp.empty:
        proc.dfp.to_csv(plan_path, index=False, encoding="utf-8-sig")
        print(f"[OK] Plan enriquecido    -> {plan_path} ({len(proc.dfp)} filas)")
    else:
        print("[INFO] No se encontro archivo de Plan/Presupuesto en --datos-dir; se omite plan_enriquecido.csv")

    # ------------------------------------------------------------------
    # 2. Checks de reconciliacion (ver docstring del modulo).
    # ------------------------------------------------------------------
    checks = []

    n_vigentes = len(proc.df)
    checks.append(("filas_crudas_en_archivo_original", n_crudas))
    checks.append(("filas_vigentes_tras_filtro_estatus", n_vigentes))
    checks.append(("filas_excluidas_canceladas_o_totales", n_crudas - n_vigentes))

    total_venta = float(proc.df["venta_sin_impuestos"].sum())
    total_por_producto = float(proc.df.groupby("producto")["venta_sin_impuestos"].sum().sum())
    checks.append(("venta_total_general", round(total_venta, 2)))
    checks.append(("venta_total_suma_por_producto", round(total_por_producto, 2)))
    checks.append(("reconciliacion_total_OK", abs(total_venta - total_por_producto) < 0.01))

    por_categoria = proc.df.groupby("categoria_negocio")["venta_sin_impuestos"].sum().sort_values(ascending=False)
    for cat, val in por_categoria.items():
        checks.append((f"venta_por_categoria_negocio::{cat}", round(float(val), 2)))

    # SKUs de producto real ("Producto (Botellas)") que cayeron en "Otros"
    # por no matchear ningun alias -- distinto de Agave/Servicios/etc, que
    # caen en "Otros" a proposito porque no son productos con SKU.
    sin_mapear_prod = proc.df[(proc.df["comparable_plan"]) & (proc.df["producto"] == "Otros")]
    checks.append(("filas_producto_sin_mapear_en_Otros", len(sin_mapear_prod)))
    checks.append(("venta_producto_sin_mapear_en_Otros", round(float(sin_mapear_prod["venta_sin_impuestos"].sum()), 2)))

    canales_no_canonicos = proc.df[proc.df["canal_norm"] == "Otros"]
    checks.append(("filas_canal_agrupadas_en_Otros", len(canales_no_canonicos)))
    checks.append(("venta_canal_agrupada_en_Otros", round(float(canales_no_canonicos["venta_sin_impuestos"].sum()), 2)))

    checks_path = os.path.join(output_dir, "resumen_checks.csv")
    pd.DataFrame(checks, columns=["check", "valor"]).to_csv(checks_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Resumen de checks   -> {checks_path}")

    # Detalle fila por fila de lo que cayo en "Otros" por falta de mapeo de
    # SKU (no confundir con categorias de negocio como Agave/Servicios que
    # SIEMPRE van a "Otros" a proposito).
    if not sin_mapear_prod.empty:
        detalle_path = os.path.join(output_dir, "productos_sin_mapear_detalle.csv")
        sin_mapear_prod.to_csv(detalle_path, index=False, encoding="utf-8-sig")
        print(f"[ADVERTENCIA] Hay {len(sin_mapear_prod)} filas de producto real sin alias en "
              f"EXPANDED_PRODUCT_MAPPING -> detalle en {detalle_path}")

    print()
    print("--- Resumen rapido ---")
    print(f"Venta total: ${total_venta:,.2f}  (reconciliacion OK: {abs(total_venta - total_por_producto) < 0.01})")
    print(por_categoria.to_string())


def main():
    parser = argparse.ArgumentParser(
        description="Exporta datos enriquecidos de Loco Tequila (ventas + plan) a CSV para validacion manual en Tableau/Power BI.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--datos-dir", type=str, required=True,
                         help="Carpeta con el/los Excel o CSV de ventas y plan (cualquier archivo futuro del cliente)")
    parser.add_argument("--semana", type=int, required=True, help="Semana ISO (1-53) de referencia")
    parser.add_argument("--anio", type=int, required=True, help="Anio de referencia")
    parser.add_argument("--output-dir", type=str, default="pruebas_manuales/validacion",
                         help="Carpeta donde se escriben los CSV de salida")
    args = parser.parse_args()

    exportar(args.datos_dir, args.semana, args.anio, args.output_dir)


if __name__ == "__main__":
    main()
