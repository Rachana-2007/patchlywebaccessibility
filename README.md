# Patchly - Web Accessibility Scanner & Visual Remediation Platform

Patchly is an automated, developer-friendly Web Accessibility (a11y) auditing and visual remediation engine built with Python. It scans web pages for WCAG 2.1 AA violations, overlays pulsating pins and glowing outlines directly on offending elements, provides hover cards with actionable code fixes, and exports issues to Excel for human assessment.

---

## 🚀 Key Capabilities

1. **Color Contrast Analysis (WCAG 1.4.3 AA)**: Calculates relative luminance and contrast ratios; automatically computes optimal accessible replacement hex codes.
2. **Alternative Text Audit (WCAG 1.1.1 A)**: Detects missing `alt`, empty `alt` on informative images, uninformative placeholder filenames (`image.png`, `untitled.jpg`), and SVGs lacking accessible names.
3. **Video Captions & Subtitles (WCAG 1.2.2 A)**: Inspects `<video>` tags to verify presence of valid `<track kind="captions">` or `<track kind="subtitles">`.
4. **Keyboard Navigation & Focus (WCAG 2.1.1, 2.4.7, 2.4.3)**:
   - Detects focus indicator suppression (`outline: none !important;`).
   - Detects non-semantic clickable elements (`div`, `span` with `onclick`) lacking keyboard support or ARIA roles.
   - Flags positive `tabindex` that disrupts natural document tab flow.
5. **Interactive Visual Overlay**: Pins glowing badges (`#1`, `#2`, ...) over failing elements; on hover/click displays a popover with root-cause explanations, copyable code diffs, and live fix simulation.
6. **Excel Export for Human Assessment**: Generates structured `.xlsx` workbooks using `openpyxl` with severity color coding, selectors, and auditor checklist columns.

---

## 📁 Project Structure

```
patchly/
├── app.py                         # Web application (Flask dashboard & visual inspector)
├── cli.py                         # Command-line interface for terminal audits & Excel export
├── sample_inaccessible_page.html  # Realistic test fixture with 17 deliberate WCAG barriers
├── SAMPLE_PAGE_AUDIT_KEY.md       # Lookup key and documentation for sample page issues
├── PROJECT_PLAN.md                # Architectural specification & roadmap
├── test_audit.xlsx                # Sample exported Excel assessment workbook
└── engine/
    ├── scanner.py                 # Core scanner coordinator & CSS selector generator
    ├── contrast.py                # Color contrast ratio & luminance optimizer
    ├── alt_text.py                # Image & SVG accessible name auditor
    ├── video_captions.py          # Video track & subtitle inspector
    ├── keyboard_nav.py            # Focus visibility, keyboard triggers & form labels
    ├── overlay_injector.py        # In-page visual flag circles, hover cards & live fix runtime
    ├── excel_exporter.py          # Formatted Excel (.xlsx) generator
    └── ml_assistant.py            # Accessibility health scoring & ML prioritization module
```

---

## 💻 How to Run Patchly

### 1. Launch the Interactive Web Dashboard & In-Page Visual Overlay

Start the web application:
```bash
python app.py
```

Then open your browser to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

#### From the Dashboard:
- Click **"⚡ Audit & Launch Inspector"** to immediately scan the built-in demo page.
- Click **"🔍 Launch Visual Overlay Viewer"** to view the sample webpage with:
  - High-visibility pulsating flag pins directly above each issue.
  - Hover/click on any pin to view the plain-English explanation, Before/After code snippet, and the **"⚡ Apply Live Fix"** button.
  - Collapsible floating bottom toolbar with total flags and severity stats.
  - Click **"Export Assessment Sheet (.xlsx)"** to download the Excel workbook.

---

### 2. Run via Command-Line Interface (CLI)

Audit a local HTML file in the terminal:
```bash
python cli.py sample_inaccessible_page.html
```

Audit and export directly to an Excel sheet for human assessment:
```bash
python cli.py sample_inaccessible_page.html --export my_audit_report.xlsx
```

Audit a live public website URL:
```bash
python cli.py https://example.com --export example_audit.xlsx
```
