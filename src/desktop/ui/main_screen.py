import flet as ft
import asyncio
import psutil
import time
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
                ft.ProgressRing(width=48, height=48, stroke_width=4, color=ORANGE),
                ft.Text("Loading...", size=14, color=WHITE, weight=ft.FontWeight.W_500),
            ],
        ),
    )


def _get_net_stats() -> tuple[str, str]:
    """Read real upload/download speed via psutil over 1 second interval."""
    try:
        before = psutil.net_io_counters(pernic=True).get("wg")
        if not before:
            return "0 KB/s", "0 KB/s"
        time.sleep(1)
        after = psutil.net_io_counters(pernic=True).get("wg")
        if not after:
            return "0 KB/s", "0 KB/s"

        tx = (after.bytes_sent - before.bytes_sent) / 1024
        rx = (after.bytes_recv - before.bytes_recv) / 1024

        def fmt(kb: float) -> str:
            if kb >= 1024:
                return f"{kb / 1024:.1f} MB/s"
            return f"{kb:.1f} KB/s"

        return fmt(tx), fmt(rx)
    except Exception:
        return "0 KB/s", "0 KB/s"


def _fmt_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS string."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_main_screen(page: ft.Page, navigate) -> ft.Container:
    """Builds the main VPN screen with live stats and connection timer."""

    def on_menu_click(e):
        navigate(e.page, "menu")

    def on_connections_click(e):
        navigate(e.page, "servers")

    def go_to_servers(e):
        navigate(e.page, "servers")

    # ─── Live stat controls (refs for in-place update) ───
    upload_text = ft.Text(
        value="0 KB/s", size=13, color=GRAY, weight=ft.FontWeight.W_600
    )
    download_text = ft.Text(
        value="0 KB/s", size=13, color=GRAY, weight=ft.FontWeight.W_600
    )
    timer_text = ft.Text(value="00:00:00", size=13, color=GRAY)

    # ─── Overlay ───
    overlay = _loading_overlay()
    overlay.visible = False

    connected = app_state.connected

    # ─── Info card ───
    def _info_col_live(badge_icon_name, label, value_control, active):
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
                    ft.Text(value=label, size=11, color=GRAY),
                    value_control,
                ],
            ),
        )

    info_card = ft.Container(
        left=24,
        top=110,
        width=327,
        height=104,
        bgcolor=WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(blur_radius=8, color="#18000000", offset=ft.Offset(0, 4)),
        content=ft.Row(
            spacing=0,
            controls=[
                _info_col_live(ft.Icons.ARROW_UPWARD, "Upload", upload_text, connected),
                ft.Container(width=1, height=104, bgcolor=DIVIDER),
                _info_col_live(
                    ft.Icons.ARROW_DOWNWARD, "Download", download_text, connected
                ),
            ],
        ),
    )

    # ─── Timer display (below connect button) ───
    timer_container = ft.Container(
        left=0,
        top=545,
        width=W,
        alignment=ft.Alignment.CENTER,
        visible=connected,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Icon(ft.Icons.TIMER_OUTLINED, color=GRAY, size=14),
                timer_text,
            ],
        ),
    )

    # ─── Connect button ───
    connect_btn = ft.Container(
        left=124,
        top=400,
        width=128,
        height=128,
        bgcolor=ORANGE if connected else WHITE,
        border_radius=64,
        shadow=ft.BoxShadow(blur_radius=12, color="#28000000", offset=ft.Offset(0, 4)),
        ink=True,
        alignment=ft.Alignment.CENTER,
        opacity=1.0,
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

    # ─── Title texts ───
    title_text = ft.Text(
        "Connected" if connected else "Not Connected",
        size=22,
        color=BLACK,
        weight=ft.FontWeight.W_700,
    )
    subtitle_text = ft.Text(
        "Your connection is secure" if connected else "Tap the button to connect",
        size=13,
        color=GRAY,
    )

    title_container = ft.Container(
        left=0,
        top=320,
        width=W,
        alignment=ft.Alignment.CENTER,
        content=title_text,
    )
    subtitle_container = ft.Container(
        left=0,
        top=350,
        width=W,
        alignment=ft.Alignment.CENTER,
        content=subtitle_text,
    )

    # ─── Background live update task ───
    _stop_tasks = {"stop": False}

    async def _live_update_loop():
        """Update upload/download stats and timer every second."""
        while not _stop_tasks["stop"]:
            if app_state.connected:
                tx, rx = await asyncio.to_thread(_get_net_stats)

                upload_text.value = tx
                upload_text.color = BLACK
                download_text.value = rx
                download_text.color = BLACK

                if app_state.connected and app_state.connected_at:
                    elapsed = int(time.time() - app_state.connected_at)
                    timer_text.value = _fmt_duration(elapsed)

                try:
                    page.update()
                except Exception:
                    break
            else:
                await asyncio.sleep(1)

    async def _start_live():
        await asyncio.sleep(0.5)
        await _live_update_loop()

    # ─── Connect/Disconnect handler ───
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
                _stop_tasks["stop"] = True
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

    connect_btn.on_click = on_connect_click

    # Start live loop if already connected on screen build
    if connected:
        page.run_task(_start_live)

    controls: list[ft.Control] = [
        ft.Container(expand=True, bgcolor=BG, border_radius=24),
        *_top_bar(on_menu_click, on_connections_click),
        info_card,
        title_container,
        subtitle_container,
        connect_btn,
        timer_container,
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
                    content=ft.Stack(width=W, height=H, controls=controls),
                )
            ],
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
        shadow=ft.BoxShadow(blur_radius=8, color="#18000000", offset=ft.Offset(0, 4)),
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
        shadow=ft.BoxShadow(blur_radius=8, color="#28F06A30", offset=ft.Offset(0, 4)),
        alignment=ft.Alignment.CENTER,
        on_click=on_connections_click,
        ink=True,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.WIFI, color=WHITE, size=18),
                ft.Text(
                    "Connections", color=WHITE, size=14, weight=ft.FontWeight.W_600
                ),
            ],
        ),
    )
    return [menu_btn, connections_btn]


def _bottom_bar(on_click) -> ft.Container:
    """Bottom server selection bar."""
    server = app_state.current_server
    flag = server["flag"] if server else "🌐"
    name = server["name"] if server else "Choose server"

    return ft.Container(
        left=24,
        top=640,
        width=327,
        height=48,
        bgcolor=WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(blur_radius=8, color="#18000000", offset=ft.Offset(0, 4)),
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
