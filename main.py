#!/usr/bin/env python3
import os, sys, time, subprocess, shutil, re
from datetime import datetime
from urllib.parse import urlparse

VERSION = "2.4"

# ========= COLORS =========
CYAN="\033[96m"; BLUE="\033[94m"; GREEN="\033[92m"
YELLOW="\033[93m"; RED="\033[91m"; WHITE="\033[97m"
BOLD="\033[1m"; RESET="\033[0m"

# ========= UI =========
def clear():
    os.system("clear" if os.name!="nt" else "cls")

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
AUTHORIZED SECURITY TESTING ONLY.
Illegal scanning is prohibited.
You are fully responsible for misuse.
════════════════════════════════════════════════════
{RESET}""")

def progress(title):
    size=45
    print(f"\n{CYAN}{BOLD}{title}{RESET}")
    for i in range(101):
        fill=int(size*i/100)
        bar="█"*fill+"░"*(size-fill)
        sys.stdout.write(f"\r[{bar}] {i}%")
        sys.stdout.flush()
        time.sleep(0.02)
    print()

# ========= INSTALL =========
def detect_pm():
    if shutil.which("apt"): return "apt"
    if shutil.which("pacman"): return "pacman"
    if shutil.which("dnf"): return "dnf"
    return None

def run(cmd):
    subprocess.call(cmd, shell=True)

def ensure_go():
    if shutil.which("go"): return True
    ans=input("Go not installed. Install now? [Y/n]: ").lower().strip()
    if ans=="n": return False
    pm=detect_pm()
    if pm=="apt": run("sudo apt update && sudo apt install -y golang")
    elif pm=="pacman": run("sudo pacman -Sy --noconfirm go")
    elif pm=="dnf": run("sudo dnf install -y golang")
    return shutil.which("go") is not None

def ensure_tool(name):
    if shutil.which(name): return True
    ans=input(f"{YELLOW}{name} not found. Install it? [Y/n]: {RESET}").lower().strip()
    if ans=="n": return False
    pm=detect_pm()

    if name in ["dalfox","nuclei","subfinder"]:
        if not ensure_go(): return False
        run(f"go install github.com/projectdiscovery/{name}/v2/cmd/{name}@latest")
        os.environ["PATH"]+=os.pathsep+os.path.expanduser("~/go/bin")

    elif name=="sqlmap":
        run("sudo apt install -y sqlmap" if pm=="apt" else f"sudo {pm} -Sy --noconfirm sqlmap")

    elif name=="nikto":
        run("sudo apt install -y nikto" if pm=="apt" else f"sudo {pm} -Sy --noconfirm nikto")

    elif name=="nmap":
        run("sudo apt install -y nmap" if pm=="apt" else f"sudo {pm} -Sy --noconfirm nmap")

    return shutil.which(name) is not None

# ========= CORE =========
def run_tool(cmd):
    try:
        p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        out="".join(p.stdout.readlines()); p.wait()
        return out
    except Exception as e:
        return str(e)

def empty_result():
    return {"info":[], "low":[], "medium":[], "high":[], "critical":[]}

def normalize_url(url):
    url=url.strip()
    if not url.startswith("http"):
        url="http://"+url
    url=url.replace("http://http://","http://").replace("https://https://","https://")
    return url

def extract_domain(url):
    p=urlparse(url)
    return p.netloc or p.path

# ========= SCANS =========
def scan_subdomain(target):
    res=empty_result()
    if not ensure_tool("subfinder"): return res
    progress("Subdomain Discovery")
    out=run_tool(["subfinder","-silent","-d",extract_domain(target)])
    for s in out.splitlines():
        res["info"].append(f"Discovered subdomain: {s}")
    if not res["info"]:
        res["info"].append("No subdomains found")
    return res

def scan_nmap(target):
    res=empty_result()
    if not ensure_tool("nmap"): return res
    progress("Port Scan (Nmap)")
    out=run_tool(["nmap","-sV","-Pn",extract_domain(target)])
    for l in out.splitlines():
        if "/tcp" in l and "open" in l:
            res["info"].append(f"Open service: {l.strip()}")
    if not res["info"]:
        res["info"].append("No open TCP services detected")
    return res

def scan_xss(target):
    res=empty_result()
    if not ensure_tool("dalfox"): return res
    progress("XSS Scan (Dalfox)")
    out=run_tool(["dalfox","url",target,"--silence"])
    for l in out.splitlines():
        ll=l.lower()
        if "found" in ll and "xss" in ll:
            res["high"].append(l.strip())
        elif "reflected" in ll:
            res["medium"].append(l.strip())
    if not res["high"] and not res["medium"]:
        res["info"].append("No XSS detected by Dalfox")
    return res

def scan_sql(target):
    res=empty_result()
    if not ensure_tool("sqlmap"): return res
    progress("SQL Injection Scan (SQLMap)")
    out=run_tool([
        "sqlmap","-u",target,"--batch",
        "--level=2","--risk=2","--threads=1","--delay=1"
    ])
    for l in out.splitlines():
        ll=l.lower()
        if "parameter" in ll and "vulnerable" in ll:
            res["critical"].append(l.strip())
        elif "sql injection" in ll:
            res["high"].append(l.strip())
    if not res["critical"] and not res["high"]:
        res["info"].append("No SQL Injection detected by SQLMap")
    return res

def scan_nikto(target):
    res=empty_result()
    if not ensure_tool("nikto"): return res
    progress("Web Server Scan (Nikto)")
    out=run_tool(["nikto","-h",target])
    for l in out.splitlines():
        if "header" in l.lower():
            res["low"].append(l.strip())
    if not res["low"]:
        res["info"].append("No low-risk web misconfigurations found")
    return res

def scan_nuclei(target):
    res=empty_result()
    if not ensure_tool("nuclei"): return res
    progress("Template Scan (Nuclei)")
    out=run_tool(["nuclei","-u",target])
    for l in out.splitlines():
        ll=l.lower()
        if "[critical]" in ll: res["critical"].append(l.strip())
        elif "[high]" in ll: res["high"].append(l.strip())
        elif "[medium]" in ll: res["medium"].append(l.strip())
        elif "[low]" in ll: res["low"].append(l.strip())
    if not any(res.values()):
        res["info"].append("No vulnerabilities detected by Nuclei")
    return res

def merge(a,b):
    for k in a: a[k]+=b[k]

def full_scan(target):
    total=empty_result()
    for f in [scan_subdomain,scan_nmap,scan_xss,scan_sql,scan_nikto,scan_nuclei]:
        merge(total,f(target))
    return total

# ========= REPORT =========
def show(title,color,emoji,items):
    print(f"{color}{emoji} {title} ({len(items)} findings){RESET}")
    for i in items:
        print(f"   - {i}")

def final_report(target,r):
    print(f"""{BOLD}
════════════════════ ONYX REPORT ════════════════════
Target : {target}
Time   : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
════════════════════════════════════════════════════
{RESET}""")
    show("INFO",BLUE,"ℹ️",r["info"])
    show("LOW",YELLOW,"🟡",r["low"])
    show("MEDIUM",GREEN,"🟢",r["medium"])
    show("HIGH",RED,"🔴",r["high"])
    show("CRITICAL",WHITE,"💥",r["critical"])

# ========= MAIN =========
def main():
    clear(); banner(); disclaimer()
    target=normalize_url(input(f"{CYAN}TARGET URL:{RESET} ").strip())

    while True:
        print(f"""
{BOLD}[ ONYX PANEL ]{RESET}
[1] Subdomain Discovery
[2] Port Scan (Nmap)
[3] XSS Scan
[4] SQL Injection Scan
[5] Nikto Scan
[6] Nuclei Scan
[7] Full Scan
[0] Exit
""")
        c=input("ONYX > ").strip()
        if c=="1": final_report(target,scan_subdomain(target))
        elif c=="2": final_report(target,scan_nmap(target))
        elif c=="3": final_report(target,scan_xss(target))
        elif c=="4": final_report(target,scan_sql(target))
        elif c=="5": final_report(target,scan_nikto(target))
        elif c=="6": final_report(target,scan_nuclei(target))
        elif c=="7": final_report(target,full_scan(target))
        elif c=="0": print("ONYX shutting down ⚡"); break
        else: print("Invalid option!")

if __name__=="__main__":
    main()
