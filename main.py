from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
import asyncio, websockets, json, threading, os

# ============ НАСТРОЙКИ ============
SERVER = "wss://nexopraim-server.onrender.com"
ROOM   = "general"
# ===================================

STORE = JsonStore(os.path.expanduser("~/.nexopraim.json"))

KV = """
<LoginScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(16)
        Widget:
        MDLabel:
            text: "Nexopraim"
            halign: "center"
            font_style: "H3"
            theme_text_color: "Primary"
        MDLabel:
            text: "Введите ваше имя"
            halign: "center"
            theme_text_color: "Hint"
        MDTextField:
            id: name_input
            hint_text: "Имя"
            mode: "rectangle"
        MDRaisedButton:
            text: "ВОЙТИ"
            pos_hint: {"center_x": 0.5}
            on_release: app.do_login()
        Widget:

<ChatScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Nexopraim"
            elevation: 4
            right_action_items: [["cog", lambda x: app.open_settings()]]
        ScrollView:
            id: scroll
            MDBoxLayout:
                id: msg_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(8)
                spacing: dp(6)
        MDBoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(4)
            spacing: dp(4)
            MDTextField:
                id: inp
                hint_text: "Сообщение..."
                on_text_validate: app.send_msg()
            MDIconButton:
                icon: "send"
                on_release: app.send_msg()
"""


class LoginScreen(MDScreen):
    pass


class ChatScreen(MDScreen):
    pass


class NexopraimApp(MDApp):
    def build(self):
        self.title = "Nexopraim"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"
        self.loop = asyncio.new_event_loop()
        self.ws = None
        self.user = "guest"
        self.running = False
        Builder.load_string(KV)
        self.sm = MDScreenManager()
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(ChatScreen(name="chat"))
        return self.sm

    def on_start(self):
        if STORE.exists("user") and STORE.get("user")["name"]:
            self.user = STORE.get("user")["name"]
            self.sm.current = "chat"
            self.start_connection()

    def do_login(self):
        name = self.sm.get_screen("login").ids.name_input.text.strip()
        if not name:
            return
        self.user = name
        STORE.put("user", name=name)
        self.sm.current = "chat"
        self.start_connection()

    def open_settings(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        self.dialog_input = MDTextField(text=self.user, hint_text="Новое имя")
        self.dialog = MDDialog(
            title="Сменить имя",
            type="custom",
            content_cls=self.dialog_input,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="СОХРАНИТЬ", on_release=lambda x: self.save_name()),
            ],
        )
        self.dialog.open()

    def save_name(self):
        new_name = self.dialog_input.text.strip()
        if new_name:
            self.user = new_name
            STORE.put("user", name=new_name)
            self.dialog.dismiss()
            self.add_system(f"Имя изменено на {new_name}. Перезапусти приложение.")

    def start_connection(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    async def connect(self):
        url = f"{SERVER}/ws/{ROOM}/{self.user}"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    Clock.schedule_once(lambda dt: self.add_system("подключено"))
                    async for raw in ws:
                        data = json.loads(raw)
                        Clock.schedule_once(
                    xx        lambda dt, d=data: self.add_bubble(d["user"], d["text"], d["user"] == self.user)
                        )
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self.add_system(f"ошибка: {err}"))
                await asyncio.sleep(3)

    def add_bubble(self, user, text, mine=False):
        chat = self.sm.get_screen("chat")
        root = chat.ids.msg_box
        color = "Primary" if mine else "Secondary"
        lbl = MDLabel(
            text=f"[b]{user}[/b]\n{text}",
            markup=True,
            size_hint_y=None,
            height=dp(60),
            halign="right" if mine else "left",
            theme_text_color=color,
        )
        lbl.bind(texture_size=lbl.setter("size"))
        root.add_widget(lbl)
        Clock.schedule_once(lambda dt: setattr(chat.ids.scroll, "scroll_y", 0), 0.1)

    def add_system(self, text):
        chat = self.sm.get_screen("chat")
        lbl = MDLabel(
            text=f"[i]{text}[/i]",
            markup=True,
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Hint",
            halign="center",
        )
        chat.ids.msg_box.add_widget(lbl)

    def send_msg(self):
        chat = self.sm.get_screen("chat")
        inp = chat.ids.inp
        text = inp.text.strip()
        if not text:
            return
        if not self.ws:
            self.add_system("нет соединения")
            return
        asyncio.run_coroutine_threadsafe(
            self.ws.send(json.dumps({"text": text})), self.loop
        )
        inp.text = ""


NexopraimApp().run()
