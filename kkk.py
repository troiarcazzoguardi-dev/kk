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
            if line.strip() in f.read():
                return
    with open(path, "a") as f:
        f.write(line + "\n")

def main():
    if os.geteuid() != 0:
        print("[-] Devi eseguire questo script come root (sudo).")
        sys.exit(1)

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

    print("\n[✓] CONFIGURAZIONE COMPLETATA")
    print("[!] RIAVVIA IL SISTEMA per rendere tutto definitivo:")
    print("    reboot")

if __name__ == "__main__":
    main()
