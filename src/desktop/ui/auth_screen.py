import flet as ft
from config.app_state import W, H
from services.auth_service import login_user, register_user
import asyncio


# ─── Colors ───
BG = "#F5F5F5"
ORANGE = "#F06A30"
WHITE = "#FFFFFF"
BLACK = "#000000"
GRAY = "#AAAAAA"


# ─── Auth State (inputs refs) ───
username_input = ft.TextField()
email_input = ft.TextField()
password_input = ft.TextField()
confirm_input = ft.TextField()


# ─── Helpers ───
def _auth_title(title: str, subtitle: str, top_pos: int):
    return [
        ft.Container(
            left=0,
            top=top_pos,
            width=W,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                title,
                size=28,
                weight=ft.FontWeight.W_800,
                color=BLACK,
            ),
        ),
        ft.Container(
            left=0,
            top=top_pos + 40,
            width=W,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(subtitle, size=14, color=GRAY),
        ),
    ]


def _input(icon, hint, top, field, password=False):
    field.expand = True
    field.hint_text = hint
    field.hint_style = ft.TextStyle(color=GRAY, size=15)
    field.text_size = 15
    field.color = BLACK
    field.cursor_color = ORANGE
    field.password = password
    field.can_reveal_password = password
    field.border = ft.InputBorder.NONE
    field.content_padding = ft.padding.symmetric(vertical=15)

    return ft.Container(
        left=24,
        top=top,
        width=327,
        height=56,
        bgcolor=WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#08000000",
            offset=ft.Offset(0, 4),
        ),
        padding=ft.Padding.only(left=16, right=8, top=0, bottom=0),
        alignment=ft.Alignment.CENTER,
        content=ft.Row(
            spacing=12,
            controls=[
                ft.Icon(icon, color=GRAY, size=20),
                field,
            ],
        ),
    )


def show_error(page: ft.Page, message: str):
    popup = ft.Container(
        width=W - 48,
        height=48,
        bgcolor=WHITE,
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=16),
        alignment=ft.Alignment.CENTER_LEFT,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#14000000",
            offset=ft.Offset(0, 2),
        ),
        content=ft.Row(
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, color=GRAY, size=18),
                ft.Text(
                    message,
                    size=14,
                    color=ORANGE,
                    weight=ft.FontWeight.W_500,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        ),
    )

    wrapper = ft.Container(
        expand=True,
        alignment=ft.Alignment.BOTTOM_CENTER,
        content=ft.Container(
            width=W,
            height=H,
            alignment=ft.Alignment.BOTTOM_CENTER,
            padding=ft.Padding.only(bottom=20),
            content=popup,
        ),
    )

    page.overlay.clear()
    page.overlay.append(wrapper)
    page.update()

    async def close_later():
        await asyncio.sleep(3)
        page.overlay.clear()
        page.update()

    page.run_task(close_later)


def parse_error(resp):
    try:
        data = resp.json()
        detail = data.get("detail")

        if isinstance(detail, list):
            return "\n".join([e.get("msg", "") for e in detail])
        return str(detail)
    except Exception:
        return "Server error"


def _button(text, top, handler):
    return ft.Container(
        left=24,
        top=top,
        width=327,
        height=56,
        bgcolor=ORANGE,
        border_radius=16,
        ink=True,
        on_click=handler,
        alignment=ft.Alignment.CENTER,
        content=ft.Text(text, color=WHITE, weight=ft.FontWeight.W_700),
    )


def _switch(text1, text2, top, handler):
    return ft.Container(
        left=0,
        top=top,
        width=W,
        alignment=ft.Alignment.CENTER,
        ink=True,
        on_click=handler,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text(text1, color=GRAY),
                ft.Text(text2, color=ORANGE, weight=ft.FontWeight.W_700),
            ],
        ),
    )


# ─── Login ───
def build_login_screen(page: ft.Page, navigate):

    def handle_login(e):
        success, resp = login_user(
            username_input.value,
            password_input.value,
        )

        if success:
            navigate(e.page, "main")
        else:
            error_msg = parse_error(resp)
            show_error(e.page, error_msg)

    def go_register(e):
        navigate(e.page, "register")

    controls = [
        ft.Container(expand=True, bgcolor=BG, border_radius=24),
        *_auth_title("Welcome Back", "Log in to secure connection", 100),
        _input(ft.Icons.PERSON_OUTLINE, "Username", 200, username_input),
        _input(ft.Icons.LOCK_OUTLINE, "Password", 272, password_input, True),
        _button("Log In", 360, handle_login),
        _switch("Don't have account?", "Sign Up", 460, go_register),
    ]

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.TOP_CENTER,
        content=ft.Container(
            width=W,
            height=H,
            bgcolor=BG,
            border_radius=24,
            content=ft.Stack(controls=controls),
        ),
    )


# ─── Register ───
def build_register_screen(page: ft.Page, navigate):

    def handle_register(e):
        success, resp = register_user(
            username_input.value,
            email_input.value,
            password_input.value,
            confirm_input.value,
        )

        if success:
            navigate(e.page, "login")
        else:
            error_msg = parse_error(resp)
            show_error(e.page, error_msg)

    def go_login(e):
        navigate(e.page, "login")

    controls = [
        ft.Container(expand=True, bgcolor=BG, border_radius=24),
        *_auth_title("Create Account", "Join VPN system", 80),
        _input(ft.Icons.PERSON_OUTLINE, "Username", 160, username_input),
        _input(ft.Icons.MAIL_OUTLINE, "Email", 232, email_input),
        _input(ft.Icons.LOCK_OUTLINE, "Password", 304, password_input, True),
        _input(ft.Icons.LOCK_RESET, "Confirm password", 376, confirm_input, True),
        _button("Sign Up", 470, handle_register),
        _switch("Already have account?", "Login", 560, go_login),
    ]

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.TOP_CENTER,
        content=ft.Container(
            width=W,
            height=H,
            bgcolor=BG,
            border_radius=24,
            content=ft.Stack(controls=controls),
        ),
    )
