#!/usr/bin/env python3
import os, sys, time, json, shutil, subprocess, threading
from datetime import datetime
from urllib.parse import urlparse

# ===================== META =====================
VERSION = "6.8"
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

# ===================== PACKAGE MANAGER DETECTION =====================
def detect_pkg_manager():
    managers = [
        ("pacman",       "sudo pacman -S --noconfirm {pkg}",  "pacman"),
        ("apt",          "sudo apt install -y {pkg}",         "apt"),
        ("apt-get",      "sudo apt-get install -y {pkg}",     "apt-get"),
        ("dnf",          "sudo dnf install -y {pkg}",         "dnf"),
        ("yum",          "sudo yum install -y {pkg}",         "yum"),
        ("zypper",       "sudo zypper install -y {pkg}",      "zypper"),
        ("emerge",       "sudo emerge {pkg}",                 "emerge"),
        ("apk",          "sudo apk add {pkg}",                "apk"),
        ("brew",         "brew install {pkg}",                "brew"),
        ("xbps-install", "sudo xbps-install -y {pkg}",       "xbps"),
        ("nix-env",      "nix-env -iA nixpkgs.{pkg}",        "nix"),
        ("pkg",          "sudo pkg install -y {pkg}",         "pkg"),
        ("pkg_add",      "sudo pkg_add {pkg}",                "pkg_add"),
    ]
    for bin_name, cmd_tpl, name in managers:
        if shutil.which(bin_name):
            return name, cmd_tpl
    return None, None

PKG_MANAGER_NAME, PKG_INSTALL_TPL = detect_pkg_manager()

PKG_NAME_MAP = {
    "go":       {"pacman":"go","apt":"golang","apt-get":"golang","dnf":"golang","yum":"golang","zypper":"go","apk":"go","brew":"go","emerge":"dev-lang/go","default":"golang"},
    "subfinder":{"pacman":"subfinder","apt":"subfinder","dnf":"subfinder","default":"subfinder"},
    "httpx":    {"pacman":"httpx","apt":"httpx","dnf":"httpx","default":"httpx"},
    "sqlmap":   {"pacman":"sqlmap","apt":"sqlmap","dnf":"sqlmap","brew":"sqlmap","default":"sqlmap"},
    "nmap":     {"pacman":"nmap","apt":"nmap","dnf":"nmap","brew":"nmap","apk":"nmap","default":"nmap"},
    "nikto":    {"pacman":"nikto","apt":"nikto","dnf":"nikto","brew":"nikto","default":"nikto"},
    "nuclei":   {"pacman":"nuclei","apt":"nuclei","dnf":"nuclei","brew":"nuclei","default":"nuclei"},
}

def get_install_cmd(tool_bin, fallback_cmd=None):
    if PKG_MANAGER_NAME is None:
        return fallback_cmd or f"# No package manager detected. Install {tool_bin} manually."
    pkg = PKG_NAME_MAP.get(tool_bin, {}).get(PKG_MANAGER_NAME) \
          or PKG_NAME_MAP.get(tool_bin, {}).get("default") \
          or tool_bin
    return PKG_INSTALL_TPL.format(pkg=pkg)

# ===================== UI =====================
def banner():
    os.system("clear")
    pm_info = f"Package Manager : {PKG_MANAGER_NAME or 'Not detected'}"
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
📦 {pm_info}
""" + C.R)
    print(C.GR + """
[ DISCLAIMER ]
ONYX is designed for authorized security testing only.
Unauthorized scanning of systems you do not own or
have permission to test is illegal and unethical.

Use responsibly. Stay legal. Stay sharp.
""" + C.R)

def bar(title, duration=3.5):
    """Fake progress bar hanya untuk install/update."""
    print(C.M + f"⚙ {title}" + C.R)
    total = 40
    for i in range(total + 1):
        pct = int(i / total * 100)
        sys.stdout.write(f"\r{C.CY}[{'█'*i}{'░'*(total-i)}] {pct:3d}%{C.R}")
        sys.stdout.flush()
        time.sleep(duration / total)
    print("\n")

def scan_bar(title, stop_event, est=60):
    """
    Progress bar yang jalan pelan sambil scan kerja di background.
    - Naik 0% → 95% selama est detik
    - Begitu stop_event di-set (scan selesai), langsung lompat ke 100%
    """
    total = 40
    print(C.M + f"⚙ {title}" + C.R)
    i = 0
    target_95 = int(total * 0.95)
    tick = est / target_95

    while i < target_95 and not stop_event.is_set():
        pct = int(i / total * 100)
        sys.stdout.write(f"\r{C.CY}[{chr(9608)*i}{chr(9617)*(total-i)}] {pct:3d}%{C.R}")
        sys.stdout.flush()
        time.sleep(tick)
        i += 1

    while i <= total:
        pct = int(i / total * 100)
        sys.stdout.write(f"\r{C.CY}[{chr(9608)*i}{chr(9617)*(total-i)}] {pct:3d}%{C.R}")
        sys.stdout.flush()
        time.sleep(0.02)
        i += 1

    sys.stdout.write(f"\r{C.G}[{chr(9608)*total}] 100% ✔ Selesai!{C.R}          \n\n")
    sys.stdout.flush()

# ===================== UTILS =====================
def host(url):
    return urlparse(url).netloc

def normalize_evidence(ev):
    if ev is None: return []
    if isinstance(ev, str): return [ev.strip()]
    if isinstance(ev, list): return [x.strip() for x in ev if isinstance(x, str)]
    return []

def add(level, title, detail, tool, cmd, evidence):
    REPORT[level].append({
        "title": title, "detail": detail,
        "tool": tool, "cmd": cmd,
        "evidence": normalize_evidence(evidence)
    })

def silent_bg(cmd):
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _symlink_to_path(binname):
    candidates = [
        os.path.expanduser(f"~/go/bin/{binname}"),
        os.path.expanduser(f"~/.local/bin/{binname}"),
        os.path.expanduser(f"~/.local/pipx/venvs/{binname}/bin/{binname}"),
        os.path.join(os.environ.get("GOPATH", ""), f"bin/{binname}"),
    ]
    for src in candidates:
        if os.path.isfile(src):
            dest = f"/usr/local/bin/{binname}"
            try:
                subprocess.call(f"sudo ln -sf {src} {dest}", shell=True)
                print(C.G + f"✔ Linked {src} → {dest}" + C.R)
            except Exception:
                print(C.Y + f"⚠ Gagal symlink. Tambahkan {os.path.dirname(src)} ke PATH." + C.R)
            return True
    return False

def ensure_go_tool(binname, go_pkg):
    if shutil.which(binname): return
    print(C.Y + f"[!] '{binname}' tidak ditemukan." + C.R)
    ans = input(C.Y + f"[?] Install via Go? (go install {go_pkg}) [Y/n]: " + C.R).strip().lower()
    if ans == "n": return
    if not shutil.which("go"):
        print(C.Y + "[!] Go tidak ditemukan. Menginstall Go dulu..." + C.R)
        subprocess.call(get_install_cmd("go", "sudo apt install -y golang"), shell=True)
        if not shutil.which("go"):
            print(C.RD + "✘ Gagal install Go. Install manual: https://go.dev/dl/" + C.R)
            return
    bar(f"Installing {binname} via Go", 3)
    gopath = os.environ.get("GOPATH", os.path.expanduser("~/go"))
    env = os.environ.copy()
    env["GOPATH"] = gopath
    env["PATH"] = f"{gopath}/bin:" + env.get("PATH", "")
    ret = subprocess.call(f"go install {go_pkg}", shell=True, env=env)
    if ret != 0:
        print(C.RD + f"✘ Gagal install {binname}." + C.R); return
    if not _symlink_to_path(binname):
        print(C.Y + f"⚠ Tambahkan ke PATH:\n  export PATH=$PATH:{gopath}/bin" + C.R)
    else:
        print(C.G + f"✔ {binname} siap dipakai global!" + C.R)

def _in_virtualenv():
    return (
        os.environ.get("VIRTUAL_ENV") is not None
        or getattr(sys, "real_prefix", None) is not None
        or (getattr(sys, "base_prefix", sys.prefix) != sys.prefix)
    )

def ensure_pip_tool(binname, pip_pkg_or_url):
    if shutil.which(binname): return
    print(C.Y + f"[!] '{binname}' tidak ditemukan." + C.R)
    ans = input(C.Y + f"[?] Install via pip? (pip install {pip_pkg_or_url}) [Y/n]: " + C.R).strip().lower()
    if ans == "n": return
    bar(f"Installing {binname} via pip", 2)
    in_venv = _in_virtualenv()
    if shutil.which("pipx"):
        ret = subprocess.call(f"pipx install '{pip_pkg_or_url}'", shell=True)
        if ret == 0:
            _symlink_to_path(binname); print(C.G + f"✔ {binname} installed via pipx!" + C.R); return
    if in_venv:
        ret = subprocess.call(f"pip install '{pip_pkg_or_url}'", shell=True)
        if ret == 0:
            _symlink_to_path(binname); print(C.G + f"✔ {binname} installed!" + C.R); return
    ret = subprocess.call(f"pip install --user '{pip_pkg_or_url}'", shell=True)
    if ret == 0:
        _symlink_to_path(binname); print(C.G + f"✔ {binname} installed!" + C.R); return
    ret = subprocess.call(f"pip install --break-system-packages '{pip_pkg_or_url}'", shell=True)
    if ret == 0:
        _symlink_to_path(binname); print(C.G + f"✔ {binname} installed!" + C.R); return
    print(C.RD + f"✘ Semua strategi gagal. Coba manual: pipx install '{pip_pkg_or_url}'" + C.R)

def ensure(binname, fallback_install_cmd=None):
    if shutil.which(binname): return
    install_cmd = get_install_cmd(binname, fallback_install_cmd)
    ans = input(C.Y + f"[?] '{binname}' tidak ada. Install: {install_cmd} ? [Y/n]: " + C.R).strip().lower()
    if ans == "n": return
    bar(f"Installing {binname}", 2)
    subprocess.call(install_cmd, shell=True)

# ===================== SCANS =====================
def scan_recon(url):
    ensure("subfinder")
    ensure("httpx")
    ensure_pip_tool("paramspider", "git+https://github.com/devanshbatham/ParamSpider.git")

    domain = host(url)
    outdir = os.path.join(HOME, "recon")
    os.makedirs(outdir, exist_ok=True)
    subs  = f"{outdir}/subs.txt"
    lhosts = f"{outdir}/hosts.txt"

    stop = threading.Event()
    spinner_t = threading.Thread(target=scan_bar, args=("🌐 Recon Scan", stop, 30))
    spinner_t.start()

    silent_bg(f"subfinder -d {domain} -silent -o {subs}").wait()
    if os.path.exists(subs):
        silent_bg(f"httpx -l {subs} -silent -o {lhosts}").wait()
        silent_bg(f"paramspider -d {domain} -o {outdir}").wait()

    stop.set(); spinner_t.join()

    if os.path.exists(subs):
        data = open(subs).read().splitlines()
        add("INFO", "Subdomain Enumeration", f"{len(data)} subdomain ditemukan", "subfinder", "", data[:10])
    if os.path.exists(lhosts):
        data = open(lhosts).read().splitlines()
        add("INFO", "Live Hosts Detection", f"{len(data)} live host", "httpx", "", data[:10])
    add("INFO", "Parameters Enumeration", "Params dikumpulkan via paramspider", "paramspider", "", [domain])

def scan_sql(url):
    ensure("sqlmap")
    cmd = (
        f"sqlmap -u {url} --batch "
        f"--level 2 --risk 1 "
        f"--threads 5 --timeout 10 "
        f"--smart --technique=BEUSTQ "
        f"--stop-on-first"
    )
    findings = []

    stop = threading.Event()
    spinner_t = threading.Thread(target=scan_bar, args=("💉 SQL Injection Scan", stop, 45))
    spinner_t.start()

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in p.stdout:
        l = line.strip()
        if any(kw in l.lower() for kw in ("payload:", "is vulnerable", "injected", "back-end dbms")):
            findings.append(l)
    p.wait()

    stop.set(); spinner_t.join()

    if findings:
        for f in findings:
            add("CRITICAL", "SQL Injection", "Confirmed SQL Injection", "sqlmap", cmd, f)
    else:
        add("INFO", "SQL Injection Scan", "Tidak ada SQLi terdeteksi", "sqlmap", cmd, [url])

def scan_xss(url):
    ensure_go_tool("dalfox", "github.com/hahwul/dalfox/v2@latest")
    cmd = f"dalfox url {url} --deep-domxss --mining-dom --mining-dict --follow-redirects --no-color"
    findings = []

    stop = threading.Event()
    spinner_t = threading.Thread(target=scan_bar, args=("🧪 XSS Scan", stop, 40))
    spinner_t.start()

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in p.stdout:
        if "[v]" in line.lower() or "[poc]" in line.lower() or "triggered xss payload" in line.lower():
            findings.append(line.strip())
    p.wait()

    stop.set(); spinner_t.join()

    if findings:
        for f in findings:
            add("CRITICAL", "Cross Site Scripting (XSS)", f, "dalfox", cmd, f)
    else:
        add("INFO", "XSS Scan", "Tidak ada XSS terdeteksi", "dalfox", cmd, [url])

def scan_web(url):
    ensure("nmap")
    ensure("nikto")
    ensure("nuclei")

    target_host = host(url)

    # ── Spinner jalan di thread sendiri ──────────────────────────────────
    stop = threading.Event()
    spinner_t = threading.Thread(target=scan_bar, args=("🕸 Web Vulnerability Scan", stop, 90))
    spinner_t.start()

    # ── Ketiga tool jalan PARALLEL ────────────────────────────────────────
    procs = {
        "nmap": subprocess.Popen(
            f"nmap -Pn -T4 -n --top-ports 1000 {target_host}",
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        ),
        "nikto": subprocess.Popen(
            f"nikto -h {url} -maxtime 90 -nointeractive",
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        ),
        "nuclei": subprocess.Popen(
            f"nuclei -u {url} -timeout 8 -rl 100 -severity low,medium,high,critical -silent",
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        ),
    }

    tool_output = {k: [] for k in procs}

    def collect(name, proc):
        try:
            out, _ = proc.communicate(timeout=150)
            tool_output[name] = [l.strip() for l in out.splitlines() if l.strip()]
        except subprocess.TimeoutExpired:
            proc.kill()
            tool_output[name] = ["[timeout] scan dihentikan setelah 2.5 menit"]

    collectors = [threading.Thread(target=collect, args=(n, p)) for n, p in procs.items()]
    for c in collectors: c.start()
    for c in collectors: c.join()

    stop.set(); spinner_t.join()

    # ── Parse hasil ───────────────────────────────────────────────────────
    open_ports = [l for l in tool_output["nmap"] if "open" in l.lower()]
    if open_ports:
        add("INFO", "Open Ports (Nmap)", f"{len(open_ports)} port terbuka", "nmap", "", open_ports[:20])
    else:
        add("INFO", "Open Ports (Nmap)", "Tidak ada port terbuka / timeout", "nmap", "", tool_output["nmap"][:5])

    nikto_hits = [l for l in tool_output["nikto"] if l.startswith("+")]
    if nikto_hits:
        for hit in nikto_hits[:15]:
            sev = "HIGH" if any(k in hit.lower() for k in ("injection","xss","rce","exec","upload","bypass")) else "MEDIUM"
            add(sev, "Nikto Finding", hit, "nikto", "", [hit])
    else:
        add("INFO", "Nikto Scan", "Tidak ada temuan / timeout", "nikto", "", [url])

    if tool_output["nuclei"]:
        for hit in tool_output["nuclei"][:15]:
            sev = "CRITICAL" if "critical" in hit.lower() else \
                  "HIGH"     if "high"     in hit.lower() else \
                  "MEDIUM"   if "medium"   in hit.lower() else "LOW"
            add(sev, "Nuclei Finding", hit, "nuclei", "", [hit])
    else:
        add("INFO", "Nuclei Scan", "Tidak ada temuan / timeout", "nuclei", "", [url])

# ===================== REPORT =====================
def save(target):
    os.makedirs(HOME, exist_ok=True)
    with open(RESULT_FILE, "w") as f:
        json.dump({
            "target": target,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report": REPORT
        }, f, indent=2)

def show_result():
    banner()
    if not os.path.exists(RESULT_FILE):
        print(C.RD + "Belum ada hasil scan." + C.R); return
    d = json.load(open(RESULT_FILE))
    print(f"🎯 Target : {d['target']}")
    print(f"⏰ Time   : {d['time']}\n")
    print("📊 Risk Summary:")
    for lvl in LEVELS:
        print(f"  {lvl:<9}: {len(d['report'][lvl])}")
    for lvl in LEVELS:
        col = C.RD if lvl == "CRITICAL" else C.Y if lvl == "HIGH" else C.CY
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
    bar("🚀 Updating ONYX", 4.5)
    p.wait()
    print(C.G + "✔ ONYX updated successfully" + C.R)
    sys.exit(0)

# ===================== HELP =====================
def help_menu():
    banner()
    print(f"""
Usage:
  onyx                Start interactive mode
  onyx --help         Show this help
  onyx --update       Update ONYX framework
  onyx --result       Show last scan result

Detected Package Manager: {PKG_MANAGER_NAME or 'None (manual install required)'}
""")

# ===================== MAIN =====================
def main():
    if "--help"   in sys.argv: help_menu(); return
    if "--update" in sys.argv: update()
    if "--result" in sys.argv: show_result(); return

    banner()
    target = input(C.CY + "🌐 Enter Target URL ➜ " + C.R).strip()
    if not target: return

    while True:
        banner()
        print(C.CY + C.B + """
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
        choice = input(C.M + "ONYX ➜ " + C.R).strip()
        for k in REPORT: REPORT[k].clear()

        if   choice == "1": scan_recon(target)
        elif choice == "2": scan_sql(target)
        elif choice == "3": scan_xss(target)
        elif choice == "4": scan_web(target)
        elif choice == "5":
            scan_recon(target); scan_sql(target)
            scan_xss(target);   scan_web(target)
        elif choice == "6":
            show_result(); input("\nPress ENTER..."); continue
        elif choice == "0":
            print(C.G + "👋 Bye bro, stay legal!" + C.R); break
        else:
            continue

        save(target)
        show_result()
        input(C.Y + "\nPress ENTER to return menu..." + C.R)

if __name__ == "__main__":
    main()
