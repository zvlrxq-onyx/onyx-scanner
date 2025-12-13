#!/usr/bin/env python3
import os, sys, subprocess, time
from datetime import datetime
from urllib.parse import urlparse

# ================= COLORS =================
CYAN="\033[96m"; GREEN="\033[92m"; YELLOW="\033[93m"
RED="\033[91m"; BLUE="\033[94m"; BOLD="\033[1m"
RESET="\033[0m"; WHITE="\033[97m"

# ================= GLOBAL =================
VERSION = "ONYX ● VULNERABILITY SCANNER v3.0.1"
REPORT = {"INFO":[], "LOW":[], "MEDIUM":[], "HIGH":[], "CRITICAL":[]}

# ================= UI =================
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
   {VERSION}
{RESET}""")

def disclaimer():
    print(f"""{BLUE}{BOLD}
════════════════════════════════════════════════════
⚠️  LEGAL DISCLAIMER
════════════════════════════════════════════════════
This tool is intended for AUTHORIZED security testing
and educational purposes ONLY.

You may use this tool ONLY on:
• Systems you own
• Systems you have explicit permission to test
• Legal penetration testing labs

Unauthorized usage is strictly prohibited.
The developer assumes NO liability for misuse,
damages, or legal consequences.

By continuing, YOU take full responsibility.
════════════════════════════════════════════════════
{RESET}""")

# ================= PROGRESS =================
def progress_bar(pct):
    width=40
    filled=int(width*pct/100)
    bar="█"*filled + "░"*(width-filled)
    sys.stdout.write(f"\r[{bar}] {pct}%")
    sys.stdout.flush()

# ================= RUNNER =================
def run_cmd(cmd, title):
    print(f"{CYAN}{BOLD}{title}{RESET}")
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    pct=0
    output=[]
    while True:
        line=proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            output.append(line.strip())
            pct=min(pct+1,95)
            progress_bar(pct)
    progress_bar(100)
    print(" completed ✔️\n")
    return output

# ================= PARSERS =================
def parse_sqlmap(lines):
    for l in lines:
        s=l.lower()
        if any(x in s for x in ["boolean-based","error-based","time-based","union query","available databases"]):
            REPORT["CRITICAL"].append(l)
        elif any(x in s for x in ["parameter:","payload:","back-end dbms"]):
            REPORT["HIGH"].append(l)
        elif "warning" in s:
            REPORT["LOW"].append(l)

def parse_dalfox(lines):
    for l in lines:
        s=l.lower()
        if "found" in s or "vulnerable" in s:
            REPORT["CRITICAL"].append(l)

def parse_nmap(lines):
    for l in lines:
        if "/tcp open" in l.lower():
            REPORT["LOW"].append(l)

def parse_nikto(lines):
    for l in lines:
        s=l.lower()
        if "osvdb" in s or "cve" in s:
            REPORT["MEDIUM"].append(l)
        elif "missing" in s:
            REPORT["LOW"].append(l)

# ================= SCANS =================
def scan_sql(target):
    cmd=[
        "sqlmap","-u",target,
        "--batch","--dbs",
        "--level=5","--risk=3",
        "--threads=2","--random-agent"
    ]
    parse_sqlmap(run_cmd(cmd,"SQL Injection Scan (AGGRESSIVE)"))

def scan_xss(target):
    cmd=[
        "dalfox","url",target,
        "--only-poc",
        "--skip-bav",
        "--waf-evasion",
        "--mining-all",
        "--worker","50"
    ]
    parse_dalfox(run_cmd(cmd,"XSS Scan (AGGRESSIVE)"))

def scan_nmap(target):
    host=urlparse(target).hostname
    parse_nmap(run_cmd(["nmap","-Pn","-sV",host],"Port Scan (Nmap)"))

def scan_nikto(target):
    parse_nikto(run_cmd(["nikto","-h",target],"Nikto Scan"))

# ================= REPORT =================
def show_report(target):
    print(f"{BOLD}════════════════════ ONYX REPORT ════════════════════{RESET}")
    print(f"Target : {target}")
    print(f"Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def block(label,color,emoji):
        items=REPORT[label]
        print(f"{color}{emoji} {label} ({len(items)}){RESET}")
        for i in items:
            print(f"   - {i}")
        print()

    block("CRITICAL",WHITE,"💥")
    block("HIGH",RED,"🔴")
    block("MEDIUM",GREEN,"🟢")
    block("LOW",YELLOW,"🟡")

# ================= MAIN =================
def main():
    clear(); banner(); disclaimer()
    target=input(f"{YELLOW}TARGET URL:{RESET} ").strip()
    if not target.startswith("http"):
        target="http://"+target

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
        REPORT["INFO"].clear()
        REPORT["LOW"].clear()
        REPORT["MEDIUM"].clear()
        REPORT["HIGH"].clear()
        REPORT["CRITICAL"].clear()

        if c=="1":
            scan_sql(target); show_report(target)
        elif c=="2":
            scan_xss(target); show_report(target)
        elif c=="3":
            scan_nmap(target); show_report(target)
        elif c=="4":
            scan_nikto(target); show_report(target)
        elif c=="5":
            scan_sql(target)
            scan_xss(target)
            scan_nmap(target)
            scan_nikto(target)
            show_report(target)
        elif c=="0":
            print("ONYX exiting ⚡"); break
        else:
            print("Invalid option!")

if __name__=="__main__":
    main()
