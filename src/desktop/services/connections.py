from config.app_state import app_state
from config.config_builder import (
    save_device,
    load_device,
    clear_device,
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
    if existing:
        try:
            start_wg(existing["config_path"])
            app_state.connected = True
            return True, None
        except Exception as e:
            clear_device()
            print("Old device failed, recreating:", e)

    try:
        # 1. keys
        private_key, public_key = generate_keys()

        # 2. create device
        resp = create_device(
            {
                "name": "desktop",
                "public_key": public_key,
                "node_id": app_state.current_server["id"],
            }
        )

        if resp.status_code != 200:
            return False, resp.text

        device = resp.json()
        device_id = device["id"]

        # 3. get config
        resp = get_device_config(device_id)
        if resp.status_code != 200:
            return False, resp.text

        cfg = resp.json()

        # 4. build wg config
        config_str = build_wg_config(
            private_key,
            cfg["assigned_ip"],
            cfg["node_public_key"],
            cfg["endpoint"],
        )

        config_path = save_wg_config(config_str)

        # 5. start wg
        start_wg(config_path)

        # 6. save state
        save_device(
            {
                "device_id": device_id,
                "private_key": private_key,
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
