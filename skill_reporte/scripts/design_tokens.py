"""
design_tokens.py
================
Tokens de diseño del sistema visual "Reporte Ventas y Margen — Loco Tequila".
Fuente: designs/Design.md
"""

# ---------------------------------------------------------------------------
# 1. Paleta de marca / estructura
# ---------------------------------------------------------------------------
BRAND_MAROON        = "#6E1E28"
BRAND_MAROON_DEEP   = "#5A1822"
HEADER_TEXT         = "#FFFFFF"
SECTION_TITLE       = "#6E1E28"
SECTION_SUBTITLE    = "#8A8A8A"
PAGE_BG             = "#FFFFFF"
RULE_LINE           = "#D9D9D9"

# ---------------------------------------------------------------------------
# 2. Colores de PRODUCTO — respetar este orden en TODA gráfica y tabla
# ---------------------------------------------------------------------------
PRODUCT_COLORS = {
    "Loco Blanco":      "#9B1C31",   # rojo vino / crimson
    "Puro Corazon":     "#9A9A9A",   # gris medio
    "Loco Ambar":       "#A96C43",   # café/ámbar
    "Loco 269":         "#1F1F1F",   # negro
    "Loco Aureo":       "#1F6E6E",   # teal/verde azulado
    "Loco 200":         "#F2C14E",   # amarillo/dorado
}

# Orden canónico de productos (para índices de tabla y gráfica)
PRODUCT_ORDER = [
    "Loco Blanco",
    "Puro Corazon",
    "Loco Ambar",
    "Loco 269",
    "Loco Aureo",
    "Loco 200",
]

# Nombres de display en español (como aparecen en el PDF)
PRODUCT_DISPLAY_NAMES = {
    "Loco Blanco":  "Loco Blanco",
    "Puro Corazon": "Puro Corazón",
    "Loco Ambar":   "Loco Ámbar",
    "Loco 269":     "Loco 269",
    "Loco Aureo":   "Loco Áureo",
    "Loco 200":     "Loco 200",
}

# ---------------------------------------------------------------------------
# 3. Colores de CANAL
# ---------------------------------------------------------------------------
CANAL_COLORS = {
    "Off Trade":                    "#1F3B5C",   # azul marino
    "Centros de Consumo (On Trade)":"#7A1E2B",   # guinda
    "Venta Directa":                "#E8A33D",   # naranja/ámbar
    "eCommerce":                    "#5A5A5A",   # gris oscuro
    "Familia y Amigos":             "#2E6E6E",   # teal
}

CANAL_ORDER = [
    "Off Trade",
    "Centros de Consumo (On Trade)",
    "Venta Directa",
    "eCommerce",
    "Familia y Amigos",
]

# Mapeo de valores en el CSV → nombre canónico de canal
CANAL_MAPPING = {
    "Off Trade":                      "Off Trade",
    "Venta Directa":                  "Venta Directa",
    "Centros de Consumo (On Trade)":  "Centros de Consumo (On Trade)",
    "On Trade":                       "Centros de Consumo (On Trade)",
    "eCommerce":                      "eCommerce",
    "E-Commerce":                     "eCommerce",
    "Familia y Amigos":               "Familia y Amigos",
    "Venta Empleado":                 "Familia y Amigos",
    "Amigos y Familiares":            "Familia y Amigos",
}

# ---------------------------------------------------------------------------
# 4. Colores de elementos de gráfica y estados
# ---------------------------------------------------------------------------
CHART_PLAN_LINE       = "#E23B2E"   # línea roja "Plan de ventas"
CHART_LASTYEAR_AREA   = "#E7D6A6"   # área "Año Pasado" (khaki claro)
CHART_GRID            = "#E2E2E2"   # cuadrícula horizontal / ejes
CHART_LABEL           = "#333333"   # etiquetas de dato sobre barras
HIGHLIGHT_CREAM       = "#FBF3DD"   # fila/columna resaltada
PILL_BG               = "#F6E2E2"   # píldora rosada de porcentaje
PILL_TEXT             = "#9B1C31"   # texto % dentro de la píldora
POS_VALUE             = "#333333"   # variación positiva / neutra
NEG_VALUE             = "#E23B2E"   # variación negativa (rojo)

# ---------------------------------------------------------------------------
# 5. Tipografía (nombres para matplotlib)
# ---------------------------------------------------------------------------
FONT_FAMILY = "DejaVu Sans"         # fallback seguro; en PDF se registra Poppins si disponible

# ---------------------------------------------------------------------------
# 6. Helpers de formato numérico (MXN)
# ---------------------------------------------------------------------------

def fmt_currency(value, decimals: int = 0) -> str:
    """Formatea un valor como moneda MXN: $1,889"""
    if value is None or (isinstance(value, float) and value != value):
        return "$0"
    try:
        if decimals == 0:
            return f"${int(round(value)):,}"
        else:
            return f"${value:,.{decimals}f}"
    except (TypeError, ValueError):
        return "$0"


def fmt_pct(value, decimals: int = 0) -> str:
    """Formatea un porcentaje: 47%"""
    if value is None or (isinstance(value, float) and value != value):
        return "0%"
    try:
        return f"{value:.{decimals}f}%"
    except (TypeError, ValueError):
        return "0%"


def fmt_int(value) -> str:
    """Formatea un entero con separador de miles: 2,829"""
    if value is None or (isinstance(value, float) and value != value):
        return "0"
    try:
        return f"{int(round(value)):,}"
    except (TypeError, ValueError):
        return "0"


def fmt_ticket(value) -> str:
    """Ticket promedio con 1 decimal: $1.4"""
    if value is None or (isinstance(value, float) and value != value):
        return "$0.0"
    try:
        return f"${value:.1f}"
    except (TypeError, ValueError):
        return "$0.0"


def hex_to_rgb(hex_color: str):
    """Convierte HEX a tuple (r, g, b) en escala 0-1 para matplotlib."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def hex_to_rgb255(hex_color: str):
    """Convierte HEX a tuple (r, g, b) en escala 0-255 para ReportLab."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# 7. Dimensiones de página (A4 landscape para el PDF)
# ---------------------------------------------------------------------------
PAGE_WIDTH_PT  = 841.89   # puntos (A4 landscape)
PAGE_HEIGHT_PT = 595.28   # puntos
MARGIN_PT      = 28.35    # ~1 cm

HEADER_HEIGHT_PT = 64     # banda maroon
FOOTER_HEIGHT_PT = 18
