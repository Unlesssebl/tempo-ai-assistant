import asyncio
import ctypes
import json
import os
import platform
import random
import uuid
from typing import Any, Dict, List

import flet as ft
import httpx

from src.core.user_profile import UserProfileProvider
from src.helpdesk.field_mapping import DEFAULT_VALUES, INTRASERVICE_FIELDS

try:
    from src.interfaces.client_storage import HistoryManager
except ImportError:
    from client_storage import HistoryManager

# --- Константы Дизайна (Quantum Bright / Deep Space) ---
BG_COLOR = "#08080C"  # Очень темный базис
SIDEBAR_BG = "#9912122B"  # 60% opacity for better acrylic effect
WHITE_COLOR = "#FFFFFF"
ACCENT_COLOR = "#A78BFA"
ACCENT_LIGHT = "#C4B5FD"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#94A3B8"
LINE_COLOR = "#232333"  # Тонкие деликатные линии
USER_BUBBLE_COLOR = "#805B21B6"  # 50% прозрачности, фиолетовый
AI_BUBBLE_COLOR = "#991E1E2E"  # 60% прозрачности, темный индиго
INPUT_BG_COLOR = "#9912122B"  # 60% opacity for acrylic effect
GOLD_STAR = "#FCD34D"
BLUE_STAR = "#38BDF8"

LIST_ITEM_ACTIVE = "#2D264F"  # Акцентный индиго для активных элементов


class AnimatedOrb(ft.Stack):
    """Центральный анимированный элемент: величественное многослойное 'дышащее' ядро"""

    def __init__(self):
        # Существенно увеличиваем общие размеры
        super().__init__(width=240, height=240)

        # 1. Внешнее мягкое облако-свечение (стало намного больше)
        self.halo = ft.Container(
            width=240,
            height=240,
            border_radius=120,
            gradient=ft.RadialGradient(colors=["#338B5CF6", "transparent"]),
            animate_scale=ft.Animation(3500, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(3500, ft.AnimationCurve.EASE_IN_OUT),
            scale=1.4,
            opacity=0.4,
        )

        # 2. Средний слой (активная пульсация - увеличен)
        self.glow = ft.Container(
            width=140,
            height=140,
            border_radius=70,
            gradient=ft.RadialGradient(colors=["#77A78BFA", "transparent"]),
            animate_scale=ft.Animation(2500, ft.AnimationCurve.EASE_IN_OUT),
            scale=1.4,
        )

        # 3. Ядро (теперь крупное и солидное)
        self.core = ft.Container(
            width=85,
            height=85,
            border_radius=35,
            bgcolor="#8B5CF6",
            shadow=ft.BoxShadow(blur_radius=50, color="#8B5CF6"),
            animate_scale=ft.Animation(2500, ft.AnimationCurve.EASE_IN_OUT),
            scale=1.0,
        )

        self.controls = [
            ft.Container(content=self.halo, alignment=ft.alignment.Alignment(0, 0)),
            ft.Container(content=self.glow, alignment=ft.alignment.Alignment(0, 0)),
            ft.Container(content=self.core, alignment=ft.alignment.Alignment(0, 0)),
        ]

    def did_mount(self):
        self.running = True
        self.page.run_task(self.pulse)

    def will_unmount(self):
        self.running = False

    async def pulse(self):
        while self.running:
            if not self.page:
                break
            try:
                # Увеличен интервал для производительности
                self.halo.scale = 1.12
                self.halo.opacity = 0.6
                self.glow.scale = 1.2
                self.core.scale = 1.08
                if self.page:
                    self.update()
                await asyncio.sleep(3.5)

                if not self.running:
                    break

                self.halo.scale = 1.0
                self.halo.opacity = 0.3
                self.glow.scale = 0.95
                self.core.scale = 0.98
                if self.page:
                    self.update()
                await asyncio.sleep(3.5)
            except Exception:
                break


# Конфигурация
DEFAULT_SERVER_URL = "http://10.245.19.85:8000"
CONFIG_FILE = "client_config.json"


class AnimatedStars(ft.Stack):
    """Оптимизированное звездное небо: минимум элементов, максимум эффекта"""

    def __init__(self):
        super().__init__(expand=True)
        self.stars_count = 150  # Оптимальный баланс
        self.twinkle_count = 12  # Только 12 звезд мерцают

    def did_mount(self):
        self.running = True
        self.page.run_task(self.create_stars)
        self.page.run_task(self.shooting_stars_logic)

    def will_unmount(self):
        self.running = False

    async def create_stars(self):
        star_colors = ["#FFFFFF", "#E8E8FF", "#B8D4FF", "#FFE8CC"]

        self.twinkle_stars = []

        for i in range(self.stars_count):
            # Плотность: больше мелких, меньше крупных
            if i < self.stars_count * 0.7:
                size = random.uniform(0.3, 0.6)
                opacity = random.uniform(0.3, 0.6)
            elif i < self.stars_count * 0.9:
                size = random.uniform(0.8, 1.2)
                opacity = random.uniform(0.5, 0.8)
            else:
                size = random.uniform(1.5, 2.0)
                opacity = random.uniform(0.7, 1.0)

            # Простой контейнер без анимаций и теней
            s = ft.Container(
                width=size,
                height=size,
                bgcolor=random.choice(star_colors),
                border_radius=size,
                left=random.randint(0, 1920),
                top=random.randint(0, 1080),
                opacity=opacity,
            )
            self.controls.append(s)

            # Только крупные звезды добавляем в список для мерцания
            if size > 1.2 and len(self.twinkle_stars) < self.twinkle_count:
                self.twinkle_stars.append(s)

        if self.page:
            self.update()

        # Простой цикл мерцания без создания новых анимаций
        while self.running:
            if not self.page:
                break
            try:
                for s in self.twinkle_stars:
                    s.opacity = random.uniform(0.4, 1.0)
                if self.page:
                    self.update()
            except Exception:
                break
            await asyncio.sleep(4)

    async def shooting_stars_logic(self):
        """Падающие звезды: чаще и эффектнее"""
        while self.running:
            if not self.page:
                break
            await asyncio.sleep(random.uniform(6, 15))  # Чаще!
            if not self.running:
                break

            try:
                start_x = random.randint(100, 1600)
                start_y = random.randint(50, 600)

                ss = ft.Container(
                    width=80,
                    height=1,
                    gradient=ft.LinearGradient(
                        colors=["#00FFFFFF", "#FFFFFFFF", "#00FFFFFF"],
                        stops=[0.0, 0.5, 1.0],
                    ),
                    left=start_x,
                    top=start_y,
                    opacity=0,
                    rotate=ft.Rotate(0.4),
                    animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_IN),
                    animate_position=ft.Animation(600, ft.AnimationCurve.EASE_OUT),
                )

                self.controls.append(ss)
                if self.page:
                    self.update()

                await asyncio.sleep(0.05)
                ss.opacity = 0.6
                ss.left = start_x + 400
                ss.top = start_y + 200
                if self.page:
                    self.update()

                await asyncio.sleep(0.6)
                ss.opacity = 0
                if self.page:
                    self.update()

                await asyncio.sleep(0.5)
                if ss in self.controls:
                    self.controls.remove(ss)
            except Exception:
                pass


class ChatItem(ft.GestureDetector):
    """Элемент списка чатов с hover-эффектами через GestureDetector."""

    def __init__(self, chat_data, is_active, on_click_callback, on_delete_callback):
        self.chat_data = chat_data
        self.is_active = is_active
        self.on_click_callback = on_click_callback
        self.on_delete_callback = on_delete_callback

        # Trash Icon Button (Hidden by default, shown on hover)
        self.delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_size=16,
            opacity=0,  # Hidden initially
            animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e: self.on_delete_callback(self.chat_data["id"]),
            hover_color=ft.Colors.TRANSPARENT,
            highlight_color=ft.Colors.TRANSPARENT,
            tooltip="Удалить чат",
            style=ft.ButtonStyle(
                color={
                    "hovered": "#FF3B30",
                    "": TEXT_SECONDARY,
                }
            ),
        )

        # Inner container for styling
        # Inner container for styling
        self.inner_container = ft.Container(
            content=ft.Row(
                [
                    # Active Indicator (Vertical Bar)
                    ft.Container(
                        width=4,
                        height=24,
                        border_radius=2,
                        bgcolor=ACCENT_COLOR if is_active else ft.Colors.TRANSPARENT,
                        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                    ),
                    # Icon + Title Group
                    ft.Row(
                        [
                            ft.Icon(
                                icon=ft.Icons.CHAT if is_active else ft.Icons.CHAT_OUTLINED,
                                size=18,
                                color=TEXT_PRIMARY if is_active else TEXT_SECONDARY,
                            ),
                            ft.Text(
                                chat_data["title"],
                                size=14,
                                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                                color=TEXT_PRIMARY if is_active else TEXT_SECONDARY,
                                no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                    # Delete Button
                    self.delete_btn,
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=ft.Padding(8, 10, 8, 10),
            border_radius=15,
            bgcolor=LIST_ITEM_ACTIVE if is_active else ft.Colors.TRANSPARENT,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )

        super().__init__(
            content=self.inner_container,
            on_tap=lambda e: self.on_click_callback(self.chat_data["id"]),
            on_enter=self._on_enter,
            on_exit=self._on_exit,
        )

    def _on_enter(self, e):
        # Hover effect for background if not active
        if not self.is_active:
            self.inner_container.bgcolor = "#1A1A24"
        # Show Delete Button
        self.delete_btn.opacity = 1
        self.delete_btn.update()
        self.inner_container.update()

    def _on_exit(self, e):
        # Reset background if not active
        if not self.is_active:
            self.inner_container.bgcolor = ft.Colors.TRANSPARENT
        # Hide Delete Button
        self.delete_btn.opacity = 0
        self.delete_btn.update()
        self.inner_container.update()


class AnimatedBackground(ft.Container):
    """Живой анимированный фон: яркие космические эффекты"""

    def __init__(self):
        # Первый слой: Яркое фиолетовое свечение
        self.glow_1 = ft.Container(
            expand=True,
            gradient=ft.RadialGradient(
                center=ft.alignment.Alignment(0, -0.5),
                radius=1.6,
                colors=[
                    "#996D28D9",
                    "transparent",
                ],  # Снижено с AA до 99 (~60% вместо 67%)
            ),
            opacity=0.1,  # Снижено с 0.9
            animate=ft.Animation(10000, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(10000, ft.AnimationCurve.EASE_IN_OUT),
        )
        # Второй слой: Синее свечение
        self.glow_2 = ft.Container(
            expand=True,
            gradient=ft.RadialGradient(
                center=ft.alignment.Alignment(0.5, 0.3),
                radius=1.9,
                colors=[
                    "#553B82F6",
                    "transparent",
                ],  # Снижено с 66 до 55 (~33% вместо 40%)
            ),
            opacity=0.5,  # Снижено с 0.7
            animate=ft.Animation(6000, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(6000, ft.AnimationCurve.EASE_IN_OUT),
        )
        super().__init__(
            expand=True,
            bgcolor="#050508",
            content=ft.Stack(
                [
                    self.glow_1,
                    self.glow_2,
                    AnimatedStars(),
                ]
            ),
        )

    def did_mount(self):
        self.running = True
        self.page.run_task(self.animate_bg)

    def will_unmount(self):
        self.running = False

    async def animate_bg(self):
        while self.running:
            if not self.page:
                break
            try:
                # Фаза 1: Фиолетовый ярче, синий тусклее
                self.glow_1.gradient.center = ft.alignment.Alignment(-0.4, -0.6)
                self.glow_1.opacity = 0.9  # Снижено с 1.0
                self.glow_2.gradient.center = ft.alignment.Alignment(0.6, 0.4)
                self.glow_2.opacity = 0.2  # Снижено с 0.3
                if self.page:
                    self.update()
                await asyncio.sleep(6)  # Восстановлено с 4

                if not self.running:
                    break

                # Фаза 2: Синий ярче, фиолетовый тусклее
                self.glow_1.gradient.center = ft.alignment.Alignment(0.3, -0.3)
                self.glow_1.opacity = 0.2  # Снижено с 0.3
                self.glow_2.gradient.center = ft.alignment.Alignment(-0.4, 0.5)
                self.glow_2.opacity = 0.9  # Снижено с 1.0
                if self.page:
                    self.update()
                await asyncio.sleep(6)  # Восстановлено с 4
            except Exception:
                break


class TempoClient:
    def __init__(self, page: ft.Page):
        self.page = page
        self.history_manager = HistoryManager()
        self.current_chat_id = None
        config = self.load_config()
        self.server_url = config.get("server_url", DEFAULT_SERVER_URL)
        self.session_id = config.get("session_id", str(uuid.uuid4()))
        self.user_login = config.get("user_login", "")
        if not self.user_login:
            self.user_login = self._get_windows_login()

        # User Context: имя из конфига или автоопределение из системы
        self.user_name = config.get("user_name", "")
        if not self.user_name:
            self.user_name = self._get_windows_display_name()
        self.last_ai_interaction = None

        # Сохраняем, если session_id был сгенерирован заново
        if "session_id" not in config:
            self.save_config(self.server_url, self.session_id, self.user_name, self.user_login)

        self.setup_page()
        self.build_ui()
        self.load_history_list()

        # Если чатов нет, создаем новый
        if not self.history_manager.get_chats():
            asyncio.create_task(self.create_new_chat())
        else:
            # Загружаем последний чат
            last_chat = self.history_manager.get_chats()[0]
            asyncio.create_task(self.load_chat(last_chat["id"]))

    def load_profile(self) -> Dict[str, str]:
        """Собирает полный профиль пользователя из всех источников."""
        # 1. Системные данные и AD
        profile = UserProfileProvider.get_combined_profile()

        # 2. Переопределяем данные из локальной БД (то что введено вручную)
        stored = self.history_manager.get_profile_data()
        profile.update(stored)

        # 3. Добавляем дефолты если пусто
        for k, v in DEFAULT_VALUES.items():
            if not profile.get(k):
                profile[k] = v

        return profile

    def save_profile_field(self, key: str, value: str):
        """Сохраняет одно поле профиля в БД."""
        self.history_manager.save_profile_data({key: value})

    def get_intraservice_extra_fields(self) -> Dict[str, Any]:
        """Формирует словарь FieldXXXX для API IntraService."""
        profile = self.load_profile()
        extra = {}
        for key, field_id in INTRASERVICE_FIELDS.items():
            val = profile.get(key)
            if val:
                extra[field_id] = val
        return extra

    def validate_profile(self) -> List[str]:
        """Проверяет наличие всех обязательных полей. Возвращает список пропущенных имен."""
        profile = self.load_profile()
        missing = []
        # Список полей, которые мы считаем критичными для валидации (для типа 1020)
        critical_fields = {
            "last_name": "Фамилия",
            "first_name": "Имя",
            "middle_name": "Отчество",
            "phone": "Телефон",
            "room": "Кабинет",
            "department": "Подразделение",
            "position": "Должность",
            "email": "Email",
            "pc_name": "Имя ПК",
        }
        for key, label in critical_fields.items():
            if not str(profile.get(key, "")).strip():
                missing.append(label)
        return missing

    async def show_profile_dialog(self, reason: str = None):
        profile = self.load_profile()

        # Поля ввода
        inputs = {
            "last_name": ft.TextField(label="Фамилия", value=profile.get("last_name"), bgcolor=INPUT_BG_COLOR),
            "first_name": ft.TextField(label="Имя", value=profile.get("first_name"), bgcolor=INPUT_BG_COLOR),
            "middle_name": ft.TextField(
                label="Отчество",
                value=profile.get("middle_name"),
                bgcolor=INPUT_BG_COLOR,
            ),
            "phone": ft.TextField(
                label="Телефон для связи",
                value=profile.get("phone"),
                bgcolor=INPUT_BG_COLOR,
            ),
            "room": ft.TextField(
                label="Кабинет / Участок",
                value=profile.get("room"),
                bgcolor=INPUT_BG_COLOR,
            ),
            "department": ft.TextField(
                label="Подразделение",
                value=profile.get("department"),
                bgcolor=INPUT_BG_COLOR,
            ),
            "position": ft.TextField(label="Должность", value=profile.get("position"), bgcolor=INPUT_BG_COLOR),
            "email": ft.TextField(label="Email", value=profile.get("email"), bgcolor=INPUT_BG_COLOR),
            "pc_name": ft.TextField(
                label="Имя компьютера",
                value=profile.get("pc_name"),
                bgcolor=INPUT_BG_COLOR,
                read_only=True,
            ),
        }

        async def save_clicked(e):
            new_data = {k: v.value for k, v in inputs.items()}
            self.history_manager.save_profile_data(new_data)
            self.close_dialog(dlg)
            if reason:
                # Если открывали из-за валидации, уведомляем
                self.page.show_snack_bar(ft.SnackBar(ft.Text("Профиль обновлен. Теперь вы можете создать заявку.")))

        dlg = ft.AlertDialog(
            title=ft.Text("Мой профиль"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(reason, color="#FF3B30", size=14) if reason else ft.Container(),
                        ft.Text(
                            "Эти данные будут использоваться для создания заявок в HelpDesk.",
                            size=12,
                            color=TEXT_SECONDARY,
                        ),
                        ft.Divider(height=10, color="transparent"),
                        ft.Column(
                            [v for v in inputs.values()],
                            scroll=ft.ScrollMode.AUTO,
                            tight=True,
                        ),
                    ],
                    spacing=10,
                    width=400,
                    tight=True,
                ),
                height=500,
            ),
            actions=[
                ft.ElevatedButton(
                    "Сохранить",
                    on_click=save_clicked,
                    bgcolor=ACCENT_COLOR,
                    color=WHITE_COLOR,
                ),
                ft.TextButton("Отмена", on_click=lambda e: self.close_dialog(dlg)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _get_windows_display_name(self) -> str:
        """
        Попытка получить полное имя пользователя (Display Name) из Windows/AD.
        Если не удается - возвращает login name или пустую строку.
        """
        try:
            if platform.system() != "Windows":
                return os.getlogin()

            GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
            NameDisplay = 3

            size = ctypes.pointer(ctypes.c_ulong(0))
            GetUserNameEx(NameDisplay, None, size)

            if size.contents.value > 0:
                buf = ctypes.create_unicode_buffer(size.contents.value)
                if GetUserNameEx(NameDisplay, buf, size):
                    return buf.value

            # Fallback to login name
            return os.getlogin()
        except Exception:
            try:
                return os.getlogin()
            except Exception:
                return ""

    def _get_windows_login(self) -> str:
        try:
            return os.getlogin()
        except Exception:
            return ""

    def save_config(self, url, session_id, user_name="", user_login=""):
        with open(CONFIG_FILE, "w") as f:
            json.dump(
                {
                    "server_url": url,
                    "session_id": session_id,
                    "user_name": user_name,
                    "user_login": user_login,
                },
                f,
            )

    def _get_user_friendly_error(self, error_text: str) -> str:
        """Преобразует технические ошибки API в понятные пользователю сообщения."""
        err = error_text.lower()

        if "все api ключи исчерпали лимиты" in err or "all api keys" in err or "all keys exhausted" in err:
            return "⚠️ Все API ключи исчерпали лимиты. Пожалуйста, попробуйте позже."

        if "503" in error_text or "unavailable" in err or "overloaded" in err:
            return "⚡ Модель сейчас перегружена. Попробуйте через минуту."

        if "429" in error_text or "resource_exhausted" in err or "rate limit" in err:
            return "⏳ Превышен лимит запросов. Попробуйте позже."

        if "failed_precondition" in err or "user location is not supported" in err:
            return "🌍 API недоступен в вашем регионе."

        if "400" in error_text and "invalid" in err:
            return "❌ Некорректный запрос. Попробуйте переформулировать."

        if "403" in error_text or "permission_denied" in err:
            return "🔒 Нет доступа к API. Обратитесь к администратору."

        if "404" in error_text or "not_found" in err:
            return "🔍 Запрашиваемый ресурс не найден."

        if "500" in error_text or "internal" in err:
            return "🔧 Внутренняя ошибка сервера. Попробуйте позже."

        if "connection error" in err or "connecttimeout" in err:
            return "🔌 Ошибка соединения с сервером. Проверьте, запущен ли backend."

        return f"⚠️ Ошибка: {error_text}"

    def setup_page(self):
        # Гарантированный абсолютный путь к иконке для Windows
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, "assets", "icon.png")

        self.page.window.icon = icon_path
        self.page.icon = icon_path
        self.page.assets_dir = "assets"

        self.page.title = "AssistantAlpha"  # <<< ТУТ МОЖНО ПОМЕНЯТЬ НАЗВАНИЕ ПРОГРАММЫ
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.window.title_bar_hidden = True
        self.page.window.frameless = False
        self.page.window.title_bar_buttons_visible = False
        self.page.bgcolor = BG_COLOR

        # Регистрация шрифтов
        self.page.fonts = {
            "Inter": "fonts/Inter-Variable.ttf",
        }

        self.page.theme = ft.Theme(
            font_family="Inter",
            color_scheme=ft.ColorScheme(primary=ACCENT_COLOR),
            visual_density=ft.VisualDensity.COMPACT,
        )

    def build_ui(self):
        # --- Компоненты ---

        # 1. Custom Title Bar
        # 1. Custom Title Bar with Sidebar Toggle (Animated container)
        self.btn_toggle_sidebar = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,  # Simple arrow icon
            icon_size=20,
            on_click=self.toggle_sidebar,
            tooltip="Показать/Скрыть меню",
            hover_color=ft.Colors.TRANSPARENT,
            highlight_color=ft.Colors.TRANSPARENT,
            style=ft.ButtonStyle(
                color={
                    "hovered": WHITE_COLOR,
                    "": TEXT_SECONDARY,
                }
            ),
        )

        # Container that moves the button
        self.toggle_btn_container = ft.Container(
            content=self.btn_toggle_sidebar,
            # Initial padding matches open sidebar (260 + 8)
            padding=ft.Padding(268, 0, 0, 0),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        # 0. Window Controls
        self.window_controls = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.MINIMIZE_ROUNDED,
                    icon_size=16,
                    on_click=self._minimize_window,
                    hover_color=ft.Colors.TRANSPARENT,
                    highlight_color=ft.Colors.TRANSPARENT,
                    style=ft.ButtonStyle(
                        color={
                            "hovered": WHITE_COLOR,
                            "": TEXT_SECONDARY,
                        }
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.CROP_SQUARE_ROUNDED,
                    icon_size=14,
                    on_click=self._toggle_maximize,
                    hover_color=ft.Colors.TRANSPARENT,
                    highlight_color=ft.Colors.TRANSPARENT,
                    style=ft.ButtonStyle(
                        color={
                            "hovered": WHITE_COLOR,
                            "": TEXT_SECONDARY,
                        }
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE_ROUNDED,
                    icon_size=16,
                    on_click=lambda _: asyncio.create_task(self.page.window.close()),
                    hover_color=ft.Colors.TRANSPARENT,
                    highlight_color=ft.Colors.TRANSPARENT,
                    style=ft.ButtonStyle(
                        color={
                            "hovered": "#E81123",
                            "": TEXT_SECONDARY,
                        }
                    ),
                ),
            ],
            spacing=0,
        )

        self.title_bar = ft.Container(
            content=ft.Row(
                [
                    self.toggle_btn_container,
                    ft.WindowDragArea(
                        content=ft.Container(bgcolor="transparent", height=38),
                        expand=True,
                    ),
                    self.window_controls,
                ],
                spacing=0,
            ),
            height=38,
        )

        # 2. Sidebar
        self.chat_list_view = ft.ListView(expand=True, spacing=4, padding=10)

        self.sidebar = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Image(
                            src="/Logo_1_blue.png",
                            height=40,
                        ),
                        padding=ft.Padding(20, 20, 20, 10),
                    ),
                    ft.Container(
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(icon=ft.Icons.ADD, size=18, color=ACCENT_COLOR),
                                    ft.Text(
                                        "Новый чат",
                                        color=WHITE_COLOR,
                                        size=14,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding(0, 12, 0, 12),
                            bgcolor="#4D2D264F",  # Насыщенный индиго для кнопки
                            border_radius=12,
                            on_click=lambda _: asyncio.create_task(self.create_new_chat()),
                            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                            on_hover=lambda e: self.on_new_chat_hover(e),
                        ),
                        padding=ft.Padding(15, 0, 15, 20),
                    ),
                    self.chat_list_view,
                    # Footer with Profile and Settings
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                icon=ft.Icons.PERSON_OUTLINED,
                                                color=TEXT_SECONDARY,
                                                size=18,
                                            ),
                                            ft.Text(
                                                "Мой профиль",
                                                color=TEXT_SECONDARY,
                                                size=14,
                                                weight=ft.FontWeight.W_500,
                                            ),
                                        ],
                                        spacing=12,
                                    ),
                                    padding=ft.Padding(12, 10, 12, 10),
                                    border_radius=10,
                                    on_click=lambda _: asyncio.create_task(self.show_profile_dialog()),
                                    ink=True,
                                ),
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                icon=ft.Icons.SETTINGS_OUTLINED,
                                                color=TEXT_SECONDARY,
                                                size=18,
                                            ),
                                            ft.Text(
                                                "Настройки",
                                                color=TEXT_SECONDARY,
                                                size=14,
                                                weight=ft.FontWeight.W_500,
                                            ),
                                        ],
                                        spacing=12,
                                    ),
                                    padding=ft.Padding(12, 10, 12, 10),
                                    border_radius=10,
                                    on_click=self.open_settings,
                                    ink=True,
                                ),
                            ],
                            spacing=0,
                        ),
                        padding=ft.Padding(15, 10, 15, 20),
                        border=ft.Border.only(top=ft.BorderSide(1, LINE_COLOR)),
                        bgcolor="transparent",
                    ),
                ],
                spacing=0,
            ),
            width=260,
            bgcolor=SIDEBAR_BG,
            blur=ft.Blur(40, 40, ft.BlurStyle.INNER),  # Усиленный блюр
            border=ft.Border(right=ft.BorderSide(1, LINE_COLOR)),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT_CUBIC),
        )

        # 3. Chat Area
        self.messages_list = ft.ListView(
            expand=True,
            spacing=16,
            padding=ft.Padding(20, 20, 20, 20),
            auto_scroll=True,
        )

        self.txt_input = ft.TextField(
            hint_text="Сообщение...",
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.InputBorder.NONE,
            focused_border_color=ft.Colors.TRANSPARENT,
            color=WHITE_COLOR,
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=5,
            shift_enter=True,
            on_submit=lambda e: asyncio.create_task(self.send_message(e)),
            content_padding=ft.Padding(15, 12, 15, 12),
            text_size=15,
            on_focus=lambda _: self.set_input_focus(True),
            on_blur=lambda _: self.set_input_focus(False),
        )

        # Кнопка отправки
        self.btn_send = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD,
            icon_size=28,
            on_click=lambda e: asyncio.create_task(self.send_message(e)),
            tooltip="Отправить (Enter)",
            hover_color=ft.Colors.TRANSPARENT,
            highlight_color=ft.Colors.TRANSPARENT,
            style=ft.ButtonStyle(
                color={
                    "hovered": WHITE_COLOR,
                    "": ACCENT_COLOR,
                }
            ),
        )

        self.loading_indicator = ft.ProgressRing(width=22, height=22, stroke_width=2, color=ACCENT_COLOR, visible=False)

        # Акриловая подложка для текста
        self.input_container = ft.Container(
            content=self.txt_input,
            bgcolor="#9912122B",
            border_radius=24,
            blur=ft.Blur(35, 35),
            border=ft.Border.all(1, "#4DFFFFFF"),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            expand=True,
        )

        # Final Assembly: Row of Input + Button
        self.input_area = ft.Container(
            content=ft.Row(
                [
                    self.input_container,
                    self.btn_send,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            padding=ft.Padding(20, 10, 20, 25),
        )

        self.main_area = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=38),  # TitleBar space
                    self.messages_list,
                    self.input_area,
                ],
                spacing=0,
            ),
            expand=True,
            bgcolor="transparent",
        )

        # Layout Assembly
        self.page.add(
            ft.Stack(
                [
                    # Background layer (Animated)
                    AnimatedBackground(),
                    # UI Layer
                    ft.Row([self.sidebar, self.main_area], spacing=0, expand=True),
                    # Title Bar Overlay
                    ft.Column([self.title_bar], height=38),
                ],
                expand=True,
            )
        )

    def set_input_focus(self, focused: bool):
        """Эффект фокуса, который идеально следует форме акрила"""
        self.input_container.border = ft.Border.all(2 if focused else 1, ACCENT_COLOR if focused else "#4DFFFFFF")
        self.input_container.update()

    def on_chat_hover(self, e):
        # Используем data для определения активного состояния (строка или bool)
        is_active = str(e.control.data).lower() == "true"
        if is_active:
            # Не меняем фон у активного при наведении
            return

        # Тонкий эффект при наведении на неактивный чат
        e.control.bgcolor = "#FFFFFF0A" if e.data == "true" else "transparent"
        e.control.update()

    def on_chip_hover(self, e):
        # Эффект подсвечивания для непрозрачных подсказок
        e.control.bgcolor = "#4B4B5E" if e.data == "true" else "#2D2D3A"  # Светлее при ховере
        e.control.border = ft.BorderSide(1, ACCENT_COLOR if e.data == "true" else "#454555")
        e.control.scale = 1.05 if e.data == "true" else 1.0
        e.control.update()

    def toggle_sidebar(self, e):
        if self.sidebar.width == 0:
            self.sidebar.width = 260
            self.btn_toggle_sidebar.icon = ft.Icons.CHEVRON_LEFT
            self.btn_toggle_sidebar.icon_color = TEXT_SECONDARY
            # Move button to the right of sidebar
            self.toggle_btn_container.padding = ft.Padding(260 + 8, 0, 0, 0)
        else:
            self.sidebar.width = 0
            self.btn_toggle_sidebar.icon = ft.Icons.CHEVRON_RIGHT
            self.btn_toggle_sidebar.icon_color = TEXT_PRIMARY  # Darker when keeping it closed to be visible
            # Move button back to start
            self.toggle_btn_container.padding = ft.Padding(8, 0, 0, 0)

        self.sidebar.update()
        self.btn_toggle_sidebar.update()
        self.toggle_btn_container.update()

    def on_new_chat_hover(self, e):
        # Subtle scale effect or opacity change
        e.control.opacity = 0.9 if e.data == "true" else 1.0
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.update()

    async def fill_input(self, text):
        self.txt_input.value = text
        await self.txt_input.focus()
        self.page.update()

    # --- Логика Чатов ---

    async def create_new_chat(self):
        new_id = self.history_manager.create_chat()
        self.load_history_list()
        await self.load_chat(new_id)

    def load_history_list(self):
        chats = self.history_manager.get_chats()
        self.chat_list_view.controls.clear()

        for chat in chats:
            is_active = chat["id"] == self.current_chat_id

            tile = ChatItem(
                chat_data=chat,
                is_active=is_active,
                on_click_callback=lambda cid: asyncio.create_task(self.load_chat(cid)),
                on_delete_callback=self.confirm_delete_chat,
            )
            self.chat_list_view.controls.append(tile)

        self.page.update()

    async def load_chat(self, chat_id):
        self.current_chat_id = chat_id
        chat = self.history_manager.get_chat(chat_id)
        if not chat:
            return

        self.messages_list.controls.clear()

        # Приветствие если чат пустой
        if not chat["messages"]:
            # Chips generator helper
            # Пирамидка подсказок с использованием FloatingChip
            self.messages_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Stack(
                                [
                                    AnimatedOrb(),
                                    ft.Container(
                                        content=ft.Icon(
                                            icon=ft.Icons.AUTO_AWESOME,
                                            size=60,
                                            color=WHITE_COLOR,
                                        ),
                                        alignment=ft.alignment.Alignment(0, 0),
                                        width=240,
                                        height=240,
                                    ),
                                ],
                                width=240,
                                height=240,
                            ),
                            ft.Text(
                                "Корпоративный Ассистент",
                                style=ft.TextStyle(
                                    size=26,
                                    weight=ft.FontWeight.BOLD,
                                    color=WHITE_COLOR,
                                    letter_spacing=-0.5,
                                ),
                            ),
                            ft.Text(
                                "Готов к работе над задачами",
                                size=14,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(0, 80, 0, 0),
                )
            )

        for msg in chat["messages"]:
            await self.render_message(msg["text"], msg["role"], animate=False)

        self.load_history_list()  # Обновить выделение
        self.page.update()

    def confirm_delete_chat(self, chat_id):
        async def do_delete(e):
            self.delete_chat(chat_id)
            self.close_dialog(dlg)

        dlg = ft.AlertDialog(
            title=ft.Text("Удаление чата"),
            content=ft.Text("Вы уверены, что хотите удалить этот чат? Это действие необратимо."),
            actions=[
                ft.TextButton(
                    "Удалить",
                    on_click=do_delete,
                    style=ft.ButtonStyle(
                        color="#FF3B30",
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    ),
                ),
                ft.TextButton("Отмена", on_click=lambda e: self.close_dialog(dlg)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def delete_chat(self, chat_id):
        print(f"[DEBUG] delete_chat called for chat_id={chat_id}")  # Debug log

        # Delete from database
        self.history_manager.delete_chat(chat_id)

        # Get remaining chats
        remaining_chats = self.history_manager.get_chats()

        if self.current_chat_id == chat_id:
            # We deleted the current chat
            if remaining_chats:
                # Load the first available chat (async task)
                asyncio.create_task(self.load_chat(remaining_chats[0]["id"]))
            else:
                # No chats left, create a new one
                self.current_chat_id = None
                asyncio.create_task(self.create_new_chat())
        else:
            # Just refresh the list
            self.load_history_list()

        self.page.update()
        print(f"[DEBUG] delete_chat completed, remaining chats: {len(remaining_chats)}")

    async def render_message(self, text, sender, animate=True):
        is_user = sender == "user"

        # Bubble Style
        bubble = ft.Container(
            content=ft.Markdown(
                text,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme="atom-one-dark",
                on_tap_link=lambda e: self.page.launch_url(e.data),
                md_style_sheet=ft.MarkdownStyleSheet(
                    p_text_style=ft.TextStyle(
                        color=WHITE_COLOR if is_user else TEXT_PRIMARY,
                        size=15,
                        font_family="Inter",
                    ),
                ),
            ),
            padding=ft.Padding(14, 10, 14, 10),
            border_radius=20,  # Более скругленные углы (Apple style)
            # Heuristic for adaptive width
            width=600 if len(text) > 80 else None,
            bgcolor=USER_BUBBLE_COLOR if is_user else AI_BUBBLE_COLOR,
            border=ft.Border.all(1, "#448B5CF6" if is_user else "#6636364D"),
            # blur отключён для производительности
            # Entrance Animation Properties
            opacity=0 if animate else 1,
            offset=ft.Offset(0, 0.1) if animate else ft.Offset(0, 0),  # Slightly larger offset
            animate_opacity=ft.Animation(500, ft.AnimationCurve.DECELERATE),
            animate_offset=ft.Animation(500, ft.AnimationCurve.DECELERATE),
        )

        row = ft.Row(
            [bubble],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

        # Удаляем приветствие если оно есть
        if len(self.messages_list.controls) == 1:
            first_ctrl = self.messages_list.controls[0]
            if isinstance(first_ctrl, ft.Container) and isinstance(first_ctrl.content, ft.Column):
                if len(first_ctrl.content.controls) > 1:
                    self.messages_list.controls.clear()

        self.messages_list.controls.append(row)

        if animate:
            self.page.update()
            await asyncio.sleep(0.05)  # Tiny delay to ensure DOM registration
            bubble.opacity = 1
            bubble.offset = ft.Offset(0, 0)
            bubble.update()
        else:
            self.page.update()

    async def send_message(self, e):
        text = self.txt_input.value.strip()
        if not text:
            return

        self.txt_input.value = ""
        self.txt_input.disabled = True
        self.btn_send.visible = False
        self.loading_indicator.visible = True
        self.page.update()

        # 1. Сохраняем и показываем user message
        self.history_manager.add_message(self.current_chat_id, "user", text)
        await self.render_message(text, "user")
        self.load_history_list()  # Обновить заголовок чата в сайдбаре

        # 2. Запрос к API
        thinking_bubble = ft.Container(
            content=ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=TEXT_SECONDARY),
                    ft.Text("AI думает...", size=14, color=TEXT_SECONDARY, italic=True),
                ],
                spacing=10,
            ),
            padding=ft.Padding(14, 10, 14, 10),
            border_radius=20,
            bgcolor=AI_BUBBLE_COLOR,
            opacity=0,
            offset=ft.Offset(0, 0.1),
            animate_opacity=ft.Animation(400, ft.AnimationCurve.DECELERATE),
            animate_offset=ft.Animation(400, ft.AnimationCurve.DECELERATE),
        )
        thinking_row = ft.Row([thinking_bubble], alignment=ft.MainAxisAlignment.START)
        self.messages_list.controls.append(thinking_row)
        self.page.update()
        thinking_bubble.opacity = 1
        thinking_bubble.offset = ft.Offset(0, 0)
        thinking_bubble.update()

        ai_response = "..."
        ticket_offer_available = False
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                resp = await client.post(
                    f"{self.server_url}/api/chat",
                    json={
                        "query": text,
                        "limit": 10,
                        "session_id": self.session_id,
                        "user_name": self.user_name if self.user_name else None,
                        "user_login": self.user_login if self.user_login else None,
                    },
                    timeout=60.0,
                )
            if resp.status_code == 200:
                payload = resp.json()
                ai_response = payload.get("answer", "Empty response")
                ticket_offer_available = bool(payload.get("ticket_offer_available", False))
            else:
                try:
                    detail = resp.json().get("detail", str(resp.status_code))
                except Exception:
                    detail = str(resp.status_code)
                ai_response = self._get_user_friendly_error(detail)
        except Exception as ex:
            ai_response = self._get_user_friendly_error(str(ex))

        # Удаляем "AI думает..." перед показом ответа
        if thinking_row in self.messages_list.controls:
            self.messages_list.controls.remove(thinking_row)

        # 3. Сохраняем и показываем AI message
        self.history_manager.add_message(self.current_chat_id, "ai", ai_response)
        await self.render_message(ai_response, "ai")
        await self.render_resolution_controls(
            query=text,
            assistant_answer=ai_response,
            ticket_offer_available=ticket_offer_available,
        )

        self.txt_input.disabled = False
        self.loading_indicator.visible = False
        self.btn_send.visible = True
        try:
            await self.txt_input.focus()
        except Exception:
            pass
        self.page.update()

    async def render_resolution_controls(self, query: str, assistant_answer: str, ticket_offer_available: bool):
        """Показывает UX-контролы 'Помогло/Не помогло' и, при необходимости, CTA на создание заявки."""
        self.last_ai_interaction = {
            "query": query,
            "assistant_answer": assistant_answer,
        }

        helped_btn = ft.OutlinedButton("Помогло", icon=ft.Icons.CHECK, on_click=lambda e: self.mark_helped())
        not_helped_btn = ft.FilledTonalButton(
            "Не помогло",
            icon=ft.Icons.CLOSE,
            on_click=lambda e: asyncio.create_task(self.mark_not_helped(query, assistant_answer)),
        )

        controls = [helped_btn, not_helped_btn]
        if ticket_offer_available:
            create_btn = ft.FilledButton(
                "Создать заявку",
                icon=ft.Icons.ADD_TASK,
                on_click=lambda e: self.open_ticket_dialog(query, assistant_answer),
            )
            controls.append(create_btn)

        row = ft.Row(controls=controls, alignment=ft.MainAxisAlignment.START, spacing=8)
        self.messages_list.controls.append(ft.Container(content=row, padding=ft.Padding(6, 2, 6, 2)))
        self.page.update()

    def mark_helped(self):
        self.page.snack_bar = ft.SnackBar(ft.Text("Отлично. Заявка не требуется."))
        self.page.snack_bar.open = True
        self.page.update()

    async def mark_not_helped(self, query: str, assistant_answer: str):
        await self.render_message(
            "Понял. Могу создать заявку в helpdesk. Нажмите кнопку `Создать заявку` и при необходимости добавьте детали.",
            "ai",
        )
        create_btn = ft.FilledButton(
            "Создать заявку",
            icon=ft.Icons.ADD_TASK,
            on_click=lambda e: self.open_ticket_dialog(query, assistant_answer),
        )
        self.messages_list.controls.append(
            ft.Container(
                content=ft.Row([create_btn], alignment=ft.MainAxisAlignment.START),
                padding=ft.Padding(6, 2, 6, 2),
            )
        )
        self.page.update()

    def open_ticket_dialog(self, query: str, assistant_answer: str):
        """Собирает до двух уточнений перед созданием заявки."""
        extra_1 = ft.TextField(
            label="Уточнение 1 (что именно не работает)",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )
        extra_2 = ft.TextField(
            label="Уточнение 2 (когда началось/как воспроизвести)",
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        async def submit_ticket(e):
            dialog.open = False
            self.page.update()
            await self.create_ticket(
                query=query,
                assistant_answer=assistant_answer,
                extra_info_1=extra_1.value.strip(),
                extra_info_2=extra_2.value.strip(),
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Создание заявки"),
            content=ft.Column(
                controls=[
                    ft.Text("Скриншоты в текущем процессе не поддерживаются."),
                    extra_1,
                    extra_2,
                ],
                tight=True,
                width=580,
            ),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self.close_dialog(dialog)),
                ft.FilledButton("Создать", on_click=lambda e: asyncio.create_task(submit_ticket(e))),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    async def create_ticket(self, query: str, assistant_answer: str, extra_info_1: str, extra_info_2: str):
        # 1. Валидация профиля
        missing = self.validate_profile()
        if missing:
            await self.show_profile_dialog(
                reason=f"Для создания заявки необходимо заполнить обязательные поля: {', '.join(missing)}"
            )
            # После закрытия диалога проверяем снова
            if self.validate_profile():
                return  # Пользователь не заполнил данные

        thinking_bubble = ft.Container(
            content=ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=TEXT_SECONDARY),
                    ft.Text(
                        "Создаю заявку в helpdesk...",
                        size=14,
                        color=TEXT_SECONDARY,
                        italic=True,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding(14, 10, 14, 10),
            border_radius=20,
            bgcolor=AI_BUBBLE_COLOR,
        )
        thinking_row = ft.Row([thinking_bubble], alignment=ft.MainAxisAlignment.START)
        self.messages_list.controls.append(thinking_row)
        self.page.update()

        # 2. Формируем payload с данными профиля
        extra_fields = self.get_intraservice_extra_fields()

        payload = {
            "query": query,
            "assistant_answer": assistant_answer,
            "session_id": self.session_id,
            "user_name": self.user_name if self.user_name else None,
            "user_login": self.user_login if self.user_login else None,
            "extra_info_1": extra_info_1 or None,
            "extra_info_2": extra_info_2 or None,
            "extra_fields": extra_fields,
        }

        result = None
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                resp = await client.post(f"{self.server_url}/api/ticket/create", json=payload, timeout=60.0)
            if resp.status_code == 200:
                result = resp.json()
            else:
                detail = None
                try:
                    detail = resp.json().get("detail")
                except Exception:
                    detail = str(resp.status_code)
                result = {
                    "ticket_created": False,
                    "ticket_number": None,
                    "ticket_draft_saved": True,
                    "ticket_creation_reason": f"Заявка не создана, черновик сохранен ({detail})",
                }
        except Exception as ex:
            result = {
                "ticket_created": False,
                "ticket_number": None,
                "ticket_draft_saved": True,
                "ticket_creation_reason": f"Заявка не создана, черновик сохранен ({str(ex)})",
            }

        if thinking_row in self.messages_list.controls:
            self.messages_list.controls.remove(thinking_row)

        if not result.get("ticket_created", False):
            self.history_manager.save_ticket_draft(
                chat_id=self.current_chat_id,
                ad_user=self.user_name or "unknown",
                query=query,
                assistant_answer=assistant_answer,
                extra_info_1=extra_info_1,
                extra_info_2=extra_info_2,
                status="pending",
            )

        message = self._format_ticket_result_message(result)
        self.history_manager.add_message(self.current_chat_id, "ai", message)
        await self.render_message(message, "ai")
        self.page.update()

    def _format_ticket_result_message(self, result: dict) -> str:
        if result.get("ticket_created"):
            ticket_no = result.get("ticket_number", "N/A")
            suffix = ""
            if result.get("fallback_all_used"):
                suffix = "\nМаршрутизация выполнена в сервис: 11. Общие вопросы (All)."
            auth_note = f"\nAuth: {result.get('auth_scheme_used', 'n/a')} | Delegation: {result.get('delegation_status', 'n/a')}"
            trace_note = f"\nTrace: {result.get('trace_id')}" if result.get("trace_id") else ""
            return (
                f"Заявка создана в helpdesk (№ {ticket_no}).\n"
                f"Отметка: Created via AI Assistant.{suffix}{auth_note}{trace_note}"
            )
        reason = result.get("ticket_creation_reason")
        error_code = result.get("error_code")
        trace_note = f"\nTrace: {result.get('trace_id')}" if result.get("trace_id") else ""
        auth_note = (
            f"\nAuth: {result.get('auth_scheme_used', 'n/a')} | Delegation: {result.get('delegation_status', 'n/a')}"
        )
        if reason:
            if error_code:
                return f"{reason}\nКод: {error_code}{auth_note}{trace_note}"
            return f"{reason}{auth_note}{trace_note}"
        return "Заявка не создана, черновик сохранен."

    # --- Settings Dialog ---
    async def clear_ai_memory(self, e):
        try:
            # 1. Пытаемся уведомить сервер об очистке текущей сессии (опционально)
            async with httpx.AsyncClient(trust_env=False) as client:
                resp = await client.post(
                    f"{self.server_url}/api/clear_history",
                    json={"session_id": self.session_id},
                    timeout=10.0,
                )
            if resp.status_code == 200:
                self.page.snack_bar = ft.SnackBar(ft.Text("Память AI успешно очищена!"))
                self.page.snack_bar.open = True
            else:
                try:
                    detail = resp.json().get("detail", str(resp.status_code))
                except Exception:
                    detail = str(resp.status_code)
                friendly_err = self._get_user_friendly_error(detail)
                self.page.snack_bar = ft.SnackBar(ft.Text(friendly_err))
                self.page.snack_bar.open = True
        except Exception as ex:
            friendly_err = self._get_user_friendly_error(str(ex))
            self.page.snack_bar = ft.SnackBar(ft.Text(friendly_err))
            self.page.snack_bar.open = True
        self.page.update()

    def _toggle_maximize(self, e):
        self.page.window.maximized = not self.page.window.maximized
        self.page.update()

    def _minimize_window(self, e):
        self.page.window.minimized = True
        self.page.update()

    def close_dialog(self, dlg):
        dlg.open = False
        self.page.update()
        # Optional: remove from overlay after closing to clean up
        # self.page.overlay.remove(dlg)

    def open_settings(self, e):
        print("[DEBUG] open_settings called")
        url_field = ft.TextField(label="Server URL", value=self.server_url)
        name_field = ft.TextField(
            label="Ваше имя (для персонализации)",
            value=self.user_name,
            hint_text="Например: Ален",
        )

        async def save(e):
            self.server_url = url_field.value
            self.user_name = name_field.value.strip()
            self.save_config(self.server_url, self.session_id, self.user_name, self.user_login)
            self.close_dialog(dlg)
            self.page.snack_bar = ft.SnackBar(ft.Text("Настройки сохранены!"))
            self.page.snack_bar.open = True
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Настройки"),
            content=ft.Column(
                [
                    name_field,
                    ft.Text(
                        "Укажите имя, чтобы AI знал, кто вы.",
                        size=12,
                        color=TEXT_SECONDARY,
                    ),
                    ft.Container(height=10),
                    url_field,
                    ft.Container(height=10),
                    ft.FilledTonalButton(
                        "Очистить память AI",
                        icon=ft.Icons.DELETE_SWEEP,
                        on_click=self.clear_ai_memory,
                        style=ft.ButtonStyle(color="#FF3B30"),
                    ),
                    ft.Text(
                        "Это удалит контекст текущего разговора для AI на сервере.",
                        size=12,
                        color=TEXT_SECONDARY,
                    ),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Сохранить", on_click=save),
                ft.TextButton("Отмена", on_click=lambda e: self.close_dialog(dlg)),
            ],
        )
        # Using overlay direct append as fallback
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        print("[DEBUG] Dialog opened via overlay")


def main(page: ft.Page):
    TempoClient(page)


if __name__ == "__main__":
    import sys

    # Корректное определение пути к ассетам для EXE (через sys._MEIPASS) и для разработки
    if hasattr(sys, "_MEIPASS"):
        assets_dir = os.path.join(sys._MEIPASS, "assets")
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "assets")

    ft.run(main, assets_dir=assets_dir)
