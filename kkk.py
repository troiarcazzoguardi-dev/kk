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

    print("[*] 1) Creo wrapper /usr/local/bin/set-ulimit.sh...")
    wrapper_path = "/usr/local/bin/set-ulimit.sh"
    write_file(
        wrapper_path,
        """#!/usr/bin/env bash
# Wrapper per impostare ulimit a 20000
ulimit -n 20000
exec "$@"
"""
    )
    run(f"chmod +x {wrapper_path}")

    print("[*] 2) Creo servizio systemd /etc/systemd/system/ulimit-20000.service...")
    service_path = "/etc/systemd/system/ulimit-20000.service"
    write_file(
        service_path,
        f"""
[Unit]
Description=Set ulimit to 20000 at boot
After=network.target

[Service]
Type=oneshot
ExecStart={wrapper_path} true
RemainAfterExit=yes
LimitNOFILE=20000:20000

[Install]
WantedBy=multi-user.target
"""
    )

    print("[*] 3) Abilito e avvio il servizio...")
    run("systemctl daemon-reload")
    run("systemctl enable ulimit-20000.service")
    run("systemctl start ulimit-20000.service")

    print("[*] 4) Imposto kernel fs.file-max...")
    ensure_line("/etc/sysctl.conf", "fs.file-max = 1000000")
    run("sysctl -p")

    print("\n[✓] CONFIGURAZIONE COMPLETATA")
    print("------------------------------------------------")
    print("⚠️ IMPORTANTE:")
    print("- Shell già aperte rimangono con soft limit 1024")
    print("- Ogni nuovo comando lanciato tramite il wrapper o qualsiasi nuovo processo avrà soft limit 20000")
    print("- Dopo reboot il servizio parte automaticamente e il limite è mantenuto")
    print("------------------------------------------------")

if __name__ == "__main__":
    main()
