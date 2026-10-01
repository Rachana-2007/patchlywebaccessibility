"""
Patchly - Main Accessibility Scanner Coordinator
Orchestrates WCAG 2.1 Principles 1, 2, and 3 Auditing:
- Principle 1: Perceivable (Text Alternatives, Media, Adaptable, Distinguishable)
- Principle 2: Operable (Keyboard, Enough Time, Seizures, Navigable, Input Modalities)
- Principle 3: Understandable (Readable, Predictable, Input Assistance)
Note: Robust guidelines (Principle 4) are strictly excluded per design criteria.
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
import requests

from engine.contrast import analyze_contrast
from engine.alt_text import audit_image_tag, audit_svg_tag
from engine.video_captions import audit_video_tag
from engine.keyboard_nav import (
    audit_focus_styling,
    audit_interactive_elements,
    audit_tabindex_order,
    audit_form_controls,
    audit_heading_hierarchy,
    audit_link_context,
    audit_bypass_blocks,
    audit_page_title,
    audit_button_labels,
    audit_target_size,
    audit_autoplay_and_refresh,
    audit_flicker_tags,
    audit_orientation_and_viewport,
    audit_input_purpose,
    audit_use_of_color,
    audit_page_language,
    audit_auto_submit,
    audit_target_blank,
    audit_required_fields
)

def build_css_selector(tag: Tag) -> str:
    """Generates an accurate, unique CSS selector to target the element in the DOM."""
    if not tag or not hasattr(tag, 'name'):
        return "body"
        
    tag_id = tag.get('id')
    if tag_id:
        return f"#{tag_id}"

    classes = tag.get('class')
    if classes and isinstance(classes, list):
        valid_classes = [c for c in classes if not c.startswith('patchly')]
        if valid_classes:
            return f"{tag.name}.{'.'.join(valid_classes[:2])}"

    parent = tag.parent
    if parent and parent.name != '[document]':
        siblings = [s for s in parent.find_all(tag.name, recursive=False)]
        if len(siblings) > 1:
            idx = siblings.index(tag) + 1
            return f"{tag.name}:nth-of-type({idx})"
            
    return tag.name

def audit_element_contrast(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 1.4.3 Contrast (Minimum) (Level AA) - Perceivable
    Analyzes color contrast on elements with inline styles or color properties.
    """
    issues = []
    styled_elements = soup.find_all(style=True)

    color_regex = re.compile(r'(?:^|;)\s*color\s*:\s*([^;]+)', re.IGNORECASE)
    bg_regex = re.compile(r'(?:^|;)\s*background(?:-color)?\s*:\s*([^;]+)', re.IGNORECASE)

    for el in styled_elements:
        style_str = el.get('style', '')
        color_match = color_regex.search(style_str)
        bg_match = bg_regex.search(style_str)

        fg_color = color_match.group(1).strip() if color_match else None
        
        if fg_color and not fg_color.startswith('var('):
            bg_color = bg_match.group(1).strip() if bg_match else None
            curr = el.parent
            while not bg_color and curr and hasattr(curr, 'get'):
                parent_style = curr.get('style', '')
                p_bg = bg_regex.search(parent_style)
                if p_bg:
                    bg_color = p_bg.group(1).strip()
                    break
                curr = curr.parent

            if not bg_color or bg_color.startswith('var(') or 'gradient' in bg_color:
                bg_color = "#ffffff"

            result = analyze_contrast(fg_color, bg_color)
            if not result['passes_aa']:
                text_snip = el.get_text(strip=True)[:35] or "Text element"
                issues.append({
                    "rule_id": "color-contrast-low",
                    "principle": "Perceivable",
                    "wcag_sc": "1.4.3 Contrast (Minimum) (Level AA)",
                    "severity": "SERIOUS" if result['contrast_ratio'] < 3.0 else "MODERATE",
                    "title": f"Low Color Contrast ({result['contrast_ratio']}:1 vs 4.5:1 AA)",
                    "element_tag": el.name,
                    "element_html": str(el)[:160],
                    "element_text": text_snip,
                    "target_selector": build_css_selector(el),
                    "description": (
                        f"Text '{text_snip}' has a contrast ratio of {result['contrast_ratio']}:1 "
                        f"(Color: {result['fg_hex']}, Background: {result['bg_hex']}). "
                        f"WCAG AA requires at least 4.5:1 for regular text."
                    ),
                    "quick_fix_code": (
                        f"/* Fix: Update text color to meet WCAG AA 4.5:1 ratio */\n"
                        f"color: {result['suggested_color']}; /* Verified Contrast Ratio >= 4.5:1 */"
                    ),
                    "suggested_action": f"Change color to {result['suggested_color']} to ensure readability for people with low vision."
                })

    return issues

def scan_html(html_content: str, source_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Main scanner coordinator. Evaluates HTML against WCAG Principles 1, 2, and 3.
    Explicitly excludes Principle 4 (Robust).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    all_issues = []

    # --- PRINCIPLE 1: PERCEIVABLE ---
    # 1.1 Text Alternatives
    images = soup.find_all('img')
    for idx, img in enumerate(images):
        issue = audit_image_tag(img, idx)
        if issue:
            issue["principle"] = "Perceivable"
            issue["target_selector"] = build_css_selector(img)
            all_issues.append(issue)

    svgs = soup.find_all('svg')
    for idx, svg in enumerate(svgs):
        issue = audit_svg_tag(svg, idx)
        if issue:
            issue["principle"] = "Perceivable"
            issue["target_selector"] = build_css_selector(svg)
            all_issues.append(issue)

    # 1.2 Time-based Media
    videos = soup.find_all('video')
    for idx, vid in enumerate(videos):
        issue = audit_video_tag(vid, idx)
        if issue:
            issue["principle"] = "Perceivable"
            issue["target_selector"] = build_css_selector(vid)
            all_issues.append(issue)

    # 1.3 Adaptable
    all_issues.extend(audit_form_controls(soup))
    all_issues.extend(audit_heading_hierarchy(soup))
    all_issues.extend(audit_orientation_and_viewport(soup))
    all_issues.extend(audit_input_purpose(soup))

    # 1.4 Distinguishable
    all_issues.extend(audit_element_contrast(soup))
    all_issues.extend(audit_use_of_color(soup))

    # --- PRINCIPLE 2: OPERABLE ---
    # 2.1 Keyboard Accessible
    focus_issues = audit_focus_styling(html_content)
    all_issues.extend(focus_issues)

    interactive_issues = audit_interactive_elements(soup)
    for issue in interactive_issues:
        tag = soup.find(issue["element_tag"], string=lambda t: t and issue.get("element_text", "") in t)
        if tag:
            issue["target_selector"] = build_css_selector(tag)
        all_issues.append(issue)

    # 2.2 Enough Time
    all_issues.extend(audit_autoplay_and_refresh(soup, html_content))

    # 2.3 Seizures
    all_issues.extend(audit_flicker_tags(soup))

    # 2.4 Navigable
    all_issues.extend(audit_tabindex_order(soup))
    all_issues.extend(audit_bypass_blocks(soup))
    all_issues.extend(audit_page_title(soup))
    all_issues.extend(audit_link_context(soup))
    all_issues.extend(audit_button_labels(soup))

    # 2.5 Input Modalities
    all_issues.extend(audit_target_size(soup))

    # --- PRINCIPLE 3: UNDERSTANDABLE ---
    # 3.1 Readable
    all_issues.extend(audit_page_language(soup))

    # 3.2 Predictable
    all_issues.extend(audit_auto_submit(soup))
    all_issues.extend(audit_target_blank(soup))

    # 3.3 Input Assistance
    all_issues.extend(audit_required_fields(soup))

    # --- EXCLUDE PRINCIPLE 4 ROBUST ---
    # Filter out any issues tagged as Robust if any exist
    filtered_issues = [i for i in all_issues if i.get("principle") != "Robust"]

    # Assign sequential flag numbers (#1, #2, ...)
    for idx, issue in enumerate(filtered_issues, start=1):
        issue["flag_id"] = idx
        issue["flag_badge"] = f"#{idx}"

    # Aggregate metrics
    severity_counts = {"CRITICAL": 0, "SERIOUS": 0, "MODERATE": 0, "MINOR": 0}
    principle_counts = {"Perceivable": 0, "Operable": 0, "Understandable": 0}

    for issue in filtered_issues:
        sev = issue.get("severity", "MODERATE")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        prn = issue.get("principle", "Perceivable")
        principle_counts[prn] = principle_counts.get(prn, 0) + 1

    return {
        "success": True,
        "source": source_url or "Direct HTML Upload",
        "total_flags": len(filtered_issues),
        "severity_summary": severity_counts,
        "principle_summary": principle_counts,
        "issues": filtered_issues
    }

def scan_url(url: str) -> Dict[str, Any]:
    """Fetches a live webpage URL and runs the scan."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Patchly-Accessibility-Bot/1.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        return scan_html(response.text, source_url=url)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch URL: {str(e)}",
            "total_flags": 0,
            "issues": []
        }
