#!/usr/bin/env python3
import os, sys, time, subprocess, shutil
from datetime import datetime
from urllib.parse import urlparse

# ========= META =========
VERSION = "2.2"

# ========= COLORS =========
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
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
     ONYX ● VULNERABILITY SCANNER v{VERSION}
{RESET}""")

def disclaimer():
    print(f"""{RED}{BOLD}
════════════════════ DISCLAIMER ════════════════════
This tool is for AUTHORIZED security testing ONLY.
Scanning targets without permission is ILLEGAL.
The author takes NO responsibility for misuse.
════════════════════════════════════════════════════
{RESET}""")

def progress(title):
    bar_len = 45
    print(f"\n{CYAN}{BOLD}{title}{RESET}")
    for i in range(101):
        filled = int(bar_len * i / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r[{bar}] {i}%")
        sys.stdout.flush()
        time.sleep(0.02)
    print()

# ========= INSTALLER =========
def detect_pm():
    if shutil.which("apt"): return "apt"
    if shutil.which("pacman"): return "pacman"
    if shutil.which("dnf"): return "dnf"
    return None

def run(cmd):
    subprocess.call(cmd, shell=True)

def ensure_go():
    if shutil.which("go"):
        return True
    ans = input("Go is not installed. Install now? [Y/n]: ").lower().strip()
    if ans == "n":
        return False
    pm = detect_pm()
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

    ans = input(f"{YELLOW}{name} not found. Install it? [Y/n]: {RESET}").lower().strip()
    if ans == "n":
        return False

    pm = detect_pm()

    if name in ["dalfox", "nuclei", "subfinder"]:
        if not ensure_go():
            return False
        run(f"go install github.com/projectdiscovery/{name}/v2/cmd/{name}@latest")
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/go/bin")

    elif name == "sqlmap":
        if pm == "apt":
            run("sudo apt install -y sqlmap")
        else:
            run(f"sudo {pm} -Sy --noconfirm sqlmap")

    elif name == "nikto":
        if pm == "apt":
            run("sudo apt install -y nikto")
        else:
            run(f"sudo {pm} -Sy --noconfirm nikto")

    return shutil.which(name) is not None

# ========= CORE =========
def run_tool(cmd):
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        out = "".join(p.stdout.readlines())
        p.wait()
        return out
    except Exception as e:
        return str(e)

def parse_severity(output):
    sev = {"info":0,"low":0,"medium":0,"high":0,"critical":0}
    for l in output.lower().splitlines():
        if "critical" in l: sev["critical"] += 1
        elif "high" in l: sev["high"] += 1
        elif "medium" in l: sev["medium"] += 1
        elif "low" in l: sev["low"] += 1
        elif "info" in l: sev["info"] += 1
    return sev

def merge(a, b):
    for k in a:
        a[k] += b.get(k, 0)

# ========= SEVERITY EXPLANATION =========
SEVERITY_EXPLANATION = {
    "info": [
        "Server banner disclosure",
        "Technology stack exposure",
        "Subdomain enumeration results"
    ],
    "low": [
        "Missing security headers (X-Frame-Options, CSP)",
        "Insecure cookie flags (HttpOnly / Secure)",
        "Directory listing enabled"
    ],
    "medium": [
        "Reflected XSS",
        "Open Redirect",
        "CSRF without token",
        "Weak CORS configuration"
    ],
    "high": [
        "Stored XSS",
        "SQL Injection (read access)",
        "File upload vulnerability",
        "Authentication bypass"
    ],
    "critical": [
        "SQL Injection (database dump)",
        "Remote Code Execution (RCE)",
        "Unauthenticated admin access",
        "Full system compromise"
    ]
}

# ========= REPORT =========
def print_examples(level, color, emoji):
    print(f"{color}{emoji} {level.upper()} EXAMPLES:{RESET}")
    for item in SEVERITY_EXPLANATION[level]:
        print(f"   - {item}")

def final_report(target, r):
    score = r["critical"]*4 + r["high"]*3 + r["medium"]*2 + r["low"]
    print(f"""{BOLD}
════════════════════ ONYX REPORT ════════════════════
Target   : {target}
Time     : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Score    : {score}
════════════════════════════════════════════════════
{BLUE}ℹ️ INFO      : {r['info']}{RESET}
{YELLOW}🟡 LOW       : {r['low']}{RESET}
{GREEN}🟢 MEDIUM    : {r['medium']}{RESET}
{RED}🔴 HIGH      : {r['high']}{RESET}
{WHITE}💥 CRITICAL  : {r['critical']}{RESET}
════════════════════════════════════════════════════
""")

    print_examples("low", YELLOW, "🟡")
    print_examples("medium", GREEN, "🟢")
    print_examples("high", RED, "🔴")
    print_examples("critical", WHITE, "💥")

# ========= FEATURES =========
def extract_domain(url):
    p = urlparse(url)
    return p.netloc or p.path

def find_subdomains(target):
    ensure_tool("subfinder")
    domain = extract_domain(target)
    progress("Subdomain Discovery")
    out = run_tool(["subfinder", "-silent", "-d", domain])
    subs = out.splitlines()
    print(f"{CYAN}🔍 Found {len(subs)} subdomains{RESET}")
    return {"info":len(subs),"low":0,"medium":0,"high":0,"critical":0}

# ========= SCANS =========
def scan_xss(t):
    ensure_tool("dalfox")
    progress("XSS Scan")
    return parse_severity(run_tool(["dalfox","url",t]))

def scan_sql(t):
    ensure_tool("sqlmap")
    progress("SQL Injection Scan")
    return parse_severity(run_tool(
        ["sqlmap","-u",t,"--dbs","--delay=1","--threads=1","--batch"]
    ))

def scan_nikto(t):
    ensure_tool("nikto")
    progress("Web Server Scan")
    return parse_severity(run_tool(["nikto","-h",t]))

def scan_nuclei(t):
    ensure_tool("nuclei")
    progress("Template Scan")
    return parse_severity(run_tool(["nuclei","-u",t]))

def full_scan(t):
    total = {"info":0,"low":0,"medium":0,"high":0,"critical":0}
    merge(total, find_subdomains(t))
    merge(total, scan_xss(t))
    merge(total, scan_sql(t))
    merge(total, scan_nikto(t))
    merge(total, scan_nuclei(t))
    return total

# ========= MAIN =========
def main():
    clear()
    banner()
    disclaimer()

    target = input(f"{CYAN}TARGET URL:{RESET} ").strip()

    while True:
        print(f"""
{BOLD}[ ONYX PANEL ]{RESET}
[1] Subdomain Discovery
[2] XSS Scan
[3] SQL Injection Scan
[4] Nikto Scan
[5] Nuclei Scan
[6] Full Scan
[0] Exit
""")
        c = input("ONYX > ").strip()

        if c == "1": final_report(target, find_subdomains(target))
        elif c == "2": final_report(target, scan_xss(target))
        elif c == "3": final_report(target, scan_sql(target))
        elif c == "4": final_report(target, scan_nikto(target))
        elif c == "5": final_report(target, scan_nuclei(target))
        elif c == "6": final_report(target, full_scan(target))
        elif c == "0":
            print("ONYX shutting down ⚡")
            break
        else:
            print("Invalid option!")

if __name__ == "__main__":
    main()
