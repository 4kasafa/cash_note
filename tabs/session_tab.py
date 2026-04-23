import customtkinter as ctk
import os
import json
from datetime import datetime
from tkinter import messagebox
from constants import SIDEBAR_COLOR, BORDER_COLOR, TEXT_COLOR, STATUS_TOTAL_BG, DISPLAY_FONT, ACCENT_COLOR, MAIN_FONT, SMALL_FONT, CONSOLE_COLOR, STATUS_PAID_BG, HEADER_FONT

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
        self.action_buttons = []
        self.item_buttons = []
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
        self.action_buttons.append(btn)
        return btn

    def create_input_btn(self, parent, text, color, bg, cat, col):
        btn = ctk.CTkButton(parent, text=text, height=38, fg_color=bg, hover_color="#e0e0e0", font=("Segoe UI", 11, "bold"), text_color=color, border_width=1, border_color=BORDER_COLOR, corner_radius=0, command=lambda: self.add_transaction(cat))
        btn.grid(row=0, column=col, sticky="ew", padx=2)
        self.action_buttons.append(btn)
        
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
        self.item_buttons = []
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
            edit_btn = ctk.CTkButton(btns, text="Edit", width=50, height=25, corner_radius=0, font=SMALL_FONT, fg_color="#f5f5f5", text_color="black", command=lambda x=idx: self.edit_transaction(x))
            delete_btn = ctk.CTkButton(btns, text="Delete", width=50, height=25, corner_radius=0, font=SMALL_FONT, fg_color="#ffebee", text_color="#d32f2f", hover_color="#ffcdd2", command=lambda x=idx: self.delete_transaction(x))
            edit_btn.pack(side="left", padx=2)
            delete_btn.pack(side="left", padx=2)
            self.item_buttons.extend([edit_btn, delete_btn])
        
        self.lbl_page.configure(text=f"Page {self.current_page + 1} of {total_pages}")
        
        total_sum = sum(t["amount"] for i, t in filtered_data)
        self.lbl_total.configure(text=f"{total_sum:,}.00".replace(",", "."))
        self.lbl_count.configure(text=f"Entries: {len(self.transactions)}")
