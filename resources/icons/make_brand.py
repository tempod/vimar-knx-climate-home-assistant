"""Genera il marchio di Vimar KNX Climate in versione chiara e scura.

Il disegno è originale e non riproduce alcun marchio di terzi. Richiama i due
mondi per forma, non per citazione:

  * la placca quadrata a spigoli molto raccordati dei comandi da parete,
  * l'arco graduato di un termostato con il cursore di setpoint,
  * la linea bus con tre nodi, il modo convenzionale di disegnare una dorsale.
"""

from __future__ import annotations

import math

# --- Geometria condivisa ---------------------------------------------------
SIZE = 512
PLATE = dict(x=24, y=24, w=464, h=464, r=112)
CX, CY, R = 256, 232, 134
ARC_START, ARC_END = 135, 45          # apertura di 90° in basso
VALUE_END = 318                        # posizione del cursore di setpoint
STROKE = 30

BUS_Y = 408
BUS_X0, BUS_X1 = 148, 364
NODE_R = 23


def point(angle: float, radius: float = R) -> tuple[float, float]:
    """Punto sulla circonferenza, angolo in gradi, y crescente verso il basso."""
    rad = math.radians(angle)
    return CX + radius * math.cos(rad), CY + radius * math.sin(rad)


def arc(start: float, end: float) -> str:
    """Percorso SVG di un arco che procede in senso orario."""
    sweep = (end - start) % 360
    x0, y0 = point(start)
    x1, y1 = point(end)
    large = 1 if sweep > 180 else 0
    return f"M {x0:.2f} {y0:.2f} A {R} {R} 0 {large} 1 {x1:.2f} {y1:.2f}"


# --- Palette ---------------------------------------------------------------
LIGHT = dict(
    plate_from="#26314A",
    plate_to="#141A26",
    bezel="rgba(255,255,255,0.10)",
    track="#3B465C",
    knob="#FFFFFF",
    knob_ring="#141A26",
    glass="#FFFFFF",
    glass_opacity="0.94",
    mercury="#FF7A3D",
    bus="#35D07F",
    node_core="#141A26",
    text="#1B2430",
)

DARK = dict(
    plate_from="#FFFFFF",
    plate_to="#E6ECF2",
    bezel="rgba(0,0,0,0.08)",
    track="#C6D1DE",
    knob="#1B2430",
    knob_ring="#FFFFFF",
    glass="#2A3646",
    glass_opacity="1",
    mercury="#FF6A28",
    bus="#12A05B",
    node_core="#FFFFFF",
    text="#F2F5F8",
)

ARC_COOL, ARC_WARM = "#52B9FF", "#FF8A45"


def mark(c: dict, prefix: str) -> str:
    """Il solo simbolo, in un viewBox 512x512."""
    kx, ky = point(VALUE_END)
    return f"""
  <defs>
    <linearGradient id="{prefix}plate" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{c['plate_from']}"/>
      <stop offset="1" stop-color="{c['plate_to']}"/>
    </linearGradient>
    <linearGradient id="{prefix}arc" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0" stop-color="{ARC_COOL}"/>
      <stop offset="1" stop-color="{ARC_WARM}"/>
    </linearGradient>
  </defs>

  <rect x="{PLATE['x']}" y="{PLATE['y']}" width="{PLATE['w']}" height="{PLATE['h']}"
        rx="{PLATE['r']}" fill="url(#{prefix}plate)"/>
  <rect x="{PLATE['x'] + 14}" y="{PLATE['y'] + 14}"
        width="{PLATE['w'] - 28}" height="{PLATE['h'] - 28}"
        rx="{PLATE['r'] - 14}" fill="none" stroke="{c['bezel']}" stroke-width="4"/>

  <path d="{arc(ARC_START, ARC_END)}" fill="none" stroke="{c['track']}"
        stroke-width="{STROKE}" stroke-linecap="round"/>
  <path d="{arc(ARC_START, VALUE_END)}" fill="none" stroke="url(#{prefix}arc)"
        stroke-width="{STROKE}" stroke-linecap="round"/>
  <circle cx="{kx:.2f}" cy="{ky:.2f}" r="19" fill="{c['knob']}"
          stroke="{c['knob_ring']}" stroke-width="5"/>

  <g fill="{c['glass']}" opacity="{c['glass_opacity']}">
    <rect x="{CX - 14}" y="{CY - 78}" width="28" height="108" rx="14"/>
    <circle cx="{CX}" cy="{CY + 48}" r="35"/>
  </g>
  <g fill="{c['mercury']}">
    <rect x="{CX - 7}" y="{CY - 42}" width="14" height="82" rx="7"/>
    <circle cx="{CX}" cy="{CY + 48}" r="22"/>
  </g>

  <line x1="{BUS_X0}" y1="{BUS_Y}" x2="{BUS_X1}" y2="{BUS_Y}"
        stroke="{c['bus']}" stroke-width="13" stroke-linecap="round"/>
  <g fill="{c['bus']}">
    <circle cx="{BUS_X0}" cy="{BUS_Y}" r="{NODE_R}"/>
    <circle cx="{CX}" cy="{BUS_Y}" r="{NODE_R}"/>
    <circle cx="{BUS_X1}" cy="{BUS_Y}" r="{NODE_R}"/>
  </g>
  <g fill="{c['node_core']}">
    <circle cx="{BUS_X0}" cy="{BUS_Y}" r="8"/>
    <circle cx="{CX}" cy="{BUS_Y}" r="8"/>
    <circle cx="{BUS_X1}" cy="{BUS_Y}" r="8"/>
  </g>"""


def icon_svg(c: dict, prefix: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
        f'width="{SIZE}" height="{SIZE}">{mark(c, prefix)}\n</svg>\n'
    )


def logo_svg(c: dict, prefix: str) -> str:
    """Simbolo più nome del progetto, su una riga."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1220 512" width="1220" height="512">
  <g>{mark(c, prefix)}
  </g>
  <text x="556" y="238" font-family="Carlito, DejaVu Sans, sans-serif"
        font-size="104" font-weight="700" fill="{c['text']}">Vimar KNX</text>
  <text x="556" y="350" font-family="Carlito, DejaVu Sans, sans-serif"
        font-size="104" font-weight="300" fill="{c['text']}" opacity="0.82">Climate</text>
</svg>
"""


if __name__ == "__main__":
    import pathlib

    # Gli SVG vengono scritti accanto a questo script, qualunque sia la
    # directory da cui lo si lancia.
    out = pathlib.Path(__file__).resolve().parent
    for name, svg in (
        ("icon.svg", icon_svg(LIGHT, "l")),
        ("dark_icon.svg", icon_svg(DARK, "d")),
        ("logo.svg", logo_svg(LIGHT, "l")),
        ("dark_logo.svg", logo_svg(DARK, "d")),
    ):
        (out / name).write_text(svg)
        print("scritto", out / name)
