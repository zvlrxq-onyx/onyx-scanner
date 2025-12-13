#!/usr/bin/env python3
import os, sys, time, subprocess, shutil
from datetime import datetime
from urllib.parse import urlparse

# ========= META =========
VERSION = "2.1"

# ========= COLOR =========
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
Authorized testing ONLY.
Scanning targets without permission is illegal.
You are fully responsible for all actions taken.
════════════════════════════════════════════════════
{RESET}""")

def progress(title):
    bar_len = 42
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
    if shutil.which("apt"): return "apt"
    if shutil.which("pacman"): return "pacman"
    if shutil.which("dnf"): return "dnf"
    return None

def run(cmd):
    subprocess.call(cmd, shell=True)

def ensure_go():
    if shutil.which("go"): return True
    ans = input("Go is not installed. Install now? [Y/n]: ").lower().strip()
    if ans == "n": return False
    pm = detect_pkg_manager()
    if pm == "apt": run("sudo apt update && sudo apt install -y golang")
    elif pm == "pacman": run("sudo pacman -Sy --noconfirm go")
    elif pm == "dnf": run("sudo dnf install -y golang")
    return shutil.which("go") is not None

def ensure_tool(name):
    if shutil.which(name): return True
    ans = input(f"{YELLOW}{name} not found. Install it? [Y/n]: {RESET}").lower().strip()
    if ans == "n": return False
    pm = detect_pkg_manager()

    if name in ["dalfox", "nuclei", "subfinder"]:
        if not ensure_go(): return False
        run(f"go install github.com/projectdiscovery/{name}/v2/cmd/{name}@latest")
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/go/bin")
    elif name == "sqlmap":
        run(f"sudo {pm} install -y sqlmap" if pm == "apt" else f"sudo {pm} -Sy --noconfirm sqlmap")
    elif name == "nikto":
        run(f"sudo {pm} install -y nikto" if pm == "apt" else f"sudo {pm} -Sy --noconfirm nikto")

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

def merge(t, c):
    for k in t: t[k] += c.get(k,0)

# ========= EXPLANATION =========
SEVERITY_DESC = {
    "info": "ℹ️ Informational findings, no direct risk.",
    "low": "🟡 Minor issue, limited impact, fix when possible.",
    "medium": "🟢 Moderate risk, could be exploited in certain conditions.",
    "high": "🔴 Serious vulnerability, high chance of exploitation.",
    "critical": "💥 Critical impact, immediate exploitation possible!"
}

# ========= REPORT =========
def final_report(target, r):
    score = r["critical"]*4 + r["high"]*3 + r["medium"]*2 + r["low"]
    print(f"""{BOLD}
════════════════════ ONYX REPORT ════════════════════
Target    : {target}
Time      : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Score     : {score}
════════════════════════════════════════════════════
{BLUE}ℹ️ INFO      : {r['info']}  — {SEVERITY_DESC['info']}{RESET}
{YELLOW}🟡 LOW       : {r['low']}   — {SEVERITY_DESC['low']}{RESET}
{GREEN}🟢 MEDIUM    : {r['medium']}— {SEVERITY_DESC['medium']}{RESET}
{RED}🔴 HIGH      : {r['high']}  — {SEVERITY_DESC['high']}{RESET}
{WHITE}💥 CRITICAL  : {r['critical']}— {SEVERITY_DESC['critical']}{RESET}
════════════════════════════════════════════════════
""")

# ========= FEATURES =========
def extract_domain(url):
    p = urlparse(url)
    return p.netloc or p.path

def find_subdomains(target):
    ensure_tool("subfinder")
    domain = extract_domain(target)
    progress("Subdomain Discovery (subfinder)")
    out = run_tool(["subfinder", "-silent", "-d", domain])
    subs = [s for s in out.splitlines() if s.strip()]
    print(f"{CYAN}🔍 Found {len(subs)} subdomains{RESET}")
    for s in subs[:20]:
        print(f" - {s}")
    return {"info":len(subs),"low":0,"medium":0,"high":0,"critical":0}

# ========= SCANS =========
def scan_xss(t):
    ensure_tool("dalfox")
    progress("XSS Scan (Dalfox)")
    return parse_severity(run_tool(["dalfox","url",t]))

def scan_sql(t):
    ensure_tool("sqlmap")
    progress("SQL Injection Scan (SQLMap)")
    return parse_severity(run_tool(["sqlmap","-u",t,"--dbs","--delay=1","--threads=1","--batch"]))

def scan_nikto(t):
    ensure_tool("nikto")
    progress("Web Server Scan (Nikto)")
    return parse_severity(run_tool(["nikto","-h",t]))

def scan_nuclei(t):
    ensure_tool("nuclei")
    progress("Template Scan (Nuclei)")
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
    clear(); banner(); disclaimer()
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
        elif c == "0": break
        else: print("Invalid option!")

if __name__ == "__main__":
    main()
