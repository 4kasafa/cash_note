import customtkinter as ctk
import os
import glob
import json
from tkinter import messagebox
from constants import HEADER_FONT, TEXT_COLOR, MAIN_FONT, CONSOLE_COLOR, BORDER_COLOR, ACCENT_COLOR, DATA_DIR

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
