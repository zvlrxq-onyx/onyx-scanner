#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import re
from datetime import datetime

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
      ONYX • NEON SECURITY SCANNER
{RESET}""")

def disclaimer():
    print(f"""{RED}
[!] DISCLAIMER
This tool is for AUTHORIZED testing only.
Use only on assets you own or legal labs.
You are fully responsible for all actions.
{RESET}""")

def progress(title):
    print(f"\n{CYAN}{title}{RESET}")
    for i in range(101):
        bar = "█" * (i // 5)
        sys.stdout.write(f"\r[{bar:<20}] {i}%")
        sys.stdout.flush()
        time.sleep(0.02)
    print()

# ========= CORE =========
def run_tool(cmd):
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        output = ""
        for line in proc.stdout:
            output += line
        proc.wait()
        return output
    except FileNotFoundError:
        return "[ERROR] Tool not found"
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
    score = (
        res["critical"] * 4 +
        res["high"] * 3 +
        res["medium"] * 2 +
        res["low"]
    )

    status = "SECURE"
    color = GREEN
    if res["critical"] > 0:
        status = "CRITICAL"
        color = RED
    elif res["high"] > 0:
        status = "HIGH RISK"
        color = RED
    elif res["medium"] > 0:
        status = "MEDIUM RISK"
        color = YELLOW

    print(f"""{color}{BOLD}
================== ONYX REPORT ==================
Target      : {target}
Date        : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Vulnerabilities:
Low         : {res['low']}
Medium      : {res['medium']}
High        : {res['high']}
Critical    : {res['critical']}

Risk Score  : {score}
Status      : {status}

Advice:
- Patch critical & high issues
- Validate all user input
- Harden server configuration
- Re-scan after fixes

===================== END =======================
{RESET}""")

# ========= SCANS =========
def scan_xss(target):
    progress("XSS Scan (Dalfox) -------------------")
    cmd = ["dalfox", "url", target]
    out = run_tool(cmd)
    return parse_severity(out)

def scan_sql(target):
    progress("SQL Injection (SQLMap) --------------")
    print(f"{YELLOW}[!] Enter SQLMap flags manually{RESET}")
    flags = input("sqlmap flags > ")
    cmd = ["sqlmap", "-u", target] + flags.split()
    out = run_tool(cmd)
    return parse_severity(out)

def scan_nikto(target):
    progress("Nikto Web Scan ----------------------")
    cmd = ["nikto", "-h", target]
    out = run_tool(cmd)
    return parse_severity(out)

def scan_nuclei(target):
    progress("Nuclei Template Scan ----------------")
    cmd = ["nuclei", "-u", target]
    out = run_tool(cmd)
    return parse_severity(out)

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

    target = input(f"{YELLOW}TARGET URL:{RESET} ")

    while True:
        print(f"""
{BOLD}[ ONYX MENU ]{RESET}
[1] XSS Scan (Dalfox)
[2] SQL Injection (SQLMap)
[3] Nikto Scan
[4] Nuclei Scan
[5] Full Scan
[0] Exit
""")

        c = input("ONYX > ")

        if c == "1":
            final_report(target, scan_xss(target))
        elif c == "2":
            final_report(target, scan_sql(target))
        elif c == "3":
            final_report(target, scan_nikto(target))
        elif c == "4":
            final_report(target, scan_nuclei(target))
        elif c == "5":
            final_report(target, full_scan(target))
        elif c == "0":
            print("ONYX exiting... ⚡")
            break
        else:
            print("Invalid option!")

if __name__ == "__main__":
    main()
