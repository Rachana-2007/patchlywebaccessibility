"""
Patchly - Multi-Page Crawler & Batch Test Run Engine
Extracts internal pages from URLs or local folders, splits them into individual Test Run assessments,
and aggregates WCAG, Section 508, and EN 301 549 compliance metrics across all sub-pages.
"""

import os
import re
import uuid
import time
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, List, Set
from bs4 import BeautifulSoup
import requests

from engine.scanner import scan_html, scan_url
from engine.ml_assistant import ml_assistant
from engine.standards_mapper import compute_standards_summary

# In-memory storage for batch Test Runs
TEST_RUNS_STORE = {}

def extract_internal_links(base_url: str, html_content: str, max_pages: int = 15) -> List[str]:
    """
    Parses HTML content of a webpage and extracts all unique internal page destinations
    accessible via navigation links, dropdown menus, header buttons, form actions, and click handlers.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc.lower()

    discovered_urls: Set[str] = {base_url}

    def process_target_url(raw_target: str):
        if not raw_target:
            return
        raw_target = raw_target.strip()
        if raw_target.startswith('#') or raw_target.startswith('javascript:') or raw_target.startswith('mailto:') or raw_target.startswith('tel:'):
            return
        
        # Check for extracted JS location redirects e.g. location.href='/page'
        js_match = re.search(r'''(?:location\.href|window\.open)\s*=\s*['"]([^'"]+)['"]''', raw_target)
        if js_match:
            raw_target = js_match.group(1)

        full_url = urljoin(base_url, raw_target)
        parsed_target = urlparse(full_url)

        if parsed_target.scheme in ['http', 'https'] and parsed_target.netloc.lower() == base_domain:
            clean_url = full_url.split('#')[0]
            discovered_urls.add(clean_url)

    # 1. Standard <a> links (including navbar dropdown menus and sub-navigation links)
    for a_tag in soup.find_all('a', href=True):
        process_target_url(a_tag['href'])
        if len(discovered_urls) >= max_pages:
            break

    # 2. Buttons with data-url, data-href, formaction, or onclick redirects
    if len(discovered_urls) < max_pages:
        for btn in soup.find_all(['button', 'input', 'div'], attrs={'onclick': True}):
            process_target_url(btn['onclick'])
            if len(discovered_urls) >= max_pages:
                break

    for btn in soup.find_all(['button', 'a', 'div'], attrs=re.compile(r'data-(url|href|target)')):
        for attr in ['data-url', 'data-href', 'data-target']:
            if btn.has_attr(attr):
                process_target_url(btn[attr])
                break
        if len(discovered_urls) >= max_pages:
            break

    # 3. Form action destinations
    if len(discovered_urls) < max_pages:
        for form in soup.find_all('form', action=True):
            process_target_url(form['action'])
            if len(discovered_urls) >= max_pages:
                break

    return list(discovered_urls)

def run_multi_page_test_run(target_url: str, max_pages: int = 8) -> Dict[str, Any]:
    """
    Executes a Multi-Page Crawler Test Run.
    Fetches the entry URL, extracts internal sub-page links, splits them into individual assessments,
    and calculates unified accessibility health & multi-standard compliance.
    """
    test_run_id = "tr-url-" + str(uuid.uuid4())[:8]
    start_time = time.time()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Patchly-Accessibility-Bot/1.0'
    }

    try:
        entry_resp = requests.get(target_url, headers=headers, timeout=10)
        entry_resp.raise_for_status()
        entry_html = entry_resp.text
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to connect to primary URL '{target_url}': {str(e)}"
        }

    # Discover and split internal sub-pages
    sub_urls = extract_internal_links(target_url, entry_html, max_pages=max_pages)

    pages_audited = []
    all_issues_combined = []

    for idx, page_url in enumerate(sub_urls, start=1):
        try:
            if page_url == target_url:
                page_results = scan_html(entry_html, source_url=target_url)
            else:
                page_results = scan_url(page_url)

            if page_results.get("success"):
                health = ml_assistant.compute_accessibility_score(page_results["issues"])
                pages_audited.append({
                    "sub_page_id": f"page-{idx}",
                    "url": page_url,
                    "title": page_results.get("source", page_url),
                    "total_flags": page_results.get("total_flags", 0),
                    "health": health,
                    "severity_summary": page_results.get("severity_summary", {}),
                    "issues": page_results.get("issues", [])
                })
                all_issues_combined.extend(page_results.get("issues", []))
        except Exception as err:
            pages_audited.append({
                "sub_page_id": f"page-{idx}",
                "url": page_url,
                "error": str(err),
                "total_flags": 0,
                "health": {"score": 0, "grade": "F", "status": "Fetch Error"},
                "issues": []
            })

    overall_health = ml_assistant.compute_accessibility_score(all_issues_combined)
    overall_standards = compute_standards_summary(all_issues_combined)

    test_run_data = {
        "success": True,
        "test_run_id": test_run_id,
        "name": f"Test Run: {target_url}",
        "type": "LIVE_URL_CRAWL",
        "entry_url": target_url,
        "total_pages_split": len(sub_urls),
        "total_flags_combined": len(all_issues_combined),
        "overall_health": overall_health,
        "overall_standards": overall_standards,
        "pages_audited": pages_audited,
        "duration_seconds": round(time.time() - start_time, 2),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    TEST_RUNS_STORE[test_run_id] = test_run_data
    return test_run_data

def run_folder_test_run(folder_path: str) -> Dict[str, Any]:
    """
    Audits a local directory containing HTML files as a batch Test Run.
    Splits all .html files in the folder into separate sub-page assessments.
    """
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return {
            "success": False,
            "error": f"Directory '{folder_path}' does not exist or is not a valid folder."
        }

    test_run_id = "tr-folder-" + str(uuid.uuid4())[:8]
    start_time = time.time()

    html_files = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(('.html', '.htm')):
                html_files.append(os.path.join(root, f))

    if not html_files:
        return {
            "success": False,
            "error": f"No .html files found in directory '{folder_path}'."
        }

    pages_audited = []
    all_issues_combined = []

    for idx, file_path in enumerate(html_files, start=1):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            rel_name = os.path.relpath(file_path, folder_path)
            page_results = scan_html(content, source_url=rel_name)

            if page_results.get("success"):
                health = ml_assistant.compute_accessibility_score(page_results["issues"])
                pages_audited.append({
                    "sub_page_id": f"file-{idx}",
                    "url": rel_name,
                    "title": rel_name,
                    "total_flags": page_results.get("total_flags", 0),
                    "health": health,
                    "severity_summary": page_results.get("severity_summary", {}),
                    "issues": page_results.get("issues", [])
                })
                all_issues_combined.extend(page_results.get("issues", []))
        except Exception as err:
            pages_audited.append({
                "sub_page_id": f"file-{idx}",
                "url": file_path,
                "error": str(err),
                "total_flags": 0,
                "health": {"score": 0, "grade": "F", "status": "File Read Error"},
                "issues": []
            })

    overall_health = ml_assistant.compute_accessibility_score(all_issues_combined)
    overall_standards = compute_standards_summary(all_issues_combined)

    folder_name = os.path.basename(os.path.abspath(folder_path))
    test_run_data = {
        "success": True,
        "test_run_id": test_run_id,
        "name": f"Folder Test Run: {folder_name}",
        "type": "LOCAL_FOLDER_BATCH",
        "folder_path": folder_path,
        "total_pages_split": len(html_files),
        "total_flags_combined": len(all_issues_combined),
        "overall_health": overall_health,
        "overall_standards": overall_standards,
        "pages_audited": pages_audited,
        "duration_seconds": round(time.time() - start_time, 2),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    TEST_RUNS_STORE[test_run_id] = test_run_data
    return test_run_data
