from desktop.services.api_client import (
    login as api_login,
    logout as api_logout,
    register as api_register,
)
from desktop.services.api_client import refresh as api_refresh
from desktop.config.config_builder import save_session
from desktop.config.app_state import app_state
from desktop.config.config_builder import load_session, clear_session


def login_user(username: str, password: str):
    resp = api_login(
        {
            "username": username,
            "password": password,
        }
    )

    if resp.status_code == 200:
        data = resp.json()

        app_state.token = data.get("access_token")
        app_state.refresh_token = data.get("refresh_token")
        app_state.is_authenticated = True

        save_session(
            {
                "token": app_state.token,
                "refresh_token": app_state.refresh_token,
            }
        )

        return True, None

    return False, resp


def try_auto_login():
    session = load_session()

    if not session:
        return False

    app_state.token = session.get("token")
    app_state.refresh_token = session.get("refresh_token")
    app_state.is_authenticated = True

    return True


def register_user(username: str, email: str, password: str, confirm: str):
    resp = api_register(
        {
            "username": username,
            "email": email,
            "password": password,
            "confirm": confirm,
        }
    )

    if resp.status_code == 200:
        return True, None

    return False, resp


def logout_user():
    try:
        if app_state.token:
            api_logout()
    except Exception:
        pass

    app_state.token = None
    app_state.refresh_token = None
    app_state.is_authenticated = False
    app_state.connected = False
    app_state.current_server = None

    clear_session()


def refresh_token():
    if not app_state.refresh_token:
        return False

    resp = api_refresh({"refresh_token": app_state.refresh_token})

    if resp.status_code == 200:
        data = resp.json()

        app_state.token = data.get("access_token")
        app_state.refresh_token = data.get("refresh_token")

        save_session(
            {
                "token": app_state.token,
                "refresh_token": app_state.refresh_token,
            }
        )

        return True

    logout_user()
    return False
