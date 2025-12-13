kk#!/usr/bin/env python3
import os, sys, time, subprocess, threading
from datetime import datetime

VERSION = "3.2"

# ===================== COLORS =====================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"

BOX = "█"
EMPTY = "░"

# ===================== REPORT =====================
REPORT = {
    "INFO": [],
    "LOW": [],
    "MEDIUM": [],
    "HIGH": [],
    "CRITICAL": []
}

# ===================== UI =====================
def banner():
    os.system("clear")
    print(C.CYAN + C.BOLD + f"""
██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝

⚡ ONYX VULNERABILITY SCANNER v{VERSION} ⚡
""" + C.RESET)

    print(C.YELLOW + """
════════════════════════════════════════════════════
⚠️  LEGAL DISCLAIMER
AUTHORIZED SECURITY TESTING ONLY.
USE ONLY ON SYSTEMS YOU OWN OR HAVE PERMISSION.
════════════════════════════════════════════════════
""" + C.RESET)

# ===================== PROGRESS BAR =====================
def run_bar(cmd, title):
    bar_len = 50
    progress = 0
    done = False
    output = []

    print(f"{C.MAGENTA}{C.BOLD}⚙ {title}{C.RESET}\n")

    def animate():
        nonlocal progress
        while not done:
            filled = BOX * progress
            empty = EMPTY * (bar_len - progress)
            sys.stdout.write(
                f"\r{C.CYAN}[{filled}{empty}] {progress*2}%{C.RESET}"
            )
            sys.stdout.flush()
            if progress < bar_len:
                progress += 1
            time.sleep(0.08)

    t = threading.Thread(target=animate)
    t.start()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in proc.stdout:
        output.append(line.strip())

    proc.wait()
    done = True
    progress = bar_len
    t.join()

    sys.stdout.write(
        f"\r{C.GREEN}[{BOX*bar_len}] 100% ✔ DONE{C.RESET}\n\n"
    )
    return output

# ===================== SCANS =====================
def scan_sql(target):
    out = run_bar(
        ["sqlmap", "-u", target, "--batch", "--level=5", "--risk=3", "--dbs"],
        "SQL Injection Scan (Aggressive)"
    )
    for l in out:
        if "Type:" in l or "Title:" in l:
            REPORT["CRITICAL"].append(l)
        if "Payload:" in l:
            REPORT["HIGH"].append(l)

def scan_xss(target):
    out = run_bar(
        ["dalfox", "url", target, "--silence", "--no-color"],
        "XSS Scan (Aggressive)"
    )
    for l in out:
        if "[POC]" in l:
            REPORT["CRITICAL"].append(l)

def scan_nmap(target):
    host = target.replace("http://", "").replace("https://", "")
    out = run_bar(
        ["nmap", "-Pn", "-T4", host],
        "Port Scan (Nmap)"
    )
    for l in out:
        if "open" in l:
            REPORT["INFO"].append(l)

def scan_nikto(target):
    out = run_bar(
        ["nikto", "-h", target],
        "Nikto Web Scan"
    )
    for l in out:
        if "+ " in l:
            REPORT["LOW"].append(l)

def scan_nuclei(target):
    out = run_bar(
        ["nuclei", "-u", target, "-severity", "low,medium,high,critical"],
        "Nuclei Template Scan"
    )
    for l in out:
        ll = l.lower()
        if "[critical]" in ll:
            REPORT["CRITICAL"].append(l)
        elif "[high]" in ll:
            REPORT["HIGH"].append(l)
        elif "[medium]" in ll:
            REPORT["MEDIUM"].append(l)
        elif "[low]" in ll:
            REPORT["LOW"].append(l)

# ===================== REPORT =====================
def show_report(target):
    print(C.BOLD + "════════════════════ ONYX REPORT ════════════════════" + C.RESET)
    print(f"{C.CYAN}🎯 Target : {target}{C.RESET}")
    print(f"{C.CYAN}⏰ Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}\n")

    for lvl, icon in [
        ("INFO", "ℹ️"),
        ("LOW", "🟡"),
        ("MEDIUM", "🟢"),
        ("HIGH", "🔴"),
        ("CRITICAL", "💥")
    ]:
        print(f"{icon} {lvl} ({len(REPORT[lvl])})")
        for f in REPORT[lvl]:
            print(f"   └─ {f}")
        print()

# ===================== UPDATE =====================
def fake_update_bar(title, duration=5):
    bar_len = 50
    print(f"{C.BLUE}{C.BOLD}⬇ {title}{C.RESET}\n")
    for i in range(bar_len + 1):
        filled = BOX * i
        empty = EMPTY * (bar_len - i)
        sys.stdout.write(
            f"\r{C.CYAN}[{filled}{empty}] {i*2}%{C.RESET}"
        )
        sys.stdout.flush()
        time.sleep(duration / bar_len)
    print(f"\n{C.GREEN}✔ Done{C.RESET}\n")

def update_onyx():
    banner()
    print(f"{C.YELLOW}🚀 Updating ONYX Core & Tools...\n{C.RESET}")

    fake_update_bar("Fetching latest ONYX release", 6)

    subprocess.call([
        "bash",
        "-c",
        "bash <(curl -s https://raw.githubusercontent.com/zvlrxq-onyx/onyx-scanner/main/install.sh)"
    ])

    fake_update_bar("Finalizing installation", 3)
    print(f"{C.GREEN}{C.BOLD}🔥 ONYX IS UP TO DATE 🔥{C.RESET}\n")

# ===================== MAIN =====================
def main():
    if "--update" in sys.argv:
        update_onyx()
        sys.exit()

    while True:
        banner()
        target = input(f"{C.CYAN}{C.BOLD}🌐 ENTER TARGET URL ➜ {C.RESET}").strip()

        while True:
            print(f"""
{C.BOLD}{C.CYAN}[ ⚡ ONYX CONTROL PANEL ⚡ ]{C.RESET}

{C.GREEN}[1]{C.RESET} 💉 SQL Injection Scan
{C.GREEN}[2]{C.RESET} 🧪 XSS Scan
{C.GREEN}[3]{C.RESET} 🌐 Port Scan (Nmap)
{C.GREEN}[4]{C.RESET} 🕷️ Nikto Scan
{C.GREEN}[5]{C.RESET} ☢️ Nuclei Scan
{C.RED}[6]{C.RESET} 🔥 FULL AGGRESSIVE SCAN
{C.GRAY}[0]{C.RESET} ❌ Exit
""")
            c = input(f"{C.BOLD}ONYX ➜ {C.RESET}").strip()

            for k in REPORT:
                REPORT[k].clear()

            if c == "1":
                scan_sql(target)
            elif c == "2":
                scan_xss(target)
            elif c == "3":
                scan_nmap(target)
            elif c == "4":
                scan_nikto(target)
            elif c == "5":
                scan_nuclei(target)
            elif c == "6":
                scan_sql(target)
                scan_xss(target)
                scan_nmap(target)
                scan_nikto(target)
                scan_nuclei(target)
            elif c == "0":
                sys.exit()
            else:
                continue

            show_report(target)
            input(f"{C.GRAY}Press ENTER to continue...{C.RESET}")

if __name__ == "__main__":
    main()

