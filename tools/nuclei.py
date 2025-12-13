import subprocess, json

def run_nuclei(target):
    process = subprocess.run(
        ["nuclei", "-u", target, "-json"],
        capture_output=True,
        text=True
    )

    results = []
    for line in process.stdout.splitlines():
        try:
            data = json.loads(line)
            results.append({
                "tool": "Nuclei Scan",
                "name": data.get("info", {}).get("name", "Unknown Issue"),
                "severity": data.get("info", {}).get("severity", "low")
            })
        except:
            pass

    return results
