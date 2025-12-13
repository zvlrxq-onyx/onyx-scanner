#!/usr/bin/env python3
import os, sys, time, subprocess
from datetime import datetime

# ================= COLORS =================
RESET="\033[0m"; BOLD="\033[1m"
CYAN="\033[96m"; GREEN="\033[92m"
YELLOW="\033[93m"; RED="\033[91m"
WHITE="\033[97m"

# ================= REPORT =================
REPORT = {}

def reset_report():
    global REPORT
    REPORT = {
        "INFO": [],
        "LOW": [],
        "MEDIUM": [],
        "HIGH": [],
        "CRITICAL": []
    }

# ================= UI =================
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
   ONYX ● VULNERABILITY SCANNER v3.0.3
{RESET}""")

def disclaimer():
    print(f"""{WHITE}
════════════════════════════════════════════════════
⚠️  LEGAL DISCLAIMER
════════════════════════════════════════════════════
AUTHORIZED SECURITY TESTING ONLY.
Use only on systems you own or have permission for.
You are fully responsible for your actions.
════════════════════════════════════════════════════
{RESET}""")

# ================= PROGRESS =================
def run_cmd(cmd, title, min_time=3):
    print(f"{CYAN}{BOLD}{title}{RESET}")
    start=time.time()
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    out=[]
    pct=0; width=40

    while proc.poll() is None:
        pct=min(pct+1,90)
        bar="█"*int(width*pct/100)+"░"*(width-int(width*pct/100))
        sys.stdout.write(f"\r[{bar}] {pct}% scanning...")
        sys.stdout.flush()
        time.sleep(0.15)

    while time.time()-start < min_time:
        pct=min(pct+1,99)
        bar="█"*int(width*pct/100)+"░"*(width-int(width*pct/100))
        sys.stdout.write(f"\r[{bar}] {pct}% finalizing...")
        sys.stdout.flush()
        time.sleep(0.1)

    for l in proc.stdout.read().splitlines():
        out.append(l)

    sys.stdout.write(f"\r[{'█'*width}] 100% completed ✔️\n\n")
    return out

# ================= PARSERS =================
def parse_sqlmap(lines):
    for l in lines:
        s=l.lower()
        if "type:" in s or "title:" in s:
            REPORT["CRITICAL"].append(l.strip())
        elif "payload:" in s:
            REPORT["HIGH"].append(l.strip())
        elif "warning" in s:
            REPORT["LOW"].append(l.strip())

def parse_dalfox(lines):
    for l in lines:
        s=l.lower()
        if s.startswith("--"): continue
        if "[poc]" in s or "[v]" in s:
            REPORT["CRITICAL"].append(l.strip())

def parse_nmap(lines):
    for l in lines:
        if "/tcp" in l and "open" in l:
            REPORT["INFO"].append(l.strip())

def parse_nikto(lines):
    for l in lines:
        if l.strip().startswith("+"):
            REPORT["LOW"].append(l.replace("+","").strip())

# ================= SCANS =================
def scan_sql(target):
    reset_report()
    out=run_cmd(
        ["sqlmap","-u",target,"--batch","--level=5","--risk=3","--threads=4","--dbs"],
        "SQL Injection Scan (Aggressive)"
    )
    parse_sqlmap(out)
    show_report(target)

def scan_xss(target):
    reset_report()
    out=run_cmd(
        ["dalfox","url",target,"--no-color","--silence","--skip-bav","--only-poc"],
        "XSS Scan (Aggressive)"
    )
    parse_dalfox(out)
    show_report(target)

def scan_nmap(target):
    reset_report()
    host=target.split("//")[-1].split("/")[0]
    out=run_cmd(["nmap","-Pn","-T4",host],"Port Scan (Nmap)")
    parse_nmap(out)
    show_report(target)

def scan_nikto(target):
    reset_report()
    out=run_cmd(["nikto","-h",target],"Nikto Scan")
    parse_nikto(out)
    show_report(target)

def full_scan(target):
    scan_sql(target)
    scan_xss(target)
    scan_nmap(target)
    scan_nikto(target)

# ================= REPORT =================
def show_report(target):
    print(f"""{WHITE}
════════════════════ ONYX REPORT ════════════════════
Target : {target}
Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
════════════════════════════════════════════════════
{RESET}""")
    for k,c,e in [
        ("INFO",CYAN,"ℹ️"),
        ("LOW",YELLOW,"🟡"),
        ("MEDIUM",GREEN,"🟢"),
        ("HIGH",RED,"🔴"),
        ("CRITICAL",RED,"💥")
    ]:
        print(f"{c}{e} {k} ({len(REPORT[k])}){RESET}")
        for i in REPORT[k]:
            print(f"   - {i}")
        print()

# ================= MAIN =================
def main():
    clear(); banner(); disclaimer()
    target=input(f"{YELLOW}TARGET URL:{RESET} ").strip()

    while True:
        print(f"""
{BOLD}[ ONYX CONTROL PANEL ]{RESET}
[1] SQL Injection Scan (Aggressive)
[2] XSS Scan (Aggressive)
[3] Port Scan (Nmap)
[4] Nikto Scan
[5] Full Scan
[0] Exit
""")
        c=input("ONYX > ").strip()
        if c=="1": scan_sql(target)
        elif c=="2": scan_xss(target)
        elif c=="3": scan_nmap(target)
        elif c=="4": scan_nikto(target)
        elif c=="5": full_scan(target)
        elif c=="0": break
        else: print("Invalid option!")

if __name__=="__main__":
    main()
