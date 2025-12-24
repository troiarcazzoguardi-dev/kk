#!/usr/bin/env python3
import subprocess
import sys
import os

def run(cmd):
    print(f"[+] {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def append_if_missing(path, line):
    if os.path.exists(path):
        with open(path, "r") as f:
            if line in f.read():
                return
    with open(path, "a") as f:
        f.write(line + "\n")

def main():
    if os.geteuid() != 0:
        print("[-] Devi eseguire questo script come root (sudo).")
        sys.exit(1)

    print("[*] Installo dipendenze...")
    run("apt update")
    run("apt install -y build-essential libssl-dev git unzip")

    print("[*] Installo wrk...")
    if not os.path.exists("/opt/wrk"):
        run("git clone https://github.com/wg/wrk.git /opt/wrk")

    os.chdir("/opt/wrk")
    run("make")
    run("cp wrk /usr/local/bin/")
    run("chmod +x /usr/local/bin/wrk")

    run("wrk --version")
    print("[✓] wrk installato correttamente")

    print("[*] Imposto ulimit globale (limits.conf)...")
    limits_conf = "/etc/security/limits.conf"
    append_if_missing(limits_conf, "* soft nofile 20000")
    append_if_missing(limits_conf, "* hard nofile 20000")

    print("[*] Imposto systemd globale...")
    for conf in ["/etc/systemd/system.conf", "/etc/systemd/user.conf"]:
        append_if_missing(conf, "DefaultLimitNOFILE=20000")

    print("[*] Imposto kernel fs.file-max...")
    sysctl_conf = "/etc/sysctl.conf"
    append_if_missing(sysctl_conf, "fs.file-max = 1000000")

    print("[*] Applico sysctl...")
    run("sysctl -p")

    print("[*] Ricarico systemd...")
    run("systemctl daemon-reexec")

    print("\n[✓] SETUP COMPLETATO")
    print("[!] RIAVVIA IL SISTEMA per applicare TUTTO definitivamente")
    print("    reboot")

if __name__ == "__main__":
    main()
