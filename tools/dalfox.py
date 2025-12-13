import subprocess

def run_dalfox(target):
    process = subprocess.run(
        ["dalfox", "url", target, "--silence"],
        capture_output=True,
        text=True
    )

    results = []

    for line in process.stdout.splitlines():
        if "VULN" in line:
            results.append({"tool": "Dalfox", "name": "XSS Vulnerability", "severity": "high"})
        elif "POC" in line:
            results.append({"tool": "Dalfox", "name": "XSS Vulnerability", "severity": "medium"})
        elif "WEAK" in line:
            results.append({"tool": "Dalfox", "name": "XSS Vulnerability", "severity": "low"})

    return results
