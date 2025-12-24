#!/usr/bin/env python3
import subprocess
import sys
import os

def run(cmd):
    print(f"[+] {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    if os.geteuid() != 0:
        print("[-] Devi eseguire questo script come root (sudo).")
        sys.exit(1)

    run("apt install -y build-essential libssl-dev git unzip")

    if not os.path.exists("wrk"):
        run("git clone https://github.com/wg/wrk.git")

    os.chdir("wrk")
    run("make")

    run("cp wrk /usr/local/bin/")
    run("chmod +x /usr/local/bin/wrk")

    run("wrk --version")
    print("[✓] wrk installato correttamente")

if __name__ == "__main__":
    main()
