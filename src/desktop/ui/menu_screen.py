import flet as ft
from desktop.config.app_state import W, H
from desktop.services.auth_service import logout_user


# ─── Colors ───
BG = "#F5F5F5"
ORANGE = "#F06A30"
ORANGE_LIGHT = "#FEF1EB"
WHITE = "#FFFFFF"
BLACK = "#000000"
GRAY = "#AAAAAA"
DIVIDER = "#CCCCCC"


# ─── Helpers ───
def _back_button(on_click) -> ft.Container:
    """Top-left back button with arrow icon."""
    return ft.Container(
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
        on_click=on_click,
        ink=True,
        content=ft.Icon(
            ft.Icons.ARROW_BACK_IOS_NEW,
            color=GRAY,
            size=18,
        ),
    )


def _avatar() -> ft.Container:
    """User avatar circle with person icon."""
    return ft.Container(
        left=123,
        top=130,
        width=128,
        height=128,
        bgcolor=WHITE,
        border_radius=64,
        shadow=ft.BoxShadow(
            blur_radius=12,
            color="#28000000",
            offset=ft.Offset(0, 4),
        ),
        alignment=ft.Alignment.CENTER,
        content=ft.Stack(
            width=80,
            height=80,
            controls=[
                # Head circle
                ft.Container(
                    left=20,
                    top=0,
                    width=40,
                    height=40,
                    bgcolor=BLACK,
                    border_radius=20,
                ),
                # Body arc (shoulders)
                ft.Container(
                    left=0,
                    top=44,
                    width=80,
                    height=40,
                    bgcolor=BLACK,
                    border_radius=ft.BorderRadius(
                        top_left=40, top_right=40, bottom_left=0, bottom_right=0
                    ),
                ),
                # Orange accent dot (status)
                ft.Container(
                    left=52,
                    top=28,
                    width=14,
                    height=14,
                    bgcolor=ORANGE,
                    border_radius=7,
                    border=ft.Border.all(2, WHITE),
                ),
            ],
        ),
    )


def _user_info() -> list[ft.Control]:
    """Username and subtitle text under avatar."""
    return [
        ft.Container(
            left=0,
            top=290,
            width=W,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                "Your Account 2024",
                size=20,
                color=BLACK,
                weight=ft.FontWeight.W_700,
                text_align=ft.TextAlign.CENTER,
            ),
        ),
        ft.Container(
            left=0,
            top=318,
            width=W,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                "yourvoure00.2024",
                size=13,
                color=GRAY,
                text_align=ft.TextAlign.CENTER,
            ),
        ),
    ]


def _menu_item(
    top: int,
    icon: str,
    label: str,
    subtitle: str,
    on_click,
    show_divider: bool = True,
) -> list[ft.Control]:
    """
    Single menu row with orange icon, label, subtitle, chevron.
    Returns the row container + optional divider as a list.
    """
    row = ft.Container(
        left=0,
        top=top,
        width=W,
        height=80,
        on_click=on_click,
        ink=True,
        bgcolor=BG,
        padding=ft.Padding.symmetric(horizontal=24, vertical=0),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                # Orange icon badge
                ft.Container(
                    width=44,
                    height=44,
                    bgcolor=ORANGE_LIGHT,
                    border_radius=12,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(icon, color=ORANGE, size=22),
                ),
                # Label + subtitle
                ft.Column(
                    spacing=2,
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            label,
                            size=15,
                            color=BLACK,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Text(
                            subtitle,
                            size=12,
                            color=GRAY,
                        ),
                    ],
                ),
                # Chevron
                ft.Icon(
                    ft.Icons.ARROW_FORWARD_IOS,
                    color=GRAY,
                    size=14,
                ),
            ],
        ),
    )

    if not show_divider:
        return [row]

    divider = ft.Container(
        left=77,
        top=top + 80,
        width=299,
        height=1,
        bgcolor=DIVIDER,
    )
    return [row, divider]


# ─── Menu screen ───
def build_menu_screen(page: ft.Page, navigate) -> ft.Container:
    """Builds the side menu / profile screen."""

    def on_back(e):
        navigate(page, "main")

    def on_my_devices(e):
        pass  # → navigate to devices screen

    def on_subscription(e):
        pass  # → navigate to subscription screen

    def on_settings(e):
        pass  # → navigate to settings screen

    def on_logout(e):
        page = e.page

        logout_user()

        from desktop.ui.auth_screen import username_input, password_input

        username_input.value = ""
        password_input.value = ""

        navigate(page, "login")

    controls: list[ft.Control] = [
        # Background
        ft.Container(
            width=W,
            height=H,
            bgcolor=BG,
            border_radius=24,
        ),
        # Back button
        _back_button(on_back),
        # Avatar
        _avatar(),
        # Username + subtitle
        *_user_info(),
        # Menu items (y positions match SVG dividers: 460, 541, 622, 703)
        *_menu_item(
            top=380,
            icon=ft.Icons.DEVICES,
            label="My Devices",
            subtitle="Manage your connected devices",
            on_click=on_my_devices,
        ),
        *_menu_item(
            top=461,
            icon=ft.Icons.WORKSPACE_PREMIUM,
            label="Subscription",
            subtitle="Pro plan · active",
            on_click=on_subscription,
        ),
        *_menu_item(
            top=542,
            icon=ft.Icons.SETTINGS_OUTLINED,
            label="Settings",
            subtitle="App preferences",
            on_click=on_settings,
        ),
        *_menu_item(
            top=623,
            icon=ft.Icons.LOGOUT,
            label="Log Out",
            subtitle="Sign out of your account",
            on_click=on_logout,
            show_divider=False,
        ),
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
