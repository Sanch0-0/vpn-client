import subprocess
import os
import time
from config.config_builder import get_wg_config_path


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


def start_wg(config_path: str, connection_name: str = "vpn-desktop") -> None:
    """
    Import a WireGuard config into NetworkManager and bring the tunnel up.
    Adds a default route through the tunnel with higher priority than WiFi.

    No sudo required — nmcli communicates with NetworkManager via D-Bus.
    NetworkManager runs as root and handles interface creation internally.

    Args:
        config_path: Path to the .conf WireGuard config file.
        connection_name: Desired NM connection name (default: 'vpn-desktop').

    Raises:
        RuntimeError: If import or activation fails.
    """
    # Remove any stale connections that might conflict
    for stale in [connection_name, "wg", "wg.conf"]:
        if _nmcli_connection_exists(stale):
            subprocess.run(
                ["nmcli", "connection", "delete", stale],
                capture_output=True,
            )

    # Import config — NM names the connection after the filename without extension
    result = subprocess.run(
        ["nmcli", "connection", "import", "type", "wireguard", "file", config_path],
        capture_output=True,
        text=True,
    )
    print(f"[wg] import: {result.stdout.strip()} | {result.stderr.strip()}")
    if result.returncode != 0:
        raise RuntimeError(f"WireGuard config import failed: {result.stderr}")

    # NM names the connection after the config filename (without extension)
    actual_name = os.path.splitext(os.path.basename(config_path))[0]

    # Rename and configure the connection before bringing it up
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

    # Read private key from config file to ensure NM uses the correct one
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

    # Bring the connection up
    result = subprocess.run(
        ["nmcli", "connection", "up", connection_name],
        capture_output=True,
        text=True,
    )
    print(f"[wg] up: {result.stdout.strip()} | {result.stderr.strip()}")
    if result.returncode != 0:
        raise RuntimeError(f"nmcli up failed: {result.stderr}")

    time.sleep(2)

    node_ip = None
    with open(config_path, "r") as f:
        for line in f:
            if line.strip().startswith("Endpoint"):
                node_ip = line.split("=", 1)[1].strip().split(":")[0]
                break

    print(f"[wg] node IP: {node_ip}")

    gw_result = subprocess.run(
        ["ip", "route", "show", "default", "dev", "wlan0"],
        capture_output=True,
        text=True,
    )
    wifi_gw = None
    for part in gw_result.stdout.split():
        if part not in (
            "default",
            "via",
            "dev",
            "wlan0",
            "proto",
            "dhcp",
            "src",
            "metric",
        ):
            try:
                import ipaddress

                ipaddress.ip_address(part)
                wifi_gw = part
                break
            except ValueError:
                continue

    print(f"[wg] wifi gateway: {wifi_gw}")

    # Route to node itself goes via wifi — prevents routing loop
    if node_ip and wifi_gw:
        subprocess.run(
            ["sudo", "ip", "route", "replace", node_ip, "via", wifi_gw, "dev", "wlan0"],
            capture_output=True,
            text=True,
        )
        print(f"[wg] node route: {node_ip} via {wifi_gw}")

    # Force default route through tunnel in main table
    iface = _get_wg_interface_name(connection_name)
    print(f"[wg] interface: {iface}")

    route_result = subprocess.run(
        ["sudo", "ip", "route", "replace", "default", "dev", iface, "metric", "50"],
        capture_output=True,
        text=True,
    )
    if route_result.returncode == 0:
        print(f"[wg] default route added via {iface} (metric 50)")
    else:
        print(f"[wg] route warning: {route_result.stderr.strip()}")


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
