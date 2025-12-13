import subprocess

def run_sqlmap(target):
    cmd = [
        "sqlmap",
        "-u", target,
        "--batch",
        "--level=5",
        "--risk=3",
        "--dbs",
        "--random-agent"
    ]

    process = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    output = (process.stdout + process.stderr).lower()
    results = []

    # === CRITICAL: Confirmed SQL Injection ===
    critical_keywords = [
        "is vulnerable",
        "sql injection",
        "parameter is vulnerable",
        "type:",
        "payload:",
        "back-end dbms",
        "available databases"
    ]

    if any(k in output for k in critical_keywords):
        results.append({
            "tool": "SQL Injection Scan",
            "name": "SQL Injection",
            "severity": "critical"
        })
        return results  # confirmed, stop here

    # === HIGH: Heuristic / partial detection ===
    high_keywords = [
        "heuristic",
        "might be injectable",
        "possible sql injection",
        "testing if the parameter"
    ]

    if any(k in output for k in high_keywords):
        results.append({
            "tool": "SQL Injection Scan",
            "name": "Possible SQL Injection",
            "severity": "high"
        })
        return results

    # === MEDIUM: WAF / filtered / blocked ===
    medium_keywords = [
        "blocked",
        "forbidden",
        "waf",
        "firewall",
        "access denied"
    ]

    if any(k in output for k in medium_keywords):
        results.append({
            "tool": "SQL Injection Scan",
            "name": "Potential SQL Injection (Filtered)",
            "severity": "medium"
        })

    return results
