#!/usr/bin/env python3
import os, sys, time, json, shutil, subprocess
from datetime import datetime
from urllib.parse import urlparse

# ===================== META =====================
VERSION = "6.0-FULL"
HOME = os.path.expanduser("~/.onyx")
RESULT_FILE = os.path.join(HOME, "last_result.json")

# ===================== COLORS =====================
class C:
    R="\033[0m"; B="\033[1m"
    CY="\033[96m"; G="\033[92m"; Y="\033[93m"
    RD="\033[91m"; M="\033[95m"; GR="\033[90m"

# ===================== DATA =====================
LEVELS = ["INFO","LOW","MEDIUM","HIGH","CRITICAL"]
REPORT = {k: [] for k in LEVELS}

# ===================== UI =====================
def banner():
    os.system("clear")
    print(C.CY+C.B+f"""
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝

⚡ ONYX {VERSION} ⚡
🛡 Authorized Security Testing Only
"""+C.R)

def bar(title, duration=3.0):
    print(C.M+f"⚙ {title}"+C.R)
    total = 40
    start = time.time()
    for i in range(total+1):
        pct = int(i/total*100)
        elapsed = time.time() - start
        eta = (elapsed/i*(total-i)) if i>0 else 0
        sys.stdout.write(
            f"\r{C.CY}[{'█'*i}{'░'*(total-i)}] {pct:3d}% | ETA {eta:4.1f}s{C.R}"
        )
        sys.stdout.flush()
        time.sleep(duration/total)
    print("\n")

# ===================== UTILS =====================
def host(url): return urlparse(url).netloc

def add(level, vuln, payload, tool, cmd, evidence):
    REPORT[level].append({
        "vuln":vuln, "payload":payload,
        "tool":tool, "cmd":cmd, "evidence":evidence
    })

def ensure(binname, install_cmd):
    if shutil.which(binname): return
    ans = input(C.Y+f"[?] Install {binname}? [Y/n]: "+C.R).strip().lower()
    if ans == "n": return
    bar(f"Installing {binname}", 2)
    subprocess.call(install_cmd, shell=True)

def silence(cmd):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

# ===================== SCANS =====================
def scan_sql(url):
    ensure("sqlmap", "sudo apt install -y sqlmap")
    bar("💉 SQL Injection (sqlmap)", 5)

    cmd = [
        "sqlmap","-u",url,"--batch",
        "--level","5","--risk","3","--threads","5"
    ]
    p = silence(cmd)

    current_param = None
    for line in p.stdout:
        l = line.lower()

        if l.startswith("parameter:"):
            current_param = line.strip()

        # MARKER VALID SQLMAP
        if ("sql injection vulnerability detected" in l or
            "the back-end dbms" in l or
            ("type:" in l and "payload:" in l)):
            add(
                "CRITICAL",
                "SQL Injection",
                current_param or "Auto-detected parameter",
                "sqlmap",
                " ".join(cmd),
                line.strip()
            )

def scan_xss(url):
    ensure("dalfox", "go install github.com/hahwul/dalfox/v2@latest")
    bar("🧪 XSS (Dalfox)", 5)

    cmd = [
        "dalfox","url",url,
        "--deep-domxss","--mining-dom","--mining-dict",
        "--follow-redirects","--no-color"
    ]
    p = silence(cmd)

    for line in p.stdout:
        # MARKER VALID DALFOX
        if ("[V]" in line or "[POC]" in line or "Triggered XSS Payload" in line):
            add(
                "CRITICAL",
                "Cross Site Scripting (XSS)",
                line.strip(),
                "dalfox",
                " ".join(cmd),
                line.strip()
            )

def scan_recon(url):
    ensure("subfinder", "sudo apt install -y subfinder")
    ensure("httpx", "sudo apt install -y httpx")
    ensure("paramspider", "pip install git+https://github.com/devanshbatham/ParamSpider.git")

    bar("🌐 Recon (subfinder + httpx + paramspider)", 4)

    domain = host(url)
    outdir = os.path.join(HOME, "recon")
    os.makedirs(outdir, exist_ok=True)

    subprocess.call(["subfinder","-d",domain,"-silent","-o",f"{outdir}/subs.txt"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["httpx","-l",f"{outdir}/subs.txt","-silent","-o",f"{outdir}/hosts.txt"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["paramspider","-d",domain,"-o",outdir],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    add(
        "LOW",
        "Reconnaissance Data",
        "Subdomains, live hosts, parameters collected",
        "recon",
        "subfinder | httpx | paramspider",
        domain
    )

def scan_web(url):
    ensure("nmap", "sudo apt install -y nmap")
    ensure("nikto", "sudo apt install -y nikto")
    ensure("nuclei", "sudo apt install -y nuclei")

    bar("🕸 Web Scan (nmap + nikto + nuclei)", 4)

    subprocess.call(["nmap","-Pn",host(url)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["nikto","-h",url],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["nuclei","-u",url],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ===================== REPORT =====================
def save(target):
    os.makedirs(HOME, exist_ok=True)
    with open(RESULT_FILE,"w") as f:
        json.dump({
            "target":target,
            "time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report":REPORT
        }, f, indent=2)

def show_result():
    banner()
    if not os.path.exists(RESULT_FILE):
        print(C.RD+"No previous result."+C.R); return
    d = json.load(open(RESULT_FILE))

    print(f"🎯 Target : {d['target']}")
    print(f"⏰ Time   : {d['time']}\n")

    print("📊 Risk Summary:")
    for lvl in LEVELS:
        print(f"  {lvl:<9}: {len(d['report'][lvl])}")

    print("\n📋 Findings:")
    for lvl in LEVELS:
        for f in d["report"][lvl]:
            col = C.RD if lvl=="CRITICAL" else C.Y if lvl=="HIGH" else C.G
            print(f"\n{col}{lvl}{C.R}")
            print(f" ├─ 🔥 Vulnerability : {f['vuln']}")
            print(f" ├─ 🧪 Payload       : {f['payload']}")
            print(f" ├─ 🧰 Tool          : {f['tool']}")
            print(f" ├─ 💻 Command       : {f['cmd']}")
            print(f" └─ 📌 Evidence      : {f['evidence']}")

# ===================== UPDATE / HELP =====================
def update():
    banner()
    bar("🚀 Updating ONYX", 3)
    subprocess.call(
        "curl -s https://raw.githubusercontent.com/zvlrxq-onyx/onyx-scanner/main/install.sh | bash",
        shell=True
    )
    print(C.G+"✔ Update completed"+C.R)
    sys.exit(0)

def help_menu():
    banner()
    print("""
Usage:
  onyx                Start interactive mode
  onyx --help         Show this help
  onyx --update       Update ONYX framework
  onyx --result       Show last scan result
""")

# ===================== MAIN =====================
def main():
    if "--help" in sys.argv: help_menu(); return
    if "--update" in sys.argv: update()
    if "--result" in sys.argv: show_result(); return

    banner()
    target = input(C.CY+"🌐 Enter Target URL ➜ "+C.R).strip()
    if not target: return

    while True:
        banner()
        print(C.G+f"🎯 Target : {target}\n"+C.R)
        print(C.CY+C.B+"""
╔══════════════════════════════════════╗
║        🕷  ONYX SCAN MENU  🕷          ║
╠══════════════════════════════════════╣
║ [1] 💉 SQL Injection Scan            ║
║ [2] 🧪 XSS Scan (Dalfox)             ║
║ [3] 🌐 Recon Scan                    ║
║ [4] 🕸 Web Vulnerability Scan         ║
║ [5] 🚀 Full Scan (ALL MODULES)       ║
║ [6] 📊 Show Last Result              ║
║ [0] ❌ Exit                          ║
╚══════════════════════════════════════╝
"""+C.R)

        choice = input(C.M+"ONYX ➜ "+C.R).strip()
        for k in REPORT: REPORT[k].clear()

        if choice=="1": scan_sql(target)
        elif choice=="2": scan_xss(target)
        elif choice=="3": scan_recon(target)
        elif choice=="4": scan_web(target)
        elif choice=="5":
            scan_recon(target)
            scan_sql(target)
            scan_xss(target)
            scan_web(target)
        elif choice=="6":
            show_result(); input("\nPress ENTER..."); continue
        elif choice=="0":
            print(C.G+"👋 Bye bro, stay legal!"+C.R); break
        else:
            continue

        save(target)
        show_result()
        input(C.Y+"\nPress ENTER to return menu..."+C.R)

if __name__=="__main__":
    main()
