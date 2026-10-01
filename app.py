"""
Patchly - Web Application Server
Flask web server powering the Patchly Accessibility Scanner,
Visual In-Page Overlay Engine, and Excel Export Service.
"""

import os
import uuid
import time
from flask import Flask, render_template, render_template_string, request, jsonify, send_file, Response
from engine.scanner import scan_html, scan_url
from engine.overlay_injector import inject_visual_overlay
from engine.excel_exporter import generate_accessibility_excel
from engine.ml_assistant import ml_assistant
from engine.standards_mapper import compute_standards_summary
from engine.crawler import run_multi_page_test_run, run_folder_test_run, TEST_RUNS_STORE

app = Flask(__name__)
SAMPLE_FILE_PATH = os.path.join(os.path.dirname(__file__), "sample_inaccessible_page.html")

# In-memory storage for scan sessions & false positive dispute portal logs
AUDIT_STORE = {}
FALSE_POSITIVES_STORE = []

def clean_old_audits():
    """Prune audits older than 2 hours to avoid memory growth."""
    now = time.time()
    stale_keys = [k for k, v in AUDIT_STORE.items() if now - v.get("created_at", 0) > 7200]
    for k in stale_keys:
        AUDIT_STORE.pop(k, None)

# ========================================================
# DASHBOARD TEMPLATE (Clean, Accessible Light Design - WCAG AA/AAA Compliant)
# ========================================================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Patchly - Accessible Web Accessibility Scanner & Remediation</title>
  <meta name="description" content="Audit web accessibility barriers against WCAG 2.1 Principles 1, 2, and 3 with automated checks, HTML file uploads, interactive visual overlay inspection, and instant quick-fix remediation.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      /* WCAG AAA/AA Compliant Light Theme Palette */
      --bg-surface: #f8fafc;
      --bg-card: #ffffff;
      --border-subtle: #e2e8f0;
      --border-strong: #cbd5e1;
      
      /* High-contrast brand colors (7.3:1 contrast against white) */
      --primary: #4338ca;
      --primary-hover: #3730a3;
      --primary-light: #eef2ff;
      --primary-ring: rgba(67, 56, 202, 0.25);
      
      /* Accessible text colors */
      --text-main: #0f172a;       /* Slate 900: 16:1 contrast on white */
      --text-secondary: #334155;  /* Slate 700: 9.6:1 contrast on white */
      --text-muted: #475569;      /* Slate 600: 5.7:1 contrast on white (WCAG AA > 4.5:1) */
      
      /* Accessible status & severity tokens (>= 4.5:1 text on tag backgrounds) */
      --critical-text: #991b1b;
      --critical-bg: #fee2e2;
      --critical-border: #fca5a5;

      --serious-text: #9a3412;
      --serious-bg: #ffedd5;
      --serious-border: #fdba74;

      --moderate-text: #854d0e;
      --moderate-bg: #fef9c3;
      --moderate-border: #fde047;

      --success-text: #065f46;
      --success-bg: #d1fae5;
      --success-border: #6ee7b7;

      --info-text: #0369a1;
      --info-bg: #e0f2fe;
      --info-border: #7dd3fc;

      --purple-text: #6b21a8;
      --purple-bg: #f3e8ff;
      --purple-border: #d8b4fe;
      
      /* Shadow tokens */
      --shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
      --shadow-lg: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
    }

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Plus Jakarta Sans', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-surface);
      background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
      background-size: 24px 24px;
      color: var(--text-main);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Accessibility: Skip Link for Keyboard Nav */
    .skip-link {
      position: absolute;
      top: -60px;
      left: 16px;
      background: var(--primary);
      color: #ffffff;
      padding: 12px 20px;
      font-weight: 700;
      font-size: 0.95rem;
      border-radius: 8px;
      z-index: 1000;
      text-decoration: none;
      box-shadow: var(--shadow-lg);
      transition: top 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .skip-link:focus {
      top: 16px;
      outline: 3px solid #1e1b4b;
      outline-offset: 2px;
    }

    *:focus-visible {
      outline: 3px solid var(--primary);
      outline-offset: 3px;
    }

    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    /* Header Navigation */
    header {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border-subtle);
      padding: 18px 32px;
      position: sticky;
      top: 0;
      z-index: 90;
      box-shadow: var(--shadow-sm);
    }
    .header-inner {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 1.35rem;
      font-weight: 800;
      color: var(--text-main);
      text-decoration: none;
      letter-spacing: -0.5px;
    }
    .brand-icon {
      background: var(--primary-light);
      color: var(--primary);
      border: 1px solid rgba(67, 56, 202, 0.2);
      border-radius: 10px;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .badge-wcag {
      background: var(--primary-light);
      color: var(--primary);
      font-size: 0.8rem;
      font-weight: 700;
      padding: 6px 14px;
      border-radius: 9999px;
      border: 1px solid rgba(67, 56, 202, 0.15);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    main {
      flex: 1;
      max-width: 1200px;
      width: 100%;
      margin: 36px auto 60px;
      padding: 0 24px;
    }

    .hero {
      text-align: center;
      margin-bottom: 36px;
    }
    .hero-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.85rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--primary);
      background: var(--primary-light);
      padding: 4px 12px;
      border-radius: 9999px;
      margin-bottom: 14px;
    }
    .hero h1 {
      font-size: 2.5rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.2;
      color: var(--text-main);
      margin-bottom: 12px;
    }
    .hero p {
      color: var(--text-muted);
      font-size: 1.125rem;
      max-width: 760px;
      margin: 0 auto;
    }

    .scanner-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 20px;
      padding: 32px;
      box-shadow: var(--shadow-lg);
      margin-bottom: 40px;
    }

    /* Tablist */
    .tab-list {
      display: flex;
      gap: 8px;
      border-bottom: 2px solid var(--border-subtle);
      padding-bottom: 4px;
      margin-bottom: 28px;
      overflow-x: auto;
    }
    .tab-item {
      background: none;
      border: none;
      border-radius: 10px 10px 0 0;
      padding: 12px 18px;
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      position: relative;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .tab-item:hover {
      color: var(--primary);
      background: var(--primary-light);
    }
    .tab-item[aria-selected="true"] {
      color: var(--primary);
      background: var(--primary-light);
    }
    .tab-item[aria-selected="true"]::after {
      content: '';
      position: absolute;
      bottom: -6px;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--primary);
      border-radius: 3px 3px 0 0;
    }

    .tab-panel {
      display: none;
    }
    .tab-panel.active {
      display: block;
      animation: fadeIn 0.25s ease-in-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Drag & Drop Upload Zone */
    .upload-zone {
      border: 2px dashed var(--border-strong);
      border-radius: 16px;
      padding: 40px 24px;
      text-align: center;
      background: #fafafa;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }
    .upload-zone:hover, .upload-zone.dragover {
      border-color: var(--primary);
      background: var(--primary-light);
    }
    .upload-zone:focus-visible {
      outline: 3px solid var(--primary);
      outline-offset: 3px;
    }
    .upload-icon {
      width: 56px;
      height: 56px;
      margin: 0 auto 16px;
      background: #ffffff;
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--primary);
      box-shadow: var(--shadow-sm);
    }
    .upload-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 6px;
    }
    .upload-desc {
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-bottom: 16px;
    }
    .file-input-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      opacity: 0;
      overflow: hidden;
      z-index: -1;
    }

    .file-selected-box {
      display: none;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 20px;
      margin-top: 20px;
      box-shadow: var(--shadow-sm);
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .file-info {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .file-info-icon {
      width: 44px;
      height: 44px;
      background: var(--primary-light);
      color: var(--primary);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 0.85rem;
    }
    .file-name {
      font-weight: 700;
      font-size: 1rem;
      color: var(--text-main);
      word-break: break-all;
    }
    .file-meta {
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    /* Buttons */
    .btn {
      font-family: inherit;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 12px 24px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease-in-out;
      border: none;
      line-height: 1.4;
    }
    .btn-primary {
      background: var(--primary);
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(67, 56, 202, 0.25);
    }
    .btn-primary:hover {
      background: var(--primary-hover);
      transform: translateY(-1px);
    }
    .btn-secondary {
      background: #ffffff;
      color: var(--text-main);
      border: 1px solid var(--border-strong);
    }
    .btn-secondary:hover {
      background: #f1f5f9;
    }
    .btn-danger-ghost {
      background: none;
      color: var(--critical-text);
      border: 1px solid transparent;
      padding: 8px 14px;
      font-size: 0.875rem;
    }
    .btn-danger-ghost:hover {
      background: var(--critical-bg);
      border-color: var(--critical-border);
    }
    .btn-inspect {
      background: var(--info-text);
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(3, 105, 161, 0.25);
    }
    .btn-inspect:hover {
      background: #0284c7;
      transform: translateY(-1px);
    }
    .btn-excel {
      background: var(--success-text);
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(6, 95, 70, 0.25);
    }
    .btn-excel:hover {
      background: #047857;
      transform: translateY(-1px);
    }
    .btn-copy {
      background: #ffffff;
      color: var(--primary);
      border: 1px solid var(--primary-ring);
      padding: 6px 14px;
      font-size: 0.825rem;
      border-radius: 6px;
      font-weight: 700;
    }
    .btn-copy:hover {
      background: var(--primary-light);
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .form-label {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .form-hint {
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    input[type="url"], textarea {
      width: 100%;
      background: #ffffff;
      border: 1.5px solid var(--border-strong);
      border-radius: 12px;
      padding: 14px 16px;
      color: var(--text-main);
      font-size: 1rem;
      font-family: inherit;
    }
    textarea {
      min-height: 200px;
      font-family: 'JetBrains Mono', Consolas, monospace;
      font-size: 0.9rem;
      resize: vertical;
    }

    .input-row {
      display: flex;
      gap: 12px;
      align-items: center;
    }

    .sample-box {
      background: var(--primary-light);
      border: 1px solid rgba(67, 56, 202, 0.2);
      border-radius: 14px;
      padding: 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      flex-wrap: wrap;
    }

    .loading-container {
      display: none;
      text-align: center;
      padding: 36px 20px;
      background: #ffffff;
      border-radius: 16px;
      border: 1px solid var(--border-subtle);
      margin-top: 24px;
    }
    .spinner {
      width: 44px;
      height: 44px;
      border: 4px solid var(--border-subtle);
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 16px;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Dashboard Results */
    #results-area {
      display: none;
      animation: fadeIn 0.3s ease-out;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: 300px 1fr;
      gap: 24px;
      margin-bottom: 36px;
    }
    @media (max-width: 900px) {
      .metrics-grid { grid-template-columns: 1fr; }
    }

    .score-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 18px;
      padding: 32px 24px;
      text-align: center;
      box-shadow: var(--shadow-md);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .score-label {
      font-size: 0.875rem;
      text-transform: uppercase;
      font-weight: 800;
      color: var(--text-muted);
    }
    .score-number {
      font-size: 4.2rem;
      font-weight: 900;
      line-height: 1;
      margin: 12px 0 8px;
      letter-spacing: -2px;
    }
    .score-grade-badge {
      font-size: 1rem;
      font-weight: 800;
      padding: 6px 16px;
      border-radius: 9999px;
      display: inline-block;
      margin-bottom: 8px;
    }

    .summary-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 18px;
      padding: 30px;
      box-shadow: var(--shadow-md);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .stats-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    @media (max-width: 600px) {
      .stats-row { grid-template-columns: repeat(2, 1fr); }
    }
    .stat-box {
      background: #f8fafc;
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 16px;
      text-align: center;
    }
    .stat-val {
      font-size: 2rem;
      font-weight: 800;
      margin-bottom: 2px;
    }
    .stat-label {
      font-size: 0.775rem;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 800;
    }

    .actions-bar {
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
    }

    /* Filter Toolbar */
    .filter-toolbar {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 18px 24px;
      margin-bottom: 24px;
      box-shadow: var(--shadow-sm);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }
    .filter-group {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .filter-title {
      font-size: 0.85rem;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--text-muted);
      letter-spacing: 0.05em;
    }
    .filter-pill {
      background: #ffffff;
      border: 1.5px solid var(--border-strong);
      border-radius: 9999px;
      padding: 6px 14px;
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-secondary);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .filter-pill:hover {
      border-color: var(--primary);
      color: var(--primary);
    }
    .filter-pill.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
    }

    /* Issues Feed & Quick Fix Boxes */
    .issues-list {
      display: flex;
      flex-direction: column;
      gap: 22px;
    }
    .issue-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-left: 6px solid #cbd5e1;
      border-radius: 16px;
      padding: 24px;
      box-shadow: var(--shadow-sm);
    }
    .issue-card.sev-critical { border-left-color: var(--critical-text); }
    .issue-card.sev-serious { border-left-color: var(--serious-text); }
    .issue-card.sev-moderate { border-left-color: var(--moderate-text); }

    .issue-header-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .issue-title-area {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .issue-badge-num {
      background: var(--primary-light);
      color: var(--primary);
      font-weight: 800;
      font-size: 0.85rem;
      padding: 4px 10px;
      border-radius: 8px;
    }
    .issue-title {
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--text-main);
    }

    .badge-pills {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .pill-principle {
      background: var(--purple-bg);
      color: var(--purple-text);
      border: 1px solid var(--purple-border);
      font-size: 0.775rem;
      font-weight: 800;
      padding: 4px 10px;
      border-radius: 9999px;
      text-transform: uppercase;
    }
    .pill-severity {
      font-size: 0.775rem;
      font-weight: 800;
      padding: 4px 10px;
      border-radius: 9999px;
      text-transform: uppercase;
      border: 1px solid transparent;
    }
    .badge-critical { background: var(--critical-bg); color: var(--critical-text); border-color: var(--critical-border); }
    .badge-serious { background: var(--serious-bg); color: var(--serious-text); border-color: var(--serious-border); }
    .badge-moderate { background: var(--moderate-bg); color: var(--moderate-text); border-color: var(--moderate-border); }

    .issue-meta-bar {
      font-size: 0.875rem;
      color: var(--text-muted);
      margin-bottom: 12px;
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
    }
    .wcag-sc-tag {
      font-weight: 700;
      color: var(--text-secondary);
    }
    .target-tag {
      font-family: 'JetBrains Mono', Consolas, monospace;
      background: #f1f5f9;
      color: var(--primary);
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 0.825rem;
    }

    .issue-desc {
      color: var(--text-secondary);
      font-size: 0.95rem;
      line-height: 1.6;
      margin-bottom: 18px;
    }

    /* Dedicated Quick Fix Section */
    .quick-fix-panel {
      background: #0f172a;
      border: 1px solid #1e293b;
      border-radius: 12px;
      padding: 18px;
      color: #f8fafc;
    }
    .quick-fix-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    .quick-fix-title {
      font-size: 0.85rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .quick-fix-code {
      font-family: 'JetBrains Mono', Consolas, monospace;
      font-size: 0.875rem;
      color: #a5b4fc;
      white-space: pre-wrap;
      word-break: break-all;
      background: #090d16;
      border: 1px solid #1e293b;
      padding: 12px 14px;
      border-radius: 8px;
      margin-bottom: 10px;
    }
    .quick-fix-action {
      font-size: 0.85rem;
      color: #94a3b8;
    }

    footer {
      margin-top: auto;
      background: #ffffff;
      border-top: 1px solid var(--border-subtle);
      padding: 24px;
      text-align: center;
      font-size: 0.875rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <!-- Skip link for keyboard accessibility (WCAG 2.4.1) -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <!-- Live Announcer for screen readers -->
  <div id="a11y-announcer" class="sr-only" role="status" aria-live="polite"></div>

  <header role="banner">
    <div class="header-inner">
      <a href="/" class="brand" aria-label="Patchly - Home">
        <div class="brand-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4"/>
          </svg>
        </div>
        <span>Patchly</span>
      </a>
      <div class="badge-wcag">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="m9 12 2 2 4-4"></path>
        </svg>
        <span>WCAG 2.1 AA Compliant Auditor</span>
      </div>
    </div>
  </header>

  <main id="main-content">
    <div class="hero">
      <div class="hero-eyebrow">
        <span>Empathetic Accessibility Engineering</span>
      </div>
      <h1>Auditing Principles 1 (Perceivable), 2 (Operable) & 3 (Understandable)</h1>
      <p>Upload HTML files, scan live URLs, or test snippets. Evaluates WCAG 2.1 guidelines with instant step-by-step quick fix remediations.</p>
    </div>

    <!-- Scanner Input Card -->
    <section class="scanner-card" aria-labelledby="scanner-heading">
      <h2 id="scanner-heading" class="sr-only">Accessibility Audit Scanner Input</h2>

      <!-- Tablist -->
      <div class="tab-list" role="tablist" aria-label="Audit Input Options">
        <button class="tab-item" role="tab" id="tab-upload-btn" aria-selected="true" aria-controls="tab-upload" tabindex="0" onclick="selectTab('upload')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <span>Upload HTML File</span>
        </button>

        <button class="tab-item" role="tab" id="tab-sample-btn" aria-selected="false" aria-controls="tab-sample" tabindex="-1" onclick="selectTab('sample')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
          <span>Built-in Demo Page</span>
        </button>

        <button class="tab-item" role="tab" id="tab-url-btn" aria-selected="false" aria-controls="tab-url" tabindex="-1" onclick="selectTab('url')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="2" y1="12" x2="22" y2="12"></line>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
          </svg>
          <span>Scan Live URL</span>
        </button>

        <button class="tab-item" role="tab" id="tab-raw-btn" aria-selected="false" aria-controls="tab-raw" tabindex="-1" onclick="selectTab('raw')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <polyline points="16 18 22 12 16 6"></polyline>
            <polyline points="8 6 2 12 8 18"></polyline>
          </svg>
          <span>Paste Code</span>
        </button>
      </div>

      <!-- Tab 1: Upload HTML File -->
      <div id="tab-upload" class="tab-panel active" role="tabpanel" aria-labelledby="tab-upload-btn">
        <div class="upload-zone" id="drop-zone" tabindex="0" role="button" aria-label="Drop your HTML file here or press Enter to browse" onclick="triggerFileInput()" onkeydown="handleDropzoneKey(event)">
          <input type="file" id="file-input" class="file-input-hidden" accept=".html,.htm" onchange="handleFileSelected(event)" aria-hidden="true">
          <div class="upload-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="12" y1="18" x2="12" y2="12"></line>
              <polyline points="9 15 12 12 15 15"></polyline>
            </svg>
          </div>
          <div class="upload-title">Choose an HTML file or drag & drop here</div>
          <div class="upload-desc">Supports standard .html and .htm files. No code pasting required.</div>
          <button type="button" class="btn btn-secondary" onclick="triggerFileInput(); event.stopPropagation();">
            Browse Computer
          </button>
        </div>

        <div class="file-selected-box" id="file-selected-box">
          <div class="file-info">
            <div class="file-info-icon" aria-hidden="true">HTML</div>
            <div>
              <div class="file-name" id="selected-file-name">filename.html</div>
              <div class="file-meta" id="selected-file-size">0 KB &bull; Ready for scan</div>
            </div>
          </div>
          <div class="file-actions">
            <button type="button" class="btn btn-danger-ghost" onclick="clearSelectedFile()">
              Remove
            </button>
            <button type="button" class="btn btn-primary" id="btn-scan-file" onclick="runUploadedFileScan()">
              Audit Uploaded File
            </button>
          </div>
        </div>
      </div>

      <!-- Tab 2: Built-in Sample Page -->
      <div id="tab-sample" class="tab-panel" role="tabpanel" aria-labelledby="tab-sample-btn">
        <div class="sample-box">
          <div>
            <div class="sample-title">ApexFlow SaaS Demo Page</div>
            <div class="sample-text">Fixture loaded with deliberate WCAG Principles 1, 2, and 3 violations (low contrast, missing labels, uncaptioned video, broken focus rings).</div>
          </div>
          <button type="button" class="btn btn-primary" onclick="runSampleScan()">
            Audit ApexFlow Demo
          </button>
        </div>
      </div>

      <!-- Tab 3: URL Scanner -->
      <div id="tab-url" class="tab-panel" role="tabpanel" aria-labelledby="tab-url-btn">
        <div class="form-group">
          <label for="target-url" class="form-label">Target Website URL</label>
          <div class="input-row">
            <input type="url" id="target-url" placeholder="https://example.com" value="https://example.com" aria-describedby="url-hint">
            <button type="button" class="btn btn-primary" onclick="runUrlScan()">
              Scan URL
            </button>
          </div>
          <div id="url-hint" class="form-hint">Enter an accessible public HTTP or HTTPS web address to audit.</div>
        </div>
      </div>

      <!-- Tab 4: Raw HTML Paste -->
      <div id="tab-raw" class="tab-panel" role="tabpanel" aria-labelledby="tab-raw-btn">
        <div class="form-group">
          <label for="raw-html" class="form-label">HTML Markup</label>
          <textarea id="raw-html" placeholder="<!DOCTYPE html><html><body>...</body></html>" aria-describedby="raw-hint"></textarea>
          <div id="raw-hint" class="form-hint">Paste full HTML document structure or component fragments.</div>
          <div style="margin-top: 14px; display: flex; justify-content: flex-end;">
            <button type="button" class="btn btn-primary" onclick="runRawHtmlScan()">
              Audit Pasted HTML
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div class="loading-container" id="loading-spinner" aria-live="assertive">
        <div class="spinner" aria-hidden="true"></div>
        <div class="loading-text" id="loading-message">Analyzing Document Accessibility...</div>
        <div class="loading-subtext">Evaluating Principles 1 (Perceivable), 2 (Operable), and 3 (Understandable)...</div>
      </div>
    </section>

    <!-- Scan Results Dashboard -->
    <section id="results-area" aria-labelledby="results-heading">
      <h2 id="results-heading" class="sr-only">Accessibility Assessment Results</h2>

      <div class="metrics-grid">
        <div class="score-card">
          <div class="score-label">Accessibility Health Score</div>
          <div class="score-number" id="score-val" aria-label="Health score: 0 out of 100">--</div>
          <div class="score-grade-badge" id="score-grade-badge">Grade: --</div>
          <div class="score-status-desc" id="score-status-desc">Calculating status...</div>
        </div>

        <div class="summary-card">
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 800; margin-bottom: 16px;">Barrier Summary</h3>
            <div class="stats-row">
              <div class="stat-box">
                <div class="stat-val" id="count-total" style="color: var(--text-main);">0</div>
                <div class="stat-label">Total Flags</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" id="count-critical" style="color: var(--critical-text);">0</div>
                <div class="stat-label">Critical</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" id="count-serious" style="color: var(--serious-text);">0</div>
                <div class="stat-label">Serious</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" id="count-moderate" style="color: var(--moderate-text);">0</div>
                <div class="stat-label">Moderate</div>
              </div>
            </div>
          </div>

          <div class="actions-bar">
            <button type="button" class="btn btn-inspect" id="btn-inspect" onclick="openInspectorWindow()">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <span>Launch Visual Overlay Viewer</span>
            </button>
            <button type="button" class="btn btn-excel" onclick="downloadExcelReport()">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              <span>Export Assessment (.xlsx)</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Filter Toolbar -->
      <div class="filter-toolbar">
        <div class="filter-group">
          <span class="filter-title">Filter by Principle:</span>
          <button type="button" class="filter-pill active" onclick="filterPrinciple('ALL', this)">All Principles</button>
          <button type="button" class="filter-pill" onclick="filterPrinciple('Perceivable', this)">1. Perceivable</button>
          <button type="button" class="filter-pill" onclick="filterPrinciple('Operable', this)">2. Operable</button>
          <button type="button" class="filter-pill" onclick="filterPrinciple('Understandable', this)">3. Understandable</button>
        </div>

        <div class="filter-group">
          <span class="filter-title">Severity:</span>
          <button type="button" class="filter-pill active" onclick="filterSeverity('ALL', this)">All Severities</button>
          <button type="button" class="filter-pill" onclick="filterSeverity('CRITICAL', this)">Critical</button>
          <button type="button" class="filter-pill" onclick="filterSeverity('SERIOUS', this)">Serious</button>
          <button type="button" class="filter-pill" onclick="filterSeverity('MODERATE', this)">Moderate</button>
        </div>
      </div>

      <!-- Issues List -->
      <h3 style="font-size: 1.4rem; font-weight: 800; margin-bottom: 20px;">Detected Barriers & Quick Fix Remediation</h3>
      <div class="issues-list" id="issues-container">
        <!-- Dynamically rendered items -->
      </div>
    </section>
  </main>

  <footer>
    <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <div>Patchly Accessibility Engine &bull; Evaluates WCAG 2.1 Principles 1, 2 & 3</div>
      <div>Robust guidelines avoided per design spec</div>
    </div>
  </footer>

  <script>
    let currentIssues = [];
    let currentAuditId = null;
    let selectedHtmlFile = null;
    let selectedFileContent = null;
    let activePrincipleFilter = 'ALL';
    let activeSeverityFilter = 'ALL';

    function announce(message) {
      const announcer = document.getElementById('a11y-announcer');
      if (announcer) announcer.textContent = message;
    }

    const tabButtons = [
      document.getElementById('tab-upload-btn'),
      document.getElementById('tab-sample-btn'),
      document.getElementById('tab-url-btn'),
      document.getElementById('tab-raw-btn')
    ];

    function selectTab(tabKey) {
      const tabs = ['upload', 'sample', 'url', 'raw'];
      tabs.forEach(t => {
        const btn = document.getElementById(`tab-${t}-btn`);
        const panel = document.getElementById(`tab-${t}`);
        const isSelected = (t === tabKey);
        btn.setAttribute('aria-selected', isSelected ? 'true' : 'false');
        btn.tabIndex = isSelected ? 0 : -1;
        if (isSelected) {
          panel.classList.add('active');
          btn.focus();
        } else {
          panel.classList.remove('active');
        }
      });
      announce(`Selected ${tabKey} tab.`);
    }

    tabButtons.forEach((btn, index) => {
      btn.addEventListener('keydown', (e) => {
        let newIndex = null;
        if (e.key === 'ArrowRight') newIndex = (index + 1) % tabButtons.length;
        else if (e.key === 'ArrowLeft') newIndex = (index - 1 + tabButtons.length) % tabButtons.length;
        else if (e.key === 'Home') newIndex = 0;
        else if (e.key === 'End') newIndex = tabButtons.length - 1;

        if (newIndex !== null) {
          e.preventDefault();
          selectTab(['upload', 'sample', 'url', 'raw'][newIndex]);
        }
      });
    });

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    function triggerFileInput() { fileInput.click(); }
    function handleDropzoneKey(e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); }
    }

    ['dragenter', 'dragover'].forEach(evt => dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add('dragover'); }));
    ['dragleave', 'drop'].forEach(evt => dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove('dragover'); }));

    dropZone.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) processFile(files[0]);
    });

    function handleFileSelected(e) {
      if (e.target.files && e.target.files.length > 0) processFile(e.target.files[0]);
    }

    function processFile(file) {
      if (!file.name.toLowerCase().endsWith('.html') && !file.name.toLowerCase().endsWith('.htm')) {
        alert('Please select a valid HTML file (.html or .htm).');
        return;
      }
      selectedHtmlFile = file;
      document.getElementById('selected-file-name').textContent = file.name;
      const sizeKb = (file.size / 1024).toFixed(1);
      document.getElementById('selected-file-size').textContent = `${sizeKb} KB • Ready for scan`;
      document.getElementById('file-selected-box').style.display = 'flex';
      announce(`Selected file ${file.name}`);

      const reader = new FileReader();
      reader.onload = evt => { selectedFileContent = evt.target.result; };
      reader.readAsText(file);
    }

    function clearSelectedFile() {
      selectedHtmlFile = null;
      selectedFileContent = null;
      fileInput.value = '';
      document.getElementById('file-selected-box').style.display = 'none';
      announce('File removed.');
    }

    function showLoading(msg = 'Analyzing Document Accessibility...') {
      document.getElementById('loading-message').textContent = msg;
      document.getElementById('loading-spinner').style.display = 'block';
      announce(msg);
    }

    function hideLoading() {
      document.getElementById('loading-spinner').style.display = 'none';
    }

    function runUploadedFileScan() {
      if (!selectedFileContent && !selectedHtmlFile) return alert('Please choose an HTML file first.');
      showLoading(`Scanning uploaded file "${selectedHtmlFile ? selectedHtmlFile.name : 'document'}"...`);
      fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html: selectedFileContent, source_title: selectedHtmlFile ? selectedHtmlFile.name : 'Uploaded HTML' })
      })
      .then(res => res.json())
      .then(data => { hideLoading(); displayResults(data); })
      .catch(err => { hideLoading(); alert('Error scanning file: ' + err.message); });
    }

    function runSampleScan() {
      showLoading('Auditing ApexFlow Sample Inaccessible Page...');
      fetch('/api/scan-sample')
        .then(res => res.json())
        .then(data => { hideLoading(); displayResults(data); })
        .catch(err => { hideLoading(); alert('Error: ' + err.message); });
    }

    function runUrlScan() {
      const url = document.getElementById('target-url').value.trim();
      if (!url) return alert('Please enter a URL.');
      showLoading(`Scanning URL ${url}...`);
      fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
      })
      .then(res => res.json())
      .then(data => { hideLoading(); displayResults(data); })
      .catch(err => { hideLoading(); alert('Error: ' + err.message); });
    }

    function runRawHtmlScan() {
      const html = document.getElementById('raw-html').value.trim();
      if (!html) return alert('Please paste HTML.');
      showLoading('Auditing pasted HTML...');
      fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html: html, source_title: 'Custom HTML' })
      })
      .then(res => res.json())
      .then(data => { hideLoading(); displayResults(data); })
      .catch(err => { hideLoading(); alert('Error: ' + err.message); });
    }

    function displayResults(data) {
      if (!data.success) {
        alert('Audit Error: ' + (data.error || 'Scanner error'));
        return;
      }
      currentIssues = data.issues || [];
      currentAuditId = data.audit_id || null;

      const resultsArea = document.getElementById('results-area');
      resultsArea.style.display = 'block';

      const score = data.health ? data.health.score : 0;
      const grade = data.health ? data.health.grade : 'N/A';
      const statusDesc = data.health ? data.health.status : 'Audit completed';

      const scoreValEl = document.getElementById('score-val');
      scoreValEl.textContent = score;
      scoreValEl.setAttribute('aria-label', `Health score: ${score} out of 100`);

      const gradeBadge = document.getElementById('score-grade-badge');
      gradeBadge.textContent = 'Grade: ' + grade;

      if (score >= 90) {
        gradeBadge.style.background = 'var(--success-bg)';
        gradeBadge.style.color = 'var(--success-text)';
        scoreValEl.style.color = 'var(--success-text)';
      } else if (score >= 70) {
        gradeBadge.style.background = 'var(--moderate-bg)';
        gradeBadge.style.color = 'var(--moderate-text)';
        scoreValEl.style.color = 'var(--moderate-text)';
      } else {
        gradeBadge.style.background = 'var(--critical-bg)';
        gradeBadge.style.color = 'var(--critical-text)';
        scoreValEl.style.color = 'var(--critical-text)';
      }

      document.getElementById('score-status-desc').textContent = statusDesc;

      const total = data.total_flags || 0;
      const critical = (data.severity_summary && data.severity_summary.CRITICAL) || 0;
      const serious = (data.severity_summary && data.severity_summary.SERIOUS) || 0;
      const moderate = (data.severity_summary && data.severity_summary.MODERATE) || 0;

      document.getElementById('count-total').textContent = total;
      document.getElementById('count-critical').textContent = critical;
      document.getElementById('count-serious').textContent = serious;
      document.getElementById('count-moderate').textContent = moderate;

      const btnInspect = document.getElementById('btn-inspect');
      if (currentAuditId) {
        btnInspect.disabled = false;
        btnInspect.style.opacity = '1';
      }

      renderIssues();
      announce(`Audit complete. Found ${total} barriers across Principles 1, 2, and 3.`);
      resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function filterPrinciple(principle, btn) {
      activePrincipleFilter = principle;
      btn.parentElement.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderIssues();
    }

    function filterSeverity(sev, btn) {
      activeSeverityFilter = sev;
      btn.parentElement.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderIssues();
    }

    function renderIssues() {
      const container = document.getElementById('issues-container');
      container.innerHTML = '';

      let filtered = currentIssues;
      if (activePrincipleFilter !== 'ALL') {
        filtered = filtered.filter(i => i.principle === activePrincipleFilter);
      }
      if (activeSeverityFilter !== 'ALL') {
        filtered = filtered.filter(i => (i.severity || '').toUpperCase() === activeSeverityFilter);
      }

      if (filtered.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 40px 20px; background: #ffffff; border-radius: 12px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 1.2rem; font-weight: 700; color: var(--text-main);">No barriers matching selected filters.</div>
            <div style="color: var(--text-muted); font-size: 0.9rem; margin-top: 4px;">Try selecting 'All Principles' or 'All Severities'.</div>
          </div>
        `;
        return;
      }

      filtered.forEach((issue, idx) => {
        const item = document.createElement('article');
        const sev = (issue.severity || 'MODERATE').toUpperCase();
        item.className = `issue-card sev-${sev.toLowerCase()}`;

        const badgeClass = `badge-${sev.toLowerCase()}`;
        const quickFix = issue.quick_fix_code || issue.suggested_action || 'No quick fix available.';
        const actionText = issue.suggested_action || 'Remediate markup to align with WCAG guidelines.';

        item.innerHTML = `
          <div class="issue-header-row">
            <div class="issue-title-area">
              <span class="issue-badge-num">${issue.flag_badge || '#' + (idx + 1)}</span>
              <h4 class="issue-title">${escapeHtml(issue.title)}</h4>
            </div>
            <div class="badge-pills">
              <span class="pill-principle">${escapeHtml(issue.principle || 'Perceivable')}</span>
              <span class="pill-severity ${badgeClass}">${sev}</span>
            </div>
          </div>

          <div class="issue-meta-bar">
            <span class="wcag-sc-tag">${escapeHtml(issue.wcag_sc || 'WCAG 2.1')}</span>
            <span>&bull;</span>
            <span>Element: <code class="target-tag">&lt;${escapeHtml(issue.element_tag || 'div')}&gt;</code></span>
          </div>

          <p class="issue-desc">${escapeHtml(issue.description || '')}</p>

          <!-- Quick Fix Section -->
          <div class="quick-fix-panel">
            <div class="quick-fix-header">
              <div class="quick-fix-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
                <span>⚡ Quick Fix & Code Remediation</span>
              </div>
              <button type="button" class="btn-copy" onclick="copyFixCode(this)">
                Copy Quick Fix
              </button>
            </div>
            <pre class="quick-fix-code"><code>${escapeHtml(quickFix)}</code></pre>
            <div class="quick-fix-action">💡 <strong>Remediation Steps:</strong> ${escapeHtml(actionText)}</div>
          </div>
        `;
        container.appendChild(item);
      });
    }

    function copyFixCode(btn) {
      const codeEl = btn.parentElement.parentElement.querySelector('.quick-fix-code code');
      if (codeEl) {
        const text = codeEl.textContent;
        navigator.clipboard.writeText(text).then(() => {
          const origText = btn.textContent;
          btn.textContent = 'Copied!';
          btn.style.background = 'var(--success-bg)';
          btn.style.color = 'var(--success-text)';
          setTimeout(() => {
            btn.textContent = origText;
            btn.style.background = '#ffffff';
            btn.style.color = 'var(--primary)';
          }, 2000);
        });
      }
    }

    function escapeHtml(text) {
      if (!text) return '';
      return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    function openInspectorWindow() {
      if (!currentAuditId) return alert('Please run an audit first.');
      window.open(`/inspect/${currentAuditId}`, '_blank');
    }

    function downloadExcelReport() {
      if (!currentIssues || currentIssues.length === 0) return alert('No issues to export.');
      showLoading('Generating WCAG Excel Assessment Report...');
      fetch('/api/export-excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issues: currentIssues, title: 'Patchly WCAG Assessment' })
      })
      .then(res => res.blob())
      .then(blob => {
        hideLoading();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Patchly_Assessment_${Date.now()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch(err => { hideLoading(); alert('Export failed: ' + err.message); });
    }
  </script>
</body>
</html>
"""

# ========================================================
# FLASK ROUTES
# ========================================================

@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception:
        return render_template_string(INDEX_HTML)

@app.route("/api/scan-sample", methods=["GET"])
def api_scan_sample():
    clean_old_audits()
    with open(SAMPLE_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    results = scan_html(content, source_url="Sample Inaccessible Page")
    results["health"] = ml_assistant.compute_accessibility_score(results["issues"])

    audit_id = "sample-" + str(uuid.uuid4())[:8]
    AUDIT_STORE[audit_id] = {
        "html": content,
        "results": results,
        "created_at": time.time()
    }
    results["audit_id"] = audit_id
    return jsonify(results)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    clean_old_audits()
    data = request.get_json() or {}
    url = data.get("url")
    html = data.get("html")
    source_title = data.get("source_title", "Web Audit")

    if url:
        results = scan_url(url)
        content = results.get("html", "")
    elif html:
        results = scan_html(html, source_url=source_title)
        content = html
    else:
        return jsonify({"success": False, "error": "No URL or HTML provided"}), 400

    results["health"] = ml_assistant.compute_accessibility_score(results["issues"])

    audit_id = "scan-" + str(uuid.uuid4())[:8]
    AUDIT_STORE[audit_id] = {
        "html": content,
        "results": results,
        "created_at": time.time()
    }
    results["audit_id"] = audit_id
    return jsonify(results)

@app.route("/api/scan-file", methods=["POST"])
def api_scan_file():
    clean_old_audits()
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    try:
        content = file.read().decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to read file: {str(e)}"}), 400

    results = scan_html(content, source_url=file.filename)
    results["health"] = ml_assistant.compute_accessibility_score(results["issues"])

    audit_id = "upload-" + str(uuid.uuid4())[:8]
    AUDIT_STORE[audit_id] = {
        "html": content,
        "results": results,
        "created_at": time.time()
    }
    results["audit_id"] = audit_id
    return jsonify(results)

@app.route("/inspect/<audit_id>")
def inspect_audit(audit_id):
    audit_data = AUDIT_STORE.get(audit_id)
    if not audit_data:
        if os.path.exists(SAMPLE_FILE_PATH):
            with open(SAMPLE_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            results = scan_html(content, source_url="Sample Inaccessible Page")
            augmented_html = inject_visual_overlay(content, results)
            return Response(augmented_html, mimetype="text/html")
        return Response("Audit session expired or not found. Please re-run the scan.", status=404)

    augmented_html = inject_visual_overlay(audit_data["html"], audit_data["results"])
    return Response(augmented_html, mimetype="text/html")

@app.route("/inspect/sample")
def inspect_sample():
    with open(SAMPLE_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    results = scan_html(content, source_url="Sample Inaccessible Page")
    augmented_html = inject_visual_overlay(content, results)
    return Response(augmented_html, mimetype="text/html")

@app.route("/api/export-excel", methods=["POST"])
def export_excel():
    data = request.get_json() or {}
    issues = data.get("issues", [])
    title = data.get("title", "Accessibility Audit")
    
    excel_stream = generate_accessibility_excel(issues, page_title=title)
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Patchly_Accessibility_Assessment.xlsx"
    )

@app.route("/api/log-false-positive", methods=["POST"])
def api_log_false_positive():
    """
    False Positive Dispute Portal API:
    Allows human reviewers to log false positives with explanations.
    The AI Auditor evaluates the dispute and automatically resolves valid tickets.
    """
    data = request.get_json() or {}
    audit_id = data.get("audit_id")
    flag_id = data.get("flag_id")
    user_explanation = data.get("user_explanation", "").strip()
    logged_by = data.get("logged_by", "Human Auditor").strip() or "Human Auditor"

    if not user_explanation:
        return jsonify({"success": False, "error": "Please provide an explanation for why this is a false positive."}), 400

    audit_session = AUDIT_STORE.get(audit_id)
    target_issue = None

    if audit_session and "results" in audit_session:
        for issue in audit_session["results"].get("issues", []):
            if str(issue.get("flag_id")) == str(flag_id):
                target_issue = issue
                break

    if not target_issue:
        # Standalone or legacy fallback
        target_issue = {
            "flag_id": flag_id or 1,
            "rule_id": data.get("rule_id", "custom-dispute"),
            "title": data.get("title", "Auditor Flagged Barrier"),
            "wcag_sc": data.get("wcag_sc", "WCAG 2.1 Criteria"),
            "section_508": data.get("section_508", "§ 1194.22 / E205.4"),
            "en_301_549": data.get("en_301_549", "Clause 9 Web Accessibility"),
            "severity": data.get("severity", "MODERATE")
        }

    # AI Auditor Evaluation
    ai_eval = ml_assistant.evaluate_false_positive_dispute(
        target_issue,
        user_explanation,
        logged_by=logged_by
    )

    ticket_id = "fp-" + str(uuid.uuid4())[:8]
    ticket = {
        "id": ticket_id,
        "audit_id": audit_id or "standalone",
        "flag_id": target_issue.get("flag_id"),
        "rule_id": target_issue.get("rule_id"),
        "issue_title": target_issue.get("title"),
        "wcag_sc": target_issue.get("wcag_sc"),
        "section_508": target_issue.get("section_508"),
        "en_301_549": target_issue.get("en_301_549"),
        "user_explanation": user_explanation,
        "logged_by": logged_by,
        "logged_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": ai_eval["status"],
        "is_approved": ai_eval["is_approved"],
        "ai_verdict": ai_eval["ai_verdict"],
        "ai_explanation": ai_eval["ai_explanation"],
        "confidence": ai_eval.get("confidence", 0.94)
    }

    # If approved by AI Auditor, mark issue as resolved in audit session & recalculate health score
    if ai_eval["is_approved"] and audit_session:
        target_issue["is_false_positive"] = True
        target_issue["dispute_ticket_id"] = ticket_id
        target_issue["ai_verdict"] = ai_eval["ai_verdict"]

        issues = audit_session["results"]["issues"]
        audit_session["results"]["health"] = ml_assistant.compute_accessibility_score(issues)
        audit_session["results"]["standards_summary"] = compute_standards_summary(issues)
        ticket["updated_health"] = audit_session["results"]["health"]
        ticket["updated_standards"] = audit_session["results"]["standards_summary"]

    FALSE_POSITIVES_STORE.insert(0, ticket)

    return jsonify({
        "success": True,
        "ticket": ticket,
        "audit_updated": audit_session is not None and ai_eval["is_approved"]
    })

@app.route("/api/false-positives", methods=["GET"])
def api_get_false_positives():
    """Returns all logged false positive dispute tickets and their AI resolution status."""
    return jsonify({
        "success": True,
        "total_tickets": len(FALSE_POSITIVES_STORE),
        "tickets": FALSE_POSITIVES_STORE
    })

@app.route("/api/test-run/crawl", methods=["POST"])
def api_test_run_crawl():
    """
    Executes a Multi-Page Crawler Test Run.
    Splits all discovered sub-pages/URLs from entry URL and assesses each page independently.
    """
    data = request.get_json() or {}
    url = data.get("url")
    max_pages = int(data.get("max_pages", 8))

    if not url:
        return jsonify({"success": False, "error": "Please provide a target URL to crawl."}), 400

    result = run_multi_page_test_run(url, max_pages=max_pages)
    return jsonify(result)

@app.route("/api/test-run/folder", methods=["POST"])
def api_test_run_folder():
    """
    Audits a local directory folder containing HTML files as a batch Test Run.
    """
    data = request.get_json() or {}
    folder_path = data.get("folder_path")

    if not folder_path:
        return jsonify({"success": False, "error": "Please provide a local folder path."}), 400

    result = run_folder_test_run(folder_path)
    return jsonify(result)

@app.route("/api/test-runs", methods=["GET"])
def api_get_test_runs():
    """Lists all active batch Test Runs and summary health metrics."""
    return jsonify({
        "success": True,
        "total_test_runs": len(TEST_RUNS_STORE),
        "test_runs": list(TEST_RUNS_STORE.values())
    })

@app.route("/api/test-run/<test_run_id>", methods=["GET"])
def api_get_test_run_detail(test_run_id):
    """Returns detailed split sub-page results for a specific Test Run."""
    test_run = TEST_RUNS_STORE.get(test_run_id)
    if not test_run:
        return jsonify({"success": False, "error": "Test Run not found or expired."}), 404
    return jsonify({"success": True, "test_run": test_run})

if __name__ == "__main__":
    print("🚀 Patchly A11y Server starting at http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
