import customtkinter as ctk
import os
import json
import tkinter.font as tkfont
from datetime import datetime
from tkinter import messagebox
from constants import SIDEBAR_COLOR, BORDER_COLOR, TEXT_COLOR, STATUS_TOTAL_BG, DISPLAY_FONT, ACCENT_COLOR, MAIN_FONT, SMALL_FONT, CONSOLE_COLOR, STATUS_PAID_BG, HEADER_FONT


def match_filter(t, current_filter):
    """True jika transaksi cocok dengan filter aktif (Split ikut Cash/NonCash/Inputs)."""
    c = t.get("category")
    if current_filter == "All":
        return True
    if current_filter == "Inputs":
        return c in ("Cash", "Non Cash", "Split")
    if current_filter == "Cash":
        return c in ("Cash", "Split")
    if current_filter == "Non Cash":
        return c in ("Non Cash", "Split")
    return c == current_filter


def display_amount(t, current_filter):
    """Nominal tampil: porsi cash/non-cash untuk Split pada filter Cash/Non Cash, total jika tidak."""
    if t.get("category") == "Split":
        if current_filter == "Cash":
            return int(t.get("cash_part", 0))
        if current_filter == "Non Cash":
            return int(t.get("noncash_part", 0))
    return int(t.get("amount", 0))

class SessionTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        self.file_path = None
        self.transactions = []
        self.current_filter = "All"
        self.editing_index = None
        self.editing_category = None
        self.current_page = 0
        self.page_size = 3
        self.action_buttons = []
        self.item_buttons = []
        self.uninput_detail_idx = None
        self.split_detail_idx = None
        self.auto_input_from_ketoko = False
        self.setup_ui()

    def setup_ui(self):
        # Header Info
        self.header_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_COLOR, height=40, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.header_frame.pack_propagate(False)
        
        self.lbl_session = ctk.CTkLabel(self.header_frame, text="Sesi: Tidak Ada", font=("Segoe UI", 10, "bold"), text_color=TEXT_COLOR)
        self.lbl_session.pack(side="left", padx=10)
        
        self.lbl_count = ctk.CTkLabel(self.header_frame, text="Transaksi: 0", font=("Segoe UI", 10), text_color="grey")
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
        self.btn_grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="btns")

        self.btn_cash = self.create_input_btn(self.btn_grid, "Cash", "#2e7d32", "#e8f5e9", "Cash", 0)
        self.btn_non = self.create_input_btn(self.btn_grid, "NonCash", "#fbc02d", "#fffde7", "Non Cash", 1)
        self.btn_split = self.create_input_btn(self.btn_grid, "Split", "#4e73df", "#eef2fb", "Split", 2)
        self.btn_unin = self.create_input_btn(self.btn_grid, "UnInput", "#d32f2f", "#ffebee", "Uninput", 3)

        # Edit Controls
        self.edit_frame = ctk.CTkFrame(self.input_area, fg_color="transparent")
        ctk.CTkButton(self.edit_frame, text="Batal", fg_color="#666666", text_color="white", corner_radius=0, font=MAIN_FONT, height=38, command=self.cancel_edit).pack(fill="x")

        # Filter Section
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=20, pady=(5, 0))
        self.filter_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="flt")

        self.btn_filter_all = self.create_filter_btn("All", "All", 0)
        self.btn_filter_inputs = self.create_filter_btn("Inputs", "Inputs", 1)
        self.btn_filter_cash = self.create_filter_btn("Cash", "Cash", 2)
        self.btn_filter_non = self.create_filter_btn("NonCash", "Non Cash", 3)
        self.btn_filter_split = self.create_filter_btn("Split", "Split", 4)
        self.btn_filter_unin = self.create_filter_btn("UnInput", "Uninput", 5)

        # List Area
        self.scroll_log = ctk.CTkScrollableFrame(self, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.scroll_log._scrollbar.grid_forget()
        self.scroll_log.pack(fill="both", expand=True, padx=20, pady=5)

        # Uninput Detail View (hidden by default)
        self.ud_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ud_header = ctk.CTkFrame(self.ud_frame, fg_color=SIDEBAR_COLOR, height=40, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.ud_header.pack(fill="x", padx=10, pady=(10, 0))
        self.ud_header.pack_propagate(False)
        ctk.CTkButton(self.ud_header, text="< Kembali", width=60, fg_color="#666666", text_color="white", corner_radius=0, font=SMALL_FONT, command=self.hide_uninput_detail).pack(side="left", padx=5)
        self.ud_title = ctk.CTkLabel(self.ud_header, text="Item Belum Diinput", font=("Segoe UI", 10, "bold"), text_color=TEXT_COLOR)
        self.ud_title.pack(side="left", expand=True)
        self.ud_scroll = ctk.CTkScrollableFrame(self.ud_frame, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.ud_scroll._scrollbar.grid_forget()
        self.ud_scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Pagination
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=20, pady=5)
        
        self.btn_prev = ctk.CTkButton(self.pagination_frame, text="<", width=30, height=25, font=("Segoe UI", 12, "bold"), fg_color="#e5e5e5", text_color="black", corner_radius=0, command=self.prev_page)
        self.btn_prev.pack(side="left")
        
        self.lbl_page = ctk.CTkLabel(self.pagination_frame, text="Halaman 1 dari 1", font=SMALL_FONT, text_color=TEXT_COLOR)
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.pagination_frame, text=">", width=30, height=25, font=("Segoe UI", 12, "bold"), fg_color="#e5e5e5", text_color="black", corner_radius=0, command=self.next_page)
        self.btn_next.pack(side="right")

        # Footer
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", side="bottom", padx=20, pady=10)
        
        self.total_display_frame = ctk.CTkFrame(self.footer, fg_color=STATUS_PAID_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.total_display_frame.pack(fill="x", pady=5)
        
        self.lbl_total_label = ctk.CTkLabel(self.total_display_frame, text="Total Nominal :", font=("Segoe UI", 16), text_color="black")
        self.lbl_total_label.pack(side="left", padx=15, pady=15)
        
        self.lbl_total = ctk.CTkLabel(self.total_display_frame, text="0.00", font=HEADER_FONT, text_color="black")
        self.lbl_total.pack(side="right", padx=15, pady=15)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_list()

    def next_page(self):
        indexed_data = list(enumerate(self.transactions))
        filtered_data = [t for i, t in indexed_data if match_filter(t, self.current_filter)]
        max_pages = (len(filtered_data) - 1) // self.page_size
        if self.current_page < max_pages:
            self.current_page += 1
            self.refresh_list()

    def create_filter_btn(self, text, cat, col):
        w = tkfont.Font(family="Segoe UI", size=10).measure(text) + 8
        btn = ctk.CTkButton(self.filter_frame, text=text, width=w, height=25, font=SMALL_FONT, fg_color="#e5e5e5", text_color="black", corner_radius=0, command=lambda: self.set_filter(cat))
        btn.grid(row=0, column=col, sticky="ew", padx=1)
        self.action_buttons.append(btn)
        return btn

    def create_input_btn(self, parent, text, color, bg, cat, col):
        w = tkfont.Font(family="Segoe UI", size=11, weight="bold").measure(text) + 8
        btn = ctk.CTkButton(parent, text=text, width=w, height=38, fg_color=bg, hover_color="#e0e0e0", font=("Segoe UI", 11, "bold"), text_color=color, border_width=1, border_color=BORDER_COLOR, corner_radius=0, command=lambda: self.add_transaction(cat))
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
        btns = {"All": self.btn_filter_all, "Inputs": self.btn_filter_inputs, "Cash": self.btn_filter_cash, "Non Cash": self.btn_filter_non, "Split": self.btn_filter_split, "Uninput": self.btn_filter_unin}
        for cat, btn in btns.items():
            is_active = cat == self.current_filter
            btn.configure(fg_color=ACCENT_COLOR if is_active else "#e5e5e5", text_color="white" if is_active else "black")

    def update_edit_visuals(self):
        btns = {"Cash": self.btn_cash, "Non Cash": self.btn_non, "Split": self.btn_split, "Uninput": self.btn_unin}
        for cat, btn in btns.items():
            if self.editing_index is not None and cat == self.editing_category:
                btn.configure(border_width=2, border_color=ACCENT_COLOR)
            else:
                btn.configure(border_width=1, border_color=BORDER_COLOR)

    def show_uninput_popup(self, existing_items=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Input Item")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 400) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 350) // 2
        dialog.geometry(f"+{x}+{y}")

        result = None
        entries = []

        items_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        items_frame.pack(fill="both", expand=True, padx=20, pady=10)

        def add_entry(val=""):
            f = ctk.CTkFrame(items_frame, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text="Item:", font=MAIN_FONT, text_color=TEXT_COLOR, width=40).pack(side="left")
            entry = ctk.CTkEntry(f, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=0)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            entry.insert(0, val)
            entry.bind("<Return>", lambda e: (add_entry(), entries[-1].focus()))
            entry.bind("<Tab>", lambda e: save_btn.focus())
            entries.append(entry)

        def on_save():
            nonlocal result
            items = [e.get().strip() for e in entries if e.get().strip()]
            if not items:
                messagebox.showwarning("Peringatan", "Silakan tambahkan minimal satu item.")
                return
            result = items
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        if existing_items:
            for item in existing_items:
                add_entry(item)
        else:
            add_entry()

        if entries:
            entries[0].focus()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="+ Tambah", fg_color="#666666", text_color="white", corner_radius=0, command=add_entry).pack(side="left", padx=5)
        save_btn = ctk.CTkButton(btn_frame, text="Simpan", fg_color=ACCENT_COLOR, text_color="white", corner_radius=0, command=on_save)
        save_btn.pack(side="right", padx=5)
        save_btn.bind("<Return>", lambda e: on_save())
        ctk.CTkButton(btn_frame, text="Batal", fg_color="#ff4444", text_color="white", corner_radius=0, command=on_cancel).pack(side="right", padx=5)

        dialog.wait_window()
        return result

    @staticmethod
    def parse_split_input(raw):
        digits = "".join(ch for ch in (raw or "").replace(".", "") if ch.isdigit())
        return int(digits) if digits else 0

    @staticmethod
    def split_counterpart(typed, total):
        """Pasangan auto-isi: 0 jika ketikan 0, else total-ketikan (batas bawah 0)."""
        if typed <= 0:
            return 0
        return max(0, total - typed)

    def show_split_popup(self, total, pre_cash=None, pre_non=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Split Tunai + Non Tunai")
        dialog.geometry("340x260")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 340) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 260) // 2
        dialog.geometry(f"+{x}+{y}")

        result = None
        total_fmt = f"{total:,}".replace(",", ".")

        ctk.CTkLabel(dialog, text=f"Total: Rp {total_fmt}", font=MAIN_FONT, text_color=TEXT_COLOR).pack(pady=(15, 5))
        lbl_rest = ctk.CTkLabel(dialog, text="", font=SMALL_FONT, text_color="grey")
        lbl_rest.pack(pady=(0, 5))

        def fmt(v):
            return f"{v:,}".replace(",", ".")

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="x", padx=20)
        ctk.CTkLabel(body, text="Tunai (Rp):", font=MAIN_FONT, text_color=TEXT_COLOR).pack(anchor="w")
        entry_cash = ctk.CTkEntry(body, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=0, justify="right")
        entry_cash.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(body, text="Non Tunai (Rp):", font=MAIN_FONT, text_color=TEXT_COLOR).pack(anchor="w")
        entry_non = ctk.CTkEntry(body, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=0, justify="right")
        entry_non.pack(fill="x")

        entry_cash.insert(0, "" if pre_cash is None else fmt(pre_cash))
        entry_non.insert(0, "" if pre_non is None else fmt(pre_non))

        def set_entry(e, v):
            e.delete(0, "end")
            e.insert(0, fmt(v))

        def own_value(e):
            digits = "".join(ch for ch in e.get().replace(".", "") if ch.isdigit())
            e.delete(0, "end")
            if digits:
                e.insert(0, fmt(int(digits)))
                return int(digits)
            return 0

        def update_rest():
            rest = total - self.parse_split_input(entry_cash.get()) - self.parse_split_input(entry_non.get())
            lbl_rest.configure(text=f"Sisa: Rp {fmt(rest)}" if rest != 0 else "Pas ✔")

        def on_cash(event=None):
            c = own_value(entry_cash)
            set_entry(entry_non, self.split_counterpart(c, total))
            update_rest()

        def on_non(event=None):
            n = own_value(entry_non)
            set_entry(entry_cash, self.split_counterpart(n, total))
            update_rest()

        entry_cash.bind("<KeyRelease>", on_cash)
        entry_non.bind("<KeyRelease>", on_non)
        entry_cash.focus()
        update_rest()

        def on_save(event=None):
            nonlocal result
            c = self.parse_split_input(entry_cash.get())
            n = self.parse_split_input(entry_non.get())
            if c + n != total:
                messagebox.showwarning("Peringatan", f"Tunai + Non Tunai harus = Rp {total_fmt}.")
                return
            result = (c, n)
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Batal", fg_color="#666666", text_color="white", corner_radius=0, command=dialog.destroy).pack(side="left", padx=5)
        save_btn = ctk.CTkButton(btn_frame, text="Simpan", fg_color=ACCENT_COLOR, text_color="white", corner_radius=0, command=on_save)
        save_btn.pack(side="right", padx=5)
        entry_non.bind("<Return>", on_save)
        entry_cash.bind("<Return>", lambda e: entry_non.focus())

        dialog.wait_window()
        return result

    def on_activate(self):
        self.entry_amount.focus_set()
        if self.file_path:
            self.lbl_session.configure(text=f"Sesi: {os.path.basename(self.file_path)}")
        self.update_filter_visuals()

    def apply_ketoko_prefill(self, raw_value: str, from_ketoko: bool = False):
        """Prefill nominal jika ada hasil baca dari Ketoko, set flag auto input."""
        self.auto_input_from_ketoko = bool(from_ketoko)
        if raw_value and raw_value.isdigit():
            formatted = "{:,}".format(int(raw_value)).replace(",", ".")
            self.entry_amount.delete(0, "end")
            self.entry_amount.insert(0, formatted)
            
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

    def _next_label(self):
        labels = [t["label"] for t in self.transactions if t.get("category") in ("Cash", "Non Cash", "Split") and isinstance(t.get("label"), int)]
        return max(labels) + 1 if labels else None

    def _ask_first_label(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Label")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 300) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        result = None
        ctk.CTkLabel(dialog, text="Nomor label pertama :", font=MAIN_FONT, text_color=TEXT_COLOR).pack(pady=(15, 5))
        entry = ctk.CTkEntry(dialog, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=0, justify="center")
        entry.pack(padx=20, fill="x")
        entry.focus()

        def on_save(event=None):
            nonlocal result
            val = entry.get().strip()
            if not val.isdigit():
                messagebox.showwarning("Peringatan", "Nomor label harus angka.")
                return
            result = int(val)
            dialog.destroy()

        entry.bind("<Return>", on_save)
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Batal", fg_color="#666666", text_color="white", corner_radius=0, command=dialog.destroy).pack(side="left", padx=5)
        save_btn = ctk.CTkButton(btn_frame, text="Simpan", fg_color=ACCENT_COLOR, text_color="white", corner_radius=0, command=on_save)
        save_btn.pack(side="right", padx=5)
        dialog.wait_window()
        return result

    def add_transaction(self, cat):
        if self.editing_index is not None:
            txn = self.transactions[self.editing_index]
            old_cat = txn["category"]
            val_str = self.entry_amount.get().replace(".", "")
            new_total = int(val_str) if val_str else int(txn["amount"])

            items = None
            if cat == "Uninput" and old_cat != "Uninput":
                items = self.show_uninput_popup()
                if items is None:
                    return

            parts = None
            if cat == "Split":
                if old_cat == "Split" and txn.get("cash_part", 0) + txn.get("noncash_part", 0) == new_total:
                    pre_c, pre_n = txn["cash_part"], txn["noncash_part"]
                else:
                    pre_c, pre_n = new_total, 0
                parts = self.show_split_popup(new_total, pre_cash=pre_c, pre_non=pre_n)
                if parts is None:
                    return

            nxt = None
            if old_cat == "Uninput" and cat != "Uninput":
                nxt = self._next_label()
                if nxt is None:
                    nxt = self._ask_first_label()
                    if nxt is None:
                        return

            if cat == "Uninput" and old_cat != "Uninput":
                txn["items"] = items
                txn.pop("label", None)

            if old_cat == "Uninput" and cat != "Uninput":
                txn.pop("items", None)
                txn["label"] = nxt

            if cat == "Split":
                txn.pop("items", None)
                txn["cash_part"], txn["noncash_part"] = parts
            elif old_cat == "Split":
                txn.pop("cash_part", None)
                txn.pop("noncash_part", None)

            if val_str:
                txn["amount"] = int(val_str)
            txn["category"] = cat
            self.save_session()
            self.cancel_edit()
            self.refresh_list()
            return

        if cat == "Uninput":
            items = self.show_uninput_popup()
            if items is None:
                return

        val_str = self.entry_amount.get().replace(".", "")
        if not val_str: return
        total = int(val_str)
        parts = None
        if cat == "Split":
            parts = self.show_split_popup(total)
            if parts is None:
                return
        txn = {
            "amount": total,
            "category": cat,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if cat == "Uninput":
            txn["items"] = items
        else:
            nxt = self._next_label()
            if nxt is None:
                nxt = self._ask_first_label()
                if nxt is None:
                    return
            txn["label"] = nxt
            if cat == "Split":
                txn["cash_part"], txn["noncash_part"] = parts
        should_trigger_pay = self.auto_input_from_ketoko and cat in ("Cash", "Non Cash", "Split")
        self.auto_input_from_ketoko = False

        self.transactions.append(txn)
        self.save_session()
        self.entry_amount.delete(0, "end")
        self.current_page = 0
        self.refresh_list()
        self.controller.return_focus(trigger_pay=should_trigger_pay)
        self.entry_amount.focus()

    def delete_transaction(self, idx):
        if messagebox.askyesno("Konfirmasi", "Hapus transaksi ini?"):
            self.transactions.pop(idx)
            self.save_session()
            self.refresh_list()

    def edit_transaction(self, idx):
        self.editing_index = idx
        self.editing_category = self.transactions[idx]["category"]
        item = self.transactions[idx]
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, f"{item['amount']:,}".replace(",", "."))
        self.edit_frame.pack(fill="x")
        self.entry_amount.focus()
        self.update_edit_visuals()

    def cancel_edit(self):
        self.editing_index = None
        self.editing_category = None
        self.entry_amount.delete(0, "end")
        self.edit_frame.pack_forget()
        self.update_edit_visuals()

    def show_uninput_detail(self, idx):
        self.uninput_detail_idx = idx
        item = self.transactions[idx]
        items = item.get("items", [])
        self.ud_title.configure(text=f"Item - Rp {item['amount']:,}".replace(",", "."))

        for w in self.ud_scroll.winfo_children():
            w.destroy()

        for i, text in enumerate(items):
            row = ctk.CTkFrame(self.ud_scroll, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=0)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=f"{i+1}.", font=MAIN_FONT, text_color=TEXT_COLOR, width=30).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(row, text=text, font=MAIN_FONT, text_color=TEXT_COLOR, anchor="w").pack(side="left", fill="x", expand=True, padx=5, pady=5)
            ctk.CTkButton(row, text="📋", width=30, height=25, corner_radius=0, font=SMALL_FONT, fg_color="#f5f5f5", text_color="black", command=lambda t=text: self.copy_clipboard(t)).pack(side="right", padx=5)

        self.scroll_log.pack_forget()
        self.pagination_frame.pack_forget()
        self.ud_frame.pack(fill="both", expand=True)

    def show_split_detail(self, idx):
        self.split_detail_idx = idx
        item = self.transactions[idx]
        cash = int(item.get("cash_part", 0))
        non = int(item.get("noncash_part", 0))
        self.ud_title.configure(text=f"Split - Rp {item['amount']:,}".replace(",", "."))

        for w in self.ud_scroll.winfo_children():
            w.destroy()

        for label, val in (("Tunai", cash), ("Non Tunai", non), ("Total", int(item["amount"]))):
            row = ctk.CTkFrame(self.ud_scroll, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=0)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=label, font=MAIN_FONT, text_color=TEXT_COLOR, anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(row, text=f"Rp {val:,}".replace(",", "."), font=("Segoe UI", 11, "bold"), text_color=ACCENT_COLOR, anchor="e").pack(side="right", padx=10, pady=5)

        self.scroll_log.pack_forget()
        self.pagination_frame.pack_forget()
        self.ud_frame.pack(fill="both", expand=True)

    def hide_uninput_detail(self):
        self.uninput_detail_idx = None
        self.split_detail_idx = None
        self.ud_frame.pack_forget()
        self.scroll_log.pack(fill="both", expand=True, padx=20, pady=5)
        self.pagination_frame.pack(fill="x", padx=20, pady=5)
        self.refresh_list()

    def copy_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def refresh_list(self):
        self.item_buttons = []
        for w in self.scroll_log.winfo_children(): w.destroy()
        
        indexed_data = list(enumerate(self.transactions))
        filtered_data = [(i, t) for i, t in indexed_data if match_filter(t, self.current_filter)]
        
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
            
            cat_color = {"Cash": "#2e7d32", "Non Cash": "#fbc02d", "Split": ACCENT_COLOR, "Uninput": "#d32f2f"}.get(item["category"], TEXT_COLOR)

            lbl_val = ctk.CTkLabel(info_frame, text=f"Rp {display_amount(item, self.current_filter):,}".replace(",", "."), font=("Segoe UI", 12, "bold"), text_color=cat_color, anchor="w")
            lbl_val.pack(fill="x")

            ts_text = f"{item['label']} | {item['timestamp']}" if isinstance(item.get("label"), int) else item['timestamp']
            lbl_ts = ctk.CTkLabel(info_frame, text=ts_text, font=("Segoe UI", 9), text_color=TEXT_COLOR, anchor="w")
            lbl_ts.pack(fill="x")

            if item["category"] == "Uninput":
                row.bind("<Double-Button-1>", lambda e, x=idx: self.show_uninput_detail(x))
                info_frame.bind("<Double-Button-1>", lambda e, x=idx: self.show_uninput_detail(x))
                lbl_val.bind("<Double-Button-1>", lambda e, x=idx: self.show_uninput_detail(x))
                lbl_ts.bind("<Double-Button-1>", lambda e, x=idx: self.show_uninput_detail(x))
            elif item["category"] == "Split":
                row.bind("<Double-Button-1>", lambda e, x=idx: self.show_split_detail(x))
                info_frame.bind("<Double-Button-1>", lambda e, x=idx: self.show_split_detail(x))
                lbl_val.bind("<Double-Button-1>", lambda e, x=idx: self.show_split_detail(x))
                lbl_ts.bind("<Double-Button-1>", lambda e, x=idx: self.show_split_detail(x))
            
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=5)
            edit_btn = ctk.CTkButton(btns, text="Edit", width=50, height=25, corner_radius=0, font=SMALL_FONT, fg_color="#f5f5f5", text_color="black", command=lambda x=idx: self.edit_transaction(x))
            delete_btn = ctk.CTkButton(btns, text="Hapus", width=50, height=25, corner_radius=0, font=SMALL_FONT, fg_color="#ffebee", text_color="#d32f2f", hover_color="#ffcdd2", command=lambda x=idx: self.delete_transaction(x))
            edit_btn.pack(side="left", padx=2)
            delete_btn.pack(side="left", padx=2)
            self.item_buttons.extend([edit_btn, delete_btn])
        
        self.lbl_page.configure(text=f"Halaman {self.current_page + 1} dari {total_pages}")
        
        total_sum = sum(display_amount(t, self.current_filter) for i, t in filtered_data)
        self.lbl_total.configure(text=f"{total_sum:,}.00".replace(",", "."))
        n_in = sum(1 for t in self.transactions if t.get("category") != "Uninput")
        n_un = sum(1 for t in self.transactions if t.get("category") == "Uninput")
        self.lbl_count.configure(text=f"Transaksi: {n_in} | uninput: {n_un}")
