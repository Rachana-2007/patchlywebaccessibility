"""
Patchly - In-Page Visual Overlay & Interactive Remediation Injector
Injects interactive floating flag markers, glowing bounding rings, hover cards,
and live DOM remediation capabilities directly into the inspected webpage.
"""

import json
from typing import Dict, Any, List

def inject_visual_overlay(html_content: str, scan_results: Dict[str, Any]) -> str:
    """
    Takes raw HTML and injects the Patchly visual overlay runtime, styles,
    and interactive quick-fix engine before </body>.
    """
    issues_json = json.dumps(scan_results.get("issues", []))
    total_flags = scan_results.get("total_flags", 0)
    summary = scan_results.get("severity_summary", {})

    overlay_bundle = f"""
<!-- ========================================================
     PATCHLY ACCESSIBILITY VISUAL OVERLAY ENGINE
========================================================= -->
<style id="patchly-overlay-styles">
  /* Patchly Base Layer */
  #patchly-root {{
    all: initial;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    position: relative;
    z-index: 2147483640;
  }}

  /* Top/Bottom Floating Control Bar */
  #patchly-toolbar {{
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(15, 23, 42, 0.94);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 9999px;
    padding: 10px 24px;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5), 0 0 20px rgba(99, 102, 241, 0.25);
    z-index: 2147483645;
    color: #ffffff;
    font-size: 14px;
    animation: patchly-slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  }}

  @keyframes patchly-slide-up {{
    from {{ transform: translate(-50%, 60px); opacity: 0; }}
    to {{ transform: translate(-50%, 0); opacity: 1; }}
  }}

  .patchly-brand-badge {{
    font-weight: 800;
    font-size: 15px;
    letter-spacing: -0.3px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #818cf8;
  }}

  .patchly-stat-pill {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
  }}
  .patchly-stat-critical {{ background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }}
  .patchly-stat-serious {{ background: rgba(249, 115, 22, 0.25); color: #fdba74; border: 1px solid rgba(249, 115, 22, 0.4); }}
  .patchly-stat-moderate {{ background: rgba(245, 158, 11, 0.25); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); }}

  .patchly-btn-excel {{
    background: linear-gradient(135deg, #10b981, #059669);
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
  }}
  .patchly-btn-excel:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.45);
  }}

  /* High-Visibility Floating Pins / Circles */
  .patchly-flag-marker {{
    position: absolute;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 2147483642;
    transform: translate(-50%, -50%);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  }}
  .patchly-flag-marker:hover {{
    transform: translate(-50%, -50%) scale(1.25);
  }}

  .patchly-flag-marker::after {{
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    border-radius: 50%;
    animation: patchly-pulse 2s infinite;
  }}

  .patchly-pin-critical {{ background: #ef4444; }}
  .patchly-pin-critical::after {{ border: 2px solid rgba(239, 68, 68, 0.7); }}

  .patchly-pin-serious {{ background: #f97316; }}
  .patchly-pin-serious::after {{ border: 2px solid rgba(249, 115, 22, 0.7); }}

  .patchly-pin-moderate {{ background: #eab308; }}
  .patchly-pin-moderate::after {{ border: 2px solid rgba(234, 179, 8, 0.7); }}

  @keyframes patchly-pulse {{
    0% {{ transform: scale(1); opacity: 0.9; }}
    70% {{ transform: scale(1.6); opacity: 0; }}
    100% {{ transform: scale(1.6); opacity: 0; }}
  }}

  /* Glowing Outline on Offending Elements */
  .patchly-highlight-element {{
    outline: 3px dashed #ef4444 !important;
    outline-offset: 4px !important;
    position: relative;
    transition: outline 0.2s;
  }}

  /* Hover Quick-Fix Popover Card */
  #patchly-popover {{
    position: absolute;
    width: 380px;
    background: #0f172a;
    color: #f8fafc;
    border-radius: 14px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.65), 0 0 30px rgba(99, 102, 241, 0.2);
    z-index: 2147483646;
    display: none;
    font-size: 13px;
    line-height: 1.5;
    animation: patchly-pop-in 0.2s ease-out;
  }}

  @keyframes patchly-pop-in {{
    from {{ opacity: 0; transform: scale(0.95); }}
    to {{ opacity: 1; transform: scale(1); }}
  }}

  .patchly-card-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
  }}

  .patchly-card-title {{
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
    margin-right: 8px;
  }}

  .patchly-card-wcag {{
    font-size: 11px;
    color: #94a3b8;
    margin-bottom: 10px;
  }}

  .patchly-card-desc {{
    color: #cbd5e1;
    margin-bottom: 14px;
  }}

  .patchly-code-box {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px;
    font-family: Consolas, Monaco, "Courier New", monospace;
    font-size: 12px;
    color: #38bdf8;
    overflow-x: auto;
    white-space: pre-wrap;
    margin-bottom: 14px;
    max-height: 140px;
  }}

  .patchly-card-actions {{
    display: flex;
    gap: 8px;
  }}

  .patchly-btn-fix {{
    flex: 1;
    background: #6366f1;
    color: #ffffff;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    text-align: center;
  }}
  .patchly-btn-fix:hover {{ background: #4f46e5; }}

  .patchly-btn-copy {{
    background: #334155;
    color: #f8fafc;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
  }}
  .patchly-btn-copy:hover {{ background: #475569; }}
</style>

<div id="patchly-root">
  <!-- Interactive Hover Card -->
  <div id="patchly-popover">
    <div class="patchly-card-header">
      <div>
        <div class="patchly-card-title" id="patchly-pop-title">Issue Title</div>
        <div class="patchly-card-wcag" id="patchly-pop-wcag">WCAG Criterion</div>
      </div>
      <span class="patchly-stat-pill" id="patchly-pop-badge">CRITICAL</span>
    </div>
    <div class="patchly-card-desc" id="patchly-pop-desc">Explanation of the barrier.</div>
    
    <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px;">
      Recommended Quick Fix:
    </div>
    <div class="patchly-code-box" id="patchly-pop-code">Fix code snippet</div>

    <div class="patchly-card-actions">
      <button type="button" class="patchly-btn-fix" id="patchly-pop-apply">⚡ Apply Live Fix</button>
      <button type="button" class="patchly-btn-copy" id="patchly-pop-copy">📋 Copy Fix</button>
    </div>
  </div>

  <!-- Floating Control Bar -->
  <div id="patchly-toolbar">
    <div class="patchly-brand-badge">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="m9 12 2 2 4-4"></path>
      </svg>
      Patchly
    </div>
    <div style="color: #cbd5e1; font-weight: 600;">{total_flags} A11y Flags Found</div>
    <span class="patchly-stat-pill patchly-stat-critical">{summary.get("CRITICAL", 0)} Critical</span>
    <span class="patchly-stat-pill patchly-stat-serious">{summary.get("SERIOUS", 0)} Serious</span>
    <span class="patchly-stat-pill patchly-stat-moderate">{summary.get("MODERATE", 0)} Moderate</span>
    
    <button type="button" class="patchly-btn-excel" onclick="window.PatchlyOverlay.exportExcel()">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      Export Assessment Sheet (.xlsx)
    </button>
  </div>
</div>

<script id="patchly-overlay-script">
(function() {{
  const issues = {issues_json};
  const popover = document.getElementById('patchly-popover');
  let activeIssue = null;

  function getSeverityClass(sev) {{
    const s = (sev || 'MODERATE').toUpperCase();
    if (s === 'CRITICAL') return 'patchly-pin-critical';
    if (s === 'SERIOUS') return 'patchly-pin-serious';
    return 'patchly-pin-moderate';
  }}

  function renderVisualPins() {{
    issues.forEach((issue) => {{
      let targetEl = null;
      if (issue.target_selector) {{
        try {{
          targetEl = document.querySelector(issue.target_selector);
        }} catch(e) {{}}
      }}

      // Fallback selector by tag or id
      if (!targetEl && issue.element_tag) {{
        const tags = Array.from(document.querySelectorAll(issue.element_tag));
        targetEl = tags.find(t => !t.dataset.patchlyFlagged);
      }}

      if (!targetEl) return;
      targetEl.dataset.patchlyFlagged = "true";
      targetEl.classList.add('patchly-highlight-element');

      // Pin marker calculation
      const rect = targetEl.getBoundingClientRect();
      const marker = document.createElement('div');
      marker.className = `patchly-flag-marker ${{getSeverityClass(issue.severity)}}`;
      marker.textContent = issue.flag_badge;
      marker.title = issue.title;

      // Position marker at top-right of element
      const pinX = rect.left + window.scrollX + Math.min(rect.width, 30);
      const pinY = rect.top + window.scrollY - 8;
      marker.style.left = `${{pinX}}px`;
      marker.style.top = `${{pinY}}px`;

      // Hover / Click behavior
      marker.addEventListener('mouseenter', (e) => showPopover(issue, e.clientX, e.clientY));
      marker.addEventListener('click', (e) => {{
        e.stopPropagation();
        showPopover(issue, e.clientX, e.clientY);
      }});

      document.body.appendChild(marker);
    }});
  }}

  function showPopover(issue, x, y) {{
    activeIssue = issue;
    document.getElementById('patchly-pop-title').textContent = issue.title;
    document.getElementById('patchly-pop-wcag').textContent = issue.wcag_sc || '';
    document.getElementById('patchly-pop-badge').textContent = (issue.severity || 'MODERATE').toUpperCase();
    document.getElementById('patchly-pop-desc').textContent = issue.description;
    document.getElementById('patchly-pop-code').textContent = issue.quick_fix_code || issue.suggested_action;

    popover.style.display = 'block';
    
    // Bounds check to avoid overflowing window edges
    let popLeft = x + 15;
    let popTop = y + 15;
    if (popLeft + 400 > window.innerWidth) popLeft = window.innerWidth - 410;
    if (popTop + 320 > window.innerHeight) popTop = y - 320;
    
    popover.style.left = `${{Math.max(10, popLeft + window.scrollX)}}px`;
    popover.style.top = `${{Math.max(10, popTop + window.scrollY)}}px`;
  }}

  // Dismiss popover on outside click
  document.addEventListener('click', (e) => {{
    if (!popover.contains(e.target) && !e.target.classList.contains('patchly-flag-marker')) {{
      popover.style.display = 'none';
    }}
  }});

  // Quick fix copy button
  document.getElementById('patchly-pop-copy').addEventListener('click', () => {{
    if (activeIssue && activeIssue.quick_fix_code) {{
      navigator.clipboard.writeText(activeIssue.quick_fix_code);
      const btn = document.getElementById('patchly-pop-copy');
      btn.textContent = '✓ Copied!';
      setTimeout(() => {{ btn.textContent = '📋 Copy Fix'; }}, 2000);
    }}
  }});

  // Live DOM Fix simulator
  document.getElementById('patchly-pop-apply').addEventListener('click', () => {{
    if (!activeIssue) return;
    const rule = activeIssue.rule_id || '';
    
    // Dynamic DOM remedy based on rule
    if (rule.includes('alt')) {{
      const img = document.querySelector(activeIssue.target_selector);
      if (img) {{
        img.setAttribute('alt', 'Verified accessible description for screen readers');
        alert('Applied Fix: Alt attribute added to image!');
      }}
    }} else if (rule.includes('contrast')) {{
      const el = document.querySelector(activeIssue.target_selector);
      if (el) {{
        el.style.color = '#0f172a';
        alert('Applied Fix: Text color updated to high-contrast navy (#0f172a)!');
      }}
    }} else if (rule.includes('focus')) {{
      const styleTag = document.createElement('style');
      styleTag.textContent = '*:focus {{ outline: 3px solid #6366f1 !important; outline-offset: 2px !important; }}';
      document.head.appendChild(styleTag);
      alert('Applied Fix: High-contrast keyboard focus indicators restored across entire page!');
    }} else if (rule.includes('clickable')) {{
      const el = document.querySelector(activeIssue.target_selector);
      if (el) {{
        el.setAttribute('tabindex', '0');
        el.setAttribute('role', 'button');
        alert('Applied Fix: Element updated with tabindex="0" and role="button"!');
      }}
    }} else {{
      alert('Applied Fix: Live remedy simulation completed for ' + activeIssue.title);
    }}
    popover.style.display = 'none';
  }});

  // Excel Export Handler
  window.PatchlyOverlay = {{
    exportExcel: function() {{
      fetch('/api/export-excel', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ issues: issues, title: document.title || 'Page Audit' }})
      }})
      .then(res => res.blob())
      .then(blob => {{
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Patchly_Assessment_${{Date.now()}}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }})
      .catch(err => alert('Failed to download Excel sheet: ' + err));
    }}
  }};

  // Wait for DOM to finish rendering
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', renderVisualPins);
  }} else {{
    setTimeout(renderVisualPins, 300);
  }}
}})();
</script>
<!-- ======================================================== -->
"""
    if "</body>" in html_content:
        return html_content.replace("</body>", f"{overlay_bundle}\n</body>")
    return html_content + overlay_bundle
