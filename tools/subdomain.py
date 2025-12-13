import subprocess

def run_subdomain(target):
    results = []
    subs = []

    domain = target.replace("http://", "").replace("https://", "").split("/")[0]

    try:
        cmd = ["subfinder", "-silent", "-d", domain]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        for line in proc.stdout.splitlines():
            sub = line.strip()
            if sub:
                subs.append(f"https://{sub}")
                results.append({
                    "tool": "Subdomain Scan",
                    "name": f"Discovered subdomain: {sub}",
                    "severity": "info"
                })

    except Exception as e:
        results.append({
            "tool": "Subdomain Scan",
            "name": f"Subdomain error: {e}",
            "severity": "low"
        })

    return results, subs
