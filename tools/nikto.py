import subprocess

def run_nikto(target):
    process = subprocess.run(
        ["nikto", "-h", target],
        capture_output=True,
        text=True
    )

    results = []
    for line in process.stdout.splitlines():
        if line.startswith("+"):
            results.append({
                "tool": "Nikto Scan",
                "name": line.strip(),
                "severity": "low"
            })
    return results
