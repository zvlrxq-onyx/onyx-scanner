#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from datetime import datetime
import shutil

# ========= COLOR =========
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
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
      ONYX ● VULNERABILITY SCANNER
{RESET}""")

def disclaimer():
    print(f"""{RED}{BOLD}
════════════════════ DISCLAIMER ════════════════════
This tool is intended ONLY for AUTHORIZED testing.

Unauthorized scanning, probing, or exploitation of
systems you do NOT own or have permission to test
is ILLEGAL and may result in criminal charges.

The author assumes NO responsibility for misuse.
By continuing, YOU accept full legal responsibility.
═════════════════════════════════════════════════════
{RESET}""")

def progress(title):
    bar_len = 40
    print(f"\n{CYAN}{BOLD}{title}{RESET}")
    for i in range(101):
        filled = int(bar_len * i / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r[{bar}] {i}%")
        sys.stdout.flush()
        time.sleep(0.02)
    print()

# ========= INSTALLER =========
def detect_pkg_manager():
    if shutil.which("apt"):
        return "apt"
    if shutil.which("pacman"):
        return "pacman"
    if shutil.which("dnf"):
        return "dnf"
    return None

def run(cmd):
    subprocess.call(cmd, shell=True)

def ensure_go():
    if shutil.which("go"):
        return True

    pm = detect_pkg_manager()
    if not pm:
        print(f"{RED}[-] Cannot detect package manager. Install Go manually.{RESET}")
        return False

    ans = input("Go is not installed. Do you want to install Go now? [Y/n]: ").strip().lower()
    if ans == "n":
        return False

    print(f"{CYAN}[+] Installing Go...{RESET}")
    if pm == "apt":
        run("sudo apt update && sudo apt install -y golang")
    elif pm == "pacman":
        run("sudo pacman -Sy --noconfirm go")
    elif pm == "dnf":
        run("sudo dnf install -y golang")

    return shutil.which("go") is not None

def ensure_tool(name):
    if shutil.which(name):
        return True

    ans = input(f"{YELLOW}{name} is not installed. Do you want to install it? [Y/n]: {RESET}").strip().lower()
    if ans == "n":
        return False

    pm = detect_pkg_manager()

    if name in ["dalfox", "nuclei"]:
        if not ensure_go():
            return False
        print(f"{CYAN}[+] Installing {name} via go install...{RESET}")
        run(f"go install github.com/projectdiscovery/{name}/v2/cmd/{name}@latest")
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/go/bin")

    elif name == "sqlmap":
        if pm == "apt":
            run("sudo apt install -y sqlmap")
        elif pm == "pacman":
            run("sudo pacman -Sy --noconfirm sqlmap")
        elif pm == "dnf":
            run("sudo dnf install -y sqlmap")

    elif name == "nikto":
        if pm == "apt":
            run("sudo apt install -y nikto")
        elif pm == "pacman":
            run("sudo pacman -Sy --noconfirm nikto")
        elif pm == "dnf":
            run("sudo dnf install -y nikto")

    return shutil.which(name) is not None

# ========= CORE =========
def run_tool(cmd):
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        out = ""
        for line in proc.stdout:
            out += line
        proc.wait()
        return out
    except Exception as e:
        return str(e)

def parse_severity(output):
    sev = {"low":0,"medium":0,"high":0,"critical":0}
    for line in output.lower().splitlines():
        if "critical" in line: sev["critical"] += 1
        elif "high" in line: sev["high"] += 1
        elif "medium" in line: sev["medium"] += 1
        elif "low" in line: sev["low"] += 1
    return sev

def merge(total, cur):
    for k in total:
        total[k] += cur[k]

# ========= REPORT =========
def final_report(target, res):
    score = res["critical"]*4 + res["high"]*3 + res["medium"]*2 + res["low"]

    status, color = "SECURE", GREEN
    if res["critical"] > 0:
        status, color = "CRITICAL", RED
    elif res["high"] > 0:
        status, color = "HIGH RISK", RED
    elif res["medium"] > 0:
        status, color = "MEDIUM RISK", YELLOW

    print(f"""{color}{BOLD}
════════════════════ ONYX REPORT ════════════════════
Target     : {target}
Scan Time : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Low        : {res['low']}
Medium     : {res['medium']}
High       : {res['high']}
Critical   : {res['critical']}

Risk Score : {score}
Status     : {status}
═════════════════════════════════════════════════════
{RESET}""")

# ========= SCANS =========
def scan_xss(target):
    ensure_tool("dalfox")
    progress("XSS Scan (Dalfox)")
    return parse_severity(run_tool(["dalfox", "url", target]))

def scan_sql(target):
    ensure_tool("sqlmap")
    progress("SQL Injection Scan (SQLMap)")
    cmd = ["sqlmap", "-u", target, "--dbs", "--delay=1", "--threads=1", "--batch"]
    return parse_severity(run_tool(cmd))

def scan_nikto(target):
    ensure_tool("nikto")
    progress("Web Server Scan (Nikto)")
    return parse_severity(run_tool(["nikto", "-h", target]))

def scan_nuclei(target):
    ensure_tool("nuclei")
    progress("Template Scan (Nuclei)")
    return parse_severity(run_tool(["nuclei", "-u", target]))

def full_scan(target):
    total = {"low":0,"medium":0,"high":0,"critical":0}
    merge(total, scan_xss(target))
    merge(total, scan_sql(target))
    merge(total, scan_nikto(target))
    merge(total, scan_nuclei(target))
    return total

# ========= MAIN =========
def main():
    clear()
    banner()
    disclaimer()

    target = input(f"{YELLOW}TARGET URL:{RESET} ").strip()

    while True:
        print(f"""
{BOLD}[ ONYX CONTROL PANEL ]{RESET}
[1] XSS Scan
[2] SQL Injection Scan
[3] Nikto Scan
[4] Nuclei Scan
[5] Full Scan
[0] Exit
""")

        c = input("ONYX > ").strip()

        if c == "1": final_report(target, scan_xss(target))
        elif c == "2": final_report(target, scan_sql(target))
        elif c == "3": final_report(target, scan_nikto(target))
        elif c == "4": final_report(target, scan_nuclei(target))
        elif c == "5": final_report(target, full_scan(target))
        elif c == "0":
            print(f"{GREEN}ONYX shutting down... ⚡{RESET}")
            break
        else:
            print(f"{RED}Invalid option!{RESET}")

if __name__ == "__main__":
    main()
