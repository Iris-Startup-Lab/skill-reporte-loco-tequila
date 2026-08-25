"""
transform_client_data.py
========================
Script ETL puente para transformar y enriquecer datos en bruto del cliente
(archivos .xlsx o .csv) y exportar los datasets canónicos de Loco Tequila:
  - loco_actuals_enriquecido.csv (20 columnas)
  - loco_actual_vs_plan_semanal.csv (21 columnas)

Uso:
  python scripts/transform_client_data.py --input-dir datos_reales_cliente --output-dir data_clean_for_reports --anio 2026
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

# Asegurar import de scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_processor import LocoDataProcessor, _load_table, _normalize_product, _normalize_canal


def transform_and_save(input_dir: str, output_dir: str, anio: int = 2026, semana: int = 33):
    os.makedirs(output_dir, exist_ok=True)
    print(f"--> Cargando y transformando datos desde: {input_dir}")
    processor = LocoDataProcessor(datos_dir=input_dir, semana=semana, anio=anio)

    # 1. Dataset de Ventas Reales (Actuals Enriquecido - 20 columnas)
    actuals_cols = [
        "semana de venta", "fecha de venta", "SKU/producto", "unidades_de_venta",
        "categoria_o_linea", "cliente", "canal", "region_o_estado", "precio_unitario",
        "venta_con_impuestos", "venta_sin_impuestos", "anio", "ml_botella", "botellas",
        "litros", "cajas_9L", "margen_pct", "margen_pesos", "sub_canal", "canal_reporte"
    ]

    df_act = processor.df.copy()
    for col in actuals_cols:
        if col not in df_act.columns:
            if col == "categoria_o_linea":
                df_act[col] = "Blanco"
            elif col == "sub_canal":
                df_act[col] = "Tradicional"
            else:
                df_act[col] = 0

    df_act_out = df_act[actuals_cols].copy()
    actuals_output_path = os.path.join(output_dir, "loco_actuals_enriquecido.csv")
    df_act_out.to_csv(actuals_output_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Ventas reales exportadas: {actuals_output_path} ({len(df_act_out)} filas)")

    # 2. Dataset de Plan Presupuesto (Plan vs Real Semanal - 21 columnas)
    if not processor.dfp.empty:
        dfp = processor.dfp.copy()
        
        # Agregar columnas de fecha_lunes
        if "fecha_lunes" not in dfp.columns:
            def _get_lunes(sem_str, yr):
                try:
                    w = int(str(sem_str).split("W")[-1])
                    return pd.to_datetime(f"{yr}-W{w:02d}-1", format="%G-W%V-%u").strftime("%Y-%m-%d")
                except Exception:
                    return f"{yr}-01-01"
            dfp["fecha_lunes"] = [_get_lunes(s, y) for s, y in zip(dfp["semana_str"], dfp["anio_num"])]

        # Consolidar a nivel (anio, semana, SKU, canal)
        agg_dict = {
            "plan_unidades": "sum",
            "plan_botellas": "sum",
            "plan_cajas_9L": "sum",
            "plan_venta_sin_impuestos": "sum",
            "plan_margen_pesos": "sum",
        }
        if "plan_venta_con_impuestos" in dfp.columns:
            agg_dict["plan_venta_con_impuestos"] = "sum"

        grp_cols = ["anio_num", "semana_str", "fecha_lunes", "producto", "canal_norm"]
        dfp_agg = dfp.groupby(grp_cols, as_index=False).agg(agg_dict)
        dfp_agg.rename(columns={
            "anio_num": "anio",
            "semana_str": "semana de venta",
            "producto": "SKU/producto",
            "canal_norm": "canal_reporte",
        }, inplace=True)
        dfp_agg["canal"] = dfp_agg["canal_reporte"]

        if "plan_venta_con_impuestos" not in dfp_agg.columns:
            dfp_agg["plan_venta_con_impuestos"] = dfp_agg["plan_venta_sin_impuestos"] * 1.53

        # Calcular comparativos de actual vs plan
        # Cruzar con ventas reales agregadas al mismo nivel
        act_agg = df_act.groupby(["anio_num", "semana_str", "producto", "canal_norm"], as_index=False).agg({
            "unidades_de_venta": "sum",
            "botellas": "sum",
            "cajas_9L": "sum",
            "venta_sin_impuestos": "sum",
            "venta_con_impuestos": "sum",
            "margen_pesos": "sum",
        }).rename(columns={
            "anio_num": "anio",
            "semana_str": "semana de venta",
            "producto": "SKU/producto",
            "canal_norm": "canal_reporte",
            "unidades_de_venta": "actual_unidades",
            "botellas": "actual_botellas",
            "cajas_9L": "actual_cajas_9L",
            "venta_sin_impuestos": "actual_venta_sin",
            "venta_con_impuestos": "actual_venta_con",
            "margen_pesos": "actual_margen",
        })

        merged_plan = pd.merge(dfp_agg, act_agg, on=["anio", "semana de venta", "SKU/producto", "canal_reporte"], how="left").fillna(0)
        merged_plan["var_vs_plan_$"] = merged_plan["actual_venta_sin"] - merged_plan["plan_venta_sin_impuestos"]
        merged_plan["var_vs_plan_%"] = np.where(
            merged_plan["plan_venta_sin_impuestos"] > 0,
            (merged_plan["var_vs_plan_$"] / merged_plan["plan_venta_sin_impuestos"]) * 100,
            0.0
        )
        merged_plan["cumplimiento_%"] = np.where(
            merged_plan["plan_venta_sin_impuestos"] > 0,
            (merged_plan["actual_venta_sin"] / merged_plan["plan_venta_sin_impuestos"]) * 100,
            0.0
        )

        plan_cols = [
            "anio", "semana de venta", "fecha_lunes", "SKU/producto", "canal", "canal_reporte",
            "plan_unidades", "plan_botellas", "plan_cajas_9L", "plan_venta_sin_impuestos",
            "plan_venta_con_impuestos", "plan_margen_pesos", "actual_unidades", "actual_botellas",
            "actual_cajas_9L", "actual_venta_sin", "actual_venta_con", "actual_margen",
            "var_vs_plan_$", "var_vs_plan_%", "cumplimiento_%"
        ]
        df_plan_out = merged_plan[plan_cols].copy()
        plan_output_path = os.path.join(output_dir, "loco_actual_vs_plan_semanal.csv")
        df_plan_out.to_csv(plan_output_path, index=False, encoding="utf-8-sig")
        print(f"[OK] Plan semanalizado exportado: {plan_output_path} ({len(df_plan_out)} filas)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transforma datos reales de cliente a esquemas canónicos de Loco Tequila.")
    parser.add_argument("--input-dir", default="datos_reales_cliente", help="Carpeta con archivos Excel o CSV de cliente")
    parser.add_argument("--output-dir", default="data_clean_for_reports", help="Carpeta de salida para los CSVs estándar")
    parser.add_argument("--anio", type=int, default=2026, help="Año de referencia (default: 2026)")
    parser.add_argument("--semana", type=int, default=33, help="Semana de referencia (default: 33)")
    args = parser.parse_args()

    transform_and_save(input_dir=args.input_dir, output_dir=args.output_dir, anio=args.anio, semana=args.semana)
