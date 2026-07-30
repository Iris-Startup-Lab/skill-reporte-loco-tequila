"""
data_processor.py
=================
Carga, limpia y transforma los CSVs de ventas de Loco Tequila.
Produce DataFrames listos para los generadores de PDF, XLSX y HTML.

Columnas clave del CSV actuals_enriquecido:
  semana de venta, fecha de venta, SKU/producto, unidades_de_venta,
  categoria_o_linea, cliente, canal, region_o_estado, precio_unitario,
  venta_con_impuestos, venta_sin_impuestos, anio, ml_botella, botellas,
  litros, cajas_9L, margen_pct, margen_pesos, sub_canal, canal_reporte

Columnas clave del CSV actual_vs_plan_semanal:
  anio, semana de venta, fecha_lunes, SKU/producto, canal, canal_reporte,
  plan_unidades, plan_botellas, plan_cajas_9L, plan_venta_sin_impuestos,
  plan_venta_con_impuestos, plan_margen_pesos, actual_unidades, actual_botellas,
  actual_cajas_9L, actual_venta_sin, actual_venta_con, actual_margen,
  var_vs_plan_$, var_vs_plan_%, cumplimiento_%
"""

import os
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

from design_tokens import (
    PRODUCT_ORDER, PRODUCT_DISPLAY_NAMES, CANAL_ORDER, CANAL_MAPPING
)


# ---------------------------------------------------------------------------
# Helpers de carga
# ---------------------------------------------------------------------------

def _detect_encoding(filepath: str) -> str:
    """Detecta encoding del archivo usando chardet; fallback a latin-1."""
    try:
        import chardet
        with open(filepath, "rb") as f:
            result = chardet.detect(f.read(50_000))
        enc = result.get("encoding") or "latin-1"
        # chardet a veces devuelve 'windows-1252' que pandas acepta
        return enc
    except ImportError:
        return "latin-1"


def _load_csv(filepath: str) -> pd.DataFrame:
    """Carga un CSV con detección automática de encoding."""
    enc = _detect_encoding(filepath)
    try:
        df = pd.read_csv(filepath, encoding=enc, low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="latin-1", low_memory=False)
    return df


def _normalize_product(name: str) -> str:
    """Normaliza nombres de producto a las claves canónicas."""
    name = str(name).strip()
    mapping = {
        "Loco Blanco":  "Loco Blanco",
        "Puro Corazon": "Puro Corazon",
        "Puro Corazón": "Puro Corazon",
        "Loco Ambar":   "Loco Ambar",
        "Loco Ámbar":   "Loco Ambar",
        "Loco 269":     "Loco 269",
        "Loco Aureo":   "Loco Aureo",
        "Loco Áureo":   "Loco Aureo",
        "Loco 200":     "Loco 200",
    }
    return mapping.get(name, name)


def _normalize_canal(canal: str) -> str:
    """Normaliza canal al nombre canónico de reporte."""
    canal = str(canal).strip()
    return CANAL_MAPPING.get(canal, canal)


def _week_str(year: int, week: int) -> str:
    return f"{year}-W{week:02d}"


def _prev_week(year: int, week: int) -> Tuple[int, int]:
    if week == 1:
        return year - 1, 52
    return year, week - 1


def _same_week_prev_year(year: int, week: int) -> Tuple[int, int]:
    return year - 1, week


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class LocoDataProcessor:
    """
    Carga los datos y expone DataFrames listos para cada sección del reporte.

    Parámetros
    ----------
    datos_dir   : carpeta con los CSVs
    semana      : número de semana ISO (1-52)
    anio        : año del reporte
    n_top_clientes : número de clientes top para desglose
    """

    def __init__(
        self,
        datos_dir: str,
        semana: int,
        anio: int,
        n_top_clientes: int = 6,
    ):
        self.datos_dir = datos_dir
        self.semana = semana
        self.anio = anio
        self.n_top_clientes = n_top_clientes

        self._load_data()
        self._enrich()

    # ------------------------------------------------------------------
    # Carga y enriquecimiento
    # ------------------------------------------------------------------

    def _load_data(self):
        actuals_path = os.path.join(self.datos_dir, "loco_actuals_enriquecido.csv")
        plan_path    = os.path.join(self.datos_dir, "loco_actual_vs_plan_semanal.csv")

        # Fallback inteligente si no existe con el nombre exacto
        if not os.path.exists(actuals_path) and os.path.isdir(self.datos_dir):
            csvs = [os.path.join(self.datos_dir, f) for f in os.listdir(self.datos_dir) if f.lower().endswith(".csv")]
            for c in csvs:
                c_name = os.path.basename(c).lower()
                if "actual" in c_name or "venta" in c_name or "enriquecido" in c_name:
                    actuals_path = c
                    break
            else:
                if csvs: actuals_path = csvs[0]

        if not os.path.exists(plan_path) and os.path.isdir(self.datos_dir):
            csvs = [os.path.join(self.datos_dir, f) for f in os.listdir(self.datos_dir) if f.lower().endswith(".csv")]
            for c in csvs:
                c_name = os.path.basename(c).lower()
                if "plan" in c_name or "presupuesto" in c_name or "vs_plan" in c_name:
                    plan_path = c
                    break

        self.df_actuals = _load_csv(actuals_path)
        self.df_plan    = _load_csv(plan_path) if os.path.exists(plan_path) else pd.DataFrame()

    def _enrich(self):
        df = self.df_actuals.copy()

        # Normalizar nombres
        df["producto"]   = df["SKU/producto"].apply(_normalize_product)
        df["canal_norm"] = df["canal_reporte"].apply(_normalize_canal)

        # Parsear semana y año
        df["semana_str"] = df["semana de venta"].astype(str).str.strip()
        df["semana_num"] = (
            df["semana_str"]
            .str.extract(r"W(\d+)")[0]
            .astype(float)
            .astype("Int64")
        )
        df["anio_num"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")

        # Parsear fecha
        df["fecha"] = pd.to_datetime(df["fecha de venta"], errors="coerce")
        df["mes"]   = df["fecha"].dt.month
        df["mes_nombre"] = df["fecha"].dt.strftime("%b/%y")

        # Numéricos
        for col in ["venta_sin_impuestos", "venta_con_impuestos",
                    "margen_pesos", "botellas", "cajas_9L",
                    "margen_pct", "precio_unitario"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        self.df = df

        # Plan también
        dfp = self.df_plan.copy()
        dfp["producto"]   = dfp["SKU/producto"].apply(_normalize_product)
        dfp["canal_norm"] = dfp["canal_reporte"].apply(_normalize_canal)
        dfp["semana_str"] = dfp["semana de venta"].astype(str).str.strip()
        dfp["semana_num"] = (
            dfp["semana_str"]
            .str.extract(r"W(\d+)")[0]
            .astype(float)
            .astype("Int64")
        )
        dfp["anio_num"] = pd.to_numeric(dfp["anio"], errors="coerce").astype("Int64")
        for col in ["plan_venta_sin_impuestos", "plan_venta_con_impuestos",
                    "plan_margen_pesos", "plan_botellas", "plan_cajas_9L"]:
            if col in dfp.columns:
                dfp[col] = pd.to_numeric(dfp[col], errors="coerce").fillna(0)

        self.dfp = dfp

    # ------------------------------------------------------------------
    # Filtros de periodo
    # ------------------------------------------------------------------

    def _filter_period(self, year: int, week: int) -> pd.DataFrame:
        df = self.df
        return df[(df["anio_num"] == year) & (df["semana_num"] == week)]

    def _filter_year(self, year: int) -> pd.DataFrame:
        return self.df[self.df["anio_num"] == year]

    def _filter_ytd(self, year: int, max_week: int) -> pd.DataFrame:
        df = self.df
        return df[(df["anio_num"] == year) & (df["semana_num"] <= max_week)]

    def _filter_month(self, year: int, month: int) -> pd.DataFrame:
        df = self.df
        return df[(df["anio_num"] == year) & (df["mes"] == month)]

    # ------------------------------------------------------------------
    # KPIs por periodo
    # ------------------------------------------------------------------

    def _kpis(self, df: pd.DataFrame) -> Dict:
        ventas = df["venta_sin_impuestos"].sum()
        botellas = df["botellas"].sum()
        cajas = df["cajas_9L"].sum()
        margen = df["margen_pesos"].sum()
        margen_pct = (margen / ventas * 100) if ventas > 0 else 0
        ticket = (ventas / botellas) if botellas > 0 else 0
        return {
            "ventas_netas": ventas,
            "botellas": botellas,
            "cajas_9l": cajas,
            "margen_pesos": margen,
            "margen_pct": margen_pct,
            "ticket_promedio": ticket,
        }

    def _plan_kpis(self, year: int, week: int) -> Dict:
        dfp = self.dfp
        p = dfp[(dfp["anio_num"] == year) & (dfp["semana_num"] == week)]
        return {
            "ventas_netas": p["plan_venta_sin_impuestos"].sum(),
            "botellas": p["plan_botellas"].sum(),
            "cajas_9l": p["plan_cajas_9L"].sum(),
            "margen_pesos": p["plan_margen_pesos"].sum(),
        }

    # ------------------------------------------------------------------
    # Público: Resumen ejecutivo
    # ------------------------------------------------------------------

    def get_resumen_ejecutivo(self) -> Dict:
        """KPIs actuales + variaciones WoW, MoM, YoY, YTD."""
        y, w = self.anio, self.semana
        py, pw = _prev_week(y, w)
        ly, lyw = _same_week_prev_year(y, w)

        cur  = self._kpis(self._filter_period(y, w))
        prev = self._kpis(self._filter_period(py, pw))
        lasty= self._kpis(self._filter_period(ly, lyw))
        plan = self._plan_kpis(y, w)

        # Mes actual
        cur_fecha = self._filter_period(y, w)["fecha"].min()
        if pd.isna(cur_fecha):
            cur_mes = 1
        else:
            cur_mes = cur_fecha.month
        mes_act  = self._kpis(self._filter_month(y, cur_mes))
        mes_prev = self._kpis(self._filter_month(y, cur_mes - 1 if cur_mes > 1 else 12))
        mes_ly   = self._kpis(self._filter_month(ly, cur_mes))

        ytd_cur  = self._kpis(self._filter_ytd(y, w))
        ytd_prev = self._kpis(self._filter_ytd(ly, lyw))

        def var(a, b, key="ventas_netas"):
            va, vb = a.get(key, 0), b.get(key, 0)
            d = va - vb
            p = (d / vb * 100) if vb != 0 else (100.0 if va > 0 else 0.0)
            return {"abs": d, "pct": p}

        return {
            "semana": w,
            "anio": y,
            "actual": cur,
            "plan": plan,
            "vs_plan": var(cur, plan),
            "vs_semana_anterior": var(cur, prev),
            "vs_anio_anterior": var(cur, lasty),
            "mes_actual": mes_act,
            "mes_vs_anterior": var(mes_act, mes_prev),
            "mes_vs_ly": var(mes_act, mes_ly),
            "ytd_actual": ytd_cur,
            "ytd_vs_ly": var(ytd_cur, ytd_prev),
        }

    # ------------------------------------------------------------------
    # Público: Tabla resumen canal × producto
    # ------------------------------------------------------------------

    def get_matriz_canal_producto(self, mode: str = "semanal") -> pd.DataFrame:
        """
        Retorna DataFrame pivotado Canal × Producto con ventas sin IVA.
        mode: 'semanal' | 'anual'
        """
        y, w = self.anio, self.semana
        if mode == "semanal":
            df = self._filter_period(y, w)
        else:
            df = self._filter_ytd(y, w)

        piv = (
            df.groupby(["canal_norm", "producto"])["venta_sin_impuestos"]
            .sum()
            .unstack(fill_value=0)
        )
        # Asegurar columnas en orden canónico
        for p in PRODUCT_ORDER:
            if p not in piv.columns:
                piv[p] = 0
        piv = piv.reindex(columns=PRODUCT_ORDER, fill_value=0)

        # Asegurar filas en orden canónico
        for c in CANAL_ORDER:
            if c not in piv.index:
                piv.loc[c] = 0
        piv = piv.reindex(CANAL_ORDER, fill_value=0)

        piv["Total"] = piv.sum(axis=1)
        totals = piv.sum(axis=0)
        totals.name = "Total"
        piv = pd.concat([piv, totals.to_frame().T])
        return piv

    # ------------------------------------------------------------------
    # Público: Top clientes
    # ------------------------------------------------------------------

    def get_top_clientes(self, mode: str = "anual") -> list:
        """Retorna lista de los N clientes con mayor venta en el periodo."""
        y, w = self.anio, self.semana
        if mode == "semanal":
            df = self._filter_period(y, w)
        else:
            df = self._filter_ytd(y, w)

        top = (
            df.groupby("cliente")["venta_sin_impuestos"]
            .sum()
            .nlargest(self.n_top_clientes)
            .index.tolist()
        )
        return top

    def get_detalle_clientes(self, clientes: list, mode: str = "anual") -> pd.DataFrame:
        """Tabla producto × cliente para los clientes indicados."""
        y, w = self.anio, self.semana
        if mode == "semanal":
            df = self._filter_period(y, w)
        else:
            df = self._filter_ytd(y, w)

        df_top = df[df["cliente"].isin(clientes)]
        piv = (
            df_top.groupby(["cliente", "producto"])["venta_sin_impuestos"]
            .sum()
            .unstack(fill_value=0)
        )
        for p in PRODUCT_ORDER:
            if p not in piv.columns:
                piv[p] = 0
        piv = piv.reindex(columns=PRODUCT_ORDER, fill_value=0)
        piv["Total"] = piv.sum(axis=1)
        piv = piv.sort_values("Total", ascending=False)
        return piv

    # ------------------------------------------------------------------
    # Público: Histórico mensual (para gráfica de barras apiladas + línea)
    # ------------------------------------------------------------------

    def get_historico_mensual(self) -> pd.DataFrame:
        """
        DataFrame: index = (año, mes), columnas = productos + Total.
        Solo incluye meses hasta la semana actual del año corriente.
        """
        y, w = self.anio, self.semana
        cur_fecha = self._filter_period(y, w)["fecha"].min()
        if pd.isna(cur_fecha):
            cur_mes = 12
        else:
            cur_mes = cur_fecha.month

        df_hist = self.df[
            ((self.df["anio_num"] == y - 1)) |
            ((self.df["anio_num"] == y) & (self.df["mes"] <= cur_mes))
        ]

        piv = (
            df_hist.groupby(["anio_num", "mes", "producto"])["venta_sin_impuestos"]
            .sum()
            .unstack(fill_value=0)
        )
        for p in PRODUCT_ORDER:
            if p not in piv.columns:
                piv[p] = 0
        piv = piv.reindex(columns=PRODUCT_ORDER, fill_value=0)
        piv["Total"] = piv.sum(axis=1)
        piv = piv.reset_index()
        piv["label"] = piv.apply(
            lambda r: datetime(int(r["anio_num"]), int(r["mes"]), 1).strftime("%b/%y"), axis=1
        )
        return piv

    # ------------------------------------------------------------------
    # Público: Serie semanal (8-12 semanas) para gráficas combo SKU/canal
    # ------------------------------------------------------------------

    def get_serie_semanal(
        self,
        n_semanas: int = 12,
        group_by: str = "producto",  # 'producto' | 'canal'
        filtro: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retorna ventas semanales de las últimas n_semanas.
        Si filtro != None, filtra por el producto o canal indicado.
        """
        y, w = self.anio, self.semana

        # Construir lista de (year, week) hacia atrás
        periodos = []
        cy, cw = y, w
        for _ in range(n_semanas):
            periodos.append((cy, cw))
            cy, cw = _prev_week(cy, cw)

        periodos = list(reversed(periodos))

        # Filtrar datos
        cond = pd.Series(False, index=self.df.index)
        for ay, aw in periodos:
            cond |= (self.df["anio_num"] == ay) & (self.df["semana_num"] == aw)
        df_sub = self.df[cond].copy()

        if filtro and group_by == "producto":
            df_sub = df_sub[df_sub["producto"] == filtro]
        elif filtro and group_by == "canal":
            df_sub = df_sub[df_sub["canal_norm"] == filtro]

        group_col = "producto" if group_by == "producto" else "canal_norm"

        piv = (
            df_sub.groupby(["anio_num", "semana_num", group_col])["venta_sin_impuestos"]
            .sum()
            .unstack(fill_value=0)
        )
        piv["Total"] = piv.sum(axis=1)
        piv = piv.reset_index()

        # Etiquetas de semana: "W30"
        piv["label"] = piv["semana_num"].apply(lambda x: f"W{int(x):02d}")

        return piv

    def get_serie_semanal_botellas(
        self,
        n_semanas: int = 12,
        group_by: str = "producto",
        filtro: Optional[str] = None,
    ) -> pd.DataFrame:
        """Igual que get_serie_semanal pero en botellas."""
        y, w = self.anio, self.semana
        periodos = []
        cy, cw = y, w
        for _ in range(n_semanas):
            periodos.append((cy, cw))
            cy, cw = _prev_week(cy, cw)
        periodos = list(reversed(periodos))

        cond = pd.Series(False, index=self.df.index)
        for ay, aw in periodos:
            cond |= (self.df["anio_num"] == ay) & (self.df["semana_num"] == aw)
        df_sub = self.df[cond].copy()

        if filtro and group_by == "producto":
            df_sub = df_sub[df_sub["producto"] == filtro]
        elif filtro and group_by == "canal":
            df_sub = df_sub[df_sub["canal_norm"] == filtro]

        group_col = "producto" if group_by == "producto" else "canal_norm"

        piv = (
            df_sub.groupby(["anio_num", "semana_num", group_col])["botellas"]
            .sum()
            .unstack(fill_value=0)
        )
        piv["Total"] = piv.sum(axis=1)
        piv = piv.reset_index()
        piv["label"] = piv["semana_num"].apply(lambda x: f"W{int(x):02d}")
        return piv

    def get_plan_semanal(
        self,
        n_semanas: int = 12,
        filtro_producto: Optional[str] = None,
        filtro_canal: Optional[str] = None,
    ) -> pd.DataFrame:
        """Plan semanal de ventas sin IVA para las últimas n semanas."""
        y, w = self.anio, self.semana
        periodos = []
        cy, cw = y, w
        for _ in range(n_semanas):
            periodos.append((cy, cw))
            cy, cw = _prev_week(cy, cw)
        periodos = list(reversed(periodos))

        cond = pd.Series(False, index=self.dfp.index)
        for ay, aw in periodos:
            cond |= (self.dfp["anio_num"] == ay) & (self.dfp["semana_num"] == aw)
        dfp_sub = self.dfp[cond].copy()

        if filtro_producto:
            dfp_sub = dfp_sub[dfp_sub["producto"] == filtro_producto]
        if filtro_canal:
            dfp_sub = dfp_sub[dfp_sub["canal_norm"] == filtro_canal]

        agg = dfp_sub.groupby(["anio_num", "semana_num"])["plan_venta_sin_impuestos"].sum().reset_index()
        agg["label"] = agg["semana_num"].apply(lambda x: f"W{int(x):02d}")
        return agg

    # ------------------------------------------------------------------
    # Público: Tabla comparativa WoW / MoM / YoY
    # ------------------------------------------------------------------

    def get_tabla_comparativa(self) -> Dict:
        """Retorna dict con todas las comparaciones de periodo."""
        return self.get_resumen_ejecutivo()

    # ------------------------------------------------------------------
    # Público: Análisis por producto (ranking + tendencia)
    # ------------------------------------------------------------------

    def get_ranking_productos(self, mode: str = "anual") -> pd.DataFrame:
        y, w = self.anio, self.semana
        if mode == "semanal":
            df = self._filter_period(y, w)
        else:
            df = self._filter_ytd(y, w)

        agg = (
            df.groupby("producto")
            .agg(
                ventas=("venta_sin_impuestos", "sum"),
                botellas=("botellas", "sum"),
                cajas=("cajas_9L", "sum"),
                margen=("margen_pesos", "sum"),
            )
            .reset_index()
        )
        agg["margen_pct"] = (agg["margen"] / agg["ventas"] * 100).fillna(0)
        agg["participacion_pct"] = (agg["ventas"] / agg["ventas"].sum() * 100).fillna(0)
        agg["producto_display"] = agg["producto"].map(PRODUCT_DISPLAY_NAMES).fillna(agg["producto"])

        # Orden canónico
        cat = pd.CategoricalDtype(PRODUCT_ORDER, ordered=True)
        agg["producto_cat"] = agg["producto"].astype(cat)
        agg = agg.sort_values("producto_cat").drop(columns=["producto_cat"])
        return agg

    # ------------------------------------------------------------------
    # Público: Análisis regional
    # ------------------------------------------------------------------

    def get_analisis_regional(self, mode: str = "anual") -> pd.DataFrame:
        y, w = self.anio, self.semana
        if mode == "semanal":
            df = self._filter_period(y, w)
        else:
            df = self._filter_ytd(y, w)

        agg = (
            df.groupby("region_o_estado")
            .agg(
                ventas=("venta_sin_impuestos", "sum"),
                botellas=("botellas", "sum"),
            )
            .reset_index()
            .sort_values("ventas", ascending=False)
        )
        agg["participacion_pct"] = (agg["ventas"] / agg["ventas"].sum() * 100).fillna(0)
        return agg

    # ------------------------------------------------------------------
    # Público: Tabla SKU × periodo (para páginas individuales del PDF)
    # ------------------------------------------------------------------

    def get_tabla_sku(self, producto: str) -> Dict:
        """
        Retorna KPIs de un SKU para: semana actual, semana anterior,
        año anterior (misma semana), plan, YTD, YTD año anterior.
        """
        y, w = self.anio, self.semana
        py, pw = _prev_week(y, w)
        ly, lyw = _same_week_prev_year(y, w)

        def kpis_sku(dfq):
            dfs = dfq[dfq["producto"] == producto]
            v = dfs["venta_sin_impuestos"].sum()
            b = dfs["botellas"].sum()
            c = dfs["cajas_9L"].sum()
            m = dfs["margen_pesos"].sum()
            mp = (m / v * 100) if v > 0 else 0
            t = (v / b) if b > 0 else 0
            return {"ventas": v, "botellas": b, "cajas": c,
                    "margen_pesos": m, "margen_pct": mp, "ticket": t}

        cur   = kpis_sku(self._filter_period(y, w))
        prev  = kpis_sku(self._filter_period(py, pw))
        lasty = kpis_sku(self._filter_period(ly, lyw))
        ytd   = kpis_sku(self._filter_ytd(y, w))
        ytd_ly= kpis_sku(self._filter_ytd(ly, lyw))

        # Plan semanal del SKU
        dfp_sku = self.dfp[
            (self.dfp["anio_num"] == y) &
            (self.dfp["semana_num"] == w) &
            (self.dfp["producto"] == producto)
        ]
        plan_v = dfp_sku["plan_venta_sin_impuestos"].sum()
        plan_b = dfp_sku["plan_botellas"].sum()

        return {
            "producto": producto,
            "semana_actual": cur,
            "semana_anterior": prev,
            "anio_anterior": lasty,
            "plan": {"ventas": plan_v, "botellas": plan_b},
            "ytd": ytd,
            "ytd_anio_anterior": ytd_ly,
        }

    # ------------------------------------------------------------------
    # Público: Oportunidades y riesgos (análisis automático)
    # ------------------------------------------------------------------

    def get_oportunidades_riesgos(self) -> list:
        """
        Genera lista automática de hallazgos: tipo, descripción, impacto, recomendación.
        """
        resumen = self.get_resumen_ejecutivo()
        rankings = self.get_ranking_productos("anual")
        items = []

        # WoW
        wow = resumen["vs_semana_anterior"]
        if wow["pct"] < -10:
            items.append({
                "hallazgo": f"Caída semanal del {abs(wow['pct']):.0f}% vs semana anterior",
                "tipo": "Riesgo",
                "impacto": f"${abs(wow['abs']):,.0f} MXN sin IVA",
                "recomendacion": "Revisar causa raíz: cliente, producto o región con mayor caída",
            })
        elif wow["pct"] > 10:
            items.append({
                "hallazgo": f"Crecimiento semanal del {wow['pct']:.0f}% vs semana anterior",
                "tipo": "Oportunidad",
                "impacto": f"${wow['abs']:,.0f} MXN adicionales",
                "recomendacion": "Identificar driver y replicar en otras regiones/canales",
            })

        # vs Plan
        vp = resumen["vs_plan"]
        if vp["pct"] < -5:
            items.append({
                "hallazgo": f"Ventas {abs(vp['pct']):.0f}% por debajo del plan",
                "tipo": "Riesgo",
                "impacto": f"${abs(vp['abs']):,.0f} MXN de brecha vs plan",
                "recomendacion": "Activar plan de recuperación en canales de mayor gap",
            })

        # YTD vs año anterior
        ytd_var = resumen["ytd_vs_ly"]
        if ytd_var["pct"] > 5:
            items.append({
                "hallazgo": f"YTD crece {ytd_var['pct']:.0f}% vs mismo período año anterior",
                "tipo": "Oportunidad",
                "impacto": f"${ytd_var['abs']:,.0f} MXN acumulados adicionales",
                "recomendacion": "Sostener ritmo; monitorear capacidad operativa",
            })
        elif ytd_var["pct"] < -5:
            items.append({
                "hallazgo": f"YTD cae {abs(ytd_var['pct']):.0f}% vs mismo período año anterior",
                "tipo": "Riesgo",
                "impacto": f"${abs(ytd_var['abs']):,.0f} MXN menos que el año anterior",
                "recomendacion": "Revisar estrategia de precio y mix de canal",
            })

        # Concentración de productos
        if not rankings.empty:
            top1 = rankings.iloc[0]
            if top1["participacion_pct"] > 50:
                items.append({
                    "hallazgo": f"{PRODUCT_DISPLAY_NAMES.get(top1['producto'], top1['producto'])} concentra "
                                f"{top1['participacion_pct']:.0f}% de las ventas",
                    "tipo": "Riesgo",
                    "impacto": "Alta dependencia de un solo SKU",
                    "recomendacion": "Diversificar mix impulsando Loco Ámbar y Loco Áureo",
                })

        # Si hay pocos hallazgos, agregar nota de mercado
        if len(items) < 3:
            items.append({
                "hallazgo": "Contexto de mercado no disponible en datos internos",
                "tipo": "Información",
                "impacto": "N/D",
                "recomendacion": "Complementar con datos de exportaciones CRT y precio de agave",
            })

        return items[:6]  # máximo 6 hallazgos

    # ------------------------------------------------------------------
    # Público: DataFrame completo para dashboard HTML
    # ------------------------------------------------------------------

    def get_dataframe_dashboard(self) -> pd.DataFrame:
        """Retorna el DataFrame enriquecido completo para el dashboard."""
        cols = [
            "semana_str", "fecha", "producto", "canal_norm",
            "cliente", "region_o_estado", "mes",
            "venta_sin_impuestos", "botellas", "cajas_9L",
            "margen_pesos", "margen_pct", "precio_unitario",
            "anio_num", "semana_num",
        ]
        df_out = self.df[cols].copy()
        df_out.columns = [
            "semana", "fecha", "producto", "canal",
            "cliente", "estado", "mes",
            "venta_sin_iva", "botellas", "cajas_9l",
            "margen_pesos", "margen_pct", "precio_unitario",
            "anio", "semana_num",
        ]
        df_out["producto_display"] = df_out["producto"].map(PRODUCT_DISPLAY_NAMES).fillna(df_out["producto"])
        return df_out

    # ------------------------------------------------------------------
    # Público: Comparativo custom entre dos periodos arbitrarios
    # ------------------------------------------------------------------

    def get_comparativo_custom(
        self,
        modo: str,              # 'semana' | 'mes' | 'anio'
        periodo_a: Dict,        # {'semana':30,'anio':2026} | {'mes':6,'anio':2026} | {'anio':2026}
        periodo_b: Dict,        # mismo esquema
    ) -> Dict:
        """
        Compara dos periodos arbitrarios y retorna un dict con:
          - kpis_a, kpis_b: métricas de cada periodo
          - variacion: diferencias absolutas y porcentuales
          - por_producto: DataFrame comparativo por SKU
          - por_canal: DataFrame comparativo por canal
          - por_cliente: DataFrame comparativo por cliente
          - labels: {'a': 'Semana 30-2026', 'b': 'Semana 25-2026'}

        modo = 'semana' : compara semanas ISO individuales
        modo = 'mes'    : compara meses completos
        modo = 'anio'   : compara años completos
        """
        # Filtrar periodo A
        df_a = self._filter_by_periodo(modo, periodo_a)
        df_b = self._filter_by_periodo(modo, periodo_b)

        kpis_a = self._kpis(df_a)
        kpis_b = self._kpis(df_b)

        # Variaciones
        def var(a_val, b_val):
            d = a_val - b_val
            p = (d / b_val * 100) if b_val != 0 else (100.0 if a_val > 0 else 0.0)
            return {"abs": d, "pct": p}

        variacion = {k: var(kpis_a[k], kpis_b[k]) for k in kpis_a}

        # Por producto
        prod_a = df_a.groupby("producto")["venta_sin_impuestos"].sum().rename("periodo_a")
        prod_b = df_b.groupby("producto")["venta_sin_impuestos"].sum().rename("periodo_b")
        por_producto = pd.concat([prod_a, prod_b], axis=1).fillna(0)
        por_producto["variacion_abs"] = por_producto["periodo_a"] - por_producto["periodo_b"]
        por_producto["variacion_pct"] = (
            (por_producto["variacion_abs"] / por_producto["periodo_b"]) * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)
        # Mantener orden canonico
        por_producto = por_producto.reindex(
            [p for p in PRODUCT_ORDER if p in por_producto.index]
        )

        # Por canal
        canal_a = df_a.groupby("canal_norm")["venta_sin_impuestos"].sum().rename("periodo_a")
        canal_b = df_b.groupby("canal_norm")["venta_sin_impuestos"].sum().rename("periodo_b")
        por_canal = pd.concat([canal_a, canal_b], axis=1).fillna(0)
        por_canal["variacion_abs"] = por_canal["periodo_a"] - por_canal["periodo_b"]
        por_canal["variacion_pct"] = (
            (por_canal["variacion_abs"] / por_canal["periodo_b"]) * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)
        por_canal = por_canal.reindex(
            [c for c in CANAL_ORDER if c in por_canal.index]
        )

        # Por cliente (top 10 combinado)
        top_cli = (
            pd.concat([df_a, df_b])
            .groupby("cliente")["venta_sin_impuestos"]
            .sum()
            .nlargest(10)
            .index
        )
        cli_a = df_a[df_a["cliente"].isin(top_cli)].groupby("cliente")["venta_sin_impuestos"].sum().rename("periodo_a")
        cli_b = df_b[df_b["cliente"].isin(top_cli)].groupby("cliente")["venta_sin_impuestos"].sum().rename("periodo_b")
        por_cliente = pd.concat([cli_a, cli_b], axis=1).fillna(0)
        por_cliente["variacion_abs"] = por_cliente["periodo_a"] - por_cliente["periodo_b"]
        por_cliente["variacion_pct"] = (
            (por_cliente["variacion_abs"] / por_cliente["periodo_b"]) * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)
        por_cliente = por_cliente.sort_values("periodo_a", ascending=False)

        # Etiquetas legibles
        labels = {
            "a": self._periodo_label(modo, periodo_a),
            "b": self._periodo_label(modo, periodo_b),
        }

        return {
            "modo": modo,
            "labels": labels,
            "kpis_a": kpis_a,
            "kpis_b": kpis_b,
            "variacion": variacion,
            "por_producto": por_producto,
            "por_canal": por_canal,
            "por_cliente": por_cliente,
        }

    def _filter_by_periodo(self, modo: str, periodo: Dict) -> pd.DataFrame:
        """Filtra el DataFrame según el modo y los parámetros del periodo."""
        df = self.df
        if modo == "semana":
            return df[
                (df["anio_num"] == periodo["anio"]) &
                (df["semana_num"] == periodo["semana"])
            ]
        elif modo == "mes":
            return df[
                (df["anio_num"] == periodo["anio"]) &
                (df["mes"] == periodo["mes"])
            ]
        elif modo == "anio":
            return df[df["anio_num"] == periodo["anio"]]
        else:
            raise ValueError(f"Modo no soportado: {modo}. Usa 'semana', 'mes' o 'anio'.")

    def _periodo_label(self, modo: str, periodo: Dict) -> str:
        """Genera etiqueta legible para un periodo."""
        MESES = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
        }
        if modo == "semana":
            return f"Semana {periodo['semana']:02d}-{periodo['anio']}"
        elif modo == "mes":
            mes_nombre = MESES.get(periodo["mes"], str(periodo["mes"]))
            return f"{mes_nombre}/{str(periodo['anio'])[2:]}"
        elif modo == "anio":
            return f"Anio {periodo['anio']}"
        return str(periodo)

    # ------------------------------------------------------------------
    # Público: Serie mensual por canal/producto (para el comparativo)
    # ------------------------------------------------------------------

    def get_serie_mensual(
        self,
        anio: Optional[int] = None,
        group_by: str = "producto",
        filtro: Optional[str] = None,
    ) -> pd.DataFrame:
        """Ventas mensuales del año especificado (o el año del reporte)."""
        anio = anio or self.anio
        df = self.df[self.df["anio_num"] == anio].copy()

        if filtro and group_by == "producto":
            df = df[df["producto"] == filtro]
        elif filtro and group_by == "canal":
            df = df[df["canal_norm"] == filtro]

        group_col = "producto" if group_by == "producto" else "canal_norm"
        piv = (
            df.groupby(["mes", group_col])["venta_sin_impuestos"]
            .sum()
            .unstack(fill_value=0)
        )
        piv["Total"] = piv.sum(axis=1)
        piv = piv.reset_index()
        MESES = {
            1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
            7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic",
        }
        piv["label"] = piv["mes"].map(MESES)
        return piv
