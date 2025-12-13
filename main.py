#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import threading
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from tools.subdomain import run_subdomain
from tools.alive import run_alive
from tools.dalfox import run_dalfox
from tools.sqlmap import run_sqlmap
from tools.nuclei import run_nuclei
from tools.nikto import run_nikto

console = Console()

# ======================================================
# BANNER
# ======================================================
BANNER = r"""
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝ 
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗ 
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
"""

# ======================================================
# DISCLAIMER (PROFESSIONAL)
# ======================================================
DISCLAIMER = """
ONYX v1.6 :: Vulnerability Scanner

LEGAL DISCLAIMER & WARNING:

This tool is designed strictly for EDUCATIONAL PURPOSES and
AUTHORIZED SECURITY TESTING ONLY.

You are STRICTLY PROHIBITED from using this tool against any system,
network, website, or application that you do NOT own or do NOT have
EXPLICIT WRITTEN PERMISSION to test.

Unauthorized scanning, probing, enumeration, or exploitation of systems
may be illegal and could result in severe civil and criminal penalties
under applicable local, national, and international laws.

BY USING THIS TOOL, YOU AGREE THAT:
- You are the lawful owner of the target system, OR
- You have obtained clear, explicit authorization from the system owner
- You accept FULL responsibility for all actions performed using this tool
- The developer and contributors of ONYX SHALL NOT be held liable for
  any misuse, damage, data loss, service disruption, or legal consequences

If you do NOT agree with these terms, DO NOT USE THIS TOOL.

USE RESPONSIBLY. STAY LEGAL. HACK ETHICALLY.
"""

# ======================================================
# SEVERITY
# ======================================================
SEV = {
    "critical": "💀 CRITICAL",
    "high": "🔴 HIGH",
    "medium": "🟡 MEDIUM",
    "low": "🟢 LOW",
    "info": "🔵 INFO",
}

def sev_of(r):
    return (r.get("severity") or "low").lower()

# ======================================================
# PROGRESS RUNNER (SMOOTH & BIG)
# ======================================================
def progress_run(title, func, *args):
    result = None

    with Progress(
        TextColumn(f"[bold cyan]{title}"),
        BarColumn(bar_width=50),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:

        task = progress.add_task(title, total=100)

        def worker():
            nonlocal result
            result = func(*args)
            progress.update(task, completed=100)

        t = threading.Thread(target=worker)
        t.start()

        while t.is_alive():
            progress.advance(task, 1)
            time.sleep(0.1)

        t.join()

    return result

# ======================================================
# FULL SCAN
# ======================================================
def full_scan(target):
    all_results = []

    # 1) Subdomain discovery
    sub_out = progress_run("🌐 Subdomain Discovery", run_subdomain, target)
    if isinstance(sub_out, tuple):
        sub_results, subs = sub_out
        all_results += sub_results
    else:
        subs = []

    # Fallback: kalau subdomain kosong → pakai target URL
    targets = subs if subs else [target]

    # 2) Alive check
    alive = progress_run("⚡ Alive Host Check", run_alive, targets)
    targets = alive if alive else targets
    for u in targets:
        all_results.append({
            "tool": "Alive Check",
            "name": f"Alive host: {u}",
            "severity": "info"
        })

    # 3) Scans per target
    for url in targets:
        all_results += progress_run("🧪 XSS Scan", run_dalfox, url)
        all_results += progress_run("🔍 Nuclei Scan", run_nuclei, url)
        all_results += progress_run("🛡️ Nikto Scan", run_nikto, url)
        all_results += progress_run("💉 SQL Injection Scan", run_sqlmap, url)

    return all_results

# ======================================================
# OUTPUT
# ======================================================
def print_results(results):
    if not results:
        console.print("\n[green]✔ No vulnerabilities found[/green]")
        return

    console.print("\n[bold red]🚨 VULNERABILITIES FOUND[/bold red]")
    order = ["critical", "high", "medium", "low", "info"]
    for sev in order:
        for r in results:
            if sev_of(r) == sev:
                console.print(f"{SEV[sev]} → {r['name']} ({r['tool']})")

def print_summary(results):
    summary = {k: 0 for k in SEV}
    for r in results:
        summary[sev_of(r)] += 1

    console.print("\n[bold cyan]📊 RISK SUMMARY[/bold cyan]")
    for k in ["critical", "high", "medium", "low", "info"]:
        console.print(f"{SEV[k]}: {summary[k]}")

# ======================================================
# MAIN
# ======================================================
def main():
    console.clear()
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(f"[dim]{DISCLAIMER}[/dim]\n")

    target = console.input("🎯 Target URL: ").strip()
    if not target:
        console.print("[red]Target URL is required[/red]")
        return

    console.print("""
SELECT SCAN TYPE

[1] 🚀 FULL SCAN (Subdomain → Alive → Auto Scan)
[2] 🌐 Subdomain Discovery Only
[3] 🧪 XSS Scan (URL)
[4] 💉 SQL Injection Scan (URL)
[5] 🔍 Nuclei Scan (URL)
[6] 🛡️ Nikto Scan (URL)
""")

    choice = console.input("Select option: ").strip()
    results = []

    if choice == "1":
        results = full_scan(target)
    elif choice == "2":
        out = progress_run("🌐 Subdomain Discovery", run_subdomain, target)
        results = out[0] if isinstance(out, tuple) else out
    elif choice == "3":
        results = progress_run("🧪 XSS Scan", run_dalfox, target)
    elif choice == "4":
        results = progress_run("💉 SQL Injection Scan", run_sqlmap, target)
    elif choice == "5":
        results = progress_run("🔍 Nuclei Scan", run_nuclei, target)
    elif choice == "6":
        results = progress_run("🛡️ Nikto Scan", run_nikto, target)
    else:
        console.print("[red]Invalid option[/red]")
        return

    print_results(results)
    print_summary(results)
    console.print("\n[bold green]✅ SCAN COMPLETED[/bold green]")

if __name__ == "__main__":
    main()
