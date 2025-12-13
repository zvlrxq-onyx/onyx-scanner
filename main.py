#!/usr/bin/env python3
import os, sys, time, subprocess
from datetime import datetime

# ========= COLORS =========
CYAN="\033[96m"; GREEN="\033[92m"; YELLOW="\033[93m"
RED="\033[91m"; BOLD="\033[1m"; RESET="\033[0m"

# ========= UI =========
def clear(): os.system("clear" if os.name!="nt" else "cls")

def banner():
    print(f"""{CYAN}{BOLD}
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
   ONYX ● VULNERABILITY SCANNER v2.8 AGGRESSIVE
{RESET}""")

def disclaimer():
    print(f"""{YELLOW}
AUTHORIZED SECURITY TESTING ONLY
Use only on assets you own or have permission for
{RESET}""")

# ========= SMART PROGRESS =========
def progress(proc, title):
    width=40; pct=0
    print(f"{CYAN}{title}{RESET}")
    while proc.poll() is None:
        pct=min(pct+1,95)
        bar="█"*int(width*pct/100)+"░"*(width-int(width*pct/100))
        sys.stdout.write(f"\r[{bar}] {pct}%")
        sys.stdout.flush()
        time.sleep(0.4)
    print(f"\r[{'█'*width}] 100% ✔️")

# ========= RUN =========
def run(cmd, title):
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    progress(proc,title)
    return proc.communicate()[0]

# ========= PARSER =========
def parse_sql(out):
    sev={"critical":[], "high":[], "medium":[], "low":[]}

    for l in out.splitlines():
        s=l.lower().strip()

        if not s or s.startswith(("[*]","[info] starting","___","|_")):
            continue

        if any(k in s for k in [
            "available databases",
            "union query",
            "boolean-based blind",
            "error-based",
            "time-based blind"
        ]):
            sev["critical"].append(l)

        elif "payload:" in s or "parameter:" in s or "back-end dbms" in s:
            sev["high"].append(l)

        elif "xss" in s:
            sev["medium"].append(l)

        elif "warning" in s:
            sev["low"].append(l)

    return sev

def parse_xss(out):
    sev={"critical":[], "high":[], "medium":[], "low":[]}
    for l in out.splitlines():
        s=l.lower()
        if "stored xss" in s:
            sev["high"].append(l)
        elif "reflected xss" in s:
            sev["medium"].append(l)
    return sev

# ========= SCANS =========
def scan_sql(target):
    cmd=[
        "sqlmap","-u",target,
        "--batch","--level=5","--risk=3",
        "--dbs","--random-agent",
        "--threads=1"
    ]
    out=run(cmd,"SQL Injection Scan (AGGRESSIVE)")
    return parse_sql(out)

def scan_xss(target):
    out=run(["dalfox","url",target,"--auto"],"XSS Scan (AGGRESSIVE)")
    return parse_xss(out)

# ========= REPORT =========
def report(target, sev):
    print(f"\n{BOLD}════════════ ONYX REPORT ════════════{RESET}")
    print(f"Target : {target}")
    print(f"Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"💥 CRITICAL ({len(sev['critical'])})")
    for i in sev["critical"]: print(f"   - {i}")

    print(f"\n🔴 HIGH ({len(sev['high'])})")
    for i in sev["high"]: print(f"   - {i}")

    print(f"\n🟢 MEDIUM ({len(sev['medium'])})")
    for i in sev["medium"]: print(f"   - {i}")

    print(f"\n🟡 LOW ({len(sev['low'])})")
    for i in sev["low"]: print(f"   - {i}")

# ========= MAIN =========
def main():
    clear(); banner(); disclaimer()
    target=input("TARGET URL: ").strip()

    while True:
        print("""
[1] SQL Injection Scan (AGGRESSIVE)
[2] XSS Scan (AGGRESSIVE)
[3] Full Scan
[0] Exit
""")
        c=input("ONYX > ").strip()

        if c=="1":
            report(target, scan_sql(target))
        elif c=="2":
            report(target, scan_xss(target))
        elif c=="3":
            total={"critical":[], "high":[], "medium":[], "low":[]}
            for s in (scan_sql(target), scan_xss(target)):
                for k in total: total[k]+=s[k]
            report(target,total)
        elif c=="0":
            break

if __name__=="__main__":
    main()
