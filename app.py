import customtkinter as ctk
import os
from tkinter import messagebox
from constants import BG_COLOR, BORDER_COLOR, ACCENT_COLOR, DATA_DIR
from windows_api_manager import WindowsAPIManager
from tabs.vault_tab import VaultTab
from tabs.session_tab import SessionTab
from tabs.user_tab import UserTab
from tabs.calculate_tab import CalculateTab
from tabs.modal_tab import ModalTab
from tabs.kasir_tab import KasirTab

class CashNoteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.max_content_width = 820

        self.title("Cash Note")
        self.geometry("400x550")
        self.resizable(True, True)
        self.minsize(400, 550)
        self.configure(fg_color=BG_COLOR)

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        # Global State
        self.current_file = None
        self.active_tab = "CAL"

        # Managers
        self.windows_api = WindowsAPIManager(self)

        # Main Layout
        self.setup_main_layout()

        # Tabs
        self.tabs = {}
        self.create_tabs()
        self.show_tab("CAL")

        # Windows API Initialization
        self.after(500, self.windows_api.init_windows_api)
        self.windows_api.start_hotkey_listener()

        # Keyboard Bindings (Global)
        self.bind_all("<Alt-v>", lambda e: self.show_tab("VLT"))
        self.bind_all("<Alt-a>", lambda e: self.show_tab("ACT"))
        self.bind_all("<Alt-u>", lambda e: self.show_tab("USR"))
        self.bind_all("<Alt-c>", lambda e: self.show_tab("CAL"))
        self.bind_all("<Alt-m>", lambda e: self.show_tab("MOD"))
        self.bind_all("<Alt-k>", lambda e: self.show_tab("KSR"))
        self.bind_all("<Alt-V>", lambda e: self.show_tab("VLT"))
        self.bind_all("<Alt-A>", lambda e: self.show_tab("ACT"))
        self.bind_all("<Alt-U>", lambda e: self.show_tab("USR"))
        self.bind_all("<Alt-C>", lambda e: self.show_tab("CAL"))
        self.bind_all("<Alt-M>", lambda e: self.show_tab("MOD"))
        self.bind_all("<Alt-K>", lambda e: self.show_tab("KSR"))
        self.bind_all("<Escape>", self.handle_escape)
        self.main_container.bind("<Configure>", self.update_content_width)
        self.after(0, self.update_content_width)

    def setup_main_layout(self):
        # Main Work Area
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.pack(side="top", fill="both", expand=True)
        self.content_shell = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        self.content_shell.place(relx=0.5, rely=0, anchor="n")

    def create_tabs(self):
        self.tabs["VLT"] = VaultTab(self.content_shell, self)
        self.tabs["ACT"] = SessionTab(self.content_shell, self)
        self.tabs["USR"] = UserTab(self.content_shell, self)
        self.tabs["CAL"] = CalculateTab(self.content_shell, self)
        self.tabs["MOD"] = ModalTab(self.content_shell, self)
        self.tabs["KSR"] = KasirTab(self.content_shell, self)

    def show_tab(self, tab_id):
        if tab_id == "ACT" and not self.current_file:
            messagebox.showwarning("Akses Ditolak", "Silakan mulai sesi baru atau buka sesi yang sudah ada terlebih dahulu.")
            return

        # Hide current
        for tab in self.tabs.values():
            tab.pack_forget()

        # Show new
        self.tabs[tab_id].pack(fill="both", expand=True)
        self.active_tab = tab_id

        if tab_id == "VLT":
            self.tabs["VLT"].refresh_vault_list()
        elif tab_id == "ACT":
            self.tabs["ACT"].on_activate()
        elif tab_id == "CAL":
            self.tabs["CAL"].on_activate()
        elif tab_id == "USR":
            self.tabs["USR"].on_activate()
        elif tab_id == "MOD":
            self.tabs["MOD"].on_activate()
        elif tab_id == "KSR":
            self.tabs["KSR"].on_activate()

    def handle_escape(self, event=None):
        if self.active_tab == "USR":
            usr_tab = self.tabs.get("USR")
            if usr_tab and usr_tab.form_view.winfo_ismapped():
                usr_tab.show_list_view()
            else:
                self.show_tab("CAL")
        elif self.active_tab == "CAL":
            cal_tab = self.tabs.get("CAL")
            if cal_tab and cal_tab.preview_view.winfo_ismapped():
                cal_tab.show_input_view()
        elif self.active_tab == "KSR":
            self.show_tab("CAL")

    def update_content_width(self, event=None):
        width = min(self.main_container.winfo_width(), self.max_content_width)
        height = self.main_container.winfo_height()
        if width <= 1 or height <= 1:
            return
        self.content_shell.place_configure(width=width, height=height)

    def return_focus(self):
        self.windows_api.return_focus()
