#!/usr/bin/env python3
import os, sys, time, subprocess, threading, shutil, json
from datetime import datetime

VERSION = "3.3"

# ===================== PATH =====================
ONYX_DIR = os.path.expanduser("~/.onyx")
RESULT_FILE = f"{ONYX_DIR}/last_result.json"

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
    "sqlmap": {"install": "sqlmap"},
    "nmap": {"install": "nmap"},
    "nikto": {"install": "nikto"},
    "nuclei": {"install": "nuclei"},
    "dalfox": {"go": "github.com/hahwul/dalfox/v2@latest"}
}

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

# ===================== PROGRESS =====================
def run_bar(cmd, title):
    bar_len = 50
    progress = 0
    done = False
    output = []

    print(f"{C.MAGENTA}{C.BOLD}⚙ {title}{C.RESET}\n")

    def animate():
        nonlocal progress
        while not done:
            sys.stdout.write(
                f"\r{C.CYAN}[{BOX*progress}{EMPTY*(bar_len-progress)}] {progress*2}%{C.RESET}"
            )
            sys.stdout.flush()
            if progress < bar_len:
                progress += 1
            time.sleep(0.08)

    t = threading.Thread(target=animate)
    t.start()

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        output.append(line.strip())

    proc.wait()
    done = True
    progress = bar_len
    t.join()

    print(f"\r{C.GREEN}[{BOX*bar_len}] 100% ✔ DONE{C.RESET}\n")
    return output

# ===================== SCANS =====================
def scan_sql(t): 
    for l in run_bar(["sqlmap","-u",t,"--batch","--level=5","--risk=3"],"SQL Injection"):
        if "Payload:" in l: REPORT["HIGH"].append(l)

def scan_xss(t): 
    for l in run_bar(["dalfox","url",t,"--silence"],"XSS Scan"):
        if "[POC]" in l: REPORT["CRITICAL"].append(l)

def scan_nmap(t): 
    for l in run_bar(["nmap","-Pn",t.replace("http://","").replace("https://","")],"Port Scan"):
        if "open" in l: REPORT["INFO"].append(l)

def scan_nikto(t): 
    for l in run_bar(["nikto","-h",t],"Nikto Scan"):
        if "+ " in l: REPORT["LOW"].append(l)

def scan_nuclei(t): 
    for l in run_bar(["nuclei","-u",t],"Nuclei Scan"):
        ll=l.lower()
        if "[critical]" in ll: REPORT["CRITICAL"].append(l)
        elif "[high]" in ll: REPORT["HIGH"].append(l)
        elif "[medium]" in ll: REPORT["MEDIUM"].append(l)
        elif "[low]" in ll: REPORT["LOW"].append(l)

# ===================== SAVE RESULT =====================
def save_result(target):
    os.makedirs(ONYX_DIR, exist_ok=True)
    data = {
        "target": target,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report": REPORT
    }
    with open(RESULT_FILE,"w") as f:
        json.dump(data,f,indent=2)

# ===================== SHOW RESULT =====================
def show_saved_result():
    banner()
    if not os.path.exists(RESULT_FILE):
        print(f"{C.RED}No scan result found{C.RESET}\n")
        return

    with open(RESULT_FILE) as f:
        data=json.load(f)

    print(f"{C.CYAN}🎯 Target : {data['target']}{C.RESET}")
    print(f"{C.CYAN}⏰ Time   : {data['time']}{C.RESET}\n")

    for lvl in ["INFO","LOW","MEDIUM","HIGH","CRITICAL"]:
        print(f"{lvl} ({len(data['report'][lvl])})")
        for i in data["report"][lvl]:
            print(f" └─ {i}")
        print()

# ===================== MAIN =====================
def main():
    if "--result" in sys.argv:
        show_saved_result()
        sys.exit()

    banner()
    target = input(f"{C.CYAN}{C.BOLD}🌐 ENTER TARGET ➜ {C.RESET}")

    scan_sql(target)
    scan_xss(target)
    scan_nmap(target)
    scan_nikto(target)
    scan_nuclei(target)

    save_result(target)

    print(f"{C.GREEN}✔ Scan completed & result saved{C.RESET}")
    print(f"{C.GRAY}Use: onyx --result to view last scan{C.RESET}")

if __name__=="__main__":
    main()
