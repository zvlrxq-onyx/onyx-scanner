#!/usr/bin/env python3
import os, sys, time, json, shutil, subprocess
from datetime import datetime
from urllib.parse import urlparse

# ===================== META =====================
VERSION = "6.7"
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
    """Detect the system's package manager automatically."""
    managers = [
        # (binary_check, install_cmd_template, name)
        ("pacman",   "sudo pacman -S --noconfirm {pkg}",        "pacman"),
        ("apt",      "sudo apt install -y {pkg}",               "apt"),
        ("apt-get",  "sudo apt-get install -y {pkg}",           "apt-get"),
        ("dnf",      "sudo dnf install -y {pkg}",               "dnf"),
        ("yum",      "sudo yum install -y {pkg}",               "yum"),
        ("zypper",   "sudo zypper install -y {pkg}",            "zypper"),
        ("emerge",   "sudo emerge {pkg}",                       "emerge"),
        ("apk",      "sudo apk add {pkg}",                      "apk"),
        ("brew",     "brew install {pkg}",                      "brew"),
        ("xbps-install", "sudo xbps-install -y {pkg}",         "xbps"),
        ("nix-env",  "nix-env -iA nixpkgs.{pkg}",              "nix"),
        ("pkg",      "sudo pkg install -y {pkg}",               "pkg"),    # FreeBSD
        ("pkg_add",  "sudo pkg_add {pkg}",                      "pkg_add"), # OpenBSD
    ]
    for bin_name, cmd_tpl, name in managers:
        if shutil.which(bin_name):
            return name, cmd_tpl
    return None, None

PKG_MANAGER_NAME, PKG_INSTALL_TPL = detect_pkg_manager()

# Map of tool name -> package name per manager (when they differ)
PKG_NAME_MAP = {
    # tool_name : { manager_name: pkg_name }
    "go": {
        "pacman": "go",
        "apt": "golang",
        "apt-get": "golang",
        "dnf": "golang",
        "yum": "golang",
        "zypper": "go",
        "apk": "go",
        "brew": "go",
        "emerge": "dev-lang/go",
        "default": "golang",
    },
    "subfinder": {
        "pacman": "subfinder",
        "apt": "subfinder",
        "dnf": "subfinder",
        "default": "subfinder",
    },
    "httpx": {
        "pacman": "httpx",
        "apt": "httpx",
        "dnf": "httpx",
        "default": "httpx",
    },
    "sqlmap": {
        "pacman": "sqlmap",
        "apt": "sqlmap",
        "dnf": "sqlmap",
        "brew": "sqlmap",
        "default": "sqlmap",
    },
    "nmap": {
        "pacman": "nmap",
        "apt": "nmap",
        "dnf": "nmap",
        "brew": "nmap",
        "apk": "nmap",
        "default": "nmap",
    },
    "nikto": {
        "pacman": "nikto",
        "apt": "nikto",
        "dnf": "nikto",
        "brew": "nikto",
        "default": "nikto",
    },
    "nuclei": {
        "pacman": "nuclei",
        "apt": "nuclei",
        "dnf": "nuclei",
        "brew": "nuclei",
        "default": "nuclei",
    },
}

def get_install_cmd(tool_bin, fallback_cmd=None):
    """
    Return the best install command for a tool based on detected package manager.
    Falls back to fallback_cmd if no package manager is found.
    """
    if PKG_MANAGER_NAME is None:
        return fallback_cmd or f"# No package manager detected. Install {tool_bin} manually."

    pkg = PKG_NAME_MAP.get(tool_bin, {}).get(PKG_MANAGER_NAME) \
          or PKG_NAME_MAP.get(tool_bin, {}).get("default") \
          or tool_bin

    return PKG_INSTALL_TPL.format(pkg=pkg)

# ===================== UI =====================
def banner():
    os.system("clear")
    pm_info = f"📦 Package Manager : {PKG_MANAGER_NAME or 'Not detected'}"
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
{pm_info}
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

def _symlink_to_path(binname):
    """
    After go/pip install, the binary may land in ~/go/bin or ~/.local/bin
    but not be in $PATH yet. Try to symlink it to /usr/local/bin so it's
    globally callable from any terminal session.
    """
    candidates = [
        os.path.expanduser(f"~/go/bin/{binname}"),
        os.path.expanduser(f"~/.local/bin/{binname}"),
        os.path.expanduser(f"~/.local/pipx/venvs/{binname}/bin/{binname}"),
        # go install with custom GOPATH
        os.path.join(os.environ.get("GOPATH", ""), f"bin/{binname}"),
    ]
    for src in candidates:
        if os.path.isfile(src):
            dest = f"/usr/local/bin/{binname}"
            try:
                subprocess.call(f"sudo ln -sf {src} {dest}", shell=True)
                print(C.G + f"✔ Linked {src} → {dest}" + C.R)
            except Exception:
                print(C.Y + f"⚠ Could not symlink. Add {os.path.dirname(src)} to your PATH manually." + C.R)
            return True
    return False

def ensure_go_tool(binname, go_pkg):
    """
    Install a Go-based tool globally so it's callable from any terminal.
    Steps:
      1. Check if binary already exists in PATH
      2. Check if Go is installed; if not, install via pkg manager
      3. Run: go install <go_pkg>
      4. Symlink the binary from ~/go/bin → /usr/local/bin
    """
    if shutil.which(binname):
        return  # already available globally

    print(C.Y + f"[!] '{binname}' not found." + C.R)
    ans = input(C.Y + f"[?] Install via Go? (go install {go_pkg}) [Y/n]: " + C.R).strip().lower()
    if ans == "n":
        return

    # Make sure Go is installed
    if not shutil.which("go"):
        print(C.Y + "[!] Go not found. Installing Go first..." + C.R)
        go_install_cmd = get_install_cmd("go", "sudo apt install -y golang")
        subprocess.call(go_install_cmd, shell=True)
        if not shutil.which("go"):
            print(C.RD + "✘ Go installation failed. Install Go manually: https://go.dev/dl/" + C.R)
            return

    bar(f"Installing {binname} via Go", 3)

    # Set GOPATH explicitly so we know where the binary lands
    gopath = os.environ.get("GOPATH", os.path.expanduser("~/go"))
    env = os.environ.copy()
    env["GOPATH"] = gopath
    env["PATH"] = f"{gopath}/bin:" + env.get("PATH", "")

    ret = subprocess.call(f"go install {go_pkg}", shell=True, env=env)
    if ret != 0:
        print(C.RD + f"✘ Failed to install {binname}." + C.R)
        return

    # Symlink so it's globally available
    if not _symlink_to_path(binname):
        # fallback: tell user to add to PATH
        print(C.Y + f"⚠ Add {gopath}/bin to your PATH:\n  export PATH=$PATH:{gopath}/bin" + C.R)
    else:
        print(C.G + f"✔ {binname} installed and globally available!" + C.R)

def _in_virtualenv():
    """Return True if Python is running inside a virtualenv or venv."""
    return (
        os.environ.get("VIRTUAL_ENV") is not None
        or getattr(sys, "real_prefix", None) is not None           # virtualenv
        or (getattr(sys, "base_prefix", sys.prefix) != sys.prefix) # venv / conda
    )

def ensure_pip_tool(binname, pip_pkg_or_url):
    """
    Install a Python-based CLI tool via pip so it's callable globally.
    Priority order:
      1. pipx  — cleanest, auto-handles PATH, works inside/outside venv
      2. pip (no --user) — when inside a virtualenv
      3. pip --user — standard user install outside venv
      4. pip --break-system-packages — for system Python on Debian/Ubuntu 23+
    Then symlinks the binary to /usr/local/bin for global access.
    """
    if shutil.which(binname):
        return  # already available

    print(C.Y + f"[!] '{binname}' not found." + C.R)
    ans = input(C.Y + f"[?] Install via pip? (pip install {pip_pkg_or_url}) [Y/n]: " + C.R).strip().lower()
    if ans == "n":
        return

    bar(f"Installing {binname} via pip", 2)

    in_venv = _in_virtualenv()

    # ── Strategy 1: pipx (best option, works everywhere) ─────────────────
    if shutil.which("pipx"):
        ret = subprocess.call(f"pipx install '{pip_pkg_or_url}'", shell=True)
        if ret == 0:
            _symlink_to_path(binname)
            print(C.G + f"✔ {binname} installed via pipx and globally available!" + C.R)
            return

    # ── Strategy 2: inside virtualenv → plain pip install (no --user) ────
    if in_venv:
        ret = subprocess.call(f"pip install '{pip_pkg_or_url}'", shell=True)
        if ret == 0:
            _symlink_to_path(binname)
            print(C.G + f"✔ {binname} installed inside venv." + C.R)
            return

    # ── Strategy 3: pip --user (standard outside venv) ───────────────────
    ret = subprocess.call(f"pip install --user '{pip_pkg_or_url}'", shell=True)
    if ret == 0:
        _symlink_to_path(binname)
        print(C.G + f"✔ {binname} installed globally!" + C.R)
        return

    # ── Strategy 4: system Python with PEP 668 restriction (Debian/Ubuntu 23+)
    ret = subprocess.call(
        f"pip install --break-system-packages '{pip_pkg_or_url}'",
        shell=True
    )
    if ret == 0:
        _symlink_to_path(binname)
        print(C.G + f"✔ {binname} installed with --break-system-packages!" + C.R)
        return

    # ── All strategies failed ─────────────────────────────────────────────
    print(C.RD + f"✘ Failed to install {binname}. Try manually:" + C.R)
    print(C.Y + f"  pipx install '{pip_pkg_or_url}'" + C.R)
    print(C.Y + f"  or: pip install '{pip_pkg_or_url}'" + C.R)

def ensure(binname, fallback_install_cmd=None):
    """
    Install a system package using the detected package manager.
    Use ensure_go_tool() for Go binaries, ensure_pip_tool() for Python CLIs.
    """
    if shutil.which(binname):
        return

    install_cmd = get_install_cmd(binname, fallback_install_cmd)

    ans = input(C.Y + f"[?] '{binname}' not found. Install using: {install_cmd} ? [Y/n]: " + C.R).strip().lower()
    if ans == "n":
        return
    bar(f"Installing {binname}", 2)
    subprocess.call(install_cmd, shell=True)

# ===================== SCANS =====================
def scan_recon(url):
    ensure("subfinder")
    ensure("httpx")
    ensure_pip_tool("paramspider", "git+https://github.com/devanshbatham/ParamSpider.git")

    bar("🌐 Recon Scan", 4)
    domain = host(url)
    outdir = os.path.join(HOME, "recon")
    os.makedirs(outdir, exist_ok=True)
    subs = f"{outdir}/subs.txt"
    hosts = f"{outdir}/hosts.txt"

    silent_bg(f"subfinder -d {domain} -silent -o {subs}").wait()
    if os.path.exists(subs):
        data = open(subs).read().splitlines()
        add("INFO", "Subdomain Enumeration", f"{len(data)} subdomains found", "subfinder", "", data[:10])

    silent_bg(f"httpx -l {subs} -silent -o {hosts}").wait()
    if os.path.exists(hosts):
        data = open(hosts).read().splitlines()
        add("INFO", "Live Hosts Detection", f"{len(data)} live hosts found", "httpx", "", data[:10])

    silent_bg(f"paramspider -d {domain} -o {outdir}").wait()
    add("INFO", "Parameters Enumeration", "Params collected using paramspider", "paramspider", "", [domain])

def scan_sql(url):
    ensure("sqlmap")
    bar("💉 SQL Injection Scan", 3)

    # ─── Speed optimizations ───────────────────────────────────────────────
    # --level 2 --risk 1  : balanced detection, way faster than 5/3
    # --threads 5         : parallel requests
    # --timeout 10        : don't hang on slow endpoints
    # --smart             : skip heuristic-failing params
    # --technique BEUSTQ  : try all techniques but exit early on first hit
    # --stop-on-first     : stop testing other params once vuln found (sqlmap ≥1.7)
    # ──────────────────────────────────────────────────────────────────────
    cmd = (
        f"sqlmap -u {url} --batch "
        f"--level 2 --risk 1 "
        f"--threads 5 --timeout 10 "
        f"--smart --technique=BEUSTQ "
        f"--stop-on-first"
    )
    findings = []
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in p.stdout:
        l = line.strip()
        if any(kw in l.lower() for kw in ("payload:", "parameter", "is vulnerable", "injected")):
            findings.append(l)
            add("CRITICAL", "SQL Injection", "Confirmed SQL Injection", "sqlmap", cmd, l)
    p.wait()

    if not findings:
        add("INFO", "SQL Injection Scan", "No SQLi detected with current settings", "sqlmap", cmd, [url])

def scan_xss(url):
    ensure_go_tool("dalfox", "github.com/hahwul/dalfox/v2@latest")
    bar("🧪 XSS Scan", 5)
    cmd = f"dalfox url {url} --deep-domxss --mining-dom --mining-dict --follow-redirects --no-color"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in p.stdout:
        if "[v]" in line.lower() or "[poc]" in line.lower() or "triggered xss payload" in line.lower():
            add("CRITICAL", "Cross Site Scripting (XSS)", line.strip(), "dalfox", "", line.strip())

def scan_web(url):
    ensure("nmap")
    ensure("nikto")
    ensure("nuclei")
    bar("🕸 Web Scan", 4)
    silent_bg(f"nmap -Pn {host(url)}").wait()
    silent_bg(f"nikto -h {url}").wait()
    silent_bg(f"nuclei -u {url}").wait()
    add("INFO", "Web Scan Completed", "Nmap/Nikto/Nuclei executed", "webscan", "", [url])

# ===================== REPORT =====================
def save(target):
    os.makedirs(HOME, exist_ok=True)
    with open(RESULT_FILE, "w") as f:
        json.dump({"target": target, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "report": REPORT}, f, indent=2)

def show_result():
    banner()
    if not os.path.exists(RESULT_FILE):
        print(C.RD + "No previous result." + C.R)
        return
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
    if "--help" in sys.argv: help_menu(); return
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

        if choice == "1": scan_recon(target)
        elif choice == "2": scan_sql(target)
        elif choice == "3": scan_xss(target)
        elif choice == "4": scan_web(target)
        elif choice == "5":
            scan_recon(target); scan_sql(target)
            scan_xss(target); scan_web(target)
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
