import flet as ft
from config.app_state import W, H, app_state


# ─── Colors ───
BG = "#F5F5F5"
ORANGE = "#F06A30"
ORANGE_LIGHT = "#FEF1EB"
WHITE = "#FFFFFF"
BLACK = "#000000"
GRAY = "#AAAAAA"
DARK_GRAY = "#888888"
DIVIDER = "#EEEEEE"

REGION_MAP = {
    "ams": ("Amsterdam", "Netherlands", "🇳🇱"),
    "fra": ("Frankfurt", "Germany", "🇩🇪"),
    "lhr": ("London", "UK", "🇬🇧"),
    "par": ("Paris", "France", "🇫🇷"),
    "waw": ("Warsaw", "Poland", "🇵🇱"),
    "mad": ("Madrid", "Spain", "🇪🇸"),
    "sgp": ("Singapore", "Singapore", "🇸🇬"),
    "nrt": ("Tokyo", "Japan", "🇯🇵"),
    "icn": ("Seoul", "South Korea", "🇰🇷"),
    "bom": ("Mumbai", "India", "🇮🇳"),
    "syd": ("Sydney", "Australia", "🇦🇺"),
    "ewr": ("New Jersey", "USA", "🇺🇸"),
    "ord": ("Chicago", "USA", "🇺🇸"),
    "dfw": ("Dallas", "USA", "🇺🇸"),
    "lax": ("Los Angeles", "USA", "🇺🇸"),
    "sea": ("Seattle", "USA", "🇺🇸"),
    "atl": ("Atlanta", "USA", "🇺🇸"),
    "mia": ("Miami", "USA", "🇺🇸"),
    "yto": ("Toronto", "Canada", "🇨🇦"),
    "sao": ("São Paulo", "Brazil", "🇧🇷"),
    "jnb": ("Johannesburg", "South Africa", "🇿🇦"),
    "mil": ("Milan", "Italy", "🇮🇹"),
    "lon": ("London", "UK", "🇬🇧"),
    "sto": ("Stockholm", "Sweden", "🇸🇪"),
    "vie": ("Vienna", "Austria", "🇦🇹"),
    "zrh": ("Zurich", "Switzerland", "🇨🇭"),
}


# ─── UI Helpers ───
def _header(top_pos: int) -> ft.Container:
    return ft.Container(
        left=24,
        top=top_pos,
        width=327,
        content=ft.Text(
            "Choose server location",
            size=20,
            color=BLACK,
            weight=ft.FontWeight.W_700,
        ),
    )


def resolve_region_full(region_code: str):
    return REGION_MAP.get(region_code, ("Unknown", "Unknown", "🌐"))


def _search_bar(top_pos: int) -> ft.Container:
    return ft.Container(
        left=24,
        top=top_pos,
        width=327,
        height=48,
        bgcolor=WHITE,
        border_radius=16,
        padding=ft.Padding.symmetric(horizontal=16),
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#08000000",
            offset=ft.Offset(0, 2),
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Search location", color=GRAY, size=15),
                ft.Icon(ft.Icons.SEARCH, color=GRAY),
            ],
        ),
    )


def _section_title(text: str, top_pos: int) -> ft.Container:
    return ft.Container(
        left=24,
        top=top_pos,
        width=327,
        content=ft.Text(
            text,
            size=12,
            color=DARK_GRAY,
            weight=ft.FontWeight.W_700,
        ),
    )


def _server_item(server: dict, premium: bool, navigate) -> ft.Container:

    city, country, flag = resolve_region_full(server["region"])
    name = f"{city}, {country}"
    active = app_state.current_server and app_state.current_server["name"] == name

    bg_color = ORANGE if active else WHITE
    text_color = WHITE if active else BLACK
    signal_color = WHITE if active else ORANGE
    divider_color = "#40FFFFFF" if active else DIVIDER
    shadow_color = "#28F06A30" if active else "#18000000"

    if active:
        right_icon = ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color=WHITE, size=14)
    elif premium:
        right_icon = ft.Icon(ft.Icons.WORKSPACE_PREMIUM, color=ORANGE, size=20)
    else:
        right_icon = ft.Icon(ft.Icons.ARROW_FORWARD_IOS, color=GRAY, size=14)

    def select_server(e):
        if premium:
            pass

        app_state.current_server = {
            "id": server["id"],
            "name": name,
            "flag": flag,
            "host": server["host"],
            "region": server["region"],
        }
        navigate(e.page, "main")

    return ft.Container(
        width=327,
        height=56,
        bgcolor=bg_color,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color=shadow_color,
            offset=ft.Offset(0, 4),
        ),
        padding=ft.Padding.symmetric(horizontal=16),
        ink=True,
        on_click=select_server,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Text(flag, size=22),
                        ft.Text(
                            name,
                            size=15,
                            color=text_color,
                            weight=ft.FontWeight.W_600,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=16,
                    controls=[
                        ft.Icon(
                            ft.Icons.SIGNAL_CELLULAR_ALT,
                            color=signal_color,
                            size=18,
                        ),
                        ft.Container(width=1, height=24, bgcolor=divider_color),
                        right_icon,
                    ],
                ),
            ],
        ),
    )


def _premium_list(top_pos: int, navigate) -> ft.Container:
    return ft.Container(
        left=24,
        top=top_pos,
        width=327,
        height=H - top_pos - 20,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                _server_item(
                    {"region": "mil", "id": None, "host": None}, True, navigate
                ),
                _server_item(
                    {"region": "lon", "id": None, "host": None}, True, navigate
                ),
                _server_item(
                    {"region": "sto", "id": None, "host": None}, True, navigate
                ),
                _server_item(
                    {"region": "waw", "id": None, "host": None}, True, navigate
                ),
                _server_item(
                    {"region": "ams", "id": None, "host": None}, True, navigate
                ),
                _server_item(
                    {"region": "vie", "id": None, "host": None}, True, navigate
                ),
                _server_item(
                    {"region": "mad", "id": None, "host": None}, True, navigate
                ),
                _server_item(
                    {"region": "zrh", "id": None, "host": None}, True, navigate
                ),
            ],
        ),
    )


# ─── Main screen ───
def build_server_location_screen(page: ft.Page, navigate) -> ft.Container:
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.TOP_CENTER,
        content=ft.Container(
            width=W,
            height=H,
            bgcolor=BG,
            border_radius=24,
            content=ft.Stack(
                width=W,
                height=H,
                controls=[
                    _header(40),
                    _search_bar(80),
                    _section_title("FREE LOCATIONS", 152),
                    ft.Container(
                        left=24,
                        top=184,
                        content=ft.Column(
                            spacing=16,
                            controls=[
                                _server_item(server, False, navigate)
                                for server in app_state.servers
                            ],
                        ),
                    ),
                    _section_title("PREMIUM LOCATIONS", 416),
                    _premium_list(448, navigate),
                ],
            ),
        ),
    )
