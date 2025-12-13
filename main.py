#!/usr/bin/env python3
import os, sys, time, subprocess, threading, shutil
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

# ===================== TOOLS =====================
TOOLS = {
    "sqlmap": {
        "check": ["sqlmap", "--version"],
        "install": "sqlmap"
    },
    "nmap": {
        "check": ["nmap", "--version"],
        "install": "nmap"
    },
    "nikto": {
        "check": ["nikto", "-Version"],
        "install": "nikto"
    },
    "nuclei": {
        "check": ["nuclei", "-version"],
        "install": "nuclei"
    },
    "dalfox": {
        "check": ["dalfox", "version"],
        "go": "github.com/hahwul/dalfox/v2@latest"
    }
}

# ===================== REPORT =====================
REPORT = {
    "INFO": [],
    "LOW": [],
    "MEDIUM": [],
    "HIGH": [],
    "CRITICAL": []
}

# ===================== BANNER =====================
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
            sys.stdout.write(f"\r{C.CYAN}[{filled}{empty}] {progress*2}%{C.RESET}")
            sys.stdout.flush()
            if progress < bar_len:
                progress += 1
            time.sleep(0.08)

    t = threading.Thread(target=animate)
    t.start()

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in proc.stdout:
        output.append(line.strip())

    proc.wait()
    done = True
    progress = bar_len
    t.join()
    sys.stdout.write(f"\r{C.GREEN}[{BOX*bar_len}] 100% ✔ DONE{C.RESET}\n\n")
    return output

# ===================== FAKE PROGRESS =====================
def fake_update_bar(title, duration=5):
    bar_len = 50
    print(f"{C.BLUE}{C.BOLD}⬇ {title}{C.RESET}\n")
    for i in range(bar_len + 1):
        filled = BOX * i
        empty = EMPTY * (bar_len - i)
        sys.stdout.write(f"\r{C.CYAN}[{filled}{empty}] {i*2}%{C.RESET}")
        sys.stdout.flush()
        time.sleep(duration / bar_len)
    print(f"\n{C.GREEN}✔ Done{C.RESET}\n")

# ===================== OS / PACKAGE =====================
def detect_pkg_manager():
    if shutil.which("pacman"): return "pacman"
    if shutil.which("apt"): return "apt"
    if shutil.which("dnf"): return "dnf"
    if shutil.which("yum"): return "yum"
    if shutil.which("apk"): return "apk"
    return None

def install_pkg(pkg, pm):
    cmds = {
        "pacman": f"sudo pacman -Sy --noconfirm {pkg}",
        "apt": f"sudo apt install -y {pkg}",
        "dnf": f"sudo dnf install -y {pkg}",
        "yum": f"sudo yum install -y {pkg}",
        "apk": f"sudo apk add {pkg}"
    }
    return cmds.get(pm)

def ensure_go(pm):
    if shutil.which("go"): return True
    print(f"{C.YELLOW}[!] Go not found{C.RESET}")
    ans = input("Install Go now? [Y/n]: ").lower()
    if ans == "n": return False
    fake_update_bar("Installing Go", 5)
    cmd = install_pkg("golang", pm)
    subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return shutil.which("go") is not None

def check_and_install_tools():
    pm = detect_pkg_manager()
    if not pm:
        print(f"{C.RED}[!] Unsupported package manager{C.RESET}")
        return
    print(f"{C.CYAN}🧠 Detected package manager: {pm}{C.RESET}\n")
    for tool, meta in TOOLS.items():
        if shutil.which(tool):
            print(f"{C.GREEN}[✔] {tool} installed{C.RESET}")
            continue
        print(f"{C.YELLOW}[!] {tool} not found{C.RESET}")
        ans = input(f"Install {tool}? [Y/n]: ").lower()
        if ans == "n": continue
        if tool == "dalfox":
            if not ensure_go(pm):
                print(f"{C.RED}[-] Skipping dalfox{C.RESET}")
                continue
            fake_update_bar("Installing Dalfox", 4)
            subprocess.call(f"go install {meta['go']}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            fake_update_bar(f"Installing {tool}", 3)
            cmd = install_pkg(meta["install"], pm)
            subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"\n{C.GREEN}✔ Tool check completed{C.RESET}\n")

# ===================== SCANS =====================
def scan_sql(target):
    out = run_bar(["sqlmap", "-u", target, "--batch", "--level=5", "--risk=3", "--dbs"], "SQL Injection Scan (Aggressive)")
    for l in out:
        if "Type:" in l or "Title:" in l: REPORT["CRITICAL"].append(l)
        if "Payload:" in l: REPORT["HIGH"].append(l)

def scan_xss(target):
    out = run_bar(["dalfox", "url", target, "--silence", "--no-color"], "XSS Scan (Aggressive)")
    for l in out:
        if "[POC]" in l: REPORT["CRITICAL"].append(l)

def scan_nmap(target):
    host = target.replace("http://", "").replace("https://", "")
    out = run_bar(["nmap", "-Pn", "-T4", host], "Port Scan (Nmap)")
    for l in out:
        if "open" in l: REPORT["INFO"].append(l)

def scan_nikto(target):
    out = run_bar(["nikto", "-h", target], "Nikto Web Scan")
    for l in out:
        if "+ " in l: REPORT["LOW"].append(l)

def scan_nuclei(target):
    out = run_bar(["nuclei", "-u", target, "-severity", "low,medium,high,critical"], "Nuclei Template Scan")
    for l in out:
        ll = l.lower()
        if "[critical]" in ll: REPORT["CRITICAL"].append(l)
        elif "[high]" in ll: REPORT["HIGH"].append(l)
        elif "[medium]" in ll: REPORT["MEDIUM"].append(l)
        elif "[low]" in ll: REPORT["LOW"].append(l)

# ===================== REPORT =====================
def show_report(target):
    print(C.BOLD + "════════════════════ ONYX REPORT ════════════════════" + C.RESET)
    print(f"{C.CYAN}🎯 Target : {target}{C.RESET}")
    print(f"{C.CYAN}⏰ Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}\n")
    for lvl, icon in [("INFO","ℹ️"),("LOW","🟡"),("MEDIUM","🟢"),("HIGH","🔴"),("CRITICAL","💥")]:
        print(f"{icon} {lvl} ({len(REPORT[lvl])})")
        for f in REPORT[lvl]: print(f"   └─ {f}")
        print()

# ===================== UPDATE =====================
def update_onyx():
    banner()
    print(f"{C.YELLOW}🚀 Updating ONYX Core & Tools...\n{C.RESET}")
    fake_update_bar("Fetching latest ONYX release", 6)
    subprocess.call("bash <(curl -s https://raw.githubusercontent.com/zvlrxq-onyx/onyx-scanner/main/install.sh)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fake_update_bar("Finalizing installation", 3)
    print(f"{C.GREEN}{C.BOLD}🔥 ONYX IS UP TO DATE 🔥{C.RESET}\n")

# ===================== MAIN =====================
def main():
    if "--update" in sys.argv:
        update_onyx()
        sys.exit()

    check_and_install_tools()  # AUTO CHECK

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
            for k in REPORT: REPORT[k].clear()
            if c == "1": scan_sql(target)
            elif c == "2": scan_xss(target)
            elif c == "3": scan_nmap(target)
            elif c == "4": scan_nikto(target)
            elif c == "5": scan_nuclei(target)
            elif c == "6":
                scan_sql(target); scan_xss(target); scan_nmap(target); scan_nikto(target); scan_nuclei(target)
            elif c == "0": sys.exit()
            else: continue
            show_report(target)
            input(f"{C.GRAY}Press ENTER to continue...{C.RESET}")
            break  # Kembali ke ASCII + ENTER TARGET

if __name__ == "__main__":
    main()
