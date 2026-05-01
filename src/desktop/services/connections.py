import os
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
    get_servers,
    create_device,
    get_device_config,
    revoke_device,
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

    if existing and os.path.exists(wg_path):
        try:
            start_wg(wg_path)
            app_state.connected = True
            return True, None
        except Exception as e:
            print("Reuse failed, recreating:", e)
            clear_device()

    try:
        private_key, public_key = generate_keys()

        machine_id = get_machine_id()
        device_name = f"desktop-{machine_id}"

        resp = create_device(
            {
                "name": device_name,
                "public_key": public_key,
                "node_id": app_state.current_server["id"],
            }
        )

        if resp.status_code != 200:
            return False, resp.text

        device = resp.json()
        device_id = device["id"]

        resp = get_device_config(device_id)
        if resp.status_code != 200:
            return False, resp.text

        cfg = resp.json()

        config_str = build_wg_config(
            private_key,
            cfg["assigned_ip"],
            cfg["node_public_key"],
            cfg["endpoint"],
        )

        config_path = save_wg_config(config_str)
        start_wg(config_path)

        save_device(
            {
                "device_id": device_id,
                "machine_id": machine_id,
                "config_path": config_path,
            }
        )

        app_state.connected = True
        return True, None

    except Exception as e:
        return False, str(e)


# ─── DISCONNECT ───
def disconnect():
    device = load_device()
    if not device:
        return False, "No active device"

    try:
        stop_wg(device["config_path"])
    except Exception as e:
        print("wg down failed:", e)

    try:
        revoke_device(device["device_id"])
    except Exception as e:
        print("revoke failed:", e)

    clear_device()

    app_state.connected = False
    app_state.current_server = None

    return True, None
