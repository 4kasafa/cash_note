import customtkinter as ctk
import base64
import json
import os
import tempfile
import textwrap
from datetime import datetime
from tkinter import messagebox
from constants import (HEADER_FONT, TEXT_COLOR, MAIN_FONT, CONSOLE_COLOR, 
                       BORDER_COLOR, ACCENT_COLOR, USERS_FILE, CALC_HISTORY_FILE, 
                       SMALL_FONT, SIDEBAR_COLOR, STATUS_PAID_BG)

try:
    import win32print # type: ignore
except ImportError:
    win32print = None

ARABIC_RECEIPT_TEXT = '"شكراً جزيلاً"'
ARABIC_ESC_POS_IMAGE_B64 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAfAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPgAAAAAAAAHwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4AAAAAAAAAHwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4AAAAAAAAB8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPeAAcAAAAAAABwAAAAgAAHvAAAAAAAAAAAAAAAAAAAAAAAAAAAA95+BwAAAAAAAHAAAAOAAAe8AAAAAAAAAAAAAAAAAAAAAAAAAAAD3h4HAAAAAAAAcAAAD4AAB7wAAAAAAAAAAAAAAAAAAAAAAAAAAAPeDwcAAAAAAABwAAA/AAAHvAAAAAAAAAAAAAAAAAAAAAAAAAAAA94HhwAAAAAAAHAAAPwAAAe8AAAAAAAAAAAAAAAAAAAAAAAAAAAD3gPHAAAAAAAAcAAD8AA4B7wAAAAAAAAAAAAAAAAAAAAAAAAAAAHcAecAAAAAAABwAAPgADgDuAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB5wAAAAAAAHAAA8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD3AAAAH4AAcAAD4ADuAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHcAADwf4ABwAAHwAO4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAfwOAPB/wAHAAAPgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/A4AAAfwAcAAAPAAA4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD8DgAAAPgBwAAAeAADgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPwOAPgAPAHAB4A8AAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/A4AeAB8AcADwB4c84AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPcDgA4B/wBwAHADhzzgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB5weADw//AHAAcAfPPOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPn/4AP//wAcAB/////4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB8f/AA//wABwAH/////gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPg/4AD/wAAHAAf/9//8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAeAAAAAADwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAcAAAAeAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD+B/ABwAAAP4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP5/4AAAAAP/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH/AAAAAA/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAfgAAAAAD8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
ARABIC_ESC_POS_IMAGE_WIDTH = 300
ARABIC_ESC_POS_IMAGE_HEIGHT = 80
ARABIC_ESC_POS_IMAGE_BYTES_PER_ROW = 38


def cash_portion(t):
    """Porsi tunai: Cash penuh, Split = cash_part, lainnya 0 (aman untuk JSON lama)."""
    if t.get("category") == "Cash":
        return int(t.get("amount", 0))
    if t.get("category") == "Split":
        return int(t.get("cash_part", 0))
    return 0


def noncash_portion(t):
    """Porsi non tunai: Non Cash penuh, Split = noncash_part, lainnya 0."""
    if t.get("category") == "Non Cash":
        return int(t.get("amount", 0))
    if t.get("category") == "Split":
        return int(t.get("noncash_part", 0))
    return 0


class CalculateTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        
        self.denominations = [
            100000, 75000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100
        ]
        self.inputs = {} 
        self.subtotal_labels = {}
        self.expense_amount = 0
        self.expense_note = ""
        
        self.vcmd = (self.register(self.validate_numeric), "%P")
        
        self.setup_ui()

    def validate_numeric(self, P):
        if P == "" or P.isdigit():
            return True
        return False

    def setup_ui(self):
        # Container for View Switching
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # --- MODE INPUT ---
        self.input_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_view.pack(fill="both", expand=True)

        # Header: Date and Cashier Selection
        self.header_frame = ctk.CTkFrame(self.input_view, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        self.header_frame.pack(fill="x", padx=20, pady=10)
        
        # Header Top: Date & Shortcut to User Tab
        self.header_top = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_top.pack(fill="x", padx=20, pady=(12, 6))

        date_str = datetime.now().strftime("%d/%m/%Y")
        ctk.CTkLabel(self.header_top, text=f"Tanggal: {date_str}", font=("Segoe UI", 11, "bold"), text_color=ACCENT_COLOR).pack(side="left")

        self.btn_user_tab = ctk.CTkButton(
            self.header_top,
            text="User →",
            width=100,
            height=28,
            fg_color=ACCENT_COLOR,
            hover_color="#375a7f",
            text_color="white",
            corner_radius=6,
            font=("Segoe UI", 10, "bold"),
            command=lambda: self.controller.show_tab("USR")
        )
        self.btn_user_tab.pack(side="right")

        self.btn_kasir_tab = ctk.CTkButton(
            self.header_top,
            text="Laku →",
            width=100,
            height=28,
            fg_color="#4b5563",
            hover_color="#374151",
            text_color="white",
            corner_radius=6,
            font=("Segoe UI", 10, "bold"),
            command=lambda: self.controller.show_tab("KSR")
        )
        self.btn_kasir_tab.pack(side="right", padx=(0, 6))
        
        self.cashier_var = ctk.StringVar(value="Pilih data Kasir")
        self.cashier_menu = ctk.CTkOptionMenu(
            self.header_frame, 
            variable=self.cashier_var,
            values=["Pilih data Kasir"],
            fg_color=SIDEBAR_COLOR,
            text_color=TEXT_COLOR,
            button_color="#f0f0f0",
            button_hover_color="#e0e0e0",
            dropdown_fg_color=SIDEBAR_COLOR,
            dropdown_text_color=TEXT_COLOR,
            dropdown_hover_color="#f5f5f5",
            corner_radius=10,
            anchor="w",
            height=38,
            font=("Segoe UI", 11)
        )
        self.cashier_menu.pack(pady=(0, 8), padx=20, fill="x")

        # Expense & Note Menu / Section
        self.expense_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.expense_container.pack(fill="x", padx=20, pady=(0, 12))
        self.render_expense_section()

        # Scrollable Area for Denominations
        self.scroll_container = ctk.CTkScrollableFrame(self.input_view, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=15)

        for denom in self.denominations:
            self.create_denom_row(denom)

        # Footer Area
        self.footer_frame = ctk.CTkFrame(self.input_view, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=20, pady=10)
        
        self.total_frame = ctk.CTkFrame(self.footer_frame, fg_color=STATUS_PAID_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        self.total_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(self.total_frame, text="Total Keseluruhan:", font=("Segoe UI", 14, "bold"), text_color="black").pack(side="left", padx=15, pady=10)
        self.lbl_grand_total = ctk.CTkLabel(self.total_frame, text="Rp 0", font=("Segoe UI", 16, "bold"), text_color="black")
        self.lbl_grand_total.pack(side="right", padx=15, pady=10)
        
        self.comp_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        
        self.sys_row = ctk.CTkFrame(self.comp_frame, fg_color="transparent")
        self.sys_row.pack(fill="x")
        ctk.CTkLabel(self.sys_row, text="Total Sistem (Tunai):", font=("Segoe UI", 11), text_color="grey").pack(side="left", padx=5)
        self.lbl_sys_total = ctk.CTkLabel(self.sys_row, text="Tidak Ada Sesi Aktif", font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR)
        self.lbl_sys_total.pack(side="right", padx=5)
        
        self.diff_row = ctk.CTkFrame(self.comp_frame, fg_color="transparent")
        self.diff_row.pack(fill="x")
        ctk.CTkLabel(self.diff_row, text="Selisih:", font=("Segoe UI", 11), text_color="grey").pack(side="left", padx=5)
        self.lbl_diff = ctk.CTkLabel(self.diff_row, text="Rp 0", font=("Segoe UI", 12, "bold"), text_color=TEXT_COLOR)
        self.lbl_diff.pack(side="right", padx=5)
        
        self.btn_box = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.btn_box.pack(fill="x")
        
        self.btn_preview = ctk.CTkButton(self.btn_box, text="Pratinjau", fg_color=ACCENT_COLOR, text_color="white", corner_radius=5, command=self.show_preview)
        self.btn_preview.pack(side="left", expand=True, padx=5)
        ctk.CTkButton(self.btn_box, text="Reset Semua", fg_color="#666666", text_color="white", corner_radius=5, command=self.clear_all).pack(side="left", expand=True, padx=5)

        # --- MODE PREVIEW ---
        self.preview_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        # Hidden by default

        self.preview_header = ctk.CTkFrame(self.preview_view, fg_color="transparent")
        self.preview_header.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.preview_header, text="Pratinjau Struk", font=HEADER_FONT, text_color=TEXT_COLOR).pack(side="left")
        ctk.CTkButton(self.preview_header, text="Kembali", width=60, fg_color="#666666", text_color="white", command=self.show_input_view).pack(side="right")

        self.receipt_scroll = ctk.CTkScrollableFrame(self.preview_view, fg_color="#e0e0e0", corner_radius=0)
        self.receipt_scroll.pack(fill="both", expand=True, padx=20)

        self.receipt_paper = ctk.CTkFrame(self.receipt_scroll, fg_color="white", corner_radius=0, border_width=1, border_color="#ccc")
        self.receipt_paper.pack(pady=20)
        
        self.lbl_receipt_text = ctk.CTkLabel(self.receipt_paper, text="", font=("Courier New", 12), justify="left", text_color="black", padx=0, pady=20)
        self.lbl_receipt_text.pack()

        self.preview_footer = ctk.CTkFrame(self.preview_view, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.preview_footer.pack(fill="x", side="bottom")

        size_frame = ctk.CTkFrame(self.preview_footer, fg_color="transparent")
        size_frame.pack(pady=5)
        ctk.CTkLabel(size_frame, text="Ukuran Cetak:", font=SMALL_FONT).pack(side="left", padx=10)
        self.print_size_var = ctk.StringVar(value="58")
        ctk.CTkRadioButton(size_frame, text="58mm", variable=self.print_size_var, value="58", command=self.update_receipt_preview).pack(side="left", padx=5)
        ctk.CTkRadioButton(size_frame, text="80mm", variable=self.print_size_var, value="80", command=self.update_receipt_preview).pack(side="left", padx=5)

        self.btn_confirm = ctk.CTkButton(self.preview_footer, text="Simpan & Cetak", fg_color="#2e7d32", text_color="white", height=45, corner_radius=5, font=("Segoe UI", 12, "bold"), command=self.save_and_print)
        self.btn_confirm.pack(fill="x", padx=40, pady=10)

    def render_expense_section(self):
        for widget in self.expense_container.winfo_children():
            widget.destroy()

        if self.expense_amount == 0 and not self.expense_note:
            btn = ctk.CTkButton(
                self.expense_container,
                text="+ Pengeluaran & Keterangan",
                fg_color="#eef2fb",
                hover_color="#dde6f9",
                text_color=ACCENT_COLOR,
                border_width=1,
                border_color="#c7d7fa",
                corner_radius=8,
                height=32,
                font=("Segoe UI", 11, "bold"),
                command=self.show_expense_popup
            )
            btn.pack(fill="x")
        else:
            card = ctk.CTkFrame(
                self.expense_container,
                fg_color="#fff9f9" if self.expense_amount > 0 else "#f8faff",
                border_width=1,
                border_color="#ffcdd2" if self.expense_amount > 0 else "#dbe4fb",
                corner_radius=8
            )
            card.pack(fill="x")

            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True, padx=(12, 5), pady=6)

            amt_str = f"Rp {self.expense_amount:,}".replace(",", ".")
            lbl_amt = ctk.CTkLabel(
                info_box,
                text=f"Pengeluaran: {amt_str}",
                font=("Segoe UI", 11, "bold"),
                text_color="#d32f2f" if self.expense_amount > 0 else TEXT_COLOR,
                anchor="w"
            )
            lbl_amt.pack(fill="x")

            if self.expense_note:
                lbl_note = ctk.CTkLabel(
                    info_box,
                    text=f"Ket: {self.expense_note}",
                    font=SMALL_FONT,
                    text_color="#555555",
                    anchor="w"
                )
                lbl_note.pack(fill="x")

            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=(5, 8), pady=6)

            btn_edit = ctk.CTkButton(
                btn_box,
                text="Ubah",
                width=45,
                height=26,
                fg_color=ACCENT_COLOR,
                hover_color="#375a7f",
                text_color="white",
                corner_radius=5,
                font=("Segoe UI", 10, "bold"),
                command=self.show_expense_popup
            )
            btn_edit.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(
                btn_box,
                text="✕",
                width=26,
                height=26,
                fg_color="#e0e0e0",
                hover_color="#d0d0d0",
                text_color="#333333",
                corner_radius=5,
                font=("Segoe UI", 10, "bold"),
                command=self.clear_expense
            )
            btn_del.pack(side="left", padx=2)

    def show_expense_popup(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Pengeluaran & Keterangan")
        dialog.geometry("380x300")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.update_idletasks()

        x = self.winfo_rootx() + (self.winfo_width() - 380) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 300) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            container,
            text="Input Pengeluaran & Keterangan",
            font=HEADER_FONT,
            text_color=TEXT_COLOR
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            container,
            text="Nominal Pengeluaran (Rp):",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_COLOR
        ).pack(anchor="w", pady=(5, 2))

        entry_amount = ctk.CTkEntry(
            container,
            placeholder_text="0",
            height=38,
            font=("Segoe UI", 14, "bold"),
            justify="right",
            fg_color=CONSOLE_COLOR,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=6
        )
        entry_amount.pack(fill="x", pady=(0, 10))
        if self.expense_amount > 0:
            entry_amount.insert(0, f"{self.expense_amount:,}".replace(",", "."))

        def format_currency_input(event=None):
            val = entry_amount.get().replace(".", "").strip()
            val = "".join(filter(str.isdigit, val))
            if not val:
                entry_amount.delete(0, "end")
                return
            formatted = "{:,}".format(int(val)).replace(",", ".")
            entry_amount.delete(0, "end")
            entry_amount.insert(0, formatted)

        entry_amount.bind("<KeyRelease>", format_currency_input)

        ctk.CTkLabel(
            container,
            text="Keterangan:",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_COLOR
        ).pack(anchor="w", pady=(5, 2))

        entry_note = ctk.CTkEntry(
            container,
            placeholder_text="Contoh: Potongan refund kelebihan transfer",
            height=38,
            font=MAIN_FONT,
            fg_color=CONSOLE_COLOR,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=6
        )
        entry_note.pack(fill="x", pady=(0, 15))
        if self.expense_note:
            entry_note.insert(0, self.expense_note)

        def on_save(event=None):
            val_str = entry_amount.get().replace(".", "").strip()
            self.expense_amount = int(val_str) if val_str else 0
            self.expense_note = entry_note.get().strip()
            self.render_expense_section()
            dialog.destroy()

        def on_clear():
            self.expense_amount = 0
            self.expense_note = ""
            self.render_expense_section()
            dialog.destroy()

        def on_cancel(event=None):
            dialog.destroy()

        entry_amount.bind("<Return>", lambda e: entry_note.focus())
        entry_note.bind("<Return>", on_save)
        dialog.bind("<Escape>", on_cancel)

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", pady=(5, 0))

        btn_save = ctk.CTkButton(
            btn_box,
            text="Simpan",
            fg_color=ACCENT_COLOR,
            hover_color="#375a7f",
            text_color="white",
            corner_radius=6,
            font=("Segoe UI", 11, "bold"),
            height=34,
            command=on_save
        )
        btn_save.pack(side="left", expand=True, fill="x", padx=(0, 4))

        if self.expense_amount > 0 or self.expense_note:
            btn_clear = ctk.CTkButton(
                btn_box,
                text="Hapus",
                fg_color="#d32f2f",
                hover_color="#b71c1c",
                text_color="white",
                corner_radius=6,
                font=MAIN_FONT,
                height=34,
                command=on_clear
            )
            btn_clear.pack(side="left", expand=True, fill="x", padx=4)

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Batal",
            fg_color="#666666",
            hover_color="#555555",
            text_color="white",
            corner_radius=6,
            font=MAIN_FONT,
            height=34,
            command=on_cancel
        )
        btn_cancel.pack(side="left", expand=True, fill="x", padx=(4, 0))

        entry_amount.focus()

    def clear_expense(self, silent=False):
        self.expense_amount = 0
        self.expense_note = ""
        self.render_expense_section()

    def create_denom_row(self, denom):
        row = ctk.CTkFrame(self.scroll_container, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        row.pack(fill="x", pady=3, padx=5)
        ctk.CTkLabel(row, text=f"{denom:,}".replace(",", "."), font=("Segoe UI", 12, "bold"), width=80, anchor="w").pack(side="left", padx=15, pady=10)
        entry = ctk.CTkEntry(row, placeholder_text="0", width=80, justify="center", fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, validate="key", validatecommand=self.vcmd)
        entry.pack(side="left", padx=10)
        entry.bind("<KeyRelease>", lambda e, d=denom: self.update_subtotal(d))
        self.inputs[denom] = entry
        subtotal_lbl = ctk.CTkLabel(row, text="Rp 0", font=("Segoe UI", 11, "bold"), text_color=ACCENT_COLOR, anchor="e")
        subtotal_lbl.pack(side="right", padx=15)
        self.subtotal_labels[denom] = subtotal_lbl

    def update_subtotal(self, denom):
        val_str = self.inputs[denom].get().strip()
        qty = int(val_str) if val_str else 0
        subtotal = qty * denom
        self.subtotal_labels[denom].configure(text=f"Rp {subtotal:,}".replace(",", "."))
        self.update_grand_total()

    def update_grand_total(self):
        total = 0
        for denom in self.denominations:
            qty = int(self.inputs[denom].get() or 0)
            total += (qty * denom)
        self.lbl_grand_total.configure(text=f"Rp {total:,}".replace(",", "."))
        self.refresh_comparison()

    def refresh_comparison(self):
        try: physical_total = int(self.lbl_grand_total.cget("text").replace("Rp ", "").replace(".", ""))
        except: physical_total = 0
        act_tab = self.controller.tabs.get("ACT")
        if act_tab and act_tab.file_path:
            self.comp_frame.pack(fill="x", pady=(0, 10), before=self.btn_box)
            sys_cash_total = sum(cash_portion(t) for t in act_tab.transactions)
            self.lbl_sys_total.configure(text=f"Rp {sys_cash_total:,}".replace(",", "."), text_color=TEXT_COLOR)
            diff = physical_total - sys_cash_total
            diff_text = f"Rp {diff:,}".replace(",", ".")
            if diff > 0:
                diff_text = f"+ {diff_text}"
                self.lbl_diff.configure(text_color="#2e7d32")
            elif diff < 0:
                self.lbl_diff.configure(text_color="#d32f2f")
            else:
                self.lbl_diff.configure(text_color=TEXT_COLOR)
            self.lbl_diff.configure(text=diff_text)
        else:
            self.comp_frame.pack_forget()

    def show_preview(self):
        cashier_name = self.cashier_var.get()
        if cashier_name in ["Pilih data Kasir", "Data Kasir Kosong"] or "Kosong" in cashier_name:
            messagebox.showwarning("Data Tidak Lengkap", "Silakan pilih data kasir terlebih dahulu.")
            return

        total_val = int(self.lbl_grand_total.cget("text").replace("Rp ", "").replace(".", ""))
        if total_val == 0:
            messagebox.showwarning("Data Kosong", "Total perhitungan tidak boleh nol.")
            return

        # Fetch cashier details
        self.active_cashier_data = None
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
                for u in users:
                    if u["name"] == cashier_name:
                        self.active_cashier_data = u
                        break
        
        if not self.active_cashier_data:
            messagebox.showerror("Error", f"Data kasir '{cashier_name}' tidak ditemukan. Kembali ke input.")
            return

        self.input_view.pack_forget()
        self.preview_view.pack(fill="both", expand=True)
        self.update_receipt_preview()

    def show_input_view(self):
        self.preview_view.pack_forget()
        self.input_view.pack(fill="both", expand=True)

    def update_receipt_preview(self):
        size = self.print_size_var.get()
        char_width = self.get_receipt_char_width(for_print=False)
        self.receipt_paper.configure(width=280 if size == "58" else 420)
        
        receipt_text = self.generate_receipt_text(char_width)
        self.lbl_receipt_text.configure(text=receipt_text)

    def get_receipt_char_width(self, for_print=False):
        size = self.print_size_var.get()
        if for_print:
            return 30 if size == "58" else 40
        return 32 if size == "58" else 48

    def format_key_value_line(self, label, value, width):
        left = str(label)
        right = str(value)
        space = width - len(left) - len(right)
        if space < 1:
            return f"{left} {right}"
        return f"{left}{' ' * space}{right}"

    def format_amount_line(self, label, amount, width):
        right = f"Rp {amount:,}".replace(",", ".")
        space = width - len(label) - len(right)
        if space < 2:
            words = label.split(" ", 1)
            if len(words) == 2:
                first, rest = words
                space1 = width - len(first) - len(right)
                if space1 >= 1:
                    return f"{first}{' ' * space1}{right}\n{rest}"
            return f"{label} {right}"
        return f"{label}{' ' * space}{right}"

    def add_receipt_margin(self, lines, width, margin=2):
        inner_width = max(width - (margin * 2), 10)
        pad = " " * margin
        padded_lines = []

        for line in lines:
            if not line:
                padded_lines.append("")
                continue
            clipped = line[:inner_width]
            padded_lines.append(f"{pad}{clipped.ljust(inner_width)}{pad}")

        return padded_lines, inner_width

    def build_escpos_arabic_image(self):
        image_bytes = base64.b64decode(ARABIC_ESC_POS_IMAGE_B64)
        header = bytearray()
        header.extend(b"\x1b\x61\x01")  # Center align.
        header.extend(
            b"\x1d\x76\x30\x00"
            + bytes([ARABIC_ESC_POS_IMAGE_BYTES_PER_ROW & 0xFF, (ARABIC_ESC_POS_IMAGE_BYTES_PER_ROW >> 8) & 0xFF])
            + bytes([ARABIC_ESC_POS_IMAGE_HEIGHT & 0xFF, (ARABIC_ESC_POS_IMAGE_HEIGHT >> 8) & 0xFF])
        )
        footer = b"\n\x1b\x61\x00"
        return bytes(header) + image_bytes + footer

    def build_escpos_receipt(self, width):
        receipt_text = self.generate_receipt_text(width)
        payload = bytearray()
        payload.extend(b"\x1b@")  # Initialize printer.
        payload.extend(b"\x1b\x61\x00")  # Left align.

        for line in receipt_text.splitlines():
            stripped = line.strip()
            if not stripped:
                payload.extend(b"\n")
                continue

            if stripped == ARABIC_RECEIPT_TEXT:
                payload.extend(self.build_escpos_arabic_image())
            else:
                payload.extend(line.encode("ascii", errors="replace") + b"\n")

        payload.extend(b"\n")
        return bytes(payload)

    def generate_receipt_text(self, width):
        u = self.active_cashier_data
        now = datetime.now()
        act_tab = self.controller.tabs.get("ACT")
        transactions = act_tab.transactions if act_tab else []
        non_cash_total = sum(noncash_portion(t) for t in transactions)
        physical_lines = []
        physical_total = 0
        margin = 2
        inner_width = max(width - (margin * 2), 10)
        
        lines = []
        lines.append("TOKO LAY".center(inner_width))
        lines.append("Laporan Penjualan".center(inner_width))
        lines.append("-" * inner_width)
        lines.append(self.format_key_value_line("Tanggal", now.strftime('%d/%m/%Y'), inner_width))
        lines.append(self.format_key_value_line("Cabang", u["branch"], inner_width))
        lines.append(self.format_key_value_line("Shift", u["shift"], inner_width))
        lines.append(self.format_key_value_line("Kasir", u["name"], inner_width))
        lines.append(self.format_key_value_line("User ID", u["id"], inner_width))
        lines.append("-" * inner_width)
        
        for denom in self.denominations:
            qty = int(self.inputs[denom].get() or 0)
            if qty > 0:
                subtotal = qty * denom
                physical_total += subtotal
                
                left_part = f"{denom:,} x {qty}".replace(",", ".")
                right_part = f"Rp {subtotal:,}".replace(",", ".")
                
                space = inner_width - len(left_part) - len(right_part)
                if space < 1:
                    physical_lines.append(left_part)
                    physical_lines.append(right_part.rjust(inner_width))
                else:
                    physical_lines.append(f"{left_part}{' ' * space}{right_part}")
        
        sales_total = physical_total + non_cash_total + self.expense_amount
        for sub_line in self.format_amount_line("Total Penjualan", sales_total, inner_width).split("\n"):
            lines.append(sub_line)
        lines.append(self.format_amount_line("Non Tunai", non_cash_total, inner_width))
        lines.append(self.format_amount_line("Pengeluaran", self.expense_amount, inner_width))
        lines.append("-" * inner_width)
        lines.append("-- Rincian Uang Fisik --".center(inner_width))
        lines.extend(physical_lines)
        lines.append("-" * inner_width)
        lines.append(self.format_amount_line("TOTAL FISIK", physical_total, inner_width))
        lines.append("-" * inner_width)

        if self.expense_note.strip():
            raw_lines = self.expense_note.strip().splitlines()
            first = True
            for raw in raw_lines:
                prefix = "Ket: " if first else ""
                first = False
                text_to_wrap = f"{prefix}{raw}".strip()
                wrapped = textwrap.wrap(text_to_wrap, width=inner_width)
                for w in wrapped:
                    lines.append(w.center(inner_width))

        lines.append(now.strftime('%d/%m/%Y %H:%M:%S').center(inner_width))
        lines.append(ARABIC_RECEIPT_TEXT.center(inner_width))

        lines, _ = self.add_receipt_margin(lines, width, margin)
        
        return "\n".join(lines)

    def save_and_print(self):
        # Save to history first
        total_val = int(self.lbl_grand_total.cget("text").replace("Rp ", "").replace(".", ""))
        data = {
            "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "cashier": self.active_cashier_data["name"],
            "denominations": {str(d): int(self.inputs[d].get() or 0) for d in self.denominations},
            "grand_total": total_val,
            "expense": self.expense_amount,
            "note": self.expense_note
        }
        
        history = []
        if os.path.exists(CALC_HISTORY_FILE):
            try:
                with open(CALC_HISTORY_FILE, "r") as f: history = json.load(f)
            except: pass
        history.append(data)
        with open(CALC_HISTORY_FILE, "w") as f: json.dump(history, f, indent=4)

        # Printing logic using win32print
        char_width = self.get_receipt_char_width(for_print=True)
        receipt_text = self.generate_receipt_text(char_width)
        
        if win32print:
            try:
                printer_name = win32print.GetDefaultPrinter()
                if not printer_name:
                    raise Exception("Printer default tidak ditemukan. Silakan set printer di Windows.")
                
                hPrinter = win32print.OpenPrinter(printer_name)
                try:
                    # 'RAW' mode sends data directly to printer
                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("Struk Kasir", None, "RAW"))
                    try:
                        win32print.StartPagePrinter(hPrinter)
                        win32print.WritePrinter(hPrinter, self.build_escpos_receipt(char_width))
                        win32print.EndPagePrinter(hPrinter)
                    finally:
                        win32print.EndDocPrinter(hPrinter)
                finally:
                    win32print.ClosePrinter(hPrinter)
                messagebox.showinfo("Sukses", f"Data berhasil dicetak ke {printer_name}")
            except Exception as e:
                # Show specific error to help debugging
                error_msg = str(e)
                messagebox.showerror("Error Cetak", f"Gagal mencetak: {error_msg}")
        else:
            # Fallback to old method if win32print is not available
            messagebox.showwarning("Modul Hilang", "Modul win32print tidak terdeteksi. Menggunakan metode sistem...")
            fd, path = tempfile.mkstemp(suffix=".txt")
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                    tmp.write(receipt_text)
                os.startfile(path, "print")
            except Exception as e:
                messagebox.showerror("Error Cetak", f"Gagal mengirim ke printer: {e}")
        
        self.clear_all_silent()
        self.show_input_view()

    def clear_all(self):
        if messagebox.askyesno("Reset Semua", "Reset semua input ke nol?"):
            self.clear_all_silent()

    def clear_all_silent(self):
        self.clear_expense(silent=True)
        for denom in self.denominations:
            self.inputs[denom].delete(0, "end")
            self.subtotal_labels[denom].configure(text="Rp 0")
        self.lbl_grand_total.configure(text="Rp 0")
        self.refresh_comparison()

    def load_cashiers(self):
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, "r") as f:
                    users = json.load(f)
                    names = [u["name"] for u in users]
                    if names:
                        self.cashier_menu.configure(values=names)
                        if self.cashier_var.get() in ["Data Kasir Kosong", "Data Kasir Kosong (Buka Tab Kasir)", "Data Kasir Kosong (Buka User Tab)", ""]:
                            self.cashier_var.set("Pilih data Kasir")
                    else:
                        self.cashier_menu.configure(values=["Data Kasir Kosong (Buka Tab Kasir)"])
                        self.cashier_var.set("Data Kasir Kosong (Buka Tab Kasir)")
            except: pass

    def on_activate(self):
        self.load_cashiers()
        self.refresh_comparison()
