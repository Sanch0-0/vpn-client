import flet as ft
from desktop.config.app_state import W, H
from desktop.config.config_builder import load_device
from desktop.services.wireguard import is_connected
from desktop.services.auth_service import try_auto_login
from desktop.ui.auth_screen import build_login_screen, build_register_screen
from desktop.ui.main_screen import build_main_screen
from desktop.ui.server_location_screen import build_server_location_screen
from desktop.config.app_state import app_state


def navigate(page, route: str):
    page.controls.clear()

    if route not in ["login", "register"] and not app_state.is_authenticated:
        route = "login"

    if route == "login":
        page.add(build_login_screen(page, navigate))
    elif route == "main":
        page.add(build_main_screen(page, navigate))
    elif route == "register":
        page.add(build_register_screen(page, navigate))
    elif route == "servers":
        page.add(build_server_location_screen(page, navigate))
    elif route == "menu":
        from desktop.ui.menu_screen import build_menu_screen

        page.add(build_menu_screen(page, navigate))

    page.update()


def main_app(page: ft.Page):
    page.title = "VPN Client"
    page.window.width = W
    page.window.height = H
    page.window.frameless = True
    page.scroll = ft.ScrollMode.AUTO

    device = load_device()

    if device and is_connected():
        app_state.connected = True
        app_state.current_server = device.get("server")
        app_state.connected_at = device.get("connected_at")
    else:
        app_state.connected = False
        app_state.current_server = None
        app_state.connected_at = None

    if try_auto_login():
        navigate(page, "main")
    else:
        navigate(page, "login")
