#!/usr/bin/env python3
import os, sys, time, subprocess, shutil, json
from datetime import datetime

VERSION = "3.6"

# ===================== PATH =====================
ONYX_HOME = os.path.expanduser("~/.onyx")
RESULT_FILE = f"{ONYX_HOME}/last_result.json"

# ===================== COLORS =====================
class C:
    R = "\033[0m"
    B = "\033[1m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAG = "\033[95m"
    GRAY = "\033[90m"

FULL = "█"
EMPTY = "░"

# ===================== REPORT =====================
REPORT = {k: [] for k in ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]}

# ===================== TOOLS =====================
TOOLS = {
    "sqlmap": {"pkg": "sqlmap"},
    "nmap": {"pkg": "nmap"},
    "nikto": {"pkg": "nikto"},
    "nuclei": {"pkg": "nuclei"},
    "dalfox": {"go": "github.com/hahwul/dalfox/v2@latest"}
}

# ===================== UI =====================
def banner():
    os.system("clear")
    print(C.CYAN + C.B + f"""
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝

⚡ ONYX VULNERABILITY SCANNER v{VERSION} ⚡
""" + C.R)

# ===================== DISCLAIMER =====================
def disclaimer():
    print(C.RED + C.B + """
════════════════════════════════════════════════════════════
⚠️  LEGAL DISCLAIMER & TERMS OF USE
════════════════════════════════════════════════════════════

ONYX Vulnerability Scanner is designed for
AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY.

By using this tool, you acknowledge and agree that:

• You have EXPLICIT PERMISSION to test the target systems.
• You are the OWNER of the system, or you have WRITTEN CONSENT
  from the system owner to perform security testing.
• Any form of UNAUTHORIZED access, scanning, exploitation,
  or disruption of systems is STRICTLY PROHIBITED.

Misuse of this software may result in:
• Criminal charges
• Civil liability
• Severe legal consequences under local and international law

The developer(s) of ONYX:
• Are NOT responsible for misuse or damage
• Provide this tool "AS IS"
• Assume NO LIABILITY for illegal activities

⚠️ YOU ARE FULLY RESPONSIBLE FOR YOUR ACTIONS ⚠️

If you do NOT agree with these terms:
CLOSE THIS TOOL IMMEDIATELY.

════════════════════════════════════════════════════════════
""" + C.R)
    input(C.YELLOW + "Press ENTER to acknowledge and continue..." + C.R)

# ===================== PROGRESS BAR =====================
def fake_bar(title, duration=4):
    print(f"{C.MAG}{C.B}⚙ {title}{C.R}\n")
    size = 52
    for i in range(size + 1):
        pct = int(i / size * 100)
        sys.stdout.write(
            f"\r{C.CYAN}[{FULL*i}{EMPTY*(size-i)}] {pct}%{C.R}"
        )
        sys.stdout.flush()
        time.sleep(duration / size)
    print(f"\n{C.GREEN}✔ Done{C.R}\n")

# ===================== UPDATE =====================
def update_onyx():
    banner()
    print(f"{C.CYAN}{C.B}🚀 Updating ONYX Framework...{C.R}\n")

    proc = subprocess.Popen(
        [
            "bash", "-c",
            "bash <(curl -s https://raw.githubusercontent.com/zvlrxq-onyx/onyx-scanner/main/install.sh)"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    fake_bar("Syncing core & tools", 6)
    proc.wait()

    print(f"{C.GREEN}{C.B}🔥 ONYX successfully updated 🔥{C.R}\n")
    input("Press ENTER to continue...")

# ===================== OS / PKG =====================
def detect_pm():
    for pm in ["pacman", "apt", "dnf", "yum", "apk"]:
        if shutil.which(pm):
            return pm
    return None

def pkg_cmd(pkg, pm):
    return {
        "pacman": f"sudo pacman -Sy --noconfirm {pkg}",
        "apt": f"sudo apt install -y {pkg}",
        "dnf": f"sudo dnf install -y {pkg}",
        "yum": f"sudo yum install -y {pkg}",
        "apk": f"sudo apk add {pkg}"
    }.get(pm)

def ensure_go(pm):
    if shutil.which("go"):
        return True
    print(f"{C.YELLOW}[!] Go not installed{C.R}")
    if input("Install Go now? [Y/n]: ").lower() == "n":
        return False
    fake_bar("Installing Go", 5)
    subprocess.call(pkg_cmd("golang", pm), shell=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return shutil.which("go") is not None

def check_tools():
    pm = detect_pm()
    if not pm:
        print(f"{C.RED}[!] Unsupported OS{C.R}")
        return

    print(f"{C.CYAN}🧠 Detected package manager: {pm}{C.R}\n")

    for t, m in TOOLS.items():
        if shutil.which(t):
            print(f"{C.GREEN}[✔] {t} installed{C.R}")
            continue

        print(f"{C.YELLOW}[!] {t} not found{C.R}")
        if input(f"Install {t}? [Y/n]: ").lower() == "n":
            continue

        if t == "dalfox":
            if not ensure_go(pm):
                continue
            fake_bar("Installing Dalfox", 4)
            subprocess.call(
                f"go install {m['go']}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            fake_bar(f"Installing {t}", 3)
            subprocess.call(pkg_cmd(m["pkg"], pm), shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print()

# ===================== SCAN =====================
def run_scan(cmd, title, lvl, keyword=None):
    fake_bar(title, 3)
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        for l in out.splitlines():
            if not keyword or keyword in l.lower():
                REPORT[lvl].append(l)
    except:
        pass

# ===================== RESULT =====================
def save_result(target):
    os.makedirs(ONYX_HOME, exist_ok=True)
    with open(RESULT_FILE, "w") as f:
        json.dump({
            "target": target,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report": REPORT
        }, f, indent=2)

def show_result():
    banner()
    if not os.path.exists(RESULT_FILE):
        print(f"{C.RED}No previous result found{C.R}")
        return
    with open(RESULT_FILE) as f:
        d = json.load(f)

    print(f"{C.CYAN}🎯 Target : {d['target']}{C.R}")
    print(f"{C.CYAN}⏰ Time   : {d['time']}{C.R}\n")
    for k, v in d["report"].items():
        print(f"{k} ({len(v)})")
        for i in v:
            print(f" └─ {i}")
        print()

# ===================== MAIN =====================
def main():
    if "--update" in sys.argv:
        update_onyx()
        return
    if "--result" in sys.argv:
        show_result()
        return

    banner()
    disclaimer()
    check_tools()

    while True:
        banner()
        target = input(f"{C.CYAN}{C.B}🌐 ENTER TARGET ➜ {C.R}")

        for k in REPORT:
            REPORT[k].clear()

        run_scan(["sqlmap", "-u", target, "--batch"], "SQL Injection", "HIGH", "payload")
        run_scan(["dalfox", "url", target], "XSS Scan", "CRITICAL", "poc")
        run_scan(
            ["nmap", "-Pn", target.replace("http://","").replace("https://","")],
            "Port Scan", "INFO", "open"
        )
        run_scan(["nikto", "-h", target], "Nikto Scan", "LOW", "+ ")
        run_scan(["nuclei", "-u", target], "Nuclei Scan", "MEDIUM", "[")

        save_result(target)
        print(f"{C.GREEN}✔ Scan completed & saved{C.R}")
        input("Press ENTER to continue...")

if __name__ == "__main__":
    main()
