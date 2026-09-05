import customtkinter as ctk
import json
import os
from datetime import datetime
from tkinter import messagebox
from constants import (
    SIDEBAR_COLOR, BORDER_COLOR, TEXT_COLOR, 
    HEADER_FONT, MAIN_FONT, SMALL_FONT, CONSOLE_COLOR, ACCENT_COLOR, 
    MODAL_FILE
)

class ModalTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        self.modal_items = []
        self.editing_id = None

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # 1. Header Info Bar
        self.header_frame = ctk.CTkFrame(
            self, fg_color=SIDEBAR_COLOR, height=45, corner_radius=6, 
            border_width=1, border_color=BORDER_COLOR
        )
        self.header_frame.pack(fill="x", padx=15, pady=(10, 5))
        self.header_frame.pack_propagate(False)

        self.lbl_title = ctk.CTkLabel(
            self.header_frame, text="Pencatatan Modal Kasir", 
            font=HEADER_FONT, text_color=TEXT_COLOR
        )
        self.lbl_title.pack(side="left", padx=15)

        self.lbl_item_count = ctk.CTkLabel(
            self.header_frame, text="0 Item", 
            font=SMALL_FONT, text_color="grey"
        )
        self.lbl_item_count.pack(side="right", padx=15)

        # 2. Input Area (Top)
        self.input_container = ctk.CTkFrame(
            self, fg_color=SIDEBAR_COLOR, border_width=1, 
            border_color=BORDER_COLOR, corner_radius=8
        )
        self.input_container.pack(fill="x", padx=15, pady=5)

        # Amount Input Row
        amt_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        amt_frame.pack(fill="x", padx=15, pady=(10, 10))

        self.entry_amount = ctk.CTkEntry(
            amt_frame, placeholder_text="0", height=42, 
            font=("Segoe UI", 18, "bold"), justify="right", 
            fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, 
            text_color=TEXT_COLOR, corner_radius=6
        )
        self.entry_amount.pack(fill="x", pady=(2, 0))
        self.entry_amount.bind("<KeyRelease>", self.format_currency)
        self.entry_amount.bind("<Return>", lambda e: self.submit_data())

        # Buttons Frame (Add / Save Edit)
        self.btn_action_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        self.btn_action_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Default Add Button
        self.btn_add = ctk.CTkButton(
            self.btn_action_frame, text="+ Tambah Modal", height=36, 
            fg_color=ACCENT_COLOR, hover_color="#375a7f", text_color="white", 
            font=("Segoe UI", 11, "bold"), corner_radius=6, command=self.submit_data
        )
        self.btn_add.pack(fill="x")

        # Edit Buttons Box (hidden by default)
        self.edit_btn_box = ctk.CTkFrame(self.btn_action_frame, fg_color="transparent")
        self.btn_save_edit = ctk.CTkButton(
            self.edit_btn_box, text="Simpan Perubahan", height=36, 
            fg_color="#2e7d32", hover_color="#1b5e20", text_color="white", 
            font=("Segoe UI", 11, "bold"), corner_radius=6, command=self.submit_data
        )
        self.btn_save_edit.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_cancel_edit = ctk.CTkButton(
            self.edit_btn_box, text="Batal", height=36, 
            fg_color="#666666", hover_color="#555555", text_color="white", 
            font=MAIN_FONT, corner_radius=6, command=self.cancel_edit
        )
        self.btn_cancel_edit.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # 3. List Area (Scrollable)
        self.scroll_list = ctk.CTkScrollableFrame(
            self, fg_color=CONSOLE_COLOR, border_width=1, 
            border_color=BORDER_COLOR, corner_radius=8
        )
        self.scroll_list.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def on_activate(self):
        self.entry_amount.focus_set()
        self.load_data()

    def format_currency(self, event=None):
        if event and event.keysym in ("Tab", "Return"):
            return
        val = self.entry_amount.get().replace(".", "").strip()
        if not val.isdigit() and val != "":
            val = "".join(filter(str.isdigit, val))
        if val == "":
            self.entry_amount.delete(0, "end")
            return
        formatted = "{:,}".format(int(val)).replace(",", ".")
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, formatted)

    def load_data(self):
        if os.path.exists(MODAL_FILE):
            try:
                with open(MODAL_FILE, "r") as f:
                    self.modal_items = json.load(f)
            except Exception:
                self.modal_items = []
        else:
            self.modal_items = []
        self.render_list()

    def save_data(self):
        try:
            with open(MODAL_FILE, "w") as f:
                json.dump(self.modal_items, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error Simpan", f"Gagal menyimpan data modal: {e}")

    def submit_data(self):
        val_str = self.entry_amount.get().replace(".", "").strip()
        if not val_str:
            messagebox.showwarning("Input Kosong", "Silakan masukkan jumlah uang terlebih dahulu.")
            self.entry_amount.focus_set()
            return

        try:
            amount = int(val_str)
        except ValueError:
            messagebox.showwarning("Format Salah", "Jumlah uang harus berupa angka.")
            return

        if amount <= 0:
            messagebox.showwarning("Nilai Tidak Valid", "Jumlah uang harus lebih besar dari 0.")
            return

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

        if self.editing_id is not None:
            # Update existing
            for item in self.modal_items:
                if item["id"] == self.editing_id:
                    item["amount"] = amount
                    break
            self.cancel_edit()
        else:
            # Create new item
            new_item = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "amount": amount,
                "checked": False,  # Default: unchecked (ikut dihitung)
                "timestamp": now_str
            }
            self.modal_items.append(new_item)
            self.entry_amount.delete(0, "end")

        self.save_data()
        self.render_list()
        self.entry_amount.focus_set()

    def toggle_check(self, item_id, checked_val):
        for item in self.modal_items:
            if item["id"] == item_id:
                item["checked"] = checked_val
                break
        self.save_data()
        self.render_list()

    def start_edit(self, item):
        self.editing_id = item["id"]
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, f"{item['amount']:,}".replace(",", "."))

        self.btn_add.pack_forget()
        self.edit_btn_box.pack(fill="x")
        self.entry_amount.focus_set()

    def cancel_edit(self):
        self.editing_id = None
        self.entry_amount.delete(0, "end")
        self.edit_btn_box.pack_forget()
        self.btn_add.pack(fill="x")
        self.entry_amount.focus_set()

    def delete_item(self, item_id):
        if messagebox.askyesno("Konfirmasi Hapus", "Hapus catatan modal ini?"):
            self.modal_items = [i for i in self.modal_items if i["id"] != item_id]
            if self.editing_id == item_id:
                self.cancel_edit()
            self.save_data()
            self.render_list()

    def render_list(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        if not self.modal_items:
            empty_frame = ctk.CTkFrame(self.scroll_list, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=40)
            ctk.CTkLabel(
                empty_frame, text="Belum ada data modal.\nMasukkan jumlah uang di atas.", 
                font=MAIN_FONT, text_color="grey", justify="center"
            ).pack()
        else:
            # Sort newest first
            for item in reversed(self.modal_items):
                is_checked = item.get("checked", False)
                amount = item.get("amount", 0)

                # Row Card
                row = ctk.CTkFrame(
                    self.scroll_list, fg_color="white", border_width=1, 
                    border_color=BORDER_COLOR, corner_radius=6
                )
                row.pack(fill="x", pady=3, padx=2)

                # Checkbox
                cb_var = ctk.BooleanVar(value=is_checked)
                cb = ctk.CTkCheckBox(
                    row, text="", variable=cb_var, width=24, 
                    checkbox_width=18, checkbox_height=18, corner_radius=3, 
                    command=lambda i=item["id"], v=cb_var: self.toggle_check(i, v.get())
                )
                cb.pack(side="left", padx=(10, 5), pady=8)

                # Info Frame (Amount & Note)
                info_frame = ctk.CTkFrame(row, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=6)

                amt_text = f"Rp {amount:,}".replace(",", ".")
                if is_checked:
                    amount_color = "#9e9e9e"
                else:
                    amount_color = TEXT_COLOR

                lbl_amount = ctk.CTkLabel(
                    info_frame, text=amt_text, 
                    font=("Segoe UI", 12, "bold"), text_color=amount_color, anchor="w"
                )
                lbl_amount.pack(fill="x")

                desc_text = f"Waktu: {item['timestamp']}" if item.get("timestamp") else ""
                lbl_desc = ctk.CTkLabel(
                    info_frame, text=desc_text, 
                    font=("Segoe UI", 9), text_color="grey", anchor="w"
                )
                lbl_desc.pack(fill="x")

                # Action Buttons (Edit & Delete)
                actions = ctk.CTkFrame(row, fg_color="transparent")
                actions.pack(side="right", padx=8, pady=6)

                btn_edit = ctk.CTkButton(
                    actions, text="Edit", width=45, height=26, 
                    corner_radius=4, font=SMALL_FONT, fg_color="#f5f5f5", 
                    hover_color="#e0e0e0", text_color="black", 
                    command=lambda it=item: self.start_edit(it)
                )
                btn_edit.pack(side="left", padx=2)

                btn_del = ctk.CTkButton(
                    actions, text="Hapus", width=48, height=26, 
                    corner_radius=4, font=SMALL_FONT, fg_color="#ffebee", 
                    hover_color="#ffcdd2", text_color="#d32f2f", 
                    command=lambda i=item["id"]: self.delete_item(i)
                )
                btn_del.pack(side="left", padx=2)

        # Update Header count
        total_items = len(self.modal_items)
        self.lbl_item_count.configure(text=f"{total_items} Item")
