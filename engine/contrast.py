"""
Patchly - Color Contrast Calculation & Optimization Engine
Compliant with WCAG 2.1 Success Criterion 1.4.3 (Contrast Minimum - Level AA)
"""

import re
import math
from typing import Tuple, Optional, Dict, Any

def parse_color(color_str: str) -> Optional[Tuple[int, int, int, float]]:
    """
    Parses hex (#rgb, #rrggbb), rgb(), or rgba() strings into (r, g, b, alpha).
    Returns None if color format is unparseable.
    """
    if not color_str:
        return None
    
    color_str = color_str.strip().lower()

    # Named standard colors lookup
    NAMED_COLORS = {
        'white': (255, 255, 255, 1.0),
        'black': (0, 0, 0, 1.0),
        'transparent': (0, 0, 0, 0.0),
        'gray': (128, 128, 128, 1.0),
        'grey': (128, 128, 128, 1.0),
        'red': (255, 0, 0, 1.0),
        'green': (0, 128, 0, 1.0),
        'blue': (0, 0, 255, 1.0),
        'yellow': (255, 255, 0, 1.0),
    }

    if color_str in NAMED_COLORS:
        return NAMED_COLORS[color_str]

    # Hex: #rrggbb or #rgb
    if color_str.startswith('#'):
        hex_val = color_str.lstrip('#')
        if len(hex_val) == 3:
            r = int(hex_val[0] * 2, 16)
            g = int(hex_val[1] * 2, 16)
            b = int(hex_val[2] * 2, 16)
            return (r, g, b, 1.0)
        elif len(hex_val) == 6:
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            return (r, g, b, 1.0)
        elif len(hex_val) == 8:
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            a = round(int(hex_val[6:8], 16) / 255.0, 2)
            return (r, g, b, a)

    # rgb(...) or rgba(...)
    rgb_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d\.]+))?\s*\)', color_str)
    if rgb_match:
        r = int(rgb_match.group(1))
        g = int(rgb_match.group(2))
        b = int(rgb_match.group(3))
        a = float(rgb_match.group(4)) if rgb_match.group(4) is not None else 1.0
        return (r, g, b, a)

    return None

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB integers (0-255) to hex #rrggbb string."""
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"

def channel_luminance(channel: int) -> float:
    """Calculates sRGB linear channel luminance according to WCAG 2.1 formula."""
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else math.pow((c + 0.055) / 1.055, 2.4)

def calculate_relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculates the relative luminance (L) of a color (0.0 for black to 1.0 for white).
    Formula: L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    """
    r, g, b = rgb[0], rgb[1], rgb[2]
    return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)

def calculate_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """
    Calculates the WCAG contrast ratio between two RGB colors:
    CR = (L1 + 0.05) / (L2 + 0.05), where L1 is the lighter color.
    """
    l1 = calculate_relative_luminance(rgb1)
    l2 = calculate_relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)

def blend_colors(fg: Tuple[int, int, int, float], bg: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Alpha blends a semi-transparent foreground color over an opaque background."""
    alpha = fg[3]
    if alpha >= 1.0:
        return (fg[0], fg[1], fg[2])
    r = round((1 - alpha) * bg[0] + alpha * fg[0])
    g = round((1 - alpha) * bg[1] + alpha * fg[1])
    b = round((1 - alpha) * bg[2] + alpha * fg[2])
    return (r, g, b)

def find_optimal_accessible_color(fg_rgb: Tuple[int, int, int], 
                                  bg_rgb: Tuple[int, int, int], 
                                  target_ratio: float = 4.5) -> str:
    """
    Algorithmic optimization: searches the color space along the luminance gradient
    to find the closest visually harmonious color that meets or exceeds the target contrast ratio.
    """
    current_ratio = calculate_contrast_ratio(fg_rgb, bg_rgb)
    if current_ratio >= target_ratio:
        return rgb_to_hex(*fg_rgb)

    bg_lum = calculate_relative_luminance(bg_rgb)
    
    # Decide whether to darken or lighten based on background luminance
    should_darken = bg_lum > 0.5

    r, g, b = fg_rgb
    for step in range(1, 256):
        factor = (255 - step) / 255.0 if should_darken else (step / 255.0)
        
        if should_darken:
            candidate_rgb = (int(r * factor), int(g * factor), int(b * factor))
        else:
            candidate_rgb = (
                int(r + (255 - r) * (1 - factor)),
                int(g + (255 - g) * (1 - factor)),
                int(b + (255 - b) * (1 - factor))
            )
            
        ratio = calculate_contrast_ratio(candidate_rgb, bg_rgb)
        if ratio >= target_ratio:
            return rgb_to_hex(*candidate_rgb)

    # Fallback to pure black or pure white
    return "#000000" if should_darken else "#ffffff"

def analyze_contrast(fg_str: str, bg_str: str = "#ffffff", is_large_text: bool = False) -> Dict[str, Any]:
    """
    Performs full WCAG 2.1 AA & AAA contrast analysis and generates quick-fix recommendations.
    """
    target_aa = 3.0 if is_large_text else 4.5
    target_aaa = 4.5 if is_large_text else 7.0

    fg_parsed = parse_color(fg_str) or (51, 65, 85, 1.0)
    bg_parsed = parse_color(bg_str) or (255, 255, 255, 1.0)

    # Blend foreground over background if alpha < 1
    effective_bg = (bg_parsed[0], bg_parsed[1], bg_parsed[2])
    effective_fg = blend_colors(fg_parsed, effective_bg)

    ratio = calculate_contrast_ratio(effective_fg, effective_bg)
    passes_aa = ratio >= target_aa
    passes_aaa = ratio >= target_aaa

    suggested_fg_hex = None
    if not passes_aa:
        suggested_fg_hex = find_optimal_accessible_color(effective_fg, effective_bg, target_aa)

    return {
        "fg_hex": rgb_to_hex(*effective_fg),
        "bg_hex": rgb_to_hex(*effective_bg),
        "contrast_ratio": ratio,
        "required_ratio": target_aa,
        "passes_aa": passes_aa,
        "passes_aaa": passes_aaa,
        "suggested_color": suggested_fg_hex
    }
