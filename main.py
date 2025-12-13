#!/usr/bin/env python3
import subprocess
import sys
import time
import shutil
from datetime import datetime

# ========== COLORS ==========
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
WHITE = "\033[97m"

# ========== GLOBAL ==========
VERSION = "3.0.2"
REPORT = {
    "INFO": [],
    "LOW": [],
    "MEDIUM": [],
    "HIGH": [],
    "CRITICAL": []
}

# ========== UI ==========
def banner():
    print(CYAN + BOLD + r"""
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
   ONYX ● VULNERABILITY SCANNER v""" + VERSION + RESET)

def disclaimer():
    print(WHITE + """
════════════════════════════════════════════════════
⚠️  LEGAL DISCLAIMER
════════════════════════════════════════════════════
This tool is intended for AUTHORIZED security testing
and educational purposes ONLY.

Use ONLY on systems you own or have explicit permission.
Unauthorized usage is strictly prohibited.

The developer assumes NO liability.
You are fully responsible for your actions.
════════════════════════════════════════════════════
""" + RESET)

# ========== PROGRESS ENGINE ==========
def run_cmd(cmd, title, min_time=4):
    print(CYAN + BOLD + title + RESET)

    start = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    output = []
    width = 40
    pct = 0

    while proc.poll() is None:
        pct = min(pct + 1, 90)
        filled = int(width * pct / 100)
        bar = "█" * filled + "░" * (width - filled)
        sys.stdout.write(f"\r[{bar}] {pct}% scanning...")
        sys.stdout.flush()
        time.sleep(0.12)

    # smooth finish
    while time.time() - start < min_time:
        pct = min(pct + 1, 99)
        filled = int(width * pct / 100)
        bar = "█" * filled + "░" * (width - filled)
        sys.stdout.write(f"\r[{bar}] {pct}% finalizing...")
        sys.stdout.flush()
        time.sleep(0.1)

    for line in proc.stdout.read().splitlines():
        output.append(line)

    sys.stdout.write(f"\r[{'█'*width}] 100% completed ✔️\n\n")
    return output

# ========== PARSERS ==========
def parse_sqlmap(lines):
    for l in lines:
        s = l.lower()
        if "type:" in s and "blind" in s:
            REPORT["CRITICAL"].append(l.strip())
        elif "payload:" in s:
            REPORT["HIGH"].append(l.strip())
        elif "warning" in s:
            REPORT["LOW"].append(l.strip())

def parse_dalfox(lines):
    for l in lines:
        s = l.lower()

        # ignore help / flags
        if s.strip().startswith("--"):
            continue

        if "[poc]" in s or "vulnerable" in s:
            REPORT["CRITICAL"].append(l.strip())

def parse_nmap(lines):
    for l in lines:
        if "/tcp" in l and "open" in l:
            REPORT["INFO"].append(l.strip())

def parse_nikto(lines):
    for l in lines:
        if "+ " in l:
            REPORT["LOW"].append(l.strip())

# ========== REPORT ==========
def show_report(target):
    print(WHITE + BOLD + "════════════════════ ONYX REPORT ════════════════════")
    print(f"Target : {target}")
    print(f"Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("════════════════════════════════════════════════════" + RESET)

    for level, color, icon in [
        ("INFO", BLUE, "ℹ️"),
        ("LOW", YELLOW, "🟡"),
        ("MEDIUM", GREEN, "🟢"),
        ("HIGH", RED, "🔴"),
        ("CRITICAL", RED, "💥")
    ]:
        items = REPORT[level]
        print(color + f"\n{icon} {level} ({len(items)})" + RESET)
        for i in items:
            print("   - " + i)

# ========== SCANS ==========
def sql_scan(target):
    if not shutil.which("sqlmap"):
        print(RED + "sqlmap not installed!" + RESET)
        return
    lines = run_cmd(
        ["sqlmap", "-u", target, "--batch", "--dbs"],
        "SQL Injection Scan (SQLMap)"
    )
    parse_sqlmap(lines)

def xss_scan(target):
    if not shutil.which("dalfox"):
        print(RED + "dalfox not installed!" + RESET)
        return
    lines = run_cmd(
        ["dalfox", "url", target],
        "XSS Scan (Dalfox)"
    )
    parse_dalfox(lines)

def nmap_scan(target):
    host = target.replace("http://", "").replace("https://", "").split("/")[0]
    lines = run_cmd(
        ["nmap", "-Pn", host],
        "Port Scan (Nmap)"
    )
    parse_nmap(lines)

def nikto_scan(target):
    if not shutil.which("nikto"):
        print(RED + "nikto not installed!" + RESET)
        return
    lines = run_cmd(
        ["nikto", "-h", target],
        "Nikto Scan"
    )
    parse_nikto(lines)

# ========== MENU ==========
def menu():
    print("""
[ ONYX CONTROL PANEL ]
[1] SQL Injection Scan
[2] XSS Scan
[3] Port Scan (Nmap)
[4] Nikto Scan
[5] Full Scan
[0] Exit
""")

# ========== MAIN ==========
def main():
    banner()
    disclaimer()
    target = input(CYAN + "TARGET URL: " + RESET).strip()

    while True:
        menu()
        c = input(CYAN + "ONYX > " + RESET).strip()

        if c == "1":
            sql_scan(target)
            show_report(target)
        elif c == "2":
            xss_scan(target)
            show_report(target)
        elif c == "3":
            nmap_scan(target)
            show_report(target)
        elif c == "4":
            nikto_scan(target)
            show_report(target)
        elif c == "5":
            sql_scan(target)
            xss_scan(target)
            nmap_scan(target)
            nikto_scan(target)
            show_report(target)
        elif c == "0":
            sys.exit()
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
