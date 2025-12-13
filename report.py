from datetime import datetime

def generate_html_report(target, results, summary, output="report.html"):
    rows = ""
    for r in results:
        rows += f"""
        <tr class="{r['severity']}">
            <td>{r['severity'].upper()}</td>
            <td>{r['name']}</td>
            <td>{r['tool']}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>ONYX Report</title>
<style>
body {{ font-family: Arial; background:#0b0f14; color:#e6f1ff; }}
h1 {{ color:#00ffff; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ padding:10px; border:1px solid #222; }}
.critical {{ background:#5a0000; }}
.high {{ background:#7a2e00; }}
.medium {{ background:#7a6a00; }}
.low {{ background:#0f3d2e; }}
</style>
</head>
<body>
<h1>ONYX Vulnerability Report</h1>
<p><b>Target:</b> {target}</p>
<p><b>Date:</b> {datetime.now()}</p>

<h2>Risk Summary</h2>
<ul>
<li>CRITICAL: {summary['critical']}</li>
<li>HIGH: {summary['high']}</li>
<li>MEDIUM: {summary['medium']}</li>
<li>LOW: {summary['low']}</li>
</ul>

<h2>Findings</h2>
<table>
<tr><th>Severity</th><th>Issue</th><th>Scan</th></tr>
{rows}
</table>
</body>
</html>
"""
    with open(output, "w") as f:
        f.write(html)
