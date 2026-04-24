import os
import json

BASE_DIR = os.path.expanduser("~/.vpn-client")
SESSION_FILE = os.path.join(BASE_DIR, "session.json")
DEVICE_FILE = os.path.join(BASE_DIR, "device.json")
WG_CONFIG_FILE = os.path.join(BASE_DIR, "wg.conf")


def ensure_dir():
    os.makedirs(BASE_DIR, exist_ok=True)


def save_session(data: dict):
    ensure_dir()
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)


def load_session():
    if not os.path.exists(SESSION_FILE):
        return None

    with open(SESSION_FILE, "r") as f:
        return json.load(f)


def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)


# WireGuard
def save_device(data: dict):
    ensure_dir()
    with open(DEVICE_FILE, "w") as f:
        json.dump(data, f)


def load_device():
    if not os.path.exists(DEVICE_FILE):
        return None

    with open(DEVICE_FILE, "r") as f:
        return json.load(f)


def clear_device():
    if os.path.exists(DEVICE_FILE):
        os.remove(DEVICE_FILE)


def get_wg_config_path():
    ensure_dir()
    return WG_CONFIG_FILE
