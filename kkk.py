#!/usr/bin/env python3
import subprocess
import sys
import os

def run(cmd):
    print(f"[+] {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def ensure_line(path, line):
    if os.path.exists(path):
        with open(path, "r") as f:
            if line in f.read():
                return
    with open(path, "a") as f:
        f.write(line + "\n")

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content.strip() + "\n")

def main():
    if os.geteuid() != 0:
        print("[-] Devi eseguire questo script come root (sudo).")
        sys.exit(1)

    print("[*] 1) Imposto limiti globali PAM (soft + hard)...")
    limits_file = "/etc/security/limits.d/99-nofile.conf"
    write_file(
        limits_file,
        """
* soft nofile 20000
* hard nofile 1048576
"""
    )

    print("[*] 2) Abilito pam_limits per sessioni interattive...")
    ensure_line("/etc/pam.d/common-session", "session required pam_limits.so")

    print("[*] 3) Abilito pam_limits per sessioni NON interattive (SSH)...")
    ensure_line(
        "/etc/pam.d/common-session-noninteractive",
        "session required pam_limits.so"
    )

    print("[*] 4) Forzo UsePAM yes in SSH...")
    sshd_conf = "/etc/ssh/sshd_config"
    if os.path.exists(sshd_conf):
        with open(sshd_conf, "r") as f:
            content = f.read()
        if "UsePAM yes" not in content:
            content = content.replace("UsePAM no", "UsePAM yes")
            if "UsePAM" not in content:
                content += "\nUsePAM yes\n"
            with open(sshd_conf, "w") as f:
                f.write(content)

    print("[*] Riavvio SSH...")
    run("systemctl restart ssh || systemctl restart sshd")

    print("[*] 5) Imposto systemd globale (hard limit)...")
    for conf in ["/etc/systemd/system.conf", "/etc/systemd/user.conf"]:
        ensure_line(conf, "DefaultLimitNOFILE=1048576")

    print("[*] Ricarico systemd...")
    run("systemctl daemon-reexec")

    print("[*] 6) Imposto kernel fs.file-max...")
    ensure_line("/etc/sysctl.conf", "fs.file-max = 1000000")
    run("sysctl -p")

    print("\n[✓] CONFIGURAZIONE COMPLETATA CON SUCCESSO")
    print("------------------------------------------------")
    print("⚠️ IMPORTANTE:")
    print("- Chiudi COMPLETAMENTE la sessione SSH")
    print("- Rientra con una NUOVA connessione SSH")
    print("- Ora `ulimit -n` sarà 20000")
    print("- Dopo reboot resterà automatico")
    print("------------------------------------------------")

if __name__ == "__main__":
    main()
