#!/usr/bin/env python3
import subprocess
import sys
import os

def run(cmd):
    print(f"[+] {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content + "\n")

def ensure_line(path, line):
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

    print("[*] Imposto limiti PAM (soft + hard) globali...")
    limits_d = "/etc/security/limits.d/99-nofile.conf"
    write_file(limits_d, """* soft nofile 20000
* hard nofile 1048576
""")

    print("[*] Verifico pam_limits...")
    pam_file = "/etc/pam.d/common-session"
    ensure_line(pam_file, "session required pam_limits.so")

    print("[*] Imposto systemd globale (hard limit)...")
    for conf in ["/etc/systemd/system.conf", "/etc/systemd/user.conf"]:
        ensure_line(conf, "DefaultLimitNOFILE=1048576")

    print("[*] Imposto kernel fs.file-max...")
    sysctl_conf = "/etc/sysctl.conf"
    ensure_line(sysctl_conf, "fs.file-max = 1000000")
    run("sysctl -p")

    print("[*] Ricarico systemd...")
    run("systemctl daemon-reexec")

    print("\n[✓] CONFIGURAZIONE COMPLETATA")
    print("⚠️ NOTA IMPORTANTE:")
    print("- le shell GIA' aperte restano a 1024")
    print("- APRI UNA NUOVA SESSIONE SSH per vedere ulimit=20000")
    print("- dopo reboot sarà automatico")

if __name__ == "__main__":
    main()
