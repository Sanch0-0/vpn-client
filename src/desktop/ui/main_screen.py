import asyncio
import flet as ft
from config.app_state import app_state, W, H


# ─── Colors ───
BG = "#F5F5F5"
ORANGE = "#F06A30"
ORANGE_LIGHT = "#FEF1EB"
WHITE = "#FFFFFF"
BLACK = "#000000"
GRAY = "#AAAAAA"
DIVIDER = "#EEEEEE"
ORANGE_RING = "#F38859"


# ─── Small UI helpers ----
def _icon_badge(icon_color: str, bg_color: str, icon: ft.Control) -> ft.Container:
    """Small 24x24 badge with icon inside."""
    return ft.Container(
        width=24,
        height=24,
        bgcolor=bg_color,
        border_radius=4,
        alignment=ft.Alignment.CENTER,
        content=icon,
    )


def _loading_overlay() -> ft.Container:
    """Full-screen loading overlay with spinner."""
    return ft.Container(
        left=0,
        top=0,
        width=W,
        height=H,
        bgcolor="#CC000000",
        border_radius=24,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                ft.ProgressRing(
                    width=48,
                    height=48,
                    stroke_width=4,
                    color=ORANGE,
                ),
                ft.Text(
                    "Loading...",
                    size=14,
                    color=WHITE,
                    weight=ft.FontWeight.W_500,
                ),
            ],
        ),
    )


def _info_col(
    badge_icon_name: str,
    label: str,
    value: str,
    active: bool,
) -> ft.Container:
    """One column inside info card (Upload / Download)."""
    indicator_color = BLACK if active else GRAY

    return ft.Container(
        width=163,
        height=104,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            controls=[
                _icon_badge(
                    ORANGE,
                    ORANGE_LIGHT,
                    ft.Icon(badge_icon_name, color=ORANGE, size=14),
                ),
                ft.Text(
                    value=label,
                    size=11,
                    color=GRAY,
                ),
                ft.Text(
                    value=value,
                    size=13,
                    color=indicator_color,
                    weight=ft.FontWeight.W_600,
                ),
            ],
        ),
    )


def _info_card() -> ft.Container:
    """White card with upload/download stats."""
    connected = app_state.connected

    return ft.Container(
        left=24,
        top=110,
        width=327,
        height=104,
        bgcolor=WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#18000000",
            offset=ft.Offset(0, 4),
        ),
        content=ft.Row(
            spacing=0,
            controls=[
                _info_col(
                    ft.Icons.ARROW_UPWARD,
                    "Upload",
                    "1.2 MB/s" if connected else "0 MB/s",
                    connected,
                ),
                ft.Container(width=1, height=104, bgcolor=DIVIDER),
                _info_col(
                    ft.Icons.ARROW_DOWNWARD,
                    "Download",
                    "3.8 MB/s" if connected else "0 MB/s",
                    connected,
                ),
            ],
        ),
    )


def _connect_button(page: ft.Page, navigate) -> ft.Container:
    """Main connect/disconnect button with real VPN logic."""

    connected = app_state.connected
    disabled = not app_state.current_server

    outer_bg = ORANGE if connected else WHITE
    inner_stroke = ORANGE_RING if connected else DIVIDER

    icon = ft.Icon(
        ft.Icons.POWER_SETTINGS_NEW,
        color=WHITE if connected else ORANGE,
        size=32,
    )

    return ft.Container(
        left=124,
        top=400,
        width=128,
        height=128,
        bgcolor=outer_bg,
        border_radius=64,
        shadow=ft.BoxShadow(
            blur_radius=12,
            color="#28000000",
            offset=ft.Offset(0, 4),
        ),
        on_click=None if disabled else on_click,
        ink=not disabled,
        opacity=0.5 if disabled else 1,
        alignment=ft.Alignment.CENTER,
        content=ft.Container(
            width=103,
            height=103,
            border_radius=51.5,
            border=ft.Border.all(1, inner_stroke),
            alignment=ft.Alignment.CENTER,
            content=icon,
        ),
    )


def _top_bar(on_menu_click, on_connections_click) -> list[ft.Control]:
    """Top navigation bar."""
    menu_btn = ft.Container(
        left=24,
        top=32,
        width=48,
        height=48,
        bgcolor=WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#18000000",
            offset=ft.Offset(0, 4),
        ),
        alignment=ft.Alignment.CENTER,
        on_click=on_menu_click,
        ink=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
            controls=[
                ft.Container(width=18, height=2, bgcolor=GRAY, border_radius=1),
                ft.Container(width=18, height=2, bgcolor=GRAY, border_radius=1),
                ft.Container(width=12, height=2, bgcolor=GRAY, border_radius=1),
            ],
        ),
    )

    connections_btn = ft.Container(
        left=177,
        top=32,
        width=174,
        height=48,
        bgcolor=ORANGE,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#28F06A30",
            offset=ft.Offset(0, 4),
        ),
        alignment=ft.Alignment.CENTER,
        on_click=on_connections_click,
        ink=True,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.WIFI, color=WHITE, size=18),
                ft.Text(
                    "Connections",
                    color=WHITE,
                    size=14,
                    weight=ft.FontWeight.W_600,
                ),
            ],
        ),
    )

    return [menu_btn, connections_btn]


def _bottom_bar(on_click) -> ft.Container:
    server = app_state.current_server

    if server:
        flag = server["flag"]
        name = server["name"]
    else:
        flag = "🌐"
        name = "Choose server"

    return ft.Container(
        left=24,
        top=640,
        width=327,
        height=48,
        bgcolor=WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#18000000",
            offset=ft.Offset(0, 4),
        ),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.symmetric(horizontal=16),
        ink=True,
        on_click=on_click,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Text(flag, size=20),
                ft.Text(name, size=14, color=BLACK),
                ft.Container(expand=True),
                ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=GRAY),
            ],
        ),
    )


def _title_texts() -> list[ft.Control]:
    """Center title and subtitle."""
    connected = app_state.connected

    title = "Connected" if connected else "Not Connected"
    subtitle = "Your connection is secure" if connected else "Tap the button to connect"

    return [
        ft.Container(
            left=0,
            top=320,
            width=375,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                title,
                size=22,
                color=BLACK,
                weight=ft.FontWeight.W_700,
            ),
        ),
        ft.Container(
            left=0,
            top=350,
            width=375,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                subtitle,
                size=13,
                color=GRAY,
            ),
        ),
    ]


# ─── Main screen ───
def build_main_screen(page: ft.Page, navigate) -> ft.Container:

    def on_menu_click(e):
        navigate(e.page, "menu")

    def on_connections_click(e):
        navigate(e.page, "servers")

    def go_to_servers(e):
        navigate(e.page, "servers")

    # Overlay всегда в дереве, скрыт по умолчанию
    overlay = _loading_overlay()
    overlay.visible = False

    def on_connect_click(e):
        from services.connections import connect, disconnect

        async def flow():
            print("=== FLOW START ===")
            print(f"current_server: {app_state.current_server}")

            overlay.visible = True
            page.update()

            if not app_state.connected:
                print("calling connect()...")
                ok, err = await asyncio.to_thread(connect)
            else:
                print("calling disconnect()...")
                ok, err = await asyncio.to_thread(disconnect)

            print(f"result: ok={ok}, err={err}")

            overlay.visible = False

            if ok:
                navigate(page, "main")
            else:
                page.update()
                from ui.auth_screen import show_error

                show_error(page, str(err))

            print("=== FLOW END ===")

        page.run_task(flow)

    connected = app_state.connected
    disabled = not app_state.current_server

    connect_btn = ft.Container(
        left=124,
        top=400,
        width=128,
        height=128,
        bgcolor=ORANGE if connected else WHITE,
        border_radius=64,
        shadow=ft.BoxShadow(
            blur_radius=12,
            color="#28000000",
            offset=ft.Offset(0, 4),
        ),
        on_click=None if disabled else on_connect_click,
        ink=not disabled,
        opacity=0.5 if disabled else 1.0,
        alignment=ft.Alignment.CENTER,
        content=ft.Container(
            width=103,
            height=103,
            border_radius=51.5,
            border=ft.Border.all(1, ORANGE_RING if connected else DIVIDER),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                ft.Icons.POWER_SETTINGS_NEW,
                color=WHITE if connected else ORANGE,
                size=32,
            ),
        ),
    )

    controls: list[ft.Control] = [
        ft.Container(expand=True, bgcolor=BG, border_radius=24),
        *_top_bar(on_menu_click, on_connections_click),
        _info_card(),
        *_title_texts(),
        connect_btn,
        _bottom_bar(go_to_servers),
        overlay,
    ]

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.TOP_CENTER,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=W,
                    height=H,
                    bgcolor=BG,
                    border_radius=24,
                    content=ft.Stack(
                        width=W,
                        height=H,
                        controls=controls,
                    ),
                )
            ],
        ),
    )
