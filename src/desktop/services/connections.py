import os
from services.wireguard import is_connected as _wg_is_connected
from config.app_state import app_state
from config.config_builder import (
    save_device,
    load_device,
    clear_device,
    get_machine_id,
    get_wg_config_path,
)
from services.wireguard import (
    build_wg_config,
    generate_keys,
    save_wg_config,
    start_wg,
    stop_wg,
)
from services.api_client import (
    connect_device,
    disconnect_device,
    get_servers,
    create_device,
    get_device_config,
)


# ─── SERVERS ───
def load_servers():
    resp = get_servers()

    if resp.status_code == 200:
        app_state.servers = resp.json()
        return True

    return False


# ─── CONNECT ───
def connect():
    if not app_state.current_server:
        return False, "No server selected"

    existing = load_device()
    wg_path = get_wg_config_path()

    private_key, public_key = generate_keys()

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
    return True, None
