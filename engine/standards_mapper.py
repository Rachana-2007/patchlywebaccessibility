"""
Patchly - Multi-Standard Compliance Mapping Engine
Enriches WCAG accessibility scan results with Section 508 (US Federal Standard)
and EN 301 549 (European Union ICT Standard) criteria.
"""

from typing import Dict, Any, List

# Standard Mapping Table for WCAG 2.1 -> Section 508 & EN 301 549
STANDARDS_MAP = {
    "image-alt-missing": {
        "wcag_sc": "1.1.1 Non-text Content (Level A)",
        "section_508": "§ 1194.22(a) / E205.4 (Text Equivalent)",
        "en_301_549": "Clause 9.1.1.1 (Non-text Content)"
    },
    "svg-title-missing": {
        "wcag_sc": "1.1.1 Non-text Content (Level A)",
        "section_508": "§ 1194.22(a) / E205.4 (Text Equivalent)",
        "en_301_549": "Clause 9.1.1.1 (Non-text Content)"
    },
    "video-captions-missing": {
        "wcag_sc": "1.2.2 Captions (Prerecorded) (Level A)",
        "section_508": "§ 1194.22(b) / E205.4 (Multimedia Captions)",
        "en_301_549": "Clause 9.1.2.2 (Captions Prerecorded)"
    },
    "form-label-missing": {
        "wcag_sc": "1.3.1 Info and Relationships (Level A)",
        "section_508": "§ 1194.22(n) / E205.4 (Form Control Labels)",
        "en_301_549": "Clause 9.1.3.1 (Info and Relationships)"
    },
    "heading-hierarchy-skipped": {
        "wcag_sc": "1.3.1 Info and Relationships (Level A)",
        "section_508": "§ 1194.22(g) / E205.4 (Document Structure)",
        "en_301_549": "Clause 9.1.3.1 (Info and Relationships)"
    },
    "viewport-zoom-disabled": {
        "wcag_sc": "1.4.4 Resize Text (Level AA)",
        "section_508": "§ 1194.22(d) / E205.4 (Screen Scale & Contrast)",
        "en_301_549": "Clause 9.1.4.4 (Resize Text)"
    },
    "input-purpose-missing": {
        "wcag_sc": "1.3.5 Identify Input Purpose (Level AA)",
        "section_508": "§ 1194.22(n) / E205.4 (Form Inputs)",
        "en_301_549": "Clause 9.1.3.5 (Identify Input Purpose)"
    },
    "color-contrast-low": {
        "wcag_sc": "1.4.3 Contrast (Minimum) (Level AA)",
        "section_508": "§ 1194.22(c/d) / E205.4 (Visual Contrast)",
        "en_301_549": "Clause 9.1.4.3 (Contrast Minimum)"
    },
    "use-of-color-alone": {
        "wcag_sc": "1.4.1 Use of Color (Level A)",
        "section_508": "§ 1194.22(c) / E205.4 (Color Coding)",
        "en_301_549": "Clause 9.1.4.1 (Use of Color)"
    },
    "focus-indicator-missing": {
        "wcag_sc": "2.4.7 Focus Visible (Level AA)",
        "section_508": "§ 1194.22(c) / E205.4 (Visual Focus)",
        "en_301_549": "Clause 9.2.4.7 (Focus Visible)"
    },
    "interactive-element-div-click": {
        "wcag_sc": "2.1.1 Keyboard (Level A)",
        "section_508": "§ 1194.22(a) / E205.4 (Keyboard Navigation)",
        "en_301_549": "Clause 9.2.1.1 (Keyboard)"
    },
    "autoplay-media": {
        "wcag_sc": "2.2.2 Pause, Stop, Hide (Level A)",
        "section_508": "§ 1194.22(p) / E205.4 (Timeouts & Motion)",
        "en_301_549": "Clause 9.2.2.2 (Pause, Stop, Hide)"
    },
    "flicker-tag-marquee": {
        "wcag_sc": "2.3.1 Three Flashes (Level A)",
        "section_508": "§ 1194.22(j) / E205.4 (Flicker Hazards)",
        "en_301_549": "Clause 9.2.3.1 (Three Flashes)"
    },
    "tabindex-positive": {
        "wcag_sc": "2.4.3 Focus Order (Level A)",
        "section_508": "§ 1194.22(n) / E205.4 (Tab Navigation)",
        "en_301_549": "Clause 9.2.4.3 (Focus Order)"
    },
    "bypass-blocks-missing": {
        "wcag_sc": "2.4.1 Bypass Blocks (Level A)",
        "section_508": "§ 1194.22(o) / E205.4 (Skip Navigation Link)",
        "en_301_549": "Clause 9.2.4.1 (Bypass Blocks)"
    },
    "page-title-missing": {
        "wcag_sc": "2.4.2 Page Titled (Level A)",
        "section_508": "§ 1194.22(i) / E205.4 (Document / Frame Title)",
        "en_301_549": "Clause 9.2.4.2 (Page Titled)"
    },
    "link-generic-text": {
        "wcag_sc": "2.4.4 Link Purpose (In Context) (Level A)",
        "section_508": "§ 1194.22(a) / E205.4 (Descriptive Links)",
        "en_301_549": "Clause 9.2.4.4 (Link Purpose)"
    },
    "button-label-missing": {
        "wcag_sc": "4.1.2 Name, Role, Value (Level A)",
        "section_508": "§ 1194.22(n) / E205.4 (Accessible Button Name)",
        "en_301_549": "Clause 9.4.1.2 (Name, Role, Value)"
    },
    "target-size-small": {
        "wcag_sc": "2.5.8 Target Size (Minimum) (Level AA)",
        "section_508": "§ E205.4 (Touch & Click Target Accessibility)",
        "en_301_549": "Clause 9.2.5.8 (Target Size Minimum)"
    },
    "page-language-missing": {
        "wcag_sc": "3.1.1 Language of Page (Level A)",
        "section_508": "§ E205.4 (Language Specification)",
        "en_301_549": "Clause 9.3.1.1 (Language of Page)"
    },
    "auto-submit-form": {
        "wcag_sc": "3.2.2 On Input (Level A)",
        "section_508": "§ 1194.22(n) / E205.4 (Form Submission Predictability)",
        "en_301_549": "Clause 9.3.2.2 (On Input)"
    },
    "target-blank-warning": {
        "wcag_sc": "3.2.5 Change on Request (Level AAA / Best Practice)",
        "section_508": "§ 1194.22(k) / E205.4 (New Window Warnings)",
        "en_301_549": "Clause 9.3.2.5 (Change on Request)"
    },
    "required-field-indicator": {
        "wcag_sc": "3.3.2 Labels or Instructions (Level A)",
        "section_508": "§ 1194.22(n) / E205.4 (Required Field Indicators)",
        "en_301_549": "Clause 9.3.3.2 (Labels or Instructions)"
    }
}

def enrich_issue_with_standards(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Appends Section 508 and EN 301 549 standard criteria to an issue dictionary."""
    rule_id = issue.get("rule_id", "")
    mapping = STANDARDS_MAP.get(rule_id, {})
    
    if mapping:
        issue["wcag_sc"] = mapping.get("wcag_sc", issue.get("wcag_sc", "WCAG 2.1 AA"))
        issue["section_508"] = mapping.get("section_508", "§ 1194.22 / E205.4 General ICT")
        issue["en_301_549"] = mapping.get("en_301_549", "Clause 9 Web Accessibility")
    else:
        # Fallbacks if rule_id isn't explicitly mapped
        wcag = issue.get("wcag_sc", "WCAG 2.1")
        issue["section_508"] = f"§ 1194.22 / E205.4 ({wcag.split()[0]} Equivalent)"
        issue["en_301_549"] = f"Clause 9.{(wcag.split()[0] if wcag else '1')}"
        
    return issue

def compute_standards_summary(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generates multi-standard compliance status rates across WCAG, Section 508, and EN 301 549."""
    active_issues = [i for i in issues if not i.get("is_false_positive", False)]
    total = len(active_issues)
    
    sec508_violations = sum(1 for i in active_issues if i.get("severity") in ["CRITICAL", "SERIOUS"])
    en301_violations = len(active_issues)
    
    # Calculate compliance rates
    wcag_pass = max(0, 100 - (total * 4))
    sec508_pass = max(0, 100 - (sec508_violations * 6))
    en301_pass = max(0, 100 - (en301_violations * 4))

    return {
        "wcag_21": {
            "status": "PASS" if wcag_pass >= 85 else ("WARNING" if wcag_pass >= 70 else "FAIL"),
            "compliance_rate": f"{wcag_pass}%",
            "active_violations": total
        },
        "section_508": {
            "status": "PASS" if sec508_pass >= 85 else ("WARNING" if sec508_pass >= 70 else "FAIL"),
            "compliance_rate": f"{sec508_pass}%",
            "active_violations": sec508_violations,
            "standard_title": "US Rehabilitation Act Section 508 (36 CFR Part 1194 / E205)"
        },
        "en_301_549": {
            "status": "PASS" if en301_pass >= 85 else ("WARNING" if en301_pass >= 70 else "FAIL"),
            "compliance_rate": f"{en301_pass}%",
            "active_violations": en301_violations,
            "standard_title": "European Standard EN 301 549 V3.2.1 (Accessibility requirements for ICT)"
        }
    }
