import requests
from config.app_state import app_state
import os


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api/v1")


def _headers():
    headers = {}
    if app_state.token:
        headers["Authorization"] = f"Bearer {app_state.token}"
    return headers


def request(method: str, path: str, **kwargs):
    url = f"{BASE_URL}{path}"

    resp = requests.request(
        method,
        url,
        headers=_headers(),
        **kwargs,
    )

    if resp.status_code == 401:
        from services.auth_service import refresh_token

        if refresh_token():
            resp = requests.request(
                method,
                url,
                headers=_headers(),
                **kwargs,
            )

    return resp


# === AUTH ===
def login(data: dict):
    return request("POST", "/auth/login", json=data)


def register(data: dict):
    return request("POST", "/auth/register", json=data)


def refresh(data: dict):
    return request("POST", "/auth/token/refresh", json=data)


def logout():
    return request("POST", "/auth/logout")


# === NODES ===
def get_servers():
    return request("GET", "/nodes/available")


# === DEVICES ===
def create_device(data: dict):
    return request("POST", "/devices/create", json=data)


def get_device_config(device_id: str):
    return request("GET", f"/devices/{device_id}/config")


def revoke_device(device_id: str):
    return request("POST", f"/devices/{device_id}/revoke")
