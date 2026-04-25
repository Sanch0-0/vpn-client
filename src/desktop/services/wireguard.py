import subprocess
from config.config_builder import get_wg_config_path


# ─── KEY GENERATION ───
def generate_keys():
    private_key = subprocess.run(["wg", "genkey"], capture_output=True).stdout.strip()

    public_key = subprocess.run(
        ["wg", "pubkey"],
        input=private_key,
        capture_output=True,
    ).stdout.strip()

    return private_key.decode(), public_key.decode()


# ─── BUILD CONFIG ───
def build_wg_config(private_key, assigned_ip, node_public_key, endpoint):
    return f"""
[Interface]
PrivateKey = {private_key}
Address = {assigned_ip}/32
DNS = 1.1.1.1

[Peer]
PublicKey = {node_public_key}
Endpoint = {endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
""".strip()


def save_wg_config(config_str: str):
    path = get_wg_config_path()
    with open(path, "w") as f:
        f.write(config_str)
    return path


# ─── WG CONTROL ───
def start_wg(config_path: str):
    subprocess.run(["wg-quick", "up", config_path], check=True)


def stop_wg(config_path: str):
    subprocess.run(["wg-quick", "down", config_path], check=True)
