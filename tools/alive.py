import subprocess

def run_alive(subdomains):
    alive_urls = []

    try:
        proc = subprocess.run(
            ["httpx", "-silent"],
            input="\n".join(subdomains),
            text=True,
            capture_output=True,
            timeout=120
        )

        for line in proc.stdout.splitlines():
            alive_urls.append(line.strip())

    except Exception as e:
        pass

    return alive_urls
