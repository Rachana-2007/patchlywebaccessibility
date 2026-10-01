"""
Patchly - WCAG 2.1 Principles 1, 2, and 3 Audit Engine
Compliant with:
- Principle 1: Perceivable (1.1, 1.2, 1.3, 1.4)
- Principle 2: Operable (2.1, 2.2, 2.3, 2.4, 2.5)
- Principle 3: Understandable (3.1, 3.2, 3.3)
(Principle 4 Robust is intentionally excluded per design criteria)
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag

AMBIGUOUS_LINK_TEXTS = {
    'click here', 'click this', 'here', 'more', 'read more', 'learn more', 
    'link', 'go', 'view', 'continue', 'details'
}

# --------------------------------------------------------------------------
# PRINCIPLE 2: OPERABLE
# --------------------------------------------------------------------------

def audit_focus_styling(html_content: str) -> List[Dict[str, Any]]:
    """
    WCAG 2.4.7 Focus Visible (Level AA)
    Scans CSS for outline: none / 0 on :focus without replacement styling.
    """
    issues = []
    focus_outline_pattern = re.compile(
        r'([^{}]*?:focus[^{}]*?)\{\s*([^}]*?outline\s*:\s*(?:none|0)[^}]*?)\}', 
        re.IGNORECASE | re.DOTALL
    )

    matches = focus_outline_pattern.findall(html_content)
    for selector, body in matches:
        clean_selector = selector.strip().replace('\n', ' ')
        issues.append({
            "rule_id": "focus-visible-suppressed",
            "principle": "Operable",
            "wcag_sc": "2.4.7 Focus Visible (Level AA)",
            "severity": "CRITICAL",
            "title": "Visible Keyboard Focus Indicator Suppressed",
            "element_tag": "style",
            "element_html": f"{clean_selector} {{ {body.strip()} }}",
            "description": f"CSS rule '{clean_selector}' explicitly removes keyboard focus outlines (outline: none). Sighted keyboard users cannot tell which control is active.",
            "quick_fix_code": (
                f"/* Fix: Provide a clear high-contrast focus indicator */\n"
                f"{clean_selector} {{\n"
                f"  outline: 3px solid #4f46e5 !important;\n"
                f"  outline-offset: 2px !important;\n"
                f"}}"
            ),
            "suggested_action": "Never remove focus outlines without providing a high-contrast replacement focus ring."
        })

    return issues

def audit_interactive_elements(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.1.1 Keyboard (Level A)
    Detects non-semantic clickable elements (div, span, section) without keyboard hooks.
    """
    issues = []
    clickable_tags = soup.find_all(['div', 'span', 'p', 'i', 'section', 'article'])

    for el in clickable_tags:
        has_onclick = el.has_attr('onclick')
        style = el.get('style', '').lower()
        has_pointer_cursor = 'cursor: pointer' in style or 'cursor:pointer' in style
        role = el.get('role', '')
        tabindex = el.get('tabindex', None)

        if has_onclick or (has_pointer_cursor and el.get_text(strip=True)):
            is_accessible_button = role in ['button', 'link'] and tabindex is not None
            if not is_accessible_button:
                text_preview = el.get_text(strip=True)[:40] or "interactive element"
                issues.append({
                    "rule_id": "keyboard-clickable-div",
                    "principle": "Operable",
                    "wcag_sc": "2.1.1 Keyboard (Level A)",
                    "severity": "CRITICAL",
                    "title": "Interactive Element Inaccessible via Keyboard",
                    "element_tag": el.name,
                    "element_html": str(el)[:160],
                    "element_text": text_preview,
                    "description": f"Clickable <{el.name}> ('{text_preview}') cannot be focused or activated using Tab/Enter/Space keys.",
                    "quick_fix_code": (
                        f"<!-- Fix Option 1 (Recommended): Use native button -->\n"
                        f'<button type="button" class="{el.get("class", [""])[0]}">\n'
                        f'  {text_preview}\n'
                        f'</button>\n\n'
                        f'<!-- Fix Option 2: Add keyboard ARIA attributes -->\n'
                        f'<{el.name} role="button" tabindex="0" onkeydown="if(event.key===\'Enter\'||event.key===\' \') {{ this.click(); }}">'
                    ),
                    "suggested_action": "Use native <button> or add role='button', tabindex='0', and Enter/Space event handlers."
                })

    return issues

def audit_tabindex_order(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.4.3 Focus Order (Level A)
    Flags elements using positive tabindex (tabindex > 0).
    """
    issues = []
    elements_with_tabindex = soup.find_all(attrs={"tabindex": True})

    for el in elements_with_tabindex:
        try:
            val = int(el.get('tabindex'))
            if val > 0:
                issues.append({
                    "rule_id": "tabindex-positive-order",
                    "principle": "Operable",
                    "wcag_sc": "2.4.3 Focus Order (Level A)",
                    "severity": "SERIOUS",
                    "title": "Positive Tabindex Disrupts Focus Flow",
                    "element_tag": el.name,
                    "element_html": str(el)[:160],
                    "description": f"Element uses tabindex='{val}'. Positive tabindex disrupts natural document tab order for keyboard users.",
                    "quick_fix_code": f'<!-- Fix: Set tabindex="0" or remove attribute -->\n<{el.name} tabindex="0">',
                    "suggested_action": "Remove positive tabindex or set tabindex='0' to preserve natural DOM order."
                })
        except ValueError:
            pass

    return issues

def audit_bypass_blocks(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.4.1 Bypass Blocks (Level A)
    Checks for presence of skip navigation link or <main> landmark.
    """
    issues = []
    skip_link = soup.find('a', href=lambda h: h and h.startswith('#'))
    has_skip = False
    if skip_link:
        txt = skip_link.get_text(strip=True).lower()
        if 'skip' in txt or 'main' in txt or 'content' in txt:
            has_skip = True

    has_main_landmark = soup.find('main') is not None or soup.find(attrs={"role": "main"}) is not None

    if not (has_skip or has_main_landmark):
        issues.append({
            "rule_id": "skip-link-missing",
            "principle": "Operable",
            "wcag_sc": "2.4.1 Bypass Blocks (Level A)",
            "severity": "SERIOUS",
            "title": "Missing Skip Navigation Link or Main Landmark",
            "element_tag": "body",
            "element_html": "<body>...",
            "description": "Page lacks a 'Skip to main content' link or <main> landmark. Keyboard users must tab through all navigation items on every page load.",
            "quick_fix_code": (
                f'<!-- Add at top of <body> -->\n'
                f'<a href="#main-content" class="skip-link">Skip to main content</a>\n\n'
                f'<!-- Wrap main body content -->\n'
                f'<main id="main-content">\n  ...\n</main>'
            ),
            "suggested_action": "Add a skip link at top of body and wrap main page content in <main id='main-content'>."
        })

    return issues

def audit_page_title(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.4.2 Page Titled (Level A)
    Checks if page has a valid, non-empty <title>.
    """
    issues = []
    title_tag = soup.find('title')
    title_text = title_tag.get_text(strip=True) if title_tag else ""

    if not title_tag or not title_text:
        issues.append({
            "rule_id": "page-title-missing",
            "principle": "Operable",
            "wcag_sc": "2.4.2 Page Titled (Level A)",
            "severity": "CRITICAL",
            "title": "Missing or Empty Page <title> Element",
            "element_tag": "head",
            "element_html": "<head>...</head>",
            "description": "Document is missing a <title> tag in <head>. Screen readers rely on page titles to orient users when switching tabs.",
            "quick_fix_code": '<head>\n  <title>Descriptive Page Title - Company Name</title>\n</head>',
            "suggested_action": "Include a succinct, descriptive <title> inside <head>."
        })

    return issues

def audit_link_context(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.4.4 Link Purpose (In Context) (Level A)
    Detects vague/ambiguous link texts like 'click here' or 'read more'.
    """
    issues = []
    links = soup.find_all('a')

    for a in links:
        text = a.get_text(strip=True).lower()
        if text in AMBIGUOUS_LINK_TEXTS:
            issues.append({
                "rule_id": "link-non-descriptive",
                "principle": "Operable",
                "wcag_sc": "2.4.4 Link Purpose (In Context) (Level A)",
                "severity": "MODERATE",
                "title": f"Ambiguous Link Text ('{text}')",
                "element_tag": "a",
                "element_html": str(a)[:140],
                "description": f"Link uses ambiguous text '{text}'. Screen reader users navigating a link list cannot determine the target destination.",
                "quick_fix_code": f'<!-- Fix: Make link text self-descriptive -->\n<a href="{a.get("href", "#")}">View 2026 Accessibility Benchmark Report</a>',
                "suggested_action": "Replace vague phrases like 'click here' with clear, descriptive destination labels."
            })

    return issues

def audit_button_labels(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.4.6 Headings and Labels (Level AA) & 1.1.1
    Checks for empty or icon-only buttons without text or aria-label.
    """
    issues = []
    buttons = soup.find_all('button')

    for btn in buttons:
        text = btn.get_text(strip=True)
        aria_label = btn.get('aria-label', '').strip()
        aria_labelledby = btn.get('aria-labelledby', '').strip()
        
        if not (text or aria_label or aria_labelledby):
            issues.append({
                "rule_id": "button-empty-label",
                "principle": "Operable",
                "wcag_sc": "2.4.6 Headings and Labels & 1.1.1",
                "severity": "CRITICAL",
                "title": "Button Lacks Accessible Label or Text",
                "element_tag": "button",
                "element_html": str(btn)[:160],
                "description": "Button contains no visible text or aria-label attribute. Screen readers announce this as 'unlabelled button'.",
                "quick_fix_code": f'<button type="button" aria-label="Search records">\n  <svg ...></svg>\n</button>',
                "suggested_action": "Add visible text inside the button or provide an aria-label attribute."
            })

    return issues

def audit_target_size(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.5.8 Target Size (Minimum) (Level AA - WCAG 2.2 / 2.1)
    Checks for inline styles setting touch targets under 24px x 24px.
    """
    issues = []
    interactive = soup.find_all(['button', 'a', 'input'])

    for el in interactive:
        style = el.get('style', '').lower()
        width_match = re.search(r'width\s*:\s*(\d+)px', style)
        height_match = re.search(r'height\s*:\s*(\d+)px', style)

        if width_match or height_match:
            w = int(width_match.group(1)) if width_match else 44
            h = int(height_match.group(1)) if height_match else 44
            if w < 24 or h < 24:
                issues.append({
                    "rule_id": "target-size-small",
                    "principle": "Operable",
                    "wcag_sc": "2.5.8 Target Size (Minimum) (Level AA)",
                    "severity": "MODERATE",
                    "title": f"Touch Target Size Below 24x24px ({w}x{h}px)",
                    "element_tag": el.name,
                    "element_html": str(el)[:160],
                    "description": f"Interactive control target size is {w}x{h}px. Users with motor impairment or touch screens cannot tap it reliably.",
                    "quick_fix_code": f'/* Ensure minimum touch target size */\nmin-width: 24px;\nmin-height: 24px;\npadding: 8px 12px;',
                    "suggested_action": "Increase target dimensions to at least 24px by 24px with adequate padding."
                })

    return issues

def audit_autoplay_and_refresh(soup: BeautifulSoup, html_content: str) -> List[Dict[str, Any]]:
    """
    WCAG 2.2.2 Pause, Stop, Hide (Level A)
    Checks for auto-playing media without controls and meta-refresh tags.
    """
    issues = []

    # Meta refresh check
    meta_refresh = soup.find('meta', attrs={"http-equiv": re.compile(r'refresh', re.I)})
    if meta_refresh:
        content = meta_refresh.get('content', '')
        issues.append({
            "rule_id": "meta-refresh-redirect",
            "principle": "Operable",
            "wcag_sc": "2.2.2 Pause, Stop, Hide (Level A)",
            "severity": "SERIOUS",
            "title": "Automated Meta-Refresh Page Reload Enabled",
            "element_tag": "meta",
            "element_html": str(meta_refresh),
            "description": f"Meta refresh ('{content}') reloads or redirects the page automatically without user control, interrupting reading.",
            "quick_fix_code": '<!-- Remove <meta http-equiv="refresh"> and handle updates dynamically via JS with user pause controls -->',
            "suggested_action": "Remove meta refresh tags and allow users to request page updates manually."
        })

    # Autoplay videos without controls
    videos = soup.find_all('video')
    for vid in videos:
        if vid.has_attr('autoplay') and not vid.has_attr('controls'):
            issues.append({
                "rule_id": "media-autoplay-uncontrolled",
                "principle": "Operable",
                "wcag_sc": "2.2.2 Pause, Stop, Hide (Level A)",
                "severity": "CRITICAL",
                "title": "Autoplay Video Missing Pause/Stop Controls",
                "element_tag": "video",
                "element_html": str(vid)[:160],
                "description": "Video autoplays automatically without visible user controls to pause or stop playback.",
                "quick_fix_code": '<video autoplay muted controls>\n  <source ...>\n</video>',
                "suggested_action": "Add the 'controls' attribute or provide a accessible custom play/pause button."
            })

    return issues

def audit_flicker_tags(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 2.3.1 Three Flashes or Below Threshold (Level A)
    Detects deprecated <marquee> and <blink> tags.
    """
    issues = []
    flicker_tags = soup.find_all(['marquee', 'blink'])
    for tag in flicker_tags:
        issues.append({
            "rule_id": "deprecated-flicker-tag",
            "principle": "Operable",
            "wcag_sc": "2.3.1 Three Flashes or Below Threshold (Level A)",
            "severity": "CRITICAL",
            "title": f"Deprecated Flashing/Scrolling <{tag.name}> Tag Used",
            "element_tag": tag.name,
            "element_html": str(tag)[:160],
            "description": f"The <{tag.name}> element causes constant motion/scrolling that triggers vestibular disorders and concentration issues.",
            "quick_fix_code": '<!-- Replace <marquee> with static semantic layout and CSS animations with prefers-reduced-motion -->',
            "suggested_action": "Remove <marquee> / <blink> tags and use static text with accessible CSS."
        })
    return issues


# --------------------------------------------------------------------------
# PRINCIPLE 1: PERCEIVABLE
# --------------------------------------------------------------------------

def audit_orientation_and_viewport(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 1.3.4 Orientation & 1.4.4 Resize Text (Level AA)
    Checks for user-scalable=no or maximum-scale=1 in viewport meta tag.
    """
    issues = []
    meta = soup.find('meta', attrs={"name": "viewport"})
    if meta:
        content = meta.get('content', '').lower()
        if 'user-scalable=no' in content or 'maximum-scale=1' in content:
            issues.append({
                "rule_id": "viewport-zoom-disabled",
                "principle": "Perceivable",
                "wcag_sc": "1.3.4 Orientation & 1.4.4 Resize Text (Level AA)",
                "severity": "CRITICAL",
                "title": "Pinch-to-Zoom Disabled in Viewport Meta Tag",
                "element_tag": "meta",
                "element_html": str(meta),
                "description": "Viewport meta tag disables zoom (user-scalable=no or maximum-scale=1). Low-vision users cannot magnify text on mobile devices.",
                "quick_fix_code": '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                "suggested_action": "Remove user-scalable=no and maximum-scale=1 from the viewport meta tag."
            })
    return issues

def audit_input_purpose(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 1.3.5 Identify Input Purpose (Level AA)
    Checks if form inputs collecting user personal info lack autocomplete attributes.
    """
    issues = []
    inputs = soup.find_all('input')
    for inp in inputs:
        name_or_id = (inp.get('name', '') + ' ' + inp.get('id', '') + ' ' + inp.get('type', '')).lower()
        has_autocomplete = inp.has_attr('autocomplete')

        # Target common personal fields
        if any(keyword in name_or_id for keyword in ['email', 'phone', 'tel', 'name', 'password', 'address']):
            if not has_autocomplete:
                issues.append({
                    "rule_id": "form-missing-autocomplete",
                    "principle": "Perceivable",
                    "wcag_sc": "1.3.5 Identify Input Purpose (Level AA)",
                    "severity": "MODERATE",
                    "title": "Input Field Missing 'autocomplete' Attribute",
                    "element_tag": "input",
                    "element_html": str(inp)[:160],
                    "description": f"Field '{inp.get('name') or inp.get('id') or 'input'}' collects personal data but lacks autocomplete. Assistive tech cannot autofill fields.",
                    "quick_fix_code": f'<{inp.name} id="{inp.get("id", "field")}" autocomplete="email">',
                    "suggested_action": "Add appropriate autocomplete attributes (e.g. autocomplete='email', 'given-name', 'tel')."
                })
    return issues

def audit_form_controls(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 1.3.1 Info and Relationships (Level A)
    Checks that <input>, <select>, <textarea> controls have corresponding <label for="..."> or aria-label.
    """
    issues = []
    inputs = soup.find_all(['input', 'select', 'textarea'])

    for inp in inputs:
        inp_type = inp.get('type', 'text').lower()
        if inp_type in ['hidden', 'submit', 'button', 'reset', 'image']:
            continue

        inp_id = inp.get('id', '')
        aria_label = inp.get('aria-label', '')
        aria_labelledby = inp.get('aria-labelledby', '')

        wrapped_in_label = inp.find_parent('label') is not None

        has_for_label = False
        if inp_id:
            matching_label = soup.find('label', attrs={'for': inp_id})
            if matching_label and matching_label.get_text(strip=True):
                has_for_label = True

        if not (wrapped_in_label or has_for_label or aria_label or aria_labelledby):
            issues.append({
                "rule_id": "form-missing-label",
                "principle": "Perceivable",
                "wcag_sc": "1.3.1 Info and Relationships (Level A)",
                "severity": "CRITICAL",
                "title": "Form Field Lacks Associated <label>",
                "element_tag": inp.name,
                "element_html": str(inp)[:160],
                "description": f"Input field (id='{inp_id or 'none'}') lacks a programmatic label. Screen reader users hear no description.",
                "quick_fix_code": (
                    f'<label for="{inp_id or "field_id"}">Full Name</label>\n'
                    f'<{inp.name} id="{inp_id or "field_id"}" type="{inp_type}">'
                ),
                "suggested_action": f"Add an associated <label for='{inp_id or 'field_id'}'> or add aria-label='...'."
            })

    return issues

def audit_heading_hierarchy(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 1.3.1 Info and Relationships (Level A)
    Audits heading sequence for missing h1 or skipped levels.
    """
    issues = []
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    if not soup.find('h1'):
        issues.append({
            "rule_id": "heading-missing-h1",
            "principle": "Perceivable",
            "wcag_sc": "1.3.1 Info and Relationships (Level A)",
            "severity": "SERIOUS",
            "title": "Document Missing Main <h1> Heading",
            "element_tag": "body",
            "element_html": "<body>...",
            "description": "Page has no <h1> element. Screen readers use <h1> as the primary page topic indicator.",
            "quick_fix_code": '<h1>Main Section Topic Title</h1>',
            "suggested_action": "Ensure every document has exactly one primary <h1> heading."
        })

    last_level = 0
    for h in headings:
        level = int(h.name[1])
        if last_level > 0 and level > (last_level + 1):
            issues.append({
                "rule_id": "heading-order-skipped",
                "principle": "Perceivable",
                "wcag_sc": "1.3.1 Info and Relationships (Level A)",
                "severity": "MODERATE",
                "title": f"Skipped Heading Level (<h{last_level}> &rarr; <h{level}>)",
                "element_tag": h.name,
                "element_html": str(h)[:140],
                "description": f"Heading <{h.name}> skips intermediate heading levels directly after <h{last_level}>.",
                "quick_fix_code": f'<h{last_level + 1}>{h.get_text(strip=True)}</h{last_level + 1}>',
                "suggested_action": f"Change <{h.name}> to <h{last_level + 1}> or insert appropriate parent headings."
            })
        last_level = level

    return issues

def audit_use_of_color(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 1.4.1 Use of Color (Level A)
    Checks inline links within text paragraphs that lack underline or border.
    """
    issues = []
    paragraphs = soup.find_all(['p', 'span', 'li'])
    for p in paragraphs:
        links = p.find_all('a')
        for a in links:
            style = a.get('style', '').lower()
            if 'text-decoration: none' in style or 'text-decoration:none' in style:
                issues.append({
                    "rule_id": "color-only-link",
                    "principle": "Perceivable",
                    "wcag_sc": "1.4.1 Use of Color (Level A)",
                    "severity": "SERIOUS",
                    "title": "Inline Text Link Relies Solely on Color",
                    "element_tag": "a",
                    "element_html": str(a)[:160],
                    "description": "Inline link removes default underline styling (text-decoration: none). Color-blind users cannot identify links within paragraph text.",
                    "quick_fix_code": '/* Keep default underline for inline links */\na {\n  text-decoration: underline;\n  color: #4338ca;\n}',
                    "suggested_action": "Do not remove underlines from inline text links, or add a distinct icon indicator."
                })
    return issues


# --------------------------------------------------------------------------
# PRINCIPLE 3: UNDERSTANDABLE
# --------------------------------------------------------------------------

def audit_page_language(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 3.1.1 Language of Page (Level A)
    Checks if <html> has a valid lang attribute.
    """
    issues = []
    html_tag = soup.find('html')
    lang = html_tag.get('lang', '').strip() if html_tag else ""

    if not html_tag or not lang:
        issues.append({
            "rule_id": "html-lang-missing",
            "principle": "Understandable",
            "wcag_sc": "3.1.1 Language of Page (Level A)",
            "severity": "CRITICAL",
            "title": "Missing 'lang' Attribute on <html> Element",
            "element_tag": "html",
            "element_html": "<html>",
            "description": "The <html> element is missing the lang attribute (e.g. lang='en'). Screen readers cannot select correct text-to-speech pronunciation engines.",
            "quick_fix_code": '<html lang="en">',
            "suggested_action": "Add lang='en' (or target language code) to the <html> root element."
        })
    return issues

def audit_auto_submit(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 3.2.2 On Input (Level A)
    Checks for form controls that auto-submit on change without warning.
    """
    issues = []
    selects = soup.find_all(['select', 'input'])
    for sel in selects:
        onchange = sel.get('onchange', '').lower()
        if 'submit' in onchange or 'location.href' in onchange:
            issues.append({
                "rule_id": "form-auto-submit",
                "principle": "Understandable",
                "wcag_sc": "3.2.2 On Input (Level A)",
                "severity": "SERIOUS",
                "title": "Form Control Triggers Automatic Context Change",
                "element_tag": sel.name,
                "element_html": str(sel)[:160],
                "description": f"Form control has onchange='{onchange}'. Auto-submitting on change confuses screen reader users by changing context unexpectedly.",
                "quick_fix_code": '<!-- Remove auto-submit onchange and provide explicit Submit button -->\n<button type="submit">Apply Selection</button>',
                "suggested_action": "Remove automatic submission scripts and add an explicit Submit button."
            })
    return issues

def audit_target_blank(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 3.2.5 Change on Request (Level AAA / AA Best Practice)
    Checks if target="_blank" links lack screen reader warning.
    """
    issues = []
    blank_links = soup.find_all('a', target="_blank")
    for a in blank_links:
        txt = a.get_text(strip=True)
        rel = a.get('rel', '')
        has_rel_noopener = 'noopener' in rel or 'noreferrer' in rel
        aria_label = a.get('aria-label', '')
        
        if not ('(opens in new window)' in txt.lower() or 'opens in new' in aria_label.lower()):
            issues.append({
                "rule_id": "link-target-blank-unannounced",
                "principle": "Understandable",
                "wcag_sc": "3.2.5 Change on Request (Level AA)",
                "severity": "MODERATE",
                "title": "Link Opens New Window Without Accessible Warning",
                "element_tag": "a",
                "element_html": str(a)[:160],
                "description": "Link opens in a new tab (target='_blank') without warning users. This disorients screen reader users who expect single window navigation.",
                "quick_fix_code": (
                    f'<a href="{a.get("href", "#")}" target="_blank" rel="noopener" aria-label="{txt} (opens in a new tab)">\n'
                    f'  {txt} <span class="sr-only">(opens in a new tab)</span>\n'
                    f'</a>'
                ),
                "suggested_action": "Add rel='noopener' and include visible/screen-reader indication that a new tab will open."
            })
    return issues

def audit_required_fields(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    WCAG 3.3.2 Labels or Instructions (Level A)
    Checks for required inputs missing required/aria-required attributes.
    """
    issues = []
    inputs = soup.find_all(['input', 'select', 'textarea'])
    for inp in inputs:
        style_or_class = (inp.get('class', [''])[0] + ' ' + inp.get('style', '')).lower()
        if 'required' in style_or_class and not (inp.has_attr('required') or inp.get('aria-required') == 'true'):
            issues.append({
                "rule_id": "input-required-unmarked",
                "principle": "Understandable",
                "wcag_sc": "3.3.2 Labels or Instructions (Level A)",
                "severity": "MODERATE",
                "title": "Required Input Field Lacks Programmatic Requirement Attribute",
                "element_tag": inp.name,
                "element_html": str(inp)[:160],
                "description": "Field appears visually required but lacks required or aria-required='true' attributes.",
                "quick_fix_code": f'<{inp.name} id="{inp.get("id", "field")}" required aria-required="true">',
                "suggested_action": "Add explicit required and aria-required='true' attributes to mandatory form fields."
            })
    return issues
