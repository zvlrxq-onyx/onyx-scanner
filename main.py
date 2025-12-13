#!/usr/bin/env python3
import os, sys, time, subprocess, shutil, json
from datetime import datetime

VERSION = "3.8-FINAL"

# ===================== PATH =====================
ONYX_HOME = os.path.expanduser("~/.onyx")
RESULT_FILE = f"{ONYX_HOME}/last_result.json"

# ===================== COLORS =====================
class C:
    R="\033[0m"; B="\033[1m"
    CYAN="\033[96m"; GREEN="\033[92m"
    YELLOW="\033[93m"; RED="\033[91m"
    MAG="\033[95m"; GRAY="\033[90m"

FULL="█"; EMPTY="░"

# ===================== SEVERITY =====================
LEVELS = ["INFO","LOW","MEDIUM","HIGH","CRITICAL"]
ICONS = {
    "INFO":"ℹ️",
    "LOW":"🟡",
    "MEDIUM":"🟢",
    "HIGH":"🔴",
    "CRITICAL":"💥"
}

REPORT = {k: [] for k in LEVELS}

# ===================== TOOLS =====================
TOOLS = {
    "sqlmap": {"pkg":"sqlmap"},
    "dalfox": {"go":"github.com/hahwul/dalfox/v2@latest"},
    "nmap": {"pkg":"nmap"},
    "nikto": {"pkg":"nikto"},
    "nuclei": {"pkg":"nuclei"}
}

# ===================== UI =====================
def banner():
    os.system("clear")
    print(C.CYAN+C.B+f"""
██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝

⚡ ONYX VULNERABILITY SCANNER v{VERSION} ⚡
"""+C.R)

# ===================== DISCLAIMER =====================
def disclaimer():
    print(C.RED+C.B+"""
════════════════════════════════════════════════════════════
⚠️  LEGAL DISCLAIMER
════════════════════════════════════════════════════════════

ONYX is intended for AUTHORIZED SECURITY TESTING ONLY.

You MUST own the target system or have EXPLICIT permission.
Unauthorized scanning or exploitation is ILLEGAL and may
lead to criminal charges and civil liability.

The developer assumes NO RESPONSIBILITY for misuse.
YOU are fully responsible for your actions.

════════════════════════════════════════════════════════════
"""+C.R)
    input(C.YELLOW+"Press ENTER to accept and continue..."+C.R)

# ===================== PROGRESS BAR =====================
def fake_bar(title, duration=4):
    print(f"{C.MAG}{C.B}⚙ {title}{C.R}\n")
    size = 48
    for i in range(size+1):
        pct = int(i/size*100)
        sys.stdout.write(
            f"\r{C.CYAN}[{FULL*i}{EMPTY*(size-i)}] {pct}%{C.R}"
        )
        sys.stdout.flush()
        time.sleep(duration/size)
    print(f"\n{C.GREEN}✔ Done{C.R}\n")

# ===================== UPDATE =====================
def update_onyx():
    banner()
    print(C.CYAN+C.B+"🚀 Updating ONYX Framework...\n"+C.R)

    proc = subprocess.Popen(
        ["bash","-c",
         "bash <(curl -s https://raw.githubusercontent.com/zvlrxq-onyx/onyx-scanner/main/install.sh)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    fake_bar("Syncing core & tools",6)
    proc.wait()

    print(C.GREEN+C.B+"🔥 ONYX successfully updated 🔥"+C.R)
    input("Press ENTER to continue...")

# ===================== PACKAGE MANAGER =====================
def detect_pm():
    for pm in ["pacman","apt","dnf","yum","apk"]:
        if shutil.which(pm):
            return pm
    return None

def pkg_cmd(pkg,pm):
    return {
        "pacman":f"sudo pacman -Sy --noconfirm {pkg}",
        "apt":f"sudo apt install -y {pkg}",
        "dnf":f"sudo dnf install -y {pkg}",
        "yum":f"sudo yum install -y {pkg}",
        "apk":f"sudo apk add {pkg}"
    }.get(pm)

def ensure_go(pm):
    if shutil.which("go"):
        return True
    print(C.YELLOW+"[!] Go not installed"+C.R)
    if input("Install Go now? [Y/n]: ").lower()=="n":
        return False
    fake_bar("Installing Go",5)
    subprocess.call(pkg_cmd("golang",pm),shell=True,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return shutil.which("go") is not None

def check_tools():
    pm = detect_pm()
    if not pm:
        print(C.RED+"Unsupported OS"+C.R); return
    print(C.CYAN+f"🧠 Package manager: {pm}\n"+C.R)

    for t,m in TOOLS.items():
        if shutil.which(t):
            print(C.GREEN+f"[✔] {t} installed"+C.R); continue
        print(C.YELLOW+f"[!] {t} not found"+C.R)
        if input(f"Install {t}? [Y/n]: ").lower()=="n":
            continue
        if t=="dalfox":
            if not ensure_go(pm): continue
            fake_bar("Installing Dalfox",4)
            subprocess.call(
                f"go install {m['go']}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            fake_bar(f"Installing {t}",3)
            subprocess.call(
                pkg_cmd(m["pkg"],pm),
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    print()

# ===================== SCANS =====================
def run_scan(cmd,title,level,kw=None):
    fake_bar(title,3)
    try:
        out = subprocess.check_output(cmd,stderr=subprocess.STDOUT,text=True)
        for l in out.splitlines():
            if not kw or kw in l.lower():
                REPORT[level].append(l)
    except: pass

def scan_sql(t): run_scan(["sqlmap","-u",t,"--batch"],"SQL Injection","HIGH","payload")
def scan_xss(t): run_scan(["dalfox","url",t],"XSS Scan","CRITICAL","poc")
def scan_nmap(t): run_scan(["nmap","-Pn",t.replace("http://","").replace("https://","")],"Port Scan","INFO","open")
def scan_nikto(t): run_scan(["nikto","-h",t],"Nikto Scan","LOW","+ ")
def scan_nuclei(t): run_scan(["nuclei","-u",t],"Nuclei Scan","MEDIUM","[")

# ===================== REPORT =====================
def show_report(target):
    banner()
    print(C.CYAN+C.B+"════════════ ONYX SCAN REPORT ════════════"+C.R)
    print(C.GREEN+f"🎯 Target : {target}"+C.R)
    print(C.GREEN+f"⏰ Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"+C.R)

    for lvl in LEVELS:
        print(f"{ICONS[lvl]} {lvl:<9}: {len(REPORT[lvl])}")

    print(C.CYAN+"══════════════════════════════════════════\n"+C.R)

    for lvl in LEVELS:
        if not REPORT[lvl]: continue
        print(f"{ICONS[lvl]} {lvl}")
        for item in REPORT[lvl]:
            print("   └─",item)
        print()

# ===================== RESULT =====================
def save_result(target):
    os.makedirs(ONYX_HOME,exist_ok=True)
    with open(RESULT_FILE,"w") as f:
        json.dump({
            "target":target,
            "time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report":REPORT
        },f,indent=2)

def show_result():
    banner()
    if not os.path.exists(RESULT_FILE):
        print(C.RED+"No previous result found"+C.R); return
    with open(RESULT_FILE) as f:
        d=json.load(f)

    print(C.CYAN+f"🎯 Target : {d['target']}"+C.R)
    print(C.CYAN+f"⏰ Time   : {d['time']}\n"+C.R)
    for lvl in LEVELS:
        print(f"{ICONS[lvl]} {lvl}: {len(d['report'][lvl])}")

# ===================== MENU =====================
def control_panel():
    print(C.CYAN+C.B+"""
[ ONYX CONTROL PANEL ]
[1] 💉 SQL Injection Scan
[2] 🧪 XSS Scan
[3] 🌐 Port Scan (Nmap)
[4] 🕷️ Nikto Scan
[5] 🚀 Nuclei Scan
[6] 💥 Full Scan
[0] 🔙 Back
"""+C.R)

# ===================== MAIN =====================
def main():
    if "--update" in sys.argv: update_onyx(); return
    if "--result" in sys.argv: show_result(); return

    banner()
    disclaimer()
    check_tools()

    while True:
        banner()
        target = input(C.CYAN+C.B+"🌐 ENTER TARGET ➜ "+C.R).strip()
        if not target: continue

        while True:
            banner()
            print(C.GREEN+f"🎯 Target: {target}\n"+C.R)
            control_panel()
            choice = input("ONYX > ").strip()

            for k in REPORT: REPORT[k].clear()

            if choice=="1": scan_sql(target)
            elif choice=="2": scan_xss(target)
            elif choice=="3": scan_nmap(target)
            elif choice=="4": scan_nikto(target)
            elif choice=="5": scan_nuclei(target)
            elif choice=="6":
                scan_sql(target); scan_xss(target)
                scan_nmap(target); scan_nikto(target); scan_nuclei(target)
            elif choice=="0": break
            else: continue

            save_result(target)
            show_report(target)
            input(C.YELLOW+"Press ENTER to return to menu..."+C.R)

if __name__=="__main__":
    main()
