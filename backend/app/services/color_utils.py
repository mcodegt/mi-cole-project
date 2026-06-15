from __future__ import annotations

import re
from typing import Optional

_HEX_RE = re.compile(r"^#([0-9A-Fa-f]{6})$")


def parse_hex_color(value: str) -> Optional[tuple[int, int, int]]:
    match = _HEX_RE.match(value.strip())
    if not match:
        return None
    raw = match.group(1)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def relative_luminance(hex_color: str) -> Optional[float]:
    rgb = parse_hex_color(hex_color)
    if rgb is None:
        return None

    def channel(value: int) -> float:
        s = value / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def suggest_text_color_for_background(hex_color: str) -> str:
    """Contraste legible sobre el color de fondo del sidebar."""
    lum = relative_luminance(hex_color)
    if lum is None:
        return "#f8fafc"
    return "#0f172a" if lum > 0.179 else "#f8fafc"
