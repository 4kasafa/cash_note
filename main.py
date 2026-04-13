import customtkinter as ctk
import json
import os
from datetime import datetime
from tkinter import messagebox
import ctypes
from ctypes import wintypes
import threading
import time

# Hacker Vibes Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green") # Neon green theme

# Colors
BG_COLOR = "#0a0a0a"
TEXT_COLOR = "#00ff00"
ACCENT_COLOR = "#003300"
CASH_COLOR = "#00ff00"
NON_CASH_COLOR = "#ffff00"
UNINPUT_COLOR = "#ff0000"

DATA_FILE = "data.json"

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

        self.title("CASH_COUNTER_v2.0")
        self.geometry("450x700")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        # Data initialization
        self.transactions = self.load_data()
        self.migrate_data() # Ensure old categories are updated
        self.current_filter = "Cash"
        self.editing_index = None
        self.previous_hwnd = None
        self.my_hwnd = None

        self.setup_ui()
        self.refresh_list()

        # Ambil HWND aplikasi
        self.after(500, self.init_windows_api)
        
        # Start Hotkey Listener (F12 & F10 sebagai cadangan)
        self.start_hotkey_listener()

    def migrate_data(self):
        """Migrate old category names to new ones."""
        migration_map = {
            "Green": "Cash",
            "Yellow": "Non Cash",
            "Red": "Uninput"
        }
        modified = False
        for t in self.transactions:
            if t["category"] in migration_map:
                t["category"] = migration_map[t["category"]]
                modified = True
        if modified:
            self.save_data()

    def init_windows_api(self):
        self.my_hwnd = user32.GetForegroundWindow()
        # Verify title
        buf = ctypes.create_unicode_buffer(100)
        user32.GetWindowTextW(self.my_hwnd, buf, 100)
        if "CASH_COUNTER" not in buf.value:
            self.my_hwnd = user32.FindWindowW(None, "CASH_COUNTER_v2.0")
        
        if self.my_hwnd:
            self.lbl_status.configure(text="> SYSTEM_READY: PRESS F12 OR F10", text_color=TEXT_COLOR)
        else:
            self.lbl_status.configure(text="> WINDOWS_API_ERROR", text_color=UNINPUT_COLOR)

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
            self.entry_amount.focus_force()

    def return_focus(self):
        if self.previous_hwnd:
            def task():
                user32.SetForegroundWindow(self.previous_hwnd)
                self.previous_hwnd = None
            self.after(200, task)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    return json.load(f)
            except: return []
        return []

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.transactions, f, indent=4)

    def format_currency(self, event=None):
        val = self.entry_amount.get().replace(".", "")
        if not val.isdigit() and val != "":
            val = "".join(filter(str.isdigit, val))
        if val == "":
            self.entry_amount.delete(0, "end")
            return
        formatted = "{:,}".format(int(val)).replace(",", ".")
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, formatted)

    def add_transaction(self, category):
        val_str = self.entry_amount.get().replace(".", "")
        if not val_str: return
        self.transactions.append({
            "amount": int(val_str),
            "category": category,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_data()
        self.entry_amount.delete(0, "end")
        self.refresh_list()
        self.return_focus()
        self.entry_amount.focus()

    def delete_transaction(self, index):
        if messagebox.askyesno("CONFIRMATION", "DESTROY_TRANSACTION_RECORD?"):
            self.transactions.pop(index)
            self.save_data()
            self.refresh_list()
            if self.editing_index == index: self.cancel_edit()

    def edit_transaction(self, index):
        self.editing_index = index
        item = self.transactions[index]
        amount_fmt = "{:,}".format(item["amount"]).replace(",", ".")
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, amount_fmt)
        self.entry_amount.focus()
        self.btn_frame.pack_forget()
        self.edit_btn_frame.pack(fill="x")

    def save_edit(self):
        if self.editing_index is not None:
            val_str = self.entry_amount.get().replace(".", "")
            if val_str:
                self.transactions[self.editing_index]["amount"] = int(val_str)
                self.save_data()
                self.cancel_edit()
                self.refresh_list()
                self.return_focus()

    def cancel_edit(self):
        self.editing_index = None
        self.entry_amount.delete(0, "end")
        self.edit_btn_frame.pack_forget()
        self.btn_frame.pack(fill="x")
        self.entry_amount.focus()

    def set_filter(self, category):
        self.current_filter = category
        self.refresh_list()

    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        total = 0
        indexed_data = list(enumerate(self.transactions))
        filtered_data = [(i, t) for i, t in indexed_data if self.current_filter == "All" or t["category"] == self.current_filter]
        filtered_data.reverse()
        for original_index, item in filtered_data:
            amount_fmt = "{:,}".format(item["amount"]).replace(",", ".")
            color_map = {"Cash": CASH_COLOR, "Non Cash": NON_CASH_COLOR, "Uninput": UNINPUT_COLOR}
            display_color = color_map.get(item["category"], TEXT_COLOR)
            frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#111111", border_width=1, border_color=ACCENT_COLOR)
            frame.pack(fill="x", padx=5, pady=2)
            data_frame = ctk.CTkFrame(frame, fg_color="transparent")
            data_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            ctk.CTkLabel(data_frame, text=f"VAL: Rp {amount_fmt}", font=("Consolas", 14, "bold"), text_color=display_color, anchor="w").pack(fill="x")
            ctk.CTkLabel(data_frame, text=f"TS: {item['timestamp']} | TYPE: {item['category']}", font=("Consolas", 10), text_color="#006600", anchor="w").pack(fill="x")
            action_frame = ctk.CTkFrame(frame, fg_color="transparent")
            action_frame.pack(side="right", padx=5)
            ctk.CTkButton(action_frame, text="EDIT", width=40, height=25, fg_color="#1a1a1a", border_width=1, border_color="#333333", font=("Consolas", 10), command=lambda i=original_index: self.edit_transaction(i)).pack(side="left", padx=2)
            ctk.CTkButton(action_frame, text="DEL", width=40, height=25, fg_color="#1a1a1a", border_width=1, border_color="#333333", font=("Consolas", 10), hover_color=UNINPUT_COLOR, command=lambda i=original_index: self.delete_transaction(i)).pack(side="left", padx=2)
            total += item["amount"]
        self.lbl_total.configure(text=f"BUFFER_TOTAL: Rp {'{:,}'.format(total).replace(',', '.')}")
        self.update_filter_buttons()

    def update_filter_buttons(self):
        buttons = {"All": self.btn_filter_all, "Cash": self.btn_filter_green, "Non Cash": self.btn_filter_yellow, "Uninput": self.btn_filter_red}
        for cat, btn in buttons.items():
            is_active = cat == self.current_filter
            btn.configure(
                fg_color=ACCENT_COLOR if is_active else "transparent",
                border_width=1 if is_active else 0,
                border_color=TEXT_COLOR
            )

    def on_btn_focus(self, btn, event):
        btn.configure(border_width=2, border_color=TEXT_COLOR)

    def on_btn_unfocus(self, btn, event):
        btn.configure(border_width=0)

    def setup_ui(self):
        # --- Top Section: Status & Input ---
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(pady=(10, 10), padx=20, fill="x")
        
        self.lbl_status = ctk.CTkLabel(self.input_frame, text="> INITIALIZING_CORE...", font=("Consolas", 10), text_color="#006600")
        self.lbl_status.pack(pady=(0, 5), anchor="w")
        
        self.entry_amount = ctk.CTkEntry(self.input_frame, placeholder_text="ENTER_AMOUNT...", height=50, font=("Consolas", 24), justify="center", fg_color="#050505", border_color=ACCENT_COLOR, text_color=TEXT_COLOR)
        self.entry_amount.pack(fill="x", pady=(0, 15))
        self.entry_amount.bind("<KeyRelease>", self.format_currency)
        self.entry_amount.bind("<Return>", lambda e: self.btn_green.focus())

        self.btn_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x")

        # Config Buttons
        self.btn_green = ctk.CTkButton(self.btn_frame, text="CASH", fg_color="#003300", hover_color=CASH_COLOR, font=("Consolas", 12, "bold"), text_color=CASH_COLOR, border_width=1, border_color=CASH_COLOR, command=lambda: self.add_transaction("Cash"), width=100)
        self.btn_green.pack(side="left", expand=True, padx=5)
        self.btn_green.bind("<FocusIn>", lambda e: self.on_btn_focus(self.btn_green, e))
        self.btn_green.bind("<FocusOut>", lambda e: self.on_btn_unfocus(self.btn_green, e))
        self.btn_green.bind("<Return>", lambda e: self.add_transaction("Cash"))

        self.btn_yellow = ctk.CTkButton(self.btn_frame, text="NON_CASH", fg_color="#333300", hover_color=NON_CASH_COLOR, font=("Consolas", 12, "bold"), text_color=NON_CASH_COLOR, border_width=1, border_color=NON_CASH_COLOR, command=lambda: self.add_transaction("Non Cash"), width=100)
        self.btn_yellow.pack(side="left", expand=True, padx=5)
        self.btn_yellow.bind("<FocusIn>", lambda e: self.on_btn_focus(self.btn_yellow, e))
        self.btn_yellow.bind("<FocusOut>", lambda e: self.on_btn_unfocus(self.btn_yellow, e))
        self.btn_yellow.bind("<Return>", lambda e: self.add_transaction("Non Cash"))

        self.btn_red = ctk.CTkButton(self.btn_frame, text="UNINPUT", fg_color="#330000", hover_color=UNINPUT_COLOR, font=("Consolas", 12, "bold"), text_color=UNINPUT_COLOR, border_width=1, border_color=UNINPUT_COLOR, command=lambda: self.add_transaction("Uninput"), width=100)
        self.btn_red.pack(side="left", expand=True, padx=5)
        self.btn_red.bind("<FocusIn>", lambda e: self.on_btn_focus(self.btn_red, e))
        self.btn_red.bind("<FocusOut>", lambda e: self.on_btn_unfocus(self.btn_red, e))
        self.btn_red.bind("<Return>", lambda e: self.add_transaction("Uninput"))

        self.edit_btn_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.btn_save = ctk.CTkButton(self.edit_btn_frame, text="COMMIT_CHANGES", fg_color="#000033", text_color="#3399ff", border_width=1, border_color="#3399ff", font=("Consolas", 12, "bold"), command=self.save_edit)
        self.btn_save.pack(side="left", expand=True, padx=5, fill="x")
        self.btn_save.bind("<Return>", lambda e: self.save_edit())
        ctk.CTkButton(self.edit_btn_frame, text="ABORT", fg_color="#1a1a1a", text_color="gray", font=("Consolas", 12), command=self.cancel_edit, width=100).pack(side="left", padx=5)

        # --- Filter Section ---
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=20, pady=(5, 0))
        self.btn_filter_all = ctk.CTkButton(self.filter_frame, text="ALL", width=60, height=25, font=("Consolas", 10), command=lambda: self.set_filter("All"))
        self.btn_filter_all.pack(side="left", padx=2)
        self.btn_filter_green = ctk.CTkButton(self.filter_frame, text="CASH", width=60, height=25, font=("Consolas", 10), command=lambda: self.set_filter("Cash"))
        self.btn_filter_green.pack(side="left", padx=2)
        self.btn_filter_yellow = ctk.CTkButton(self.filter_frame, text="NON_C", width=60, height=25, font=("Consolas", 10), command=lambda: self.set_filter("Non Cash"))
        self.btn_filter_yellow.pack(side="left", padx=2)
        self.btn_filter_red = ctk.CTkButton(self.filter_frame, text="UNIN", width=60, height=25, font=("Consolas", 10), command=lambda: self.set_filter("Uninput"))
        self.btn_filter_red.pack(side="left", padx=2)

        # --- List Section ---
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="TRANSACTION_LOG", label_font=("Consolas", 12, "bold"), label_text_color=TEXT_COLOR, fg_color="#050505", border_width=1, border_color=ACCENT_COLOR)
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Bottom Section: TOTAL ---
        self.bottom_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#001100", border_width=1, border_color=TEXT_COLOR)
        self.bottom_frame.pack(fill="x", side="bottom")
        self.lbl_total = ctk.CTkLabel(self.bottom_frame, text="BUFFER_TOTAL: Rp 0", font=("Consolas", 18, "bold"), text_color=TEXT_COLOR)
        self.lbl_total.pack(pady=15)

if __name__ == "__main__":
    app = CashCounterApp()
    app.mainloop()
