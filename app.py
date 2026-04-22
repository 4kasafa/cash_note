import customtkinter as ctk
import os
from tkinter import messagebox
from constants import BG_COLOR, SIDEBAR_COLOR, BORDER_COLOR, ACCENT_COLOR, DATA_DIR
from windows_api_manager import WindowsAPIManager
from tabs.system_tab import SystemTab
from tabs.vault_tab import VaultTab
from tabs.session_tab import SessionTab
from tabs.user_tab import UserTab
from tabs.calculate_tab import CalculateTab

class CashNoteApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cash Note")
        self.geometry("400x550")
        self.resizable(True, True)
        self.minsize(400, 550)
        self.configure(fg_color=BG_COLOR)

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        # Global State
        self.current_file = None
        self.active_tab = "SYS"
        
        # Managers
        self.windows_api = WindowsAPIManager(self)

        # Main Layout
        self.setup_main_layout()
        
        # Tabs
        self.tabs = {}
        self.create_tabs()
        self.show_tab("SYS")

        # Windows API Initialization
        self.after(500, self.windows_api.init_windows_api)
        self.windows_api.start_hotkey_listener()

        # Keyboard Bindings (Global)
        self.bind_all("<Alt-s>", lambda e: self.show_tab("SYS"))
        self.bind_all("<Alt-v>", lambda e: self.show_tab("VLT"))
        self.bind_all("<Alt-a>", lambda e: self.show_tab("ACT"))
        self.bind_all("<Alt-u>", lambda e: self.show_tab("USR"))
        self.bind_all("<Alt-c>", lambda e: self.show_tab("CAL"))
        self.bind_all("<Alt-S>", lambda e: self.show_tab("SYS"))
        self.bind_all("<Alt-V>", lambda e: self.show_tab("VLT"))
        self.bind_all("<Alt-A>", lambda e: self.show_tab("ACT"))
        self.bind_all("<Alt-U>", lambda e: self.show_tab("USR"))
        self.bind_all("<Alt-C>", lambda e: self.show_tab("CAL"))

    def setup_main_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=50, fg_color=SIDEBAR_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.pack(side="left", fill="y")
        
        self.btn_sys = self.create_nav_btn("SYS", "S")
        self.btn_vlt = self.create_nav_btn("VLT", "V")
        self.btn_usr = self.create_nav_btn("USR", "U")
        self.btn_cal = self.create_nav_btn("CAL", "C")
        self.btn_act = self.create_nav_btn("ACT", "A")
        self.btn_act.pack_forget() # Hidden initially
        
        # Main Work Area
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.pack(side="top", fill="both", expand=True)

    def create_nav_btn(self, tab_id, text):
        btn = ctk.CTkButton(self.sidebar, text=text, width=40, height=40, corner_radius=0, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=0, text_color=ACCENT_COLOR, hover_color="#e5e5e5", command=lambda: self.show_tab(tab_id))
        btn.pack(pady=5)
        return btn

    def create_tabs(self):
        self.tabs["SYS"] = SystemTab(self.main_container, self)
        self.tabs["VLT"] = VaultTab(self.main_container, self)
        self.tabs["ACT"] = SessionTab(self.main_container, self)
        self.tabs["USR"] = UserTab(self.main_container, self)
        self.tabs["CAL"] = CalculateTab(self.main_container, self)

    def show_tab(self, tab_id):
        if tab_id == "ACT" and not self.current_file:
            messagebox.showwarning("Access Denied", "Please start a new session or open an existing one first.")
            return

        # Refresh visuals
        self.btn_sys.configure(fg_color=ACCENT_COLOR if tab_id == "SYS" else "transparent", text_color="white" if tab_id == "SYS" else ACCENT_COLOR)
        self.btn_vlt.configure(fg_color=ACCENT_COLOR if tab_id == "VLT" else "transparent", text_color="white" if tab_id == "VLT" else ACCENT_COLOR)
        self.btn_usr.configure(fg_color=ACCENT_COLOR if tab_id == "USR" else "transparent", text_color="white" if tab_id == "USR" else ACCENT_COLOR)
        self.btn_cal.configure(fg_color=ACCENT_COLOR if tab_id == "CAL" else "transparent", text_color="white" if tab_id == "CAL" else ACCENT_COLOR)
        self.btn_act.configure(fg_color=ACCENT_COLOR if tab_id == "ACT" else "transparent", text_color="white" if tab_id == "ACT" else ACCENT_COLOR)
        
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

    def return_focus(self):
        self.windows_api.return_focus()
