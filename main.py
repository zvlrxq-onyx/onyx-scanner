#!/usr/bin/env python3
import os, sys, time, json, shutil, subprocess
from datetime import datetime
from urllib.parse import urlparse

# ===================== META =====================
VERSION = "6.6"
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
    print(C.CY + C.B + f"""
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝

⚡ ONYX {VERSION} ⚡
🔵 Advanced Web Security Scanner
🛡 Authorized Security Testing Only
""" + C.R)

    print(C.GR + """
[ DISCLAIMER ]
ONYX is designed for authorized security testing only.
Unauthorized scanning of systems you do not own or
have permission to test is illegal and unethical.

Use responsibly. Stay legal. Stay sharp.
""" + C.R)

def bar(title, duration=3.5):
    print(C.M + f"⚙ {title}" + C.R)
    total = 40
    for i in range(total+1):
        pct = int(i/total*100)
        sys.stdout.write(f"\r{C.CY}[{'█'*i}{'░'*(total-i)}] {pct:3d}%{C.R}")
        sys.stdout.flush()
        time.sleep(duration/total)
    print("\n")

# ===================== UTILS =====================
def host(url): 
    return urlparse(url).netloc

def normalize_evidence(ev):
    if ev is None:
        return []
    if isinstance(ev, str):
        return [ev.strip()]
    if isinstance(ev, list):
        return [x.strip() for x in ev if isinstance(x, str)]
    return []

def add(level, title, detail, tool, cmd, evidence):
    REPORT[level].append({
        "title": title,
        "detail": detail,
        "tool": tool,
        "cmd": cmd,
        "evidence": normalize_evidence(evidence)
    })

def silent_bg(cmd):
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ensure(binname, install_cmd):
    if shutil.which(binname):
        return
    ans = input(C.Y+f"[?] Install {binname}? [Y/n]: "+C.R).strip().lower()
    if ans == "n": return
    bar(f"Installing {binname}", 2)
    subprocess.call(install_cmd, shell=True)

# ===================== SCANS =====================
def scan_recon(url):
    ensure("subfinder","sudo apt install -y subfinder")
    ensure("httpx","sudo apt install -y httpx")
    ensure("paramspider","pip install git+https://github.com/devanshbatham/ParamSpider.git")

    bar("🌐 Recon Scan", 4)
    domain = host(url)
    outdir = os.path.join(HOME,"recon")
    os.makedirs(outdir,exist_ok=True)
    subs = f"{outdir}/subs.txt"
    hosts = f"{outdir}/hosts.txt"

    silent_bg(f"subfinder -d {domain} -silent -o {subs}").wait()
    if os.path.exists(subs):
        data = open(subs).read().splitlines()
        add("INFO","Subdomain Enumeration",f"{len(data)} subdomains found","subfinder","",data[:10])

    silent_bg(f"httpx -l {subs} -silent -o {hosts}").wait()
    if os.path.exists(hosts):
        data = open(hosts).read().splitlines()
        add("INFO","Live Hosts Detection",f"{len(data)} live hosts found","httpx","",data[:10])

    silent_bg(f"paramspider -d {domain} -o {outdir}").wait()
    add("INFO","Parameters Enumeration","Params collected using paramspider","paramspider","",[domain])

def scan_sql(url):
    ensure("sqlmap","sudo apt install -y sqlmap")
    bar("💉 SQL Injection Scan",5)
    p = subprocess.Popen(f"sqlmap -u {url} --batch --level 5 --risk 3", shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in p.stdout:
        if "payload:" in line.lower():
            add("CRITICAL","SQL Injection","Confirmed SQL Injection","sqlmap","",line.strip())

def scan_xss(url):
    ensure("dalfox","go install github.com/hahwul/dalfox/v2@latest")
    bar("🧪 XSS Scan",5)
    cmd = f"dalfox url {url} --deep-domxss --mining-dom --mining-dict --follow-redirects --no-color"
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    for line in p.stdout:
        if "[v]" in line.lower() or "[poc]" in line.lower() or "triggered xss payload" in line.lower():
            add("CRITICAL","Cross Site Scripting (XSS)",line.strip(),"dalfox","",line.strip())

def scan_web(url):
    ensure("nmap","sudo apt install -y nmap")
    ensure("nikto","sudo apt install -y nikto")
    ensure("nuclei","sudo apt install -y nuclei")
    bar("🕸 Web Scan",4)
    silent_bg(f"nmap -Pn {host(url)}").wait()
    silent_bg(f"nikto -h {url}").wait()
    silent_bg(f"nuclei -u {url}").wait()
    add("INFO","Web Scan Completed","Nmap/Nikto/Nuclei executed","webscan","",[url])

# ===================== REPORT =====================
def save(target):
    os.makedirs(HOME,exist_ok=True)
    with open(RESULT_FILE,"w") as f:
        json.dump({"target":target,"time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"report":REPORT},f,indent=2)

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
    for lvl in LEVELS:
        col = C.RD if lvl=="CRITICAL" else C.Y if lvl=="HIGH" else C.CY
        for f in d["report"][lvl]:
            print(f"\n{col}{lvl}{C.R}")
            print(f" ├─ 📌 Finding : {f['title']}")
            print(f" ├─ 📄 Detail  : {f['detail']}")
            print(f" └─ 🧾 Evidence:")
            for e in f["evidence"]:
                print(f"     • {e}")

# ===================== UPDATE =====================
def update():
    banner()
    p = silent_bg("bash -c 'curl -s https://raw.githubusercontent.com/zvlrxq-onyx/onyx-scanner/main/install.sh | bash >/dev/null 2>&1'")
    bar("🚀 Updating ONYX",4.5)
    p.wait()
    print(C.G+"✔ ONYX updated successfully"+C.R)
    sys.exit(0)

# ===================== HELP =====================
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
        print(C.CY+C.B+"""
╔═════════════════════════════════════════════╗
║              🕷  ONYX SCAN MENU  🕷           ║
╠═════════════════════════════════════════════╣
║ [1] 🌐 Recon Scan (subfinder/httpx/param)   ║
║ [2] 💉 SQL Injection Scan                   ║
║ [3] 🧪 XSS Scan (Dalfox)                    ║
║ [4] 🕸 Web Vulnerability Scan                ║
║ [5] 🚀 Full Scan (ALL MODULES)              ║
║ [6] 📊 Show Last Result                     ║
║ [0] ❌ Exit                                 ║
╚═════════════════════════════════════════════╝
""" + C.R)
        choice = input(C.M+"ONYX ➜ "+C.R).strip()
        for k in REPORT: REPORT[k].clear()

        if choice=="1": scan_recon(target)
        elif choice=="2": scan_sql(target)
        elif choice=="3": scan_xss(target)
        elif choice=="4": scan_web(target)
        elif choice=="5":
            scan_recon(target); scan_sql(target)
            scan_xss(target); scan_web(target)
        elif choice=="6":
            show_result(); input("\nPress ENTER..."); continue
        elif choice=="0":
            print(C.G+"👋 Bye bro, stay legal!"+C.R); break
        else: continue

        save(target)
        show_result()
        input(C.Y+"\nPress ENTER to return menu..."+C.R)

if __name__=="__main__":
    main()
