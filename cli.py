"""
Patchly CLI - Command Line Accessibility Auditor
Audit any HTML file or live URL directly from the terminal with colored output
and automated Excel report generation.

Usage:
  python cli.py sample_inaccessible_page.html
  python cli.py sample_inaccessible_page.html --export audit.xlsx
  python cli.py https://example.com --export audit.xlsx
"""

import sys
import os
import argparse
from colorama import init, Fore, Style

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

init(autoreset=True)

from engine.scanner import scan_html, scan_url
from engine.excel_exporter import generate_accessibility_excel
from engine.ml_assistant import ml_assistant

def main():
    parser = argparse.ArgumentParser(
        description="Patchly - Automated Web Accessibility Auditor (WCAG 2.1 AA)"
    )
    parser.add_argument("target", help="Local HTML file path or Web URL to audit")
    parser.add_argument("--export", "-e", help="Output path for Excel report (.xlsx)", default=None)
    
    args = parser.parse_args()
    target = args.target

    print(f"\n{Fore.CYAN}{Style.BRIGHT}==================================================")
    print(f"  [*] PATCHLY A11Y SCANNER - WCAG 2.1 AA AUDIT")
    print(f"=================================================={Style.RESET_ALL}")
    print(f"Scanning Target: {Fore.YELLOW}{target}{Style.RESET_ALL}\n")

    if target.startswith("http://") or target.startswith("https://"):
        results = scan_url(target)
    else:
        if not os.path.exists(target):
            print(f"{Fore.RED}Error: File '{target}' does not exist.{Style.RESET_ALL}")
            sys.exit(1)
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        results = scan_html(content, source_url=target)

    if not results.get("success"):
        print(f"{Fore.RED}Audit Failed: {results.get('error')}{Style.RESET_ALL}")
        sys.exit(1)

    issues = results.get("issues", [])
    health = ml_assistant.compute_accessibility_score(issues)

    print(f"Found {Fore.MAGENTA}{len(issues)} Accessibility Flags{Style.RESET_ALL}:")
    print(f"  Critical: {Fore.RED}{results['severity_summary'].get('CRITICAL', 0)}{Style.RESET_ALL}")
    print(f"  Serious:  {Fore.YELLOW}{results['severity_summary'].get('SERIOUS', 0)}{Style.RESET_ALL}")
    print(f"  Moderate: {Fore.BLUE}{results['severity_summary'].get('MODERATE', 0)}{Style.RESET_ALL}\n")

    print(f"A11y Health Score: {Fore.CYAN}{health['score']}/100 (Grade: {health['grade']}){Style.RESET_ALL}")
    print(f"Compliance Status: {Fore.WHITE}{health['status']}{Style.RESET_ALL}")
    print(f"Estimated Remediation: {Fore.YELLOW}{health['estimated_remediation_hours']} hours{Style.RESET_ALL}\n")

    print(f"{Fore.CYAN}--- VIOLATIONS & QUICK FIXES ---{Style.RESET_ALL}")
    for issue in issues:
        sev = issue.get("severity", "MODERATE")
        color = Fore.RED if sev == "CRITICAL" else (Fore.YELLOW if sev == "SERIOUS" else Fore.BLUE)
        print(f"{color}[{issue['flag_badge']} {sev}]{Style.RESET_ALL} {Style.BRIGHT}{issue['title']}{Style.RESET_ALL}")
        print(f"  WCAG: {issue.get('wcag_sc')}")
        print(f"  Info: {issue.get('description')}")
        if issue.get("quick_fix_code"):
            print(f"  {Fore.GREEN}Quick Fix:{Style.RESET_ALL}")
            for line in issue.get("quick_fix_code").split("\n")[:4]:
                print(f"    {Fore.GREEN}{line}{Style.RESET_ALL}")
        print()

    # Excel export
    if args.export:
        out_path = args.export
        if not out_path.endswith(".xlsx"):
            out_path += ".xlsx"
        print(f"Exporting Excel assessment sheet to {Fore.GREEN}{out_path}{Style.RESET_ALL}...")
        stream = generate_accessibility_excel(issues, page_title=os.path.basename(target))
        with open(out_path, "wb") as f:
            f.write(stream.read())
        print(f"{Fore.GREEN}[OK] Excel audit workbook saved successfully!{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()
