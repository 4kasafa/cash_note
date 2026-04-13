import customtkinter as ctk
import json
import os
from datetime import datetime
from tkinter import messagebox
import ctypes
from ctypes import wintypes
import threading
import time
import glob

# Elite Hacker Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# Colors (Military/Blacksite Terminal Palette)
BG_COLOR = "#050505"
SIDEBAR_COLOR = "#080808"
CONSOLE_COLOR = "#020202"
TEXT_COLOR = "#00ff00"
ACCENT_COLOR = "#004400"
CASH_COLOR = "#00ff00"
NON_CASH_COLOR = "#ffff00"
UNINPUT_COLOR = "#ff0000"
BORDER_COLOR = "#003300"
DATA_DIR = "data"

# Windows API Constants
SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
WM_HOTKEY = 0x0312

user32 = ctypes.windll.user32

class CashCounterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BLACKSITE_TERMINAL_v2.5")
        self.geometry("550x850")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        # Global State
        self.current_file = None
        self.transactions = []
        self.previous_hwnd = None
        self.my_hwnd = None
        self.active_tab = "SYS"

        # Main Layout
        self.setup_main_layout()
        
        # Tabs
        self.tabs = {}
        self.create_tabs()
        self.show_tab("SYS")

        # System Initialization
        self.log_to_console("BOOT_SEQUENCE: OK")
        self.log_to_console(f"VAULT_DIR: {DATA_DIR} [DETECTED]")
        self.log_to_console("SYSTEM_READY: WAITING_FOR_OPERATOR")

        # Windows API
        self.after(500, self.init_windows_api)
        self.start_hotkey_listener()

        # Keyboard Bindings (Global)
        self.bind_all("<Alt-s>", lambda e: self.show_tab("SYS"))
        self.bind_all("<Alt-v>", lambda e: self.show_tab("VLT"))
        self.bind_all("<Alt-a>", lambda e: self.show_tab("ACT"))
        self.bind_all("<Alt-S>", lambda e: self.show_tab("SYS"))
        self.bind_all("<Alt-V>", lambda e: self.show_tab("VLT"))
        self.bind_all("<Alt-A>", lambda e: self.show_tab("ACT"))

    def setup_main_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=60, fg_color=SIDEBAR_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.pack(side="left", fill="y")
        
        self.btn_sys = self.create_nav_btn("SYS", "[S]", "Alt+1")
        self.btn_vlt = self.create_nav_btn("VLT", "[V]", "Alt+2")
        self.btn_act = self.create_nav_btn("ACT", "[A]", "Alt+3")
        
        # Main Work Area
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.pack(side="top", fill="both", expand=True)
        
        # Bottom Console
        self.console_frame = ctk.CTkFrame(self, height=120, fg_color=CONSOLE_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.console_frame.pack(side="bottom", fill="x")
        self.console_frame.pack_propagate(False)
        
        self.console_out = ctk.CTkTextbox(self.console_frame, font=("Consolas", 10), fg_color="transparent", text_color=TEXT_COLOR, activate_scrollbars=True, corner_radius=0)
        self.console_out.pack(fill="both", expand=True, padx=5, pady=5)
        self.console_out.configure(state="disabled")

    def create_nav_btn(self, tab_id, text, shortcut):
        btn = ctk.CTkButton(self.sidebar, text=text, width=50, height=50, corner_radius=0, font=("Consolas", 14, "bold"), fg_color="transparent", border_width=0, hover_color=ACCENT_COLOR, command=lambda: self.show_tab(tab_id))
        btn.pack(pady=5)
        return btn

    def create_tabs(self):
        self.tabs["SYS"] = SystemTab(self.main_container, self)
        self.tabs["VLT"] = VaultTab(self.main_container, self)
        self.tabs["ACT"] = SessionTab(self.main_container, self)

    def show_tab(self, tab_id):
        # Refresh visuals
        self.btn_sys.configure(fg_color=ACCENT_COLOR if tab_id == "SYS" else "transparent")
        self.btn_vlt.configure(fg_color=ACCENT_COLOR if tab_id == "VLT" else "transparent")
        self.btn_act.configure(fg_color=ACCENT_COLOR if tab_id == "ACT" else "transparent")
        
        # Hide current
        for tab in self.tabs.values():
            tab.pack_forget()
        
        # Show new
        self.tabs[tab_id].pack(fill="both", expand=True)
        self.active_tab = tab_id
        self.log_to_console(f"ACCESSING_SECTOR: {tab_id}")
        
        if tab_id == "VLT":
            self.tabs["VLT"].refresh_vault_list()
        elif tab_id == "ACT":
            if not self.current_file:
                self.log_to_console("> WARNING: NO_ACTIVE_SESSION_FOUND")
                # Optional: force redirect or keep blank
            else:
                self.tabs["ACT"].on_activate()

    def log_to_console(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.console_out.configure(state="normal")
        self.console_out.insert("end", f"{timestamp} {msg}\n")
        self.console_out.see("end")
        self.console_out.configure(state="disabled")

    # Windows API Logic
    def init_windows_api(self):
        self.my_hwnd = user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(100)
        user32.GetWindowTextW(self.my_hwnd, buf, 100)
        if "BLACKSITE" not in buf.value:
            self.my_hwnd = user32.FindWindowW(None, "BLACKSITE_TERMINAL_v2.5")

    def start_hotkey_listener(self):
        def listen():
            user32.RegisterHotKey(None, 1, 0, 0x7B) 
            user32.RegisterHotKey(None, 2, 0, 0x79) 
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    self.after(0, self.focus_app)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def focus_app(self):
        current = user32.GetForegroundWindow()
        if self.my_hwnd and current != self.my_hwnd:
            self.previous_hwnd = current
            user32.ShowWindow(self.my_hwnd, SW_RESTORE)
            user32.SetWindowPos(self.my_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            user32.SetWindowPos(self.my_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            user32.SetForegroundWindow(self.my_hwnd)
            if self.active_tab == "ACT":
                self.tabs["ACT"].entry_amount.focus_force()

    def return_focus(self):
        if self.previous_hwnd:
            def task():
                user32.SetForegroundWindow(self.previous_hwnd)
                self.previous_hwnd = None
            self.after(200, task)

class SystemTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        
        # ASCII Art
        self.ascii_label = ctk.CTkLabel(self, text="""
██████╗ ██╗      █████╗  ██████╗██╗  ██╗███████╗██╗████████╗███████╗
██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██╔════╝██║╚══██╔══╝██╔════╝
██████╔╝██║     ███████║██║     █████╔╝ ███████╗██║   ██║   █████╗  
██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ╚════██║██║   ██║   ██╔══╝  
██████╔╝███████╗██║  ██║╚██████╗██║  ██╗███████║██║   ██║   ███████╗
╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝   ╚══════╝
        """, font=("Consolas", 6), text_color=TEXT_COLOR)
        self.ascii_label.pack(pady=(40, 20))

        self.title_label = ctk.CTkLabel(self, text="> [OPERATOR_MAIN_MENU]", font=("Consolas", 20, "bold"), text_color=TEXT_COLOR)
        self.title_label.pack(pady=10)

        # Stats Section
        self.stats_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.stats_frame.pack(fill="x", padx=50, pady=20)
        
        self.add_stat("SECTOR_HEALTH", "STABLE")
        self.add_stat("ENCRYPTION", "AES-256")
        self.add_stat("STORAGE_LINK", "ACTIVE")
        self.add_stat("TERMINAL_Uptime", f"{datetime.now().strftime('%d-%m-%Y %H:%M')}")

        # Action Prompt
        self.btn_new = ctk.CTkButton(self, text="[ INITIALIZE_NEW_SESSION ]", font=("Consolas", 16, "bold"), height=60, fg_color=ACCENT_COLOR, border_width=1, border_color=TEXT_COLOR, corner_radius=0, command=self.init_session)
        self.btn_new.pack(fill="x", padx=50, pady=10)
        
        ctk.CTkLabel(self, text="> PRESS [SPACE] TO INITIALIZE", font=("Consolas", 10), text_color="#006600").pack()

    def add_stat(self, key, val):
        f = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(f, text=f"{key}:", font=("Consolas", 10, "bold"), text_color=TEXT_COLOR).pack(side="left")
        ctk.CTkLabel(f, text=val, font=("Consolas", 10), text_color=TEXT_COLOR).pack(side="right")

    def init_session(self):
        today = datetime.now().strftime("%d_%m_%Y")
        file_path = os.path.join(DATA_DIR, f"data_{today}.json")
        self.controller.current_file = file_path
        self.controller.tabs["ACT"].file_path = file_path
        self.controller.tabs["ACT"].load_session()
        self.controller.show_tab("ACT")
        self.controller.log_to_console(f"NEW_SESSION_STARTED: {os.path.basename(file_path)}")

class VaultTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        self.selected_files = set()
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="> [STORAGE_VAULT_EXPLORER]", font=("Consolas", 18, "bold"), text_color=TEXT_COLOR).pack(pady=10)
        
        self.search_entry = ctk.CTkEntry(self, placeholder_text="FILTER_BY_ID (DD_MM_YYYY)...", font=("Consolas", 12), fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, text_color=TEXT_COLOR, corner_radius=0)
        self.search_entry.pack(fill="x", padx=20, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_vault_list())

        self.scroll_vault = ctk.CTkScrollableFrame(self, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0, label_text="ARCHIVED_DATA_LOGS", label_font=("Consolas", 12), label_text_color=TEXT_COLOR)
        self.scroll_vault.pack(fill="both", expand=True, padx=20, pady=5)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_delete = ctk.CTkButton(self.btn_frame, text="TERMINATE_RECORDS", fg_color="#330000", text_color=UNINPUT_COLOR, border_width=1, border_color=UNINPUT_COLOR, corner_radius=0, font=("Consolas", 12), command=self.delete_selected)
        self.btn_delete.pack(side="left", expand=True, padx=5)
        
        self.btn_open = ctk.CTkButton(self.btn_frame, text="DECRYPT_&_MOUNT", fg_color=ACCENT_COLOR, text_color=TEXT_COLOR, border_width=1, border_color=TEXT_COLOR, corner_radius=0, font=("Consolas", 12), command=self.open_selected)
        self.btn_open.pack(side="right", expand=True, padx=5)

    def refresh_vault_list(self):
        for widget in self.scroll_vault.winfo_children():
            widget.destroy()
        
        query = self.search_entry.get().lower()
        files = glob.glob(os.path.join(DATA_DIR, "data_*.json"))
        files.sort(reverse=True)
        
        self.selected_files.clear()
        
        for f in files:
            fname = os.path.basename(f)
            if query and query not in fname: continue
            
            try:
                with open(f, "r") as jf:
                    data = json.load(jf)
                    total = sum(t["amount"] for t in data)
                    count = len(data)
            except: total, count = 0, 0

            item = ctk.CTkFrame(self.scroll_vault, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
            item.pack(fill="x", pady=2, padx=2)
            
            cb = ctk.CTkCheckBox(item, text="", width=20, checkbox_width=16, checkbox_height=16, corner_radius=0, command=lambda p=f: self.toggle_selection(p))
            cb.pack(side="left", padx=10)
            
            info = ctk.CTkButton(item, text=f"{fname} | Rp {total:,} | [ENTRIES: {count}]".replace(",", "."), font=("Consolas", 11), fg_color="transparent", text_color="#aaaaaa", hover_color=ACCENT_COLOR, anchor="w", corner_radius=0, command=lambda p=f: self.mount_file(p))
            info.pack(side="left", fill="both", expand=True)

    def toggle_selection(self, path):
        if path in self.selected_files: self.selected_files.remove(path)
        else: self.selected_files.add(path)

    def delete_selected(self):
        if not self.selected_files: return
        if messagebox.askyesno("TERMINAL_AUTH", f"PURGE {len(self.selected_files)} DATA_RECORDS?"):
            for f in self.selected_files:
                try: os.remove(f)
                except: pass
            self.controller.log_to_console(f"VAULT_CLEANUP: {len(self.selected_files)} RECORDS_PURGED")
            self.refresh_vault_list()

    def open_selected(self):
        if len(self.selected_files) != 1: return
        self.mount_file(list(self.selected_files)[0])

    def mount_file(self, path):
        self.controller.current_file = path
        self.controller.tabs["ACT"].file_path = path
        self.controller.tabs["ACT"].load_session()
        self.controller.show_tab("ACT")
        self.controller.log_to_console(f"MOUNTED_VAULT: {os.path.basename(path)}")

class SessionTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        self.file_path = None
        self.transactions = []
        self.current_filter = "All"
        self.editing_index = None
        self.setup_ui()

    def setup_ui(self):
        # Header Info
        self.header_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_COLOR, height=40, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.header_frame.pack_propagate(False)
        
        self.lbl_session = ctk.CTkLabel(self.header_frame, text="> ACTIVE_SESSION: NONE", font=("Consolas", 10, "bold"), text_color=TEXT_COLOR)
        self.lbl_session.pack(side="left", padx=10)
        
        self.lbl_count = ctk.CTkLabel(self.header_frame, text="RECORDS: 0", font=("Consolas", 10), text_color="#006600")
        self.lbl_count.pack(side="right", padx=10)

        # Main Input
        self.input_area = ctk.CTkFrame(self, fg_color="transparent")
        self.input_area.pack(fill="x", padx=20, pady=10)
        
        self.entry_amount = ctk.CTkEntry(self.input_area, placeholder_text="AWAITING_INPUT...", height=60, font=("Consolas", 32), justify="center", fg_color=CONSOLE_COLOR, border_color=TEXT_COLOR, text_color=TEXT_COLOR, corner_radius=0)
        self.entry_amount.pack(fill="x", pady=(0, 10))
        self.entry_amount.bind("<KeyRelease>", self.format_currency)
        self.entry_amount.bind("<Return>", lambda e: self.btn_cash.focus())
        
        self.btn_grid = ctk.CTkFrame(self.input_area, fg_color="transparent")
        self.btn_grid.pack(fill="x")
        
        self.btn_cash = self.create_input_btn(self.btn_grid, "CASH", CASH_COLOR, "#003300", "Cash")
        self.btn_non = self.create_input_btn(self.btn_grid, "NON_CASH", NON_CASH_COLOR, "#333300", "Non Cash")
        self.btn_unin = self.create_input_btn(self.btn_grid, "UNINPUT", UNINPUT_COLOR, "#330000", "Uninput")

        # Edit Controls
        self.edit_frame = ctk.CTkFrame(self.input_area, fg_color="transparent")
        self.btn_commit = ctk.CTkButton(self.edit_frame, text="[ COMMIT_CHANGES ]", fg_color="#000033", text_color="#3399ff", border_width=1, border_color="#3399ff", corner_radius=0, font=("Consolas", 12, "bold"), command=self.save_edit)
        self.btn_commit.pack(side="left", expand=True, padx=2, fill="x")
        ctk.CTkButton(self.edit_frame, text="[ ABORT ]", fg_color="#1a1a1a", text_color="gray", corner_radius=0, font=("Consolas", 12), command=self.cancel_edit, width=80).pack(side="left", padx=2)

        # Filter Section
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=20, pady=(5, 0))
        
        self.btn_filter_all = self.create_filter_btn("ALL", "All")
        self.btn_filter_cash = self.create_filter_btn("CASH", "Cash")
        self.btn_filter_non = self.create_filter_btn("NON_C", "Non Cash")
        self.btn_filter_unin = self.create_filter_btn("UNIN", "Uninput")

        # Log & Total
        self.scroll_log = ctk.CTkScrollableFrame(self, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0, label_text="TRANSACTION_BUFFER", label_font=("Consolas", 12), label_text_color=TEXT_COLOR)
        self.scroll_log.pack(fill="both", expand=True, padx=20, pady=5)

        self.footer = ctk.CTkFrame(self, height=70, fg_color=SIDEBAR_COLOR, border_width=1, border_color=TEXT_COLOR, corner_radius=0)
        self.footer.pack(fill="x", side="bottom")
        self.lbl_total = ctk.CTkLabel(self.footer, text="BUFFER_TOTAL: Rp 0", font=("Consolas", 20, "bold"), text_color=TEXT_COLOR)
        self.lbl_total.pack(pady=15)

    def create_filter_btn(self, text, cat):
        btn = ctk.CTkButton(self.filter_frame, text=text, width=60, height=25, font=("Consolas", 10), corner_radius=0, command=lambda: self.set_filter(cat))
        btn.pack(side="left", padx=2)
        return btn

    def create_input_btn(self, parent, text, color, bg, cat):
        btn = ctk.CTkButton(parent, text=text, fg_color=bg, hover_color=color, font=("Consolas", 12, "bold"), text_color=color, border_width=1, border_color=color, corner_radius=0, command=lambda: self.add_transaction(cat))
        btn.pack(side="left", expand=True, padx=2)
        
        # Enhanced Focus Visuals
        def on_focus(e):
            btn.configure(border_width=3, border_color=TEXT_COLOR)
        def on_unfocus(e):
            btn.configure(border_width=1, border_color=color)
            
        btn.bind("<FocusIn>", on_focus)
        btn.bind("<FocusOut>", on_unfocus)
        btn.bind("<Return>", lambda e: self.add_transaction(cat))
        btn.bind("<KP_Enter>", lambda e: self.add_transaction(cat)) # Numpad Enter support
        return btn

    def set_filter(self, cat):
        self.current_filter = cat
        self.refresh_list()
        self.update_filter_visuals()

    def update_filter_visuals(self):
        btns = {"All": self.btn_filter_all, "Cash": self.btn_filter_cash, "Non Cash": self.btn_filter_non, "Uninput": self.btn_filter_unin}
        for cat, btn in btns.items():
            is_active = cat == self.current_filter
            btn.configure(fg_color=ACCENT_COLOR if is_active else "transparent", border_width=1 if is_active else 0, border_color=TEXT_COLOR)

    def on_activate(self):
        self.entry_amount.focus_set()
        if self.file_path:
            self.lbl_session.configure(text=f"> ACTIVE_SESSION: {os.path.basename(self.file_path)}")
        self.update_filter_visuals()
            
    def load_session(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f: self.transactions = json.load(f)
        else: self.transactions = []
        self.refresh_list()
        self.update_filter_visuals()

    def save_session(self):
        with open(self.file_path, "w") as f: json.dump(self.transactions, f, indent=4)
            
    def format_currency(self, event=None):
        # Allow Tab to pass through without re-formatting
        if event and event.keysym == "Tab":
            return
            
        val = self.entry_amount.get().replace(".", "")
        if not val.isdigit() and val != "": val = "".join(filter(str.isdigit, val))
        if val == "": self.entry_amount.delete(0, "end"); return
        formatted = "{:,}".format(int(val)).replace(",", ".")
        self.entry_amount.delete(0, "end"); self.entry_amount.insert(0, formatted)

    def add_transaction(self, cat):
        val_str = self.entry_amount.get().replace(".", "")
        if not val_str: return
        self.transactions.append({
            "amount": int(val_str),
            "category": cat,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_session()
        self.controller.log_to_console(f"RECORD_ADDED: Rp {int(val_str):,} -> [{cat}]".replace(",", "."))
        self.entry_amount.delete(0, "end")
        self.refresh_list()
        self.controller.return_focus()
        self.entry_amount.focus()

    def delete_transaction(self, idx):
        if messagebox.askyesno("TERMINAL_AUTH", "PURGE_ENTRY?"):
            self.transactions.pop(idx)
            self.save_session()
            self.refresh_list()
            self.controller.log_to_console("RECORD_PURGED")

    def edit_transaction(self, idx):
        self.editing_index = idx
        item = self.transactions[idx]
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, f"{item['amount']:,}".replace(",", "."))
        self.btn_grid.pack_forget()
        self.edit_frame.pack(fill="x")
        self.entry_amount.focus()

    def save_edit(self):
        val = self.entry_amount.get().replace(".", "")
        if val:
            self.transactions[self.editing_index]["amount"] = int(val)
            self.save_session()
            self.controller.log_to_console(f"RECORD_MODIFIED: IDX_{self.editing_index}")
            self.cancel_edit()
            self.refresh_list()

    def cancel_edit(self):
        self.editing_index = None
        self.entry_amount.delete(0, "end")
        self.edit_frame.pack_forget()
        self.btn_grid.pack(fill="x")

    def refresh_list(self):
        for w in self.scroll_log.winfo_children(): w.destroy()
        total = 0
        
        # Filtering logic
        indexed_data = list(enumerate(self.transactions))
        filtered_data = [(i, t) for i, t in indexed_data if self.current_filter == "All" or t["category"] == self.current_filter]
        
        for idx, item in reversed(filtered_data):
            color = {"Cash": CASH_COLOR, "Non Cash": NON_CASH_COLOR, "Uninput": UNINPUT_COLOR}.get(item["category"], TEXT_COLOR)
            
            row = ctk.CTkFrame(self.scroll_log, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
            row.pack(fill="x", pady=2, padx=2)
            
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            lbl_val = ctk.CTkLabel(info_frame, text=f"Rp {item['amount']:,} | {item['category']}".replace(",", "."), font=("Consolas", 12, "bold"), text_color=color, anchor="w")
            lbl_val.pack(fill="x")
            
            lbl_ts = ctk.CTkLabel(info_frame, text=f"TS: {item['timestamp']}", font=("Consolas", 9), text_color="#006600", anchor="w")
            lbl_ts.pack(fill="x")
            
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=5)
            ctk.CTkButton(btns, text="MOD", width=40, height=20, corner_radius=0, font=("Consolas", 9), command=lambda x=idx: self.edit_transaction(x)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="DEL", width=40, height=20, corner_radius=0, font=("Consolas", 9), hover_color=UNINPUT_COLOR, command=lambda x=idx: self.delete_transaction(x)).pack(side="left", padx=2)
            
            total += item["amount"]
        
        self.lbl_total.configure(text=f"BUFFER_TOTAL: Rp {total:,}".replace(",", "."))
        self.lbl_count.configure(text=f"RECORDS: {len(self.transactions)}")
        self.lbl_count.configure(text=f"RECORDS: {len(self.transactions)}")

if __name__ == "__main__":
    app = CashCounterApp()
    app.mainloop()
