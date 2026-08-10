"""
logo_processor.py
=================
Procesa el logo SVG de Loco Tequila para:
  1. Generar version blanca (todos los fills -> #FFFFFF, bg transparente)
  2. Convertir SVG a PNG (para ReportLab PDF)
  3. Devolver SVG inline para el HTML
Esto es necesario para que el agente pueda asociarlo a 
los diferentes documentos existentes en el PDF y en HMTL.

El SVG original usa ~330 clases CSS con variantes de rojo/maroon.
La version blanca reemplaza todos los fills de color con #FFFFFF y
elimina cualquier background rect solido.

Dependencias (en orden de preferencia para conversion PNG):
  - cairosvg  (pip install cairosvg)    -> mejor calidad
  - svglib + reportlab                  -> alternativa sin cairo
  - Pillow (solo si hay PNG embebido)   -> fallback
"""

import os
import re
import io
import base64
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SVG_ORIGINAL = os.path.join(ASSETS_DIR, "Loco_Tequila_Logo.svg")
SVG_WHITE    = os.path.join(ASSETS_DIR, "Loco_Tequila_Logo_white.svg")
PNG_WHITE    = os.path.join(ASSETS_DIR, "Loco_Tequila_Logo_white.png")

# Tamanio del logo en el PDF (cm)
LOGO_W_CM = 5.5
LOGO_H_CM = 2.9

# ---------------------------------------------------------------------------
# Conversion SVG -> version blanca
# ---------------------------------------------------------------------------

def make_white_svg(svg_path: str = SVG_ORIGINAL,
                   out_path: str = SVG_WHITE) -> str:
    """
    Lee el SVG original y genera una version con todos los fills en blanco.
    Retorna la ruta al SVG blanco generado.
    """
    if os.path.exists(out_path):
        return out_path  # ya existe, no regenerar

    with open(svg_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    # 1. Reemplazar todos los fill:#XXXXXX dentro de <style> -> #FFFFFF
    #    excepto fill:none y fill-rule (estos no son colores)
    def _replace_fill_in_style(m):
        text = m.group(0)
        # fill:#xxxxxx -> fill:#FFFFFF (solo hex de color)
        text = re.sub(r'fill:(#[0-9A-Fa-f]{3,6})\b', 'fill:#FFFFFF', text)
        return text

    # Procesar el bloque <style>...</style>
    content = re.sub(
        r'<style[^>]*>.*?</style>',
        _replace_fill_in_style,
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    # 2. Reemplazar fills inline en elementos (fill="#XXXXXX")
    content = re.sub(
        r'fill="(#[0-9A-Fa-f]{3,6})"',
        'fill="#FFFFFF"',
        content,
        flags=re.IGNORECASE
    )

    # 3. Reemplazar fill con color en style inline: style="...fill:#xxxxxx..."
    content = re.sub(
        r'(style="[^"]*fill:)(#[0-9A-Fa-f]{3,6})',
        r'\g<1>#FFFFFF',
        content,
        flags=re.IGNORECASE
    )

    # 4. Eliminar background rect solido (si existe un rect que cubra todo)
    # Buscar rects con fill que no sea none en posicion 0,0
    content = re.sub(
        r'<rect[^>]*x=["\']0["\'][^>]*y=["\']0["\'][^>]*/?>',
        '',
        content,
        flags=re.IGNORECASE
    )

    # 5. Asegurar que el SVG tenga fondo transparente
    # Agregar background-color:transparent al SVG raiz si no tiene
    content = content.replace(
        'style="enable-background:new',
        'style="background-color:transparent;enable-background:new'
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[LOGO] SVG blanco generado: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Conversion SVG -> PNG
# ---------------------------------------------------------------------------

def svg_to_png(svg_path: str, out_path: str,
               width_px: int = 550, height_px: int = 290) -> Optional[str]:
    """
    Convierte un SVG a PNG.
    Intenta primero cairosvg (necesita DLL nativa), luego svglib+PIL.
    Retorna la ruta al PNG o None si no se pudo.
    """
    if os.path.exists(out_path):
        return out_path

    # Intento 1: cairosvg (requiere libcairo-2.dll nativa en Windows)
    try:
        import cairosvg
        cairosvg.svg2png(
            url=svg_path,
            write_to=out_path,
            output_width=width_px,
            output_height=height_px,
            background_color="transparent",
        )
        print(f"[LOGO] PNG generado con cairosvg: {out_path}")
        return out_path
    except Exception:
        pass  # silencioso — fallback a svglib

    # Intento 2: svglib + renderPM con backend PIL (no necesita rlPyCairo)
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        import reportlab.graphics.renderPM as rpm
        drawing = svg2rlg(svg_path)
        if drawing:
            # Escalar
            sx = width_px / drawing.width if drawing.width else 1
            sy = height_px / drawing.height if drawing.height else 1
            scale = min(sx, sy)
            drawing.width  = drawing.width * scale
            drawing.height = drawing.height * scale
            drawing.transform = (scale, 0, 0, scale, 0, 0)
            # Intentar con backend PIL explícito
            rpm.drawToFile(drawing, out_path, fmt="PNG", dpi=150)
            print(f"[LOGO] PNG generado con svglib/PIL: {out_path}")
            return out_path
    except Exception as e:
        print(f"[LOGO] PNG fallido: {e}")

    print("[LOGO] No se pudo convertir SVG a PNG. Usando SVG inline en el PDF.")
    return None


def get_logo_drawing_for_pdf(svg_path: str):
    """
    Retorna un ReportLab Drawing del logo (via svglib) para incrustar
    directamente en el canvas con renderPDF.draw(). NO requiere Cairo DLL.
    Retorna None si svglib no puede procesar el SVG.
    """
    try:
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(svg_path)
        return drawing
    except Exception as e:
        print(f"[LOGO] svglib drawing error: {e}")
        return None


# ---------------------------------------------------------------------------
# Obtener logo para PDF (retorna ruta a PNG o None)
# ---------------------------------------------------------------------------

def get_logo_for_pdf(svg_path: Optional[str] = None,
                     force_regen: bool = False) -> Optional[str]:
    """
    Pipeline completo para el PDF:
      1. Generar SVG blanco
      2. Convertir a PNG
      3. Retornar ruta al PNG (o None si no se pudo)
    """
    if svg_path is None:
        svg_path = SVG_ORIGINAL

    if not os.path.exists(svg_path):
        print(f"[LOGO] Archivo no encontrado: {svg_path}")
        return None

    if force_regen:
        for p in [SVG_WHITE, PNG_WHITE]:
            if os.path.exists(p):
                os.remove(p)

    # Generar SVG blanco
    white_svg = make_white_svg(svg_path, SVG_WHITE)

    # Convertir a PNG
    png_path = svg_to_png(white_svg, PNG_WHITE)

    return png_path


# ---------------------------------------------------------------------------
# Obtener logo para HTML (retorna SVG inline en base64 o como texto)
# ---------------------------------------------------------------------------

def get_logo_for_html(svg_path: Optional[str] = None,
                       mode: str = "inline") -> str:
    """
    Retorna el logo para incrustar en HTML.

    mode='inline'   -> texto SVG directo (modifica fills a blanco)
    mode='base64'   -> data URI base64 del SVG blanco
    mode='img_tag'  -> <img src="data:..."> tag completo con width/height
    """
    if svg_path is None:
        svg_path = SVG_ORIGINAL

    if not os.path.exists(svg_path):
        return _fallback_svg_text()

    # Generar SVG blanco (reutiliza si ya existe)
    white_svg_path = make_white_svg(svg_path, SVG_WHITE)

    with open(white_svg_path, encoding="utf-8", errors="replace") as f:
        svg_content = f.read()

    if mode == "inline":
        # Limpiar el XML header para embedding directo
        svg_content = re.sub(r'<\?xml[^>]*\?>', '', svg_content).strip()
        svg_content = re.sub(r'<!DOCTYPE[^>]*>', '', svg_content).strip()
        return svg_content

    elif mode in ("base64", "img_tag"):
        b64 = base64.b64encode(svg_content.encode("utf-8")).decode("ascii")
        data_uri = f"data:image/svg+xml;base64,{b64}"
        if mode == "base64":
            return data_uri
        else:
            return (f'<img src="{data_uri}" '
                    f'alt="Loco Tequila Logo" '
                    f'style="height:48px;width:auto;object-fit:contain;" />')

    return svg_content


def _fallback_svg_text() -> str:
    """SVG placeholder si no se encuentra el logo."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 60" '
        'width="200" height="60">'
        '<text x="10" y="40" font-family="Arial" font-size="28" '
        'font-weight="900" fill="white" letter-spacing="4">LOCO</text>'
        '<text x="10" y="58" font-family="Arial" font-size="11" '
        'fill="white" letter-spacing="8" opacity="0.8">TEQUILA</text>'
        '</svg>'
    )


# ---------------------------------------------------------------------------
# CLI de prueba
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Procesando logo Loco Tequila ===")
    png = get_logo_for_pdf(force_regen=True)
    print(f"PNG para PDF: {png}")

    html_tag = get_logo_for_html(mode="img_tag")
    print(f"HTML img tag (primeros 100 chars): {html_tag[:100]}...")
