#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from datetime import datetime

# ========= COLORS =========
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ========= UI =========
def clear():
    os.system("clear" if os.name != "nt" else "cls")

def banner():
    print(f"""{CYAN}{BOLD}
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
   ONYX ● VULNERABILITY SCANNER v2.7
{RESET}""")

def disclaimer():
    print(f"""{BLUE}{BOLD}
════════════════════════════════════════════════════
AUTHORIZED SECURITY TESTING ONLY.
Use only on assets you own or have permission for.
You are responsible for any misuse.
════════════════════════════════════════════════════
{RESET}""")

# ========= SMART PROGRESS =========
def smart_progress(proc, title):
    width = 40
    percent = 0
    print(f"{CYAN}{BOLD}{title}{RESET}")
    while proc.poll() is None:
        percent = min(percent + 1, 95)
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        sys.stdout.write(f"\r[{bar}] {percent}% running...")
        sys.stdout.flush()
        time.sleep(0.4)
    sys.stdout.write(f"\r[{'█'*width}] 100% completed ✔️\n")

# ========= RUN TOOL =========
def run_tool(cmd, title):
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    smart_progress(proc, title)
    output = proc.communicate()[0]
    return output

# ========= PARSER (FIXED) =========
def parse_severity(output, tool):
    sev = {"info": [], "low": [], "medium": [], "high": [], "critical": []}

    for line in output.splitlines():
        l = line.lower().strip()

        # Skip noise
        if not l or l.startswith(("__", "|_", "[*] starting", "[*] ending")):
            continue

        # ===== SQLMAP =====
        if tool == "sql":
            if any(k in l for k in [
                "boolean-based blind",
                "error-based",
                "time-based blind",
                "union query",
                "available databases"
            ]):
                sev["critical"].append(line)

            elif any(k in l for k in [
                "payload:",
                "parameter:",
                "back-end dbms"
            ]):
                sev["high"].append(line)

            elif "xss" in l:
                sev["medium"].append(line)

            elif "[warning]" in l:
                sev["low"].append(line)

            else:
                pass  # ignore sqlmap banner/log spam

        # ===== DALFOX =====
        elif tool == "xss":
            if "stored xss" in l:
                sev["high"].append(line)
            elif "reflected xss" in l:
                sev["medium"].append(line)
            elif "xss" in l:
                sev["medium"].append(line)

        # ===== NIKTO / NUCLEI =====
        elif tool in ("nikto", "nuclei"):
            if "critical" in l:
                sev["critical"].append(line)
            elif "high" in l:
                sev["high"].append(line)
            elif "medium" in l:
                sev["medium"].append(line)
            elif "missing" in l:
                sev["low"].append(line)

        # ===== NMAP =====
        elif tool == "nmap":
            if "open" in l:
                sev["info"].append(f"Open service: {line}")

    return sev

def merge(dst, src):
    for k in dst:
        dst[k].extend(src[k])

# ========= SCANS =========
def scan_sql(target):
    cmd = [
        "sqlmap", "-u", target,
        "--batch", "--level=5", "--risk=3",
        "--dbs", "--random-agent",
        "--answers=follow=N"
    ]
    out = run_tool(cmd, "SQL Injection Scan (SQLMap)")
    return parse_severity(out, "sql")

def scan_xss(target):
    out = run_tool(
        ["dalfox", "url", target, "--auto"],
        "XSS Scan (Dalfox)"
    )
    return parse_severity(out, "xss")

def scan_nikto(target):
    out = run_tool(["nikto", "-h", target], "Nikto Scan")
    return parse_severity(out, "nikto")

def scan_nmap(target):
    out = run_tool(["nmap", "-Pn", target], "Port Scan (Nmap)")
    return parse_severity(out, "nmap")

# ========= REPORT =========
def report(target, sev):
    print(f"\n{BOLD}════════════════════ ONYX REPORT ════════════════════{RESET}")
    print(f"Target : {target}")
    print(f"Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("════════════════════════════════════════════════════\n")

    print(f"💥 CRITICAL ({len(sev['critical'])})")
    for i in sev["critical"]:
        print(f"   - {i}")

    print(f"\n🔴 HIGH ({len(sev['high'])})")
    for i in sev["high"]:
        print(f"   - {i}")

    print(f"\n🟢 MEDIUM ({len(sev['medium'])})")
    for i in sev["medium"]:
        print(f"   - {i}")

    print(f"\n🟡 LOW ({len(sev['low'])})")
    for i in sev["low"]:
        print(f"   - {i}")

    print()

# ========= MAIN =========
def main():
    clear()
    banner()
    disclaimer()

    target = input(f"{YELLOW}TARGET URL:{RESET} ").strip()

    while True:
        print(f"""
{BOLD}[ ONYX PANEL ]{RESET}
[1] SQL Injection Scan
[2] XSS Scan
[3] Port Scan (Nmap)
[4] Nikto Scan
[5] Full Scan
[0] Exit
""")

        c = input("ONYX > ").strip()

        if c == "1":
            report(target, scan_sql(target))
        elif c == "2":
            report(target, scan_xss(target))
        elif c == "3":
            report(target, scan_nmap(target))
        elif c == "4":
            report(target, scan_nikto(target))
        elif c == "5":
            total = {"info": [], "low": [], "medium": [], "high": [], "critical": []}
            merge(total, scan_sql(target))
            merge(total, scan_xss(target))
            merge(total, scan_nmap(target))
            merge(total, scan_nikto(target))
            report(target, total)
        elif c == "0":
            print(f"{GREEN}Exiting ONYX... ⚡{RESET}")
            break
        else:
            print(f"{RED}Invalid option{RESET}")

if __name__ == "__main__":
    main()
