import customtkinter as ctk
import json
import os
import tempfile
from datetime import datetime
from tkinter import messagebox
from constants import (HEADER_FONT, TEXT_COLOR, MAIN_FONT, CONSOLE_COLOR, 
                       BORDER_COLOR, ACCENT_COLOR, USERS_FILE, CALC_HISTORY_FILE, 
                       SMALL_FONT, SIDEBAR_COLOR, STATUS_PAID_BG)

try:
    import win32print # type: ignore
except ImportError:
    win32print = None

class CalculateTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        
        self.denominations = [
            100000, 75000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100
        ]
        self.inputs = {} 
        self.subtotal_labels = {}
        
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
        
        date_str = datetime.now().strftime("%d/%m/%Y")
        ctk.CTkLabel(self.header_frame, text=f"Date: {date_str}", font=("Segoe UI", 11, "bold"), text_color=ACCENT_COLOR).pack(pady=(15, 5))
        
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
        self.cashier_menu.pack(pady=(0, 15), padx=25, fill="x")

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
        
        ctk.CTkLabel(self.total_frame, text="Grand Total:", font=("Segoe UI", 14, "bold"), text_color="black").pack(side="left", padx=15, pady=10)
        self.lbl_grand_total = ctk.CTkLabel(self.total_frame, text="Rp 0", font=("Segoe UI", 16, "bold"), text_color="black")
        self.lbl_grand_total.pack(side="right", padx=15, pady=10)
        
        self.comp_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.comp_frame.pack(fill="x", pady=(0, 10))
        
        self.sys_row = ctk.CTkFrame(self.comp_frame, fg_color="transparent")
        self.sys_row.pack(fill="x")
        ctk.CTkLabel(self.sys_row, text="Total System (Cash):", font=("Segoe UI", 11), text_color="grey").pack(side="left", padx=5)
        self.lbl_sys_total = ctk.CTkLabel(self.sys_row, text="No Active Session", font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR)
        self.lbl_sys_total.pack(side="right", padx=5)
        
        self.diff_row = ctk.CTkFrame(self.comp_frame, fg_color="transparent")
        self.diff_row.pack(fill="x")
        ctk.CTkLabel(self.diff_row, text="Difference:", font=("Segoe UI", 11), text_color="grey").pack(side="left", padx=5)
        self.lbl_diff = ctk.CTkLabel(self.diff_row, text="Rp 0", font=("Segoe UI", 12, "bold"), text_color=TEXT_COLOR)
        self.lbl_diff.pack(side="right", padx=5)
        
        btn_box = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        btn_box.pack(fill="x")
        
        self.btn_preview = ctk.CTkButton(btn_box, text="Preview", fg_color=ACCENT_COLOR, text_color="white", corner_radius=5, command=self.show_preview)
        self.btn_preview.pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_box, text="Clear All", fg_color="#666666", text_color="white", corner_radius=5, command=self.clear_all).pack(side="left", expand=True, padx=5)

        # --- MODE PREVIEW ---
        self.preview_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        # Hidden by default

        self.preview_header = ctk.CTkFrame(self.preview_view, fg_color="transparent")
        self.preview_header.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.preview_header, text="Preview Struk", font=HEADER_FONT, text_color=TEXT_COLOR).pack(side="left")
        ctk.CTkButton(self.preview_header, text="Back", width=60, fg_color="#666666", text_color="white", command=self.show_input_view).pack(side="right")

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
            sys_cash_total = sum(t["amount"] for t in act_tab.transactions if t["category"] == "Cash")
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
            self.lbl_sys_total.configure(text="No Active Session", text_color="grey")
            self.lbl_diff.configure(text="Rp 0", text_color="grey")

    def show_preview(self):
        cashier_name = self.cashier_var.get()
        if cashier_name in ["Pilih data Kasir", "Data Kasir Kosong"]:
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
        # Direct printing allows us to use standard 32/48 widths reliably
        char_width = 32 if size == "58" else 48
        self.receipt_paper.configure(width=280 if size == "58" else 420)
        
        receipt_text = self.generate_receipt_text(char_width)
        self.lbl_receipt_text.configure(text=receipt_text)

    def generate_receipt_text(self, width):
        u = self.active_cashier_data
        now = datetime.now()
        
        lines = []
        lines.append("Toko Lay".center(width))
        lines.append("Laporan Penjualan Kasir".center(width))
        lines.append("-" * width)
        lines.append(f"Tgl    : {now.strftime('%d/%m/%Y')}")
        lines.append(f"Cabang : {u['branch'][:width-9]}")
        lines.append(f"Nama   : {u['name'][:width-9]}")
        lines.append(f"ID     : {u['id'][:width-9]}")
        lines.append(f"Shift  : {u['shift'][:width-9]}")
        lines.append("-" * width)
        lines.append("Jumlah Uang Fisik :")
        lines.append("")
        
        grand_total = 0
        for denom in self.denominations:
            qty = int(self.inputs[denom].get() or 0)
            if qty > 0:
                subtotal = qty * denom
                grand_total += subtotal
                
                # Format: "100.000 x 10"
                left_part = f"{denom:,} x {qty}".replace(",", ".")
                # Format: "Rp 1.000.000"
                right_part = f"Rp {subtotal:,}".replace(",", ".")
                
                space = width - len(left_part) - len(right_part)
                if space < 1: # Fallback if line too long
                    lines.append(left_part)
                    lines.append(right_part.rjust(width))
                else:
                    lines.append(f"{left_part}{' ' * space}{right_part}")
        
        lines.append("-" * width)
        total_label = "Total:"
        total_val = f"Rp {grand_total:,}".replace(",", ".")
        total_space = width - len(total_label) - len(total_val)
        lines.append(f"{total_label}{' ' * total_space}{total_val}")
        lines.append("-" * width)
        
        lines.append(f"Cetak: {now.strftime('%H:%M:%S')}")
        lines.append("")
        lines.append("Terimakasih".center(width))
        lines.append("شكراً جزيلاً".center(width))
        lines.append("\n\n\n\n\n") # Extra lines for physical cutting
        
        return "\n".join(lines)

    def save_and_print(self):
        # Save to history first
        total_val = int(self.lbl_grand_total.cget("text").replace("Rp ", "").replace(".", ""))
        data = {
            "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "cashier": self.active_cashier_data["name"],
            "denominations": {str(d): int(self.inputs[d].get() or 0) for d in self.denominations},
            "grand_total": total_val
        }
        
        history = []
        if os.path.exists(CALC_HISTORY_FILE):
            try:
                with open(CALC_HISTORY_FILE, "r") as f: history = json.load(f)
            except: pass
        history.append(data)
        with open(CALC_HISTORY_FILE, "w") as f: json.dump(history, f, indent=4)

        # Printing logic using win32print
        receipt_text = self.lbl_receipt_text.cget("text")
        
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
                        # Use utf-8 for Arabic support. 
                        # Note: Some older printers might still need specific ESC/POS commands 
                        # to switch to Arabic code page, but utf-8 is the first step.
                        win32print.WritePrinter(hPrinter, receipt_text.encode('utf-8', errors='replace'))
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
        if messagebox.askyesno("Clear All", "Reset semua input ke nol?"):
            self.clear_all_silent()

    def clear_all_silent(self):
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
                    if names: self.cashier_menu.configure(values=names)
                    else:
                        self.cashier_menu.configure(values=["Data Kasir Kosong"])
                        self.cashier_var.set("Data Kasir Kosong")
            except: pass

    def on_activate(self):
        self.load_cashiers()
        self.refresh_comparison()
