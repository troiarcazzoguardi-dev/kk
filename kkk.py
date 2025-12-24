#!/usr/bin/env python3
import os
import sys
import subprocess

def run(cmd):
    print(f"[+] {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content.strip() + "\n")

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

    print("[*] 1) Imposto limiti globali PAM (soft + hard)...")
    limits_file = "/etc/security/limits.d/99-nofile.conf"
    write_file(
        limits_file,
        """
* soft nofile 20000
* hard nofile 1048576
"""
    )

    print("[*] 2) Abilito pam_limits per sessioni interattive e non-interattive...")
    ensure_line("/etc/pam.d/common-session", "session required pam_limits.so")
    ensure_line("/etc/pam.d/common-session-noninteractive", "session required pam_limits.so")

    print("[*] 3) Configuro systemd globale...")
    for conf in ["/etc/systemd/system.conf", "/etc/systemd/user.conf"]:
        ensure_line(conf, "DefaultLimitNOFILE=1048576")

    print("[*] Ricarico systemd...")
    run("systemctl daemon-reexec")

    print("[*] 4) Creo wrapper /usr/local/bin/set-ulimit.sh...")
    wrapper_path = "/usr/local/bin/set-ulimit.sh"
    write_file(
        wrapper_path,
        """#!/usr/bin/env bash
# Wrapper per eseguire comandi con ulimit elevato
ulimit -n 20000
exec "$@"
"""
    )
    run(f"chmod +x {wrapper_path}")

    print("[*] 5) Creo servizio systemd ulimit-20000...")
    service_path = "/etc/systemd/system/ulimit-20000.service"
    write_file(
        service_path,
        f"""
[Unit]
Description=Service to maintain ulimit 20000
After=network.target

[Service]
Type=simple
ExecStart={wrapper_path} sleep infinity
LimitNOFILE=20000:20000
Restart=always

[Install]
WantedBy=multi-user.target
"""
    )

    print("[*] 6) Abilito e avvio il servizio...")
    run("systemctl daemon-reload")
    run("systemctl enable ulimit-20000.service")
    run("systemctl start ulimit-20000.service")

    print("[*] 7) Imposto kernel fs.file-max...")
    ensure_line("/etc/sysctl.conf", "fs.file-max = 1000000")
    run("sysctl -p")

    print("\n[✓] TUTTO CONFIGURATO CORRETTAMENTE")
    print("------------------------------------------------")
    print("⚠️ IMPORTANTE:")
    print("- Shell già aperte rimangono con soft limit 1024")
    print("- Ogni nuovo comando lanciato tramite il wrapper o il servizio avrà ulimit=20000")
    print("- Dopo reboot il servizio parte automaticamente")
    print("------------------------------------------------")

if __name__ == "__main__":
    main()
