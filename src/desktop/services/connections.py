import os
from time import time
from desktop.services.wireguard import is_connected as _wg_is_connected
from desktop.config.app_state import app_state
from desktop.config.config_builder import (
    save_device,
    load_device,
    clear_device,
    get_machine_id,
    get_wg_config_path,
)
from desktop.services.wireguard import (
    build_wg_config,
    generate_keys,
    save_wg_config,
    start_wg,
    stop_wg,
)
from desktop.services.api_client import (
    connect_device,
    disconnect_device,
    get_best_node,
    get_servers,
    create_device,
    get_device_config,
)
from src.desktop.ui.server_location_screen import REGION_MAP


# --- HELPERS ---
def _region_to_flag(region: str) -> str:
    _, _, flag = REGION_MAP.get(region.lower(), ("Unknown", "Unknown", "🌐"))
    return flag


# ─── SERVERS ───
def load_servers():
    resp = get_servers()

    if resp.status_code == 200:
        app_state.servers = resp.json()
        return True

    return False


# ─── CONNECT ───
def connect():
    existing = load_device()
    wg_path = get_wg_config_path()
    private_key, public_key = generate_keys()

    # ─── Resolve server ───
    server = app_state.current_server
    node_id = None

    if server:
        # Explicit server selected by user
        node_id = server["id"]
    else:
        # Auto-select best node
        profile = app_state.profile or "balanced"
        resp = get_best_node(profile)
        if resp.status_code != 200:
            return False, "Failed to find available server"
        best = resp.json()
        node_id = best["id"]
        # Populate current_server so UI shows what was picked
        app_state.current_server = {
            "id": best["id"],
            "name": best["name"],
            "flag": _region_to_flag(best["region"]),
        }

    # Reuse existing device record if present
    if existing and os.path.exists(wg_path):
        device_id = existing["device_id"]
    else:
        # Create device record (no WireGuard yet)
        machine_id = get_machine_id()
        resp = create_device(
            {
                "name": f"desktop-{machine_id}",
                "public_key": public_key,
                "node_id": app_state.current_server["id"],
            }
        )
        if resp.status_code != 200:
            return False, resp.text
        device_id = resp.json()["id"]

    # Get config
    resp = get_device_config(device_id)
    if resp.status_code != 200:
        return False, resp.text
    cfg = resp.json()

    node_ip = cfg["endpoint"].split(":")[0]

    # Build and save wg config
    config_str = build_wg_config(
        private_key, cfg["assigned_ip"], cfg["node_public_key"], cfg["endpoint"]
    )
    config_path = save_wg_config(config_str)

    # Save device locally before any network calls
    save_device(
        {
            "device_id": device_id,
            "config_path": config_path,
            "node_ip": node_ip,
            "connected_at": time(),
            "server": app_state.current_server,
        }
    )

    # Add peer to node
    resp = connect_device(device_id, public_key)
    if resp.status_code != 200:
        return False, resp.text

    # Start tunnel
    if _wg_is_connected():
        # Already up — nothing to do
        app_state.connected = True
        return True, None

    # Start tunnel
    try:
        start_wg(config_path)
    except Exception as e:
        disconnect_device(device_id)
        return False, f"Tunnel failed: {str(e)}"

    app_state.connected = True
    app_state.connected_at = time()

    return True, None


def disconnect():
    device = load_device()
    if not device:
        return False, "No active device"

    node_ip = device.get("node_ip")

    try:
        stop_wg(device["config_path"], node_ip=node_ip)
    except Exception as e:
        print(f"[disconnect] wg down: {e}")

    try:
        disconnect_device(device["device_id"])
    except Exception as e:
        print(f"[disconnect] server disconnect: {e}")

    clear_device()
    app_state.connected = False
    app_state.connected_at = None

    return True, None
