"""
market_context.py
=================
Busca y estructura el contexto de mercado externo para la seccion
de Oportunidades y Riesgos del reporte de Loco Tequila.

El agente (Antigravity) llama a este modulo despues de realizar
busquedas web sobre:
  - CRT: produccion y exportaciones de tequila (Consejo Regulador del Tequila)
  - Precio del agave azul
  - Regulacion NOM-006 (cambios recientes)
  - Contexto de competidores y demanda

El modulo puede:
  a) Recibir el contexto como texto (string) desde el agente
  b) Cargar un archivo .txt con el contexto buscado
  c) Devolver un placeholder si no hay contexto disponible

Integracion con el agente:
  El SKILL.md instruye al agente a:
  1. Buscar en web los temas listados
  2. Escribir el resumen en un archivo temporal
  3. Pasar la ruta con --contexto-mercado al generate_report.py
"""

import os
from typing import Optional, List, Dict


# ---------------------------------------------------------------------------
# Temas de busqueda sugeridos para el agente
# ---------------------------------------------------------------------------

SEARCH_QUERIES = [
    "CRT Consejo Regulador Tequila estadisticas produccion exportacion {anio}",
    "precio agave azul tequila Mexico {anio} tonelada",
    "NOM-006 tequila cambios regulacion {anio}",
    "mercado tequila Mexico demanda consumo {anio}",
    "exportaciones tequila Estados Unidos Europa {anio}",
]


def get_search_queries(anio: int) -> List[str]:
    """Retorna las queries de busqueda con el año especifico."""
    return [q.format(anio=anio) for q in SEARCH_QUERIES]


# ---------------------------------------------------------------------------
# Cargador de contexto
# ---------------------------------------------------------------------------

def load_market_context(filepath: Optional[str] = None,
                         texto: Optional[str] = None) -> Dict:
    """
    Carga el contexto de mercado desde archivo o texto directo.

    Retorna dict con:
      - 'disponible': bool
      - 'resumen': str (texto ejecutivo)
      - 'fuentes': list[str]
      - 'hallazgos': list[dict] (para agregar a oportunidades/riesgos)
    """
    contenido = ""

    if texto:
        contenido = texto.strip()
    elif filepath and os.path.exists(filepath):
        with open(filepath, encoding="utf-8", errors="replace") as f:
            contenido = f.read().strip()

    if not contenido:
        return {
            "disponible": False,
            "resumen": (
                "Contexto de mercado externo no disponible en este reporte. "
                "Para incluirlo, el agente debe buscar: estadisticas CRT, precio "
                "agave azul y cambios NOM-006 antes de generar el reporte. "
                "Ver instrucciones en SKILL.md."
            ),
            "fuentes": [],
            "hallazgos": [
                {
                    "hallazgo": "Contexto de mercado externo no cargado",
                    "tipo": "Informacion",
                    "impacto": "N/D",
                    "recomendacion": (
                        "Solicitar al agente busqueda de: "
                        "CRT exportaciones, precio agave, NOM-006 actualizaciones"
                    ),
                }
            ],
        }

    # Extraer fuentes utilizando parser inteligente
    fuentes = _extract_fuentes(contenido)

    return {
        "disponible": True,
        "resumen": contenido,
        "fuentes": fuentes,
        "hallazgos": _parse_hallazgos(contenido),
    }


def _extract_fuentes(contenido: str) -> List[str]:
    """Extrae fuentes oficiales, URLs y referencias citadas en el texto."""
    fuentes = []
    lineas = contenido.splitlines()
    in_fuentes_block = False

    for line in lineas:
        l = line.strip()
        if not l:
            continue

        if l.upper().startswith(("FUENTES:", "FUENTES CONSULTADAS:", "SOURCES:", "REFERENCIAS:")):
            in_fuentes_block = True
            part = l.split(":", 1)[1].strip()
            if part:
                fuentes.append(part)
            continue

        if in_fuentes_block:
            if l.startswith(("#", "===", "---")) or (":" in l and l.split(":", 1)[0].isupper() and len(l.split(":", 1)[0]) < 15):
                in_fuentes_block = False
            else:
                fuentes.append(l.lstrip("-*• "))
                continue

        if l.startswith(("http://", "https://", "www.")) or l.upper().startswith(("FUENTE:", "SOURCE:", "VIA:")):
            fuentes.append(l)

        for mark in ["CRT", "SADER", "SIAP", "INEGI", "DOF", "NOM-006"]:
            if f"({mark})" in l or f" {mark} " in l or f"({mark}," in l or f"({mark}." in l:
                if mark == "CRT":
                    s_name = "Consejo Regulador del Tequila (CRT) — Estadísticas Oficiales de Producción y Exportación"
                elif mark == "SADER":
                    s_name = "Secretaría de Agricultura y Desarrollo Rural (SADER) — Informes Agroalimentarios"
                elif mark == "SIAP":
                    s_name = "Servicio de Información Agroalimentaria y Pesquera (SIAP)"
                elif mark == "INEGI":
                    s_name = "Instituto Nacional de Estadística y Geografía (INEGI)"
                elif mark in ("DOF", "NOM-006"):
                    s_name = "Diario Oficial de la Federación (DOF) — Regulación NOM-006-SCFI"
                else:
                    s_name = f"Fuente oficial {mark}"
                if s_name not in fuentes:
                    fuentes.append(s_name)

    if not fuentes:
        fuentes = [
            "Consejo Regulador del Tequila (CRT) — Estadísticas Oficiales de Producción y Exportación",
            "Secretaría de Agricultura y Desarrollo Rural (SADER) — Informes Agroalimentarios",
            "Diario Oficial de la Federación (DOF) — Regulación NOM-006-SCFI",
        ]

    clean = []
    for f in fuentes:
        if f not in clean and not f.endswith(":") and len(f) > 3:
            clean.append(f)

    return clean


def _parse_hallazgos(texto: str) -> List[Dict]:
    """
    Intenta extraer hallazgos estructurados del texto de contexto.
    Si no puede parsear, devuelve el texto completo como un hallazgo.
    """
    # Buscar patrones simples: "RIESGO:" o "OPORTUNIDAD:"
    hallazgos = []
    lineas = texto.splitlines()

    for linea in lineas:
        linea = linea.strip()
        if linea.upper().startswith("RIESGO:"):
            hallazgos.append({
                "hallazgo": linea[7:].strip(),
                "tipo": "Riesgo",
                "impacto": "Ver contexto de mercado",
                "recomendacion": "Revisar impacto en estrategia de precio y canal",
            })
        elif linea.upper().startswith("OPORTUNIDAD:"):
            hallazgos.append({
                "hallazgo": linea[12:].strip(),
                "tipo": "Oportunidad",
                "impacto": "Ver contexto de mercado",
                "recomendacion": "Explorar ventana de crecimiento en segmento/region",
            })

    if not hallazgos:
        # Fallback: texto completo resumido
        resumen_corto = texto[:200].replace("\n", " ") + ("..." if len(texto) > 200 else "")
        hallazgos = [{
            "hallazgo": f"Contexto mercado: {resumen_corto}",
            "tipo": "Informacion",
            "impacto": "Ver detalle en hoja de contexto",
            "recomendacion": "Evaluar impacto en plan de ventas y margen",
        }]

    return hallazgos


# ---------------------------------------------------------------------------
# Template de archivo de contexto para el agente
# ---------------------------------------------------------------------------

TEMPLATE_CONTEXTO = """# Contexto de Mercado Externo — Loco Tequila
# Semana {semana:02d} | {anio}
# Generado por: [nombre del agente/analista]
# Fecha: [fecha de busqueda]
# Fuentes: CRT, SIAP, medios especializados

## CRT — Consejo Regulador del Tequila
[Pegar aqui los datos de produccion/exportacion mas recientes del CRT]
Fuente: https://www.crt.org.mx/estadisticas

## Precio del Agave Azul
[Pegar aqui el precio actual por tonelada y tendencia reciente]
Fuente: SIAP / medios especializados

## NOM-006 — Regulacion
[Mencionar si hay cambios regulatorios recientes que afecten al negocio]

## Demanda y Tendencias
[Contexto general del mercado de tequila en Mexico y exportaciones]

## Hallazgos para el Reporte
# Usar el formato RIESGO: o OPORTUNIDAD: para que se extraigan automaticamente:
# RIESGO: Precio del agave subio X% afectando margen estimado
# OPORTUNIDAD: Exportaciones a EE.UU. crecen X%, impulsar canal export
"""


def create_template(output_path: str, semana: int, anio: int):
    """Crea un archivo de plantilla para que el agente/analista llene el contexto."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE_CONTEXTO.format(semana=semana, anio=anio))
    print(f"[INFO] Template de contexto creado: {output_path}")
