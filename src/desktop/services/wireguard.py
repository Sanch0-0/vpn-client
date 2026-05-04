import subprocess
import os
import time
from config.config_builder import get_wg_config_path


# -----------------
# Helpers
# -----------------


def generate_keys():
    private_key = subprocess.run(["wg", "genkey"], capture_output=True).stdout.strip()
    public_key = subprocess.run(
        ["wg", "pubkey"], input=private_key, capture_output=True
    ).stdout.strip()
    return private_key.decode(), public_key.decode()


def build_wg_config(private_key, assigned_ip, node_public_key, endpoint):
    return f"""[Interface]
PrivateKey = {private_key}
Address = {assigned_ip}/32

[Peer]
PublicKey = {node_public_key}
Endpoint = {endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
""".strip()


def save_wg_config(config_str: str) -> str:
    path = get_wg_config_path()
    with open(path, "w") as f:
        f.write(config_str)
    os.chmod(path, 0o600)
    return path


def _get_node_ip_from_config(config_path: str) -> str | None:
    """Parse Endpoint IP from WireGuard config file."""
    try:
        with open(config_path, "r") as f:
            for line in f:
                if line.strip().startswith("Endpoint"):
                    endpoint = line.split("=", 1)[1].strip()
                    # format: "1.2.3.4:51820" or "[2001:db8::1]:51820"
                    host = endpoint.rsplit(":", 1)[0].strip("[]")
                    return host
    except Exception:
        return None
    return None


def _get_wifi_gateway() -> str | None:
    """Extract default gateway of the wlan0 interface (or any non-tunnel)."""
    result = subprocess.run(
        ["ip", "route", "show", "default"], capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        # typical: default via 192.168.1.1 dev wlan0 proto dhcp metric 600
        if "dev wlan0" in line or "dev wlp" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "via" and i + 1 < len(parts):
                    return parts[i + 1]
    # fallback: try to get from NetworkManager
    nm_result = subprocess.run(
        ["nmcli", "-t", "-f", "GATEWAY", "dev", "show", "wlan0"],
        capture_output=True,
        text=True,
    )
    return nm_result.stdout.strip() or None


def _nmcli_connection_exists(name: str) -> bool:
    """Check if a NetworkManager connection with given name exists."""
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME", "connection", "show"],
        capture_output=True,
        text=True,
    )
    return name in result.stdout.splitlines()


def _get_wg_interface_name(connection_name: str) -> str:
    """
    Resolve the actual WireGuard network interface name assigned by NM.
    Falls back to 'wg' if detection fails.
    """
    result = subprocess.run(
        [
            "nmcli",
            "-t",
            "-f",
            "GENERAL.IP-IFACE",
            "connection",
            "show",
            connection_name,
        ],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if "IP-IFACE" in line:
            iface = line.split(":")[-1].strip()
            if iface:
                return iface
    return "wg"


def _add_routes(config_path: str, connection_name: str) -> None:
    """Add routing overrides: node via WiFi, default via WireGuard."""
    node_ip = _get_node_ip_from_config(config_path)
    wifi_gw = _get_wifi_gateway()
    iface = _get_wg_interface_name(connection_name)

    if not iface:
        print("[wg] could not determine WireGuard interface, routes not added")
        return

    # 1. Route to the VPN node itself via WiFi (prevents routing loop)
    if node_ip and wifi_gw:
        subprocess.run(
            ["sudo", "ip", "route", "replace", node_ip, "via", wifi_gw, "dev", "wlan0"],
            capture_output=True,
            text=True,
        )
        print(f"[wg] node route: {node_ip} via {wifi_gw}")

    # 2. Default route via WireGuard interface with higher priority (lower metric)
    subprocess.run(
        ["sudo", "ip", "route", "replace", "default", "dev", iface, "metric", "50"],
        capture_output=True,
        text=True,
    )
    print(f"[wg] default route added via {iface} (metric 50)")


def start_wg(config_path: str, connection_name: str = "vpn-desktop") -> None:
    """
    Import a WireGuard config into NetworkManager and bring the tunnel up.
    Adds a default route through the tunnel with higher priority than WiFi.
    """
    # 1. Reuse existing connection if already imported — just bring it up
    if _nmcli_connection_exists(connection_name):
        result = subprocess.run(
            ["nmcli", "connection", "up", connection_name],
            capture_output=True,
            text=True,
        )
        print(f"[wg] reuse up: {result.stdout.strip()}")
        if result.returncode == 0:
            _add_routes(config_path, connection_name)
            return
        # If reuse failed — fall through to reimport
        subprocess.run(
            ["nmcli", "connection", "delete", connection_name], capture_output=True
        )

    # 2. Import config — NM names the connection after the filename without extension
    result = subprocess.run(
        ["nmcli", "connection", "import", "type", "wireguard", "file", config_path],
        capture_output=True,
        text=True,
    )
    print(f"[wg] import: {result.stdout.strip()} | {result.stderr.strip()}")
    if result.returncode != 0:
        raise RuntimeError(f"WireGuard config import failed: {result.stderr}")

    # 3. Determine the auto-generated connection name (filename w/o extension)
    actual_name = os.path.splitext(os.path.basename(config_path))[0]

    # 4. Rename and configure the connection before bringing it up
    subprocess.run(
        [
            "nmcli",
            "connection",
            "modify",
            actual_name,
            "connection.id",
            connection_name,
            "ipv4.ignore-auto-dns",
            "yes",
            "ipv4.never-default",
            "no",
            "ipv4.route-metric",
            "50",
            "ipv4.route-table",
            "254",
            "ipv4.ignore-auto-routes",
            "yes",
        ],
        capture_output=True,
        text=True,
    )

    # 5. Explicitly set private key from config file (avoids NM key file issues)
    private_key = None
    with open(config_path, "r") as f:
        for line in f:
            if line.strip().startswith("PrivateKey"):
                private_key = line.split("=", 1)[1].strip()
                break
    if private_key:
        subprocess.run(
            [
                "nmcli",
                "connection",
                "modify",
                connection_name,
                "wireguard.private-key",
                private_key,
            ],
            capture_output=True,
            text=True,
        )
        print("[wg] private key explicitly set")

    # 6. Bring the connection up
    result = subprocess.run(
        ["nmcli", "connection", "up", connection_name],
        capture_output=True,
        text=True,
    )
    print(f"[wg] up: {result.stdout.strip()} | {result.stderr.strip()}")
    if result.returncode != 0:
        raise RuntimeError(f"nmcli up failed: {result.stderr}")

    time.sleep(2)  # Allow interface to settle

    # 7. Add custom routes (node via Wi‑Fi, default via wg)
    _add_routes(config_path, connection_name)


def stop_wg(
    config_path: str,
    connection_name: str = "vpn-desktop",
    node_ip: str | None = None,
) -> None:
    """
    Bring down the WireGuard tunnel and remove it from NetworkManager.
    NetworkManager automatically restores the default WiFi route on disconnect.

    Args:
        config_path: Path to the .conf file (unused, kept for interface consistency).
        connection_name: NM connection name to remove (default: 'vpn-desktop').
    """
    # Remove the manually added default route before disconnecting
    # to avoid a brief routing blackhole
    iface = _get_wg_interface_name(connection_name)
    subprocess.run(
        ["sudo", "ip", "route", "del", "default", "dev", iface, "metric", "50"],
        capture_output=True,
    )

    if node_ip:
        subprocess.run(
            ["sudo", "ip", "route", "del", node_ip],
            capture_output=True,
        )

    # Bring down and delete all possible wg connection names
    for name in [connection_name, "wg", "wg.conf"]:
        if _nmcli_connection_exists(name):
            subprocess.run(
                ["nmcli", "connection", "down", name],
                capture_output=True,
            )
            subprocess.run(
                ["nmcli", "connection", "delete", name],
                capture_output=True,
            )

    print("[wg] tunnel stopped and connection removed")


def is_connected(connection_name: str = "vpn-desktop") -> bool:
    """Check if VPN connection is currently active."""
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,STATE", "connection", "show", "--active"],
        capture_output=True,
        text=True,
    )
    return connection_name in result.stdout
