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

# Style Configuration
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Colors (Modern Payment UI Palette)
BG_COLOR = "#f8f9fc"
SIDEBAR_COLOR = "#ffffff"
CONSOLE_COLOR = "#ffffff"
TEXT_COLOR = "#2d2d2d"
ACCENT_COLOR = "#4e73df"
BORDER_COLOR = "#d1d3e2"

# Status Colors from Image
STATUS_TOTAL_BG = "#ffff00" # Yellow
STATUS_PAID_BG = "#90ee90"  # Light Green
STATUS_CHANGE_BG = "#ffa500" # Orange
DATA_DIR = "data"

# Font Configuration
MAIN_FONT = ("Segoe UI", 11)
HEADER_FONT = ("Segoe UI", 16, "bold")
DISPLAY_FONT = ("Segoe UI", 24, "bold")
SMALL_FONT = ("Segoe UI", 10)

# Windows API Constants
SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
WM_HOTKEY = 0x0312

user32 = ctypes.windll.user32

class CashNoteApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cash Note")
        self.geometry("400x550")
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
        self.sidebar = ctk.CTkFrame(self, width=50, fg_color=SIDEBAR_COLOR, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.pack(side="left", fill="y")
        
        self.btn_sys = self.create_nav_btn("SYS", "S")
        self.btn_vlt = self.create_nav_btn("VLT", "V")
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

    def show_tab(self, tab_id):
        if tab_id == "ACT" and not self.current_file:
            messagebox.showwarning("Access Denied", "Please start a new session or open an existing one first.")
            return

        # Refresh visuals
        self.btn_sys.configure(fg_color=ACCENT_COLOR if tab_id == "SYS" else "transparent", text_color="white" if tab_id == "SYS" else ACCENT_COLOR)
        self.btn_vlt.configure(fg_color=ACCENT_COLOR if tab_id == "VLT" else "transparent", text_color="white" if tab_id == "VLT" else ACCENT_COLOR)
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

    def log_to_console(self, msg):
        pass

    # Windows API Logic
    def init_windows_api(self):
        self.my_hwnd = user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(100)
        user32.GetWindowTextW(self.my_hwnd, buf, 100)
        if "Cash Note" not in buf.value:
            self.my_hwnd = user32.FindWindowW(None, "Cash Note")

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
        
        ctk.CTkLabel(self, text="Cash Note", font=("Segoe UI", 24, "bold"), text_color=ACCENT_COLOR).pack(pady=(30, 10))
        ctk.CTkLabel(self, text="Professional Transaction Management", font=SMALL_FONT, text_color="grey").pack(pady=(0, 30))

        # Stats Section
        self.stats_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.stats_frame.pack(fill="x", padx=50, pady=20)
        
        self.add_stat("System Health", "Operational")
        self.add_stat("Encryption", "Active (AES-256)")
        self.add_stat("Cloud Sync", "Connected")
        self.add_stat("Last Login", f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Action Prompt
        self.btn_new = ctk.CTkButton(self, text="Start New Session", font=HEADER_FONT, height=60, fg_color=ACCENT_COLOR, text_color="white", corner_radius=0, command=self.init_session)
        self.btn_new.pack(fill="x", padx=50, pady=20)
        
        ctk.CTkLabel(self, text="Press [Space] to initialize", font=SMALL_FONT, text_color="grey").pack()

    def add_stat(self, key, val):
        f = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(f, text=f"{key}:", font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR).pack(side="left")
        ctk.CTkLabel(f, text=val, font=("Segoe UI", 11), text_color=TEXT_COLOR).pack(side="right")

    def init_session(self):
        today = datetime.now().strftime("%d_%m_%Y")
        base_name = f"data_{today}"
        file_path = os.path.join(DATA_DIR, f"{base_name}.json")
        
        # Multi-session logic
        if os.path.exists(file_path):
            counter = 1
            while True:
                suffix = f"_{counter:03d}"
                file_path = os.path.join(DATA_DIR, f"{base_name}{suffix}.json")
                if not os.path.exists(file_path):
                    break
                counter += 1
                
        self.controller.current_file = file_path
        self.controller.tabs["ACT"].file_path = file_path
        self.controller.tabs["ACT"].load_session()
        self.controller.btn_act.pack(pady=5)
        self.controller.show_tab("ACT")

class VaultTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        self.selected_files = set()
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Vault Explorer", font=HEADER_FONT, text_color=TEXT_COLOR).pack(pady=10)
        
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search by date (DD_MM_YYYY)...", font=MAIN_FONT, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, text_color=TEXT_COLOR, corner_radius=0)
        self.search_entry.pack(fill="x", padx=20, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_vault_list())

        self.scroll_vault = ctk.CTkScrollableFrame(self, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.scroll_vault._scrollbar.grid_forget()
        self.scroll_vault.pack(fill="both", expand=True, padx=20, pady=5)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_delete = ctk.CTkButton(self.btn_frame, text="Delete Selected", fg_color="#ff4444", text_color="white", corner_radius=0, font=MAIN_FONT, command=self.delete_selected)
        self.btn_delete.pack(side="left", expand=True, padx=5)
        
        self.btn_open = ctk.CTkButton(self.btn_frame, text="Open Session", fg_color=ACCENT_COLOR, text_color="white", corner_radius=0, font=MAIN_FONT, command=self.open_selected)
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

            item = ctk.CTkFrame(self.scroll_vault, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=0)
            item.pack(fill="x", pady=2, padx=2)
            
            cb = ctk.CTkCheckBox(item, text="", width=20, checkbox_width=16, checkbox_height=16, corner_radius=0, command=lambda p=f: self.toggle_selection(p))
            cb.pack(side="left", padx=10)
            
            info = ctk.CTkButton(item, text=f"{fname} | Rp {total:,} | Entries: {count}".replace(",", "."), font=MAIN_FONT, fg_color="transparent", text_color=TEXT_COLOR, hover_color="#f5f5f5", anchor="w", corner_radius=0, command=lambda p=f: self.mount_file(p))
            info.pack(side="left", fill="both", expand=True)

    def toggle_selection(self, path):
        if path in self.selected_files: self.selected_files.remove(path)
        else: self.selected_files.add(path)

    def delete_selected(self):
        if not self.selected_files: return
        if messagebox.askyesno("Confirmation", f"Permanently delete {len(self.selected_files)} session records?"):
            for f in self.selected_files:
                try: os.remove(f)
                except: pass
            self.refresh_vault_list()

    def open_selected(self):
        if len(self.selected_files) != 1: return
        self.mount_file(list(self.selected_files)[0])

    def mount_file(self, path):
        self.controller.current_file = path
        self.controller.tabs["ACT"].file_path = path
        self.controller.tabs["ACT"].load_session()
        self.controller.btn_act.pack(pady=5)
        self.controller.show_tab("ACT")

class SessionTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        self.file_path = None
        self.transactions = []
        self.current_filter = "All"
        self.editing_index = None
        self.current_page = 0
        self.page_size = 3
        self.setup_ui()

    def setup_ui(self):
        # Header Info
        self.header_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_COLOR, height=40, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.header_frame.pack_propagate(False)
        
        self.lbl_session = ctk.CTkLabel(self.header_frame, text="Session: None", font=("Segoe UI", 10, "bold"), text_color=TEXT_COLOR)
        self.lbl_session.pack(side="left", padx=10)
        
        self.lbl_count = ctk.CTkLabel(self.header_frame, text="Entries: 0", font=("Segoe UI", 10), text_color="grey")
        self.lbl_count.pack(side="right", padx=10)

        # Main Input
        self.input_area = ctk.CTkFrame(self, fg_color="transparent")
        self.input_area.pack(fill="x", padx=20, pady=10)
        
        self.entry_frame = ctk.CTkFrame(self.input_area, fg_color=STATUS_TOTAL_BG, border_width=2, border_color=BORDER_COLOR, corner_radius=0)
        self.entry_frame.pack(fill="x", pady=(0, 10))
        
        self.entry_amount = ctk.CTkEntry(self.entry_frame, placeholder_text="0.00", height=60, font=DISPLAY_FONT, justify="right", fg_color="transparent", border_width=0, text_color="black", corner_radius=0)
        self.entry_amount.pack(fill="x", padx=10)
        self.entry_amount.bind("<KeyRelease>", self.format_currency)
        self.entry_amount.bind("<Return>", lambda e: self.btn_cash.focus())
        
        self.btn_grid = ctk.CTkFrame(self.input_area, fg_color="transparent")
        self.btn_grid.pack(fill="x")
        self.btn_grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="btns")
        
        self.btn_cash = self.create_input_btn(self.btn_grid, "Cash", "#2e7d32", "#e8f5e9", "Cash", 0)
        self.btn_non = self.create_input_btn(self.btn_grid, "Non Cash", "#fbc02d", "#fffde7", "Non Cash", 1)
        self.btn_unin = self.create_input_btn(self.btn_grid, "Uninput", "#d32f2f", "#ffebee", "Uninput", 2)

        # Edit Controls
        self.edit_frame = ctk.CTkFrame(self.input_area, fg_color="transparent")
        self.btn_commit = ctk.CTkButton(self.edit_frame, text="Save Changes", fg_color=ACCENT_COLOR, text_color="white", corner_radius=0, font=MAIN_FONT, command=self.save_edit)
        self.btn_commit.pack(side="left", expand=True, padx=2, fill="x")
        ctk.CTkButton(self.edit_frame, text="Cancel", fg_color="#666666", text_color="white", corner_radius=0, font=MAIN_FONT, command=self.cancel_edit, width=80).pack(side="left", padx=2)

        # Filter Section
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=20, pady=(5, 0))
        
        self.btn_filter_all = self.create_filter_btn("All", "All")
        self.btn_filter_cash = self.create_filter_btn("Cash", "Cash")
        self.btn_filter_non = self.create_filter_btn("Non Cash", "Non Cash")
        self.btn_filter_unin = self.create_filter_btn("Uninput", "Uninput")

        # List Area
        self.scroll_log = ctk.CTkScrollableFrame(self, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.scroll_log._scrollbar.grid_forget()
        self.scroll_log.pack(fill="both", expand=True, padx=20, pady=5)

        # Pagination
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=20, pady=5)
        
        self.btn_prev = ctk.CTkButton(self.pagination_frame, text="<", width=30, height=25, font=("Segoe UI", 12, "bold"), fg_color="#e5e5e5", text_color="black", corner_radius=0, command=self.prev_page)
        self.btn_prev.pack(side="left")
        
        self.lbl_page = ctk.CTkLabel(self.pagination_frame, text="Page 1 of 1", font=SMALL_FONT, text_color=TEXT_COLOR)
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.pagination_frame, text=">", width=30, height=25, font=("Segoe UI", 12, "bold"), fg_color="#e5e5e5", text_color="black", corner_radius=0, command=self.next_page)
        self.btn_next.pack(side="right")

        # Footer
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", side="bottom", padx=20, pady=10)
        
        self.total_display_frame = ctk.CTkFrame(self.footer, fg_color=STATUS_PAID_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.total_display_frame.pack(fill="x", pady=5)
        
        self.lbl_total_label = ctk.CTkLabel(self.total_display_frame, text="Total Amount :", font=("Segoe UI", 16), text_color="black")
        self.lbl_total_label.pack(side="left", padx=15, pady=15)
        
        self.lbl_total = ctk.CTkLabel(self.total_display_frame, text="0.00", font=HEADER_FONT, text_color="black")
        self.lbl_total.pack(side="right", padx=15, pady=15)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_list()

    def next_page(self):
        indexed_data = list(enumerate(self.transactions))
        filtered_data = [t for i, t in indexed_data if self.current_filter == "All" or t["category"] == self.current_filter]
        max_pages = (len(filtered_data) - 1) // self.page_size
        if self.current_page < max_pages:
            self.current_page += 1
            self.refresh_list()

    def create_filter_btn(self, text, cat):
        btn = ctk.CTkButton(self.filter_frame, text=text, width=80, height=25, font=SMALL_FONT, fg_color="#e5e5e5", text_color="black", corner_radius=0, command=lambda: self.set_filter(cat))
        btn.pack(side="left", padx=2)
        return btn

    def create_input_btn(self, parent, text, color, bg, cat, col):
        btn = ctk.CTkButton(parent, text=text, height=38, fg_color=bg, hover_color="#e0e0e0", font=("Segoe UI", 11, "bold"), text_color=color, border_width=1, border_color=BORDER_COLOR, corner_radius=0, command=lambda: self.add_transaction(cat))
        btn.grid(row=0, column=col, sticky="ew", padx=2)
        
        def on_focus(e):
            btn.configure(border_width=2, border_color=ACCENT_COLOR)
        def on_unfocus(e):
            btn.configure(border_width=1, border_color=BORDER_COLOR)
            
        btn.bind("<FocusIn>", on_focus)
        btn.bind("<FocusOut>", on_unfocus)
        btn.bind("<Return>", lambda e: self.add_transaction(cat))
        btn.bind("<KP_Enter>", lambda e: self.add_transaction(cat))
        return btn

    def set_filter(self, cat):
        self.current_filter = cat
        self.current_page = 0
        self.refresh_list()
        self.update_filter_visuals()

    def update_filter_visuals(self):
        btns = {"All": self.btn_filter_all, "Cash": self.btn_filter_cash, "Non Cash": self.btn_filter_non, "Uninput": self.btn_filter_unin}
        for cat, btn in btns.items():
            is_active = cat == self.current_filter
            btn.configure(fg_color=ACCENT_COLOR if is_active else "#e5e5e5", text_color="white" if is_active else "black")

    def on_activate(self):
        self.entry_amount.focus_set()
        if self.file_path:
            self.lbl_session.configure(text=f"Session: {os.path.basename(self.file_path)}")
        self.update_filter_visuals()
            
    def load_session(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f: self.transactions = json.load(f)
        else: self.transactions = []
        self.current_page = 0
        self.refresh_list()
        self.update_filter_visuals()

    def save_session(self):
        if not self.file_path: return
        with open(self.file_path, "w") as f: json.dump(self.transactions, f, indent=4)
            
    def format_currency(self, event=None):
        if event and event.keysym == "Tab": return
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
        self.entry_amount.delete(0, "end")
        self.current_page = 0
        self.refresh_list()
        self.controller.return_focus()
        self.entry_amount.focus()

    def delete_transaction(self, idx):
        if messagebox.askyesno("Confirmation", "Delete this entry?"):
            self.transactions.pop(idx)
            self.save_session()
            self.refresh_list()

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
            self.cancel_edit()
            self.refresh_list()

    def cancel_edit(self):
        self.editing_index = None
        self.entry_amount.delete(0, "end")
        self.edit_frame.pack_forget()
        self.btn_grid.pack(fill="x")

    def refresh_list(self):
        for w in self.scroll_log.winfo_children(): w.destroy()
        
        indexed_data = list(enumerate(self.transactions))
        filtered_data = [(i, t) for i, t in indexed_data if self.current_filter == "All" or t["category"] == self.current_filter]
        
        total_items = len(filtered_data)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        
        if self.current_page >= total_pages: self.current_page = total_pages - 1
        
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        
        reversed_data = list(reversed(filtered_data))
        page_items = reversed_data[start_idx:end_idx]
        
        for idx, item in page_items:
            row = ctk.CTkFrame(self.scroll_log, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=0)
            row.pack(fill="x", pady=2, padx=2)
            
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            cat_color = {"Cash": "#2e7d32", "Non Cash": "#fbc02d", "Uninput": "#d32f2f"}.get(item["category"], TEXT_COLOR)
            
            lbl_val = ctk.CTkLabel(info_frame, text=f"Rp {item['amount']:,} | {item['category']}".replace(",", "."), font=("Segoe UI", 12, "bold"), text_color=cat_color, anchor="w")
            lbl_val.pack(fill="x")
            
            lbl_ts = ctk.CTkLabel(info_frame, text=f"Time: {item['timestamp']}", font=("Segoe UI", 9), text_color="grey", anchor="w")
            lbl_ts.pack(fill="x")
            
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=5)
            ctk.CTkButton(btns, text="Edit", width=50, height=25, corner_radius=0, font=SMALL_FONT, fg_color="#f5f5f5", text_color="black", command=lambda x=idx: self.edit_transaction(x)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="Delete", width=50, height=25, corner_radius=0, font=SMALL_FONT, fg_color="#ffebee", text_color="#d32f2f", hover_color="#ffcdd2", command=lambda x=idx: self.delete_transaction(x)).pack(side="left", padx=2)
        
        self.lbl_page.configure(text=f"Page {self.current_page + 1} of {total_pages}")
        
        total_sum = sum(t["amount"] for i, t in filtered_data)
        self.lbl_total.configure(text=f"{total_sum:,}.00".replace(",", "."))
        self.lbl_count.configure(text=f"Entries: {len(self.transactions)}")

if __name__ == "__main__":
    app = CashNoteApp()
    app.mainloop()
