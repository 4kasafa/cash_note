import customtkinter as ctk
import json
import os
import threading
from constants import (
    HEADER_FONT, MAIN_FONT, SMALL_FONT, TEXT_COLOR, BG_COLOR,
    SIDEBAR_COLOR, CONSOLE_COLOR, BORDER_COLOR, ACCENT_COLOR,
    USERS_FILE, COLOR_KURANG, COLOR_LEBIH, COLOR_PAS
)
from gas_service import gas_service

def format_rupiah(val):
    try:
        n = int(val)
    except (ValueError, TypeError):
        return "Rp 0"
    is_neg = n < 0
    formatted = f"{abs(n):,}".replace(",", ".")
    return f"Rp -{formatted}" if is_neg else f"Rp {formatted}"

class KasirTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        
        self.users = []
        self.selected_user = None
        self.is_loading = False
        self.cashier_var = ctk.StringVar(value="Pilih User Kasir")
        
        self.setup_ui()

    def setup_ui(self):
        # 1. Header Bar (Navigation & Title)
        self.header_frame = ctk.CTkFrame(
            self, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self.header_frame.pack(fill="x", padx=15, pady=(10, 6))

        # Top row in header: Title, Badge, and Manage User Button
        top_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(10, 6))

        title_box = ctk.CTkFrame(top_row, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box, text="Tab Kasir", font=HEADER_FONT, text_color=TEXT_COLOR
        ).pack(side="left")

        # Right button: Go to User Tab
        self.btn_manage_user = ctk.CTkButton(
            top_row,
            text="User →",
            width=135,
            height=28,
            fg_color="#4b5563",
            hover_color="#374151",
            text_color="white",
            corner_radius=6,
            font=("Segoe UI", 10, "bold"),
            command=lambda: self.controller.show_tab("USR")
        )
        self.btn_manage_user.pack(side="right")

        # Selector Row in header: OptionMenu & Refresh Button
        selector_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        selector_row.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            selector_row, text="Pilih Kasir:", font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR
        ).pack(side="left", padx=(0, 8))

        self.cashier_menu = ctk.CTkOptionMenu(
            selector_row,
            variable=self.cashier_var,
            values=["Belum ada data kasir"],
            fg_color="#f3f4f6",
            text_color=TEXT_COLOR,
            button_color="#e5e7eb",
            button_hover_color="#d1d5db",
            dropdown_fg_color=SIDEBAR_COLOR,
            dropdown_text_color=TEXT_COLOR,
            dropdown_hover_color="#f3f4f6",
            corner_radius=6,
            anchor="w",
            height=32,
            font=("Segoe UI", 11),
            command=self.on_cashier_changed
        )
        self.cashier_menu.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_refresh = ctk.CTkButton(
            selector_row,
            text="↻ Muat Ulang",
            width=100,
            height=32,
            fg_color=ACCENT_COLOR,
            hover_color="#375a7f",
            text_color="white",
            corner_radius=6,
            font=("Segoe UI", 10, "bold"),
            command=self.trigger_fetch
        )
        self.btn_refresh.pack(side="right")

        # 2. Status Banner / Cashier Info Card
        self.banner_frame = ctk.CTkFrame(
            self, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self.banner_frame.pack(fill="x", padx=15, pady=(0, 6))

        self.banner_content = ctk.CTkFrame(self.banner_frame, fg_color="transparent")
        self.banner_content.pack(fill="x", padx=15, pady=8)

        self.lbl_kasir_info = ctk.CTkLabel(
            self.banner_content, text="Pilih salah satu kasir di atas untuk memulai.",
            font=MAIN_FONT, text_color=TEXT_COLOR, anchor="w"
        )
        self.lbl_kasir_info.pack(side="left", fill="x", expand=True)

        self.lbl_kasir_status = ctk.CTkLabel(
            self.banner_content, text="", font=("Segoe UI", 9, "bold"), corner_radius=4, height=22
        )
        self.lbl_kasir_status.pack(side="right")

        # 3. Summary Metric Cards
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=15, pady=(0, 6))
        self.summary_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="summary")

        # Card 1: Total Transaksi
        self.card_tx = ctk.CTkFrame(
            self.summary_frame, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self.card_tx.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        ctk.CTkLabel(self.card_tx, text="Total Transaksi (5 Hari)", font=("Segoe UI", 9, "bold"), text_color="grey").pack(pady=(6, 2))
        self.lbl_val_tx = ctk.CTkLabel(self.card_tx, text="0", font=("Segoe UI", 18, "bold"), text_color=ACCENT_COLOR)
        self.lbl_val_tx.pack(pady=(0, 6))

        # Card 2: Total Kurang
        self.card_kurang = ctk.CTkFrame(
            self.summary_frame, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self.card_kurang.grid(row=0, column=1, sticky="nsew", padx=2)
        ctk.CTkLabel(self.card_kurang, text="Total Selisih Kurang", font=("Segoe UI", 9, "bold"), text_color=COLOR_KURANG).pack(pady=(6, 2))
        self.lbl_val_kurang = ctk.CTkLabel(self.card_kurang, text="Rp 0", font=("Segoe UI", 15, "bold"), text_color=COLOR_KURANG)
        self.lbl_val_kurang.pack(pady=(0, 6))

        # Card 3: Total Lebih
        self.card_lebih = ctk.CTkFrame(
            self.summary_frame, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self.card_lebih.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
        ctk.CTkLabel(self.card_lebih, text="Total Selisih Lebih", font=("Segoe UI", 9, "bold"), text_color=COLOR_LEBIH).pack(pady=(6, 2))
        self.lbl_val_lebih = ctk.CTkLabel(self.card_lebih, text="Rp 0", font=("Segoe UI", 15, "bold"), text_color=COLOR_LEBIH)
        self.lbl_val_lebih.pack(pady=(0, 6))

        # 4. Scrollable Container for Transactions List
        self.scroll_tx = ctk.CTkScrollableFrame(
            self, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self.scroll_tx.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def on_activate(self):
        """Called when user switches to Tab Kasir."""
        self.load_users()

    def load_users(self):
        """Read users from data/users.json and populate cashier menu."""
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
            except Exception:
                self.users = []
        else:
            self.users = []

        names = [u.get("name", "Tanpa Nama") for u in self.users]

        if not names:
            self.cashier_menu.configure(values=["Belum ada data kasir"])
            self.cashier_var.set("Belum ada data kasir")
            self.selected_user = None
            self.render_no_cashiers_state()
            return

        self.cashier_menu.configure(values=names)

        current_val = self.cashier_var.get()
        if current_val in names:
            self.on_cashier_changed(current_val)
        else:
            first_user = names[0]
            self.cashier_var.set(first_user)
            self.on_cashier_changed(first_user)

    def on_cashier_changed(self, chosen_name):
        """Handle selection change from dropdown."""
        user = next((u for u in self.users if u.get("name") == chosen_name), None)
        self.selected_user = user
        self.update_cashier_status_banner()

        if not user:
            return

        has_email = bool(user.get("email", "").strip())
        has_pwd = bool(user.get("password", "").strip())

        if has_email and has_pwd:
            # Auto-request to GAS
            self.trigger_fetch()
        else:
            # Show prompt that user lacks credentials
            self.render_missing_credentials_state(user)

    def update_cashier_status_banner(self):
        if not self.selected_user:
            self.lbl_kasir_info.configure(text="Belum ada kasir yang dipilih.")
            self.lbl_kasir_status.configure(text="")
            return

        u = self.selected_user
        info_text = f"👤 {u.get('name')}  |  Cabang: {u.get('branch', '-')}  |  Shift: {u.get('shift', '-')}"
        if u.get("email"):
            info_text += f"  |  ✉ {u.get('email')}"
        self.lbl_kasir_info.configure(text=info_text)

        has_cred = bool(u.get("email") and u.get("password"))
        if has_cred:
            self.lbl_kasir_status.configure(
                text="  ● Login GAS Tersedia  ", text_color="white", fg_color=COLOR_LEBIH
            )
        else:
            self.lbl_kasir_status.configure(
                text="  ⚠️ Belum Ada Akun GAS  ", text_color="white", fg_color="#f59e0b"
            )

    def trigger_fetch(self):
        """Initiate non-blocking background request to GAS."""
        if self.is_loading:
            return

        if not self.selected_user:
            return

        email = self.selected_user.get("email", "").strip()
        pwd = self.selected_user.get("password", "").strip()
        cashier_name = self.selected_user.get("name", "")

        if not email or not pwd:
            self.render_missing_credentials_state(self.selected_user)
            return

        self.is_loading = True
        self.btn_refresh.configure(state="disabled", text="⏳ Memuat...")
        self.render_loading_state()

        def worker():
            res = gas_service.fetch_kasir_summary(email, pwd, cashier_name)
            self.after(0, lambda: self.handle_fetch_result(res))

        threading.Thread(target=worker, daemon=True).start()

    def handle_fetch_result(self, res):
        """Process GAS response on the main UI thread."""
        self.is_loading = False
        self.btn_refresh.configure(state="normal", text="↻ Muat Ulang")

        if not res or not res.get("success"):
            err_msg = res.get("message", "Gagal menghubungi server GAS") if res else "Tidak ada respon"
            self.render_error_state(err_msg)
            return

        # Update metric cards
        self.lbl_val_tx.configure(text=str(res.get("total_transaksi", 0)))
        self.lbl_val_kurang.configure(text=format_rupiah(res.get("total_kurang", 0)))
        self.lbl_val_lebih.configure(text=format_rupiah(res.get("total_lebih", 0)))

        # Render transactions
        data = res.get("data", [])
        self.render_transactions_list(data)

    def clear_scroll_area(self):
        for w in self.scroll_tx.winfo_children():
            w.destroy()

    def render_loading_state(self):
        self.clear_scroll_area()
        box = ctk.CTkFrame(self.scroll_tx, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        box.pack(fill="x", padx=10, pady=25)

        ctk.CTkLabel(
            box, text="⏳ Menghubungkan ke Google Apps Script...",
            font=("Segoe UI", 12, "bold"), text_color=ACCENT_COLOR
        ).pack(pady=(20, 6))

        ctk.CTkLabel(
            box, text="Sedang memverifikasi kredensial login & menarik data 5 hari terakhir.",
            font=SMALL_FONT, text_color="grey"
        ).pack(pady=(0, 20))

    def render_missing_credentials_state(self, user):
        self.clear_scroll_area()
        self.lbl_val_tx.configure(text="0")
        self.lbl_val_kurang.configure(text="Rp 0")
        self.lbl_val_lebih.configure(text="Rp 0")

        box = ctk.CTkFrame(self.scroll_tx, fg_color="#fffbeb", border_width=1, border_color="#fcd34d", corner_radius=8)
        box.pack(fill="x", padx=10, pady=20)

        ctk.CTkLabel(
            box, text="⚠️ Kredensial Login GAS Belum Lengkap",
            font=("Segoe UI", 13, "bold"), text_color="#b45309"
        ).pack(pady=(15, 6))

        ctk.CTkLabel(
            box,
            text=f"Kasir '{user.get('name')}' belum memiliki Email dan Password untuk login ke Google Apps Script.\n"
                 "Silakan lengkapi data email dan password melalui menu Kelola User.",
            font=MAIN_FONT, text_color="#92400e", justify="center"
        ).pack(padx=20, pady=(0, 15))

        btn = ctk.CTkButton(
            box, text="Buka Menu User (Alt + U)", height=32,
            fg_color="#d97706", hover_color="#b45309", text_color="white",
            corner_radius=6, font=("Segoe UI", 10, "bold"),
            command=lambda: self.controller.show_tab("USR")
        )
        btn.pack(pady=(0, 15))

    def render_no_cashiers_state(self):
        self.clear_scroll_area()
        box = ctk.CTkFrame(self.scroll_tx, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        box.pack(fill="x", padx=10, pady=20)

        ctk.CTkLabel(
            box, text="Belum Ada Data Kasir Terdaftar",
            font=("Segoe UI", 13, "bold"), text_color=TEXT_COLOR
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            box, text="Silakan tambahkan data kasir terlebih dahulu melalui Menu User.",
            font=MAIN_FONT, text_color="grey"
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            box, text="+ Tambah Kasir (Alt + U)", height=32,
            fg_color=ACCENT_COLOR, hover_color="#375a7f", text_color="white",
            corner_radius=6, font=("Segoe UI", 10, "bold"),
            command=lambda: self.controller.show_tab("USR")
        ).pack(pady=(0, 20))

    def render_error_state(self, err_msg):
        self.clear_scroll_area()
        box = ctk.CTkFrame(self.scroll_tx, fg_color="#fef2f2", border_width=1, border_color="#fca5a5", corner_radius=8)
        box.pack(fill="x", padx=10, pady=20)

        ctk.CTkLabel(
            box, text="❌ Terjadi Kesalahan",
            font=("Segoe UI", 13, "bold"), text_color="#b91c1c"
        ).pack(pady=(15, 6))

        ctk.CTkLabel(
            box, text=str(err_msg),
            font=MAIN_FONT, text_color="#991b1b", justify="center"
        ).pack(padx=20, pady=(0, 15))

        btn = ctk.CTkButton(
            box, text="Coba Lagi", height=32, width=120,
            fg_color="#dc2626", hover_color="#b91c1c", text_color="white",
            corner_radius=6, font=("Segoe UI", 10, "bold"),
            command=self.trigger_fetch
        )
        btn.pack(pady=(0, 15))

    def render_transactions_list(self, data):
        self.clear_scroll_area()

        if not data:
            box = ctk.CTkFrame(self.scroll_tx, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=8)
            box.pack(fill="x", padx=10, pady=20)
            ctk.CTkLabel(
                box, text="Tidak ada transaksi dalam 5 hari terakhir.",
                font=MAIN_FONT, text_color="grey"
            ).pack(pady=25)
            return

        for idx, item in enumerate(data):
            row_card = ctk.CTkFrame(
                self.scroll_tx, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=8
            )
            row_card.pack(fill="x", padx=8, pady=4)

            # Top Line: Index, Tanggal, Shift Badge, Cabang
            top_line = ctk.CTkFrame(row_card, fg_color="transparent")
            top_line.pack(fill="x", padx=12, pady=(8, 4))

            idx_lbl = ctk.CTkLabel(
                top_line, text=f"#{idx + 1}", font=("Segoe UI", 10, "bold"), text_color="#9ca3af"
            )
            idx_lbl.pack(side="left", padx=(0, 8))

            date_lbl = ctk.CTkLabel(
                top_line, text=str(item.get("tanggal", "—")), font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR
            )
            date_lbl.pack(side="left", padx=(0, 8))

            shift_text = str(item.get("shift", "—")).capitalize()
            shift_badge = ctk.CTkLabel(
                top_line, text=f" {shift_text} ", font=("Segoe UI", 9, "bold"),
                fg_color="#f3f4f6", text_color="#374151", corner_radius=4, height=18
            )
            shift_badge.pack(side="left", padx=(0, 8))

            cabang_lbl = ctk.CTkLabel(
                top_line, text=f"📍 {item.get('cabang', '—')}", font=("Segoe UI", 9), text_color="grey"
            )
            cabang_lbl.pack(side="right")

            # Middle Line: Kasir & Amounts (Komputer vs Fisik)
            mid_line = ctk.CTkFrame(row_card, fg_color="transparent")
            mid_line.pack(fill="x", padx=12, pady=2)

            kasir_name = str(item.get("kasir", "—"))
            ctk.CTkLabel(
                mid_line, text=f"Kasir: {kasir_name}", font=SMALL_FONT, text_color="grey"
            ).pack(side="left")

            amt_box = ctk.CTkFrame(mid_line, fg_color="transparent")
            amt_box.pack(side="right")

            total_komp = item.get("totalKomputer", 0)
            uang_fisik = item.get("uangFisik", 0)

            ctk.CTkLabel(
                amt_box, text=f"Komp: {format_rupiah(total_komp)}",
                font=("Segoe UI", 10, "bold"), text_color="#0284c7"
            ).pack(side="left", padx=(0, 10))

            ctk.CTkLabel(
                amt_box, text=f"Fisik: {format_rupiah(uang_fisik)}",
                font=("Segoe UI", 10, "bold"), text_color=TEXT_COLOR
            ).pack(side="left")

            # Bottom Line: Selisih Status Badge & Difference Amount
            bot_line = ctk.CTkFrame(row_card, fg_color="transparent")
            bot_line.pack(fill="x", padx=12, pady=(4, 8))

            status_selisih = str(item.get("statusSelisih", "PAS")).upper()
            selisih_val = item.get("jumlahSelisih", 0)

            if status_selisih == "KURANG" or selisih_val < 0:
                s_badge_bg = "#fee2e2"
                s_badge_fg = COLOR_KURANG
                s_text = "KURANG"
            elif status_selisih == "LEBIH" or selisih_val > 0:
                s_badge_bg = "#d1fae5"
                s_badge_fg = COLOR_LEBIH
                s_text = "LEBIH"
            else:
                s_badge_bg = "#f3f4f6"
                s_badge_fg = COLOR_PAS
                s_text = "PAS"

            badge_selisih = ctk.CTkLabel(
                bot_line, text=f" {s_text} ", font=("Segoe UI", 9, "bold"),
                fg_color=s_badge_bg, text_color=s_badge_fg, corner_radius=4, height=20
            )
            badge_selisih.pack(side="left")

            diff_lbl = ctk.CTkLabel(
                bot_line, text=f"Selisih: {format_rupiah(selisih_val)}",
                font=("Segoe UI", 11, "bold"), text_color=s_badge_fg
            )
            diff_lbl.pack(side="right")
