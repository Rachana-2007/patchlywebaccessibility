"""
Patchly - Image Alternative Text & Non-Text Content Inspector
Compliant with WCAG 2.1 Success Criterion 1.1.1 (Non-text Content - Level A)
"""

import os
import re
from typing import Dict, Any, Optional
from bs4 import Tag

# Common suspicious placeholder / filename patterns used mistakenly as alt text
GENERIC_PLACEHOLDER_PATTERNS = [
    r'^image\.(png|jpg|jpeg|gif|webp|svg)$',
    r'^img_\d+\.(png|jpg|jpeg)$',
    r'^picture\b',
    r'^photo\b',
    r'^graphic\b',
    r'^icon\b',
    r'^banner\b',
    r'^untitled\b',
    r'^\d+$',
    r'^\.+$',
    r'^logo\.(png|svg|jpg)$'
]

def is_suspicious_alt(alt_text: str) -> bool:
    """Returns True if the alt text appears to be a generic placeholder or raw filename."""
    cleaned = alt_text.strip().lower()
    for pattern in GENERIC_PLACEHOLDER_PATTERNS:
        if re.search(pattern, cleaned):
            return True
    return False

def generate_contextual_alt_fix(img_tag: Tag) -> str:
    """
    Infers an intelligent, descriptive suggestion for alt text based on
    surrounding context, parent tags, or src filename semantics.
    """
    src = img_tag.get('src', '')
    parent = img_tag.parent
    
    # Check parent heading or caption
    if parent:
        caption = parent.find(['figcaption', 'h1', 'h2', 'h3', 'h4', 'span'])
        if caption and caption.get_text(strip=True):
            clean_cap = caption.get_text(strip=True)[:60]
            return f"Illustration showing {clean_cap}"

    # Extract human readable keywords from filename
    if src:
        filename = os.path.splitext(os.path.basename(src.split('?')[0]))[0]
        # Replace hyphens, underscores, numbers
        words = re.sub(r'[-_0-9]+', ' ', filename).strip()
        if len(words) > 2 and not words.lower().startswith('img'):
            return f"Visual overview of {words.title()}"

    return "Descriptive summary of image content for screen readers"

def audit_image_tag(img_tag: Tag, index: int) -> Optional[Dict[str, Any]]:
    """
    Audits a single <img> tag for WCAG 1.1.1 compliance.
    Returns issue dict if violation found, else None.
    """
    has_alt = img_tag.has_attr('alt')
    alt_value = img_tag.get('alt', '')
    role = img_tag.get('role', '')
    aria_hidden = img_tag.get('aria-hidden', '')

    # 1. Marked as decorative explicitly
    if role == 'presentation' or aria_hidden == 'true':
        return None

    # 2. Case: Completely missing alt attribute
    if not has_alt:
        suggested = generate_contextual_alt_fix(img_tag)
        return {
            "rule_id": "image-alt-missing",
            "wcag_sc": "1.1.1 Non-text Content (Level A)",
            "severity": "CRITICAL",
            "title": "Missing Alternative Text Attribute",
            "element_tag": "img",
            "element_html": str(img_tag)[:180],
            "description": "Image is completely missing the 'alt' attribute. Screen reader users will hear raw URLs or filenames.",
            "quick_fix_code": f'<img src="{img_tag.get("src", "...")}" alt="{suggested}">',
            "suggested_action": f'Add alt="{suggested}" or alt="" if purely decorative.'
        }

    # 3. Case: Junk or placeholder alt text (e.g. "image.png")
    if is_suspicious_alt(alt_value):
        suggested = generate_contextual_alt_fix(img_tag)
        return {
            "rule_id": "image-alt-suspicious",
            "wcag_sc": "1.1.1 Non-text Content (Level A)",
            "severity": "SERIOUS",
            "title": "Non-Descriptive / Placeholder Alt Text",
            "element_tag": "img",
            "element_html": str(img_tag)[:180],
            "description": f'The alt text "{alt_value}" is uninformative and resembles a raw filename or placeholder.',
            "quick_fix_code": f'<img src="{img_tag.get("src", "...")}" alt="{suggested}">',
            "suggested_action": f'Replace "{alt_value}" with meaningful descriptive text.'
        }

    return None

def audit_svg_tag(svg_tag: Tag, index: int) -> Optional[Dict[str, Any]]:
    """
    Audits inline <svg> icons/graphics for accessible names or aria-hidden.
    """
    aria_hidden = svg_tag.get('aria-hidden', '')
    aria_label = svg_tag.get('aria-label', '')
    title_tag = svg_tag.find('title')
    role = svg_tag.get('role', '')

    # If hidden from assistive technologies, it's fine
    if aria_hidden == 'true':
        return None

    # If it lacks both title and aria-label
    if not aria_label and not (title_tag and title_tag.get_text(strip=True)):
        return {
            "rule_id": "svg-accessible-name",
            "wcag_sc": "1.1.1 Non-text Content (Level A)",
            "severity": "MODERATE",
            "title": "SVG Icon Missing Accessible Name or aria-hidden",
            "element_tag": "svg",
            "element_html": str(svg_tag)[:150] + "...",
            "description": "Inline SVG graphic has no <title>, aria-label, or aria-hidden attribute. Assistive technologies cannot determine its purpose.",
            "quick_fix_code": '<svg aria-hidden="true" ...> (if decorative) OR <svg aria-label="Icon description" ...>',
            "suggested_action": 'Add aria-hidden="true" if decorative, or add aria-label="Brand Icon" if informative.'
        }

    return None
