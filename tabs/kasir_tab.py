import customtkinter as ctk
import json
import os
import re
import threading
from datetime import datetime
from constants import (
    HEADER_FONT, MAIN_FONT, SMALL_FONT, TEXT_COLOR, BG_COLOR,
    SIDEBAR_COLOR, CONSOLE_COLOR, BORDER_COLOR, ACCENT_COLOR,
    USERS_FILE, DATA_DIR, COLOR_KURANG, COLOR_LEBIH, COLOR_PAS,
    laku_file_for
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
        self.syncing_for = None
        self.cached_data = []
        self.last_sync = None
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
        ctk.CTkLabel(self.card_tx, text="Total Transaksi (Bulan Ini)", font=("Segoe UI", 9, "bold"), text_color="grey").pack(pady=(6, 2))
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

    _BULAN = {
        "januari": 1, "jan": 1, "january": 1,
        "februari": 2, "feb": 2, "february": 2, "peb": 2,
        "maret": 3, "mar": 3, "march": 3,
        "april": 4, "apr": 4,
        "mei": 5, "may": 5,
        "juni": 6, "jun": 6, "june": 6,
        "juli": 7, "jul": 7, "july": 7,
        "agustus": 8, "agu": 8, "agst": 8, "ags": 8, "aug": 8, "august": 8,
        "september": 9, "sep": 9, "sept": 9,
        "oktober": 10, "okt": 10, "oct": 10, "october": 10,
        "november": 11, "nov": 11,
        "desember": 12, "des": 12, "dec": 12, "december": 12,
    }

    @staticmethod
    def _parse_date(tgl):
        # ponytail: dukung angka + nama bulan ID/EN, gagal -> None (fail-open di caller)
        if tgl is None:
            return None
        if isinstance(tgl, datetime):
            return tgl.date()
        try:
            from datetime import date as _d
            if isinstance(tgl, _d):
                return tgl
        except Exception:
            pass
        s = str(tgl or "").strip()
        if not s:
            return None
        s_low = s.lower()
        m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
            except ValueError:
                pass
        m = re.search(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", s)
        if m:
            try:
                d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if y < 100:
                    y += 2000
                return datetime(y, mo, d).date()
            except ValueError:
                pass
        m = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{2,4})", s_low)
        if m:
            try:
                d = int(m.group(1))
                mo = KasirTab._BULAN.get(m.group(2), 0)
                y = int(m.group(3))
                if y < 100:
                    y += 2000
                if mo:
                    return datetime(y, mo, d).date()
            except ValueError:
                pass
        return None

    @staticmethod
    def _periode_of_tanggal(tgl):
        """Periode 28-27: tgl 28+ masuk periode bulan berikut. Gagal parse -> None."""
        d = KasirTab._parse_date(tgl)
        if d is None:
            return None
        y, mo = d.year, d.month
        if d.day >= 28:
            mo += 1
            if mo > 12:
                mo = 1
                y += 1
        return f"{y:04d}-{mo:02d}"

    def _current_month(self):
        # periode berjalan 28-27 (nama dipertahankan agar diff kecil)
        return self._periode_of_tanggal(datetime.now().date()) or datetime.now().strftime("%Y-%m")

    def _is_current_periode(self, item):
        p = self._periode_of_tanggal((item or {}).get("tanggal") if isinstance(item, dict) else item)
        return p is None or p == self._current_month()

    def _storage_path(self, user):
        uid = (user.get("id") or user.get("name") or "anon") if user else "anon"
        return laku_file_for(uid, self._current_month())

    def load_cached_laku(self, user):
        """Load cache periode berjalan; purge otomatis item luar periode."""
        self.cached_data = []
        self.last_sync = None
        if not user:
            return [], None
        path = self._storage_path(user)
        if not os.path.exists(path):
            return [], None
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            data = obj.get("data", []) if isinstance(obj, dict) else []
            data = data if isinstance(data, list) else []
            self.last_sync = obj.get("last_sync") if isinstance(obj, dict) else None
            cur = self._current_month()
            filtered = [it for it in data if not isinstance(it, dict) or self._periode_of_tanggal(it.get("tanggal")) in (None, cur)]
            self.cached_data = filtered
            if len(filtered) != len(data):
                self.selected_user = user
                self.save_cached_laku()
        except Exception:
            self.cached_data = []
            self.last_sync = None
        return self.cached_data, self.last_sync

    def save_cached_laku(self):
        if not self.selected_user:
            return
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        obj = {
            "kasir_id": self.selected_user.get("id", ""),
            "kasir_name": self.selected_user.get("name", ""),
            "month": self._current_month(),
            "last_sync": self.last_sync or datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "data": self.cached_data,
        }
        try:
            with open(self._storage_path(self.selected_user), "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def update_summary(self, data):
        total_tx = len(data)
        total_kurang = 0
        total_lebih = 0
        for item in data:
            try:
                selisih = int(item.get("jumlahSelisih", 0) or 0)
            except (ValueError, TypeError):
                selisih = 0
            if selisih < 0:
                total_kurang += abs(selisih)
            elif selisih > 0:
                total_lebih += selisih
        self.lbl_val_tx.configure(text=str(total_tx))
        self.lbl_val_kurang.configure(text=format_rupiah(total_kurang))
        self.lbl_val_lebih.configure(text=format_rupiah(total_lebih))

    def on_cashier_changed(self, chosen_name):
        """Render cache dulu, lalu sinkron GAS di background."""
        user = next((u for u in self.users if u.get("name") == chosen_name), None)
        self.selected_user = user
        if not user:
            self.update_cashier_status_banner()
            return

        data, _ = self.load_cached_laku(user)
        self.update_summary(data)
        if data:
            self.render_transactions_list(data)
        self.update_cashier_status_banner()

        has_email = bool(user.get("email", "").strip())
        has_pwd = bool(user.get("password", "").strip())
        if has_email and has_pwd:
            self.sync_gas_background()
        elif not data:
            self.render_missing_credentials_state(user)

    def count_conflicts(self):
        return sum(1 for it in self.cached_data if isinstance(it, dict) and "_conflict" in it)

    def refresh_sync_label(self):
        if not self.selected_user:
            return
        has_cred = bool(self.selected_user.get("email") and self.selected_user.get("password"))
        if not has_cred:
            self.lbl_kasir_status.configure(
                text="  ⚠️ Belum Ada Akun GAS  ", text_color="white", fg_color="#f59e0b"
            )
            return
        if self.is_loading:
            self.lbl_kasir_status.configure(
                text="  ⏳ Sinkron GAS...  ", text_color="white", fg_color="#6b7280"
            )
            return
        n_conf = self.count_conflicts()
        if n_conf:
            self.lbl_kasir_status.configure(
                text=f"  ⚠ {n_conf} konflik  ", text_color="white", fg_color="#dc2626"
            )
            return
        if self.last_sync:
            self.lbl_kasir_status.configure(
                text=f"  ✓ {self.last_sync}  ", text_color="white", fg_color=COLOR_LEBIH
            )
            return
        self.lbl_kasir_status.configure(
            text="  ● Login GAS Tersedia  ", text_color="white", fg_color=COLOR_LEBIH
        )

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
        self.refresh_sync_label()

    @staticmethod
    def _norm(v):
        return str(v or "").strip().lower()

    def _tx_key(self, item):
        return (self._norm(item.get("tanggal")), self._norm(item.get("shift")), self._norm(item.get("cabang")))

    @staticmethod
    def _to_int(v):
        if isinstance(v, (int, float)):
            try:
                return int(v)
            except Exception:
                return 0
        s = "".join(c for c in str(v or "") if c.isdigit() or c == "-")
        s = s.strip("-") and ("-" + s.replace("-", "") if str(v or "").strip().startswith("-") else s.replace("-", "")) or "0"
        try:
            return int(s or 0)
        except Exception:
            return 0

    def _is_conflict(self, a, b):
        for k in ("totalKomputer", "uangFisik", "jumlahSelisih"):
            if self._to_int(a.get(k)) != self._to_int(b.get(k)):
                return True
        return False

    def merge_gas_data(self, gas_data):
        """Merge incremental periode berjalan saja; luar periode di-skip. Return (n_new, n_conflict)."""
        cur_periode = self._current_month()
        # ponytail: bersihkan sisa luar periode yang telanjur di memori/file lama
        self.cached_data = [it for it in self.cached_data if not isinstance(it, dict) or self._periode_of_tanggal(it.get("tanggal")) in (None, cur_periode)]
        idx = {self._tx_key(it): i for i, it in enumerate(self.cached_data) if isinstance(it, dict)}
        n_new = 0
        for g in gas_data or []:
            if not isinstance(g, dict):
                continue
            p = self._periode_of_tanggal(g.get("tanggal"))
            if p is not None and p != cur_periode:
                continue
            key = self._tx_key(g)
            if key not in idx:
                clean = {k: v for k, v in g.items() if k != "_conflict"}
                self.cached_data.append(clean)
                idx[key] = len(self.cached_data) - 1
                n_new += 1
            else:
                cur = self.cached_data[idx[key]]
                if self._is_conflict(cur, g):
                    prev_gas = (cur.get("_conflict") or {}).get("gas_item")
                    if prev_gas is None or self._is_conflict(prev_gas, g):
                        cur["_conflict"] = {
                            "lokal": {
                                "totalKomputer": cur.get("totalKomputer", 0),
                                "uangFisik": cur.get("uangFisik", 0),
                                "jumlahSelisih": cur.get("jumlahSelisih", 0),
                            },
                            "gas": {
                                "totalKomputer": g.get("totalKomputer", 0),
                                "uangFisik": g.get("uangFisik", 0),
                                "jumlahSelisih": g.get("jumlahSelisih", 0),
                            },
                            "gas_item": {k: v for k, v in g.items() if k != "_conflict"},
                        }
        n_conflict = self.count_conflicts()
        return n_new, n_conflict

    def trigger_fetch(self):
        """Tombol ↻: render cache lalu sinkron ulang."""
        if self.selected_user:
            data, _ = self.load_cached_laku(self.selected_user)
            # ponytail: jangan kosongkan list saat refresh manual
            if data and not self.cached_data:
                self.cached_data = data
            self.update_summary(self.cached_data)
            if self.cached_data:
                self.render_transactions_list(self.cached_data)
        self.sync_gas_background()

    def sync_gas_background(self):
        """Fetch GAS tanpa blokir UI; list tetap tampil dari cache."""
        if self.is_loading:
            return
        if not self.selected_user:
            return
        user = self.selected_user
        email = (user.get("email") or "").strip()
        pwd = (user.get("password") or "").strip()
        cashier_name = user.get("name", "")
        if not email or not pwd:
            if not self.cached_data:
                self.render_missing_credentials_state(user)
            self.update_cashier_status_banner()
            return

        token = f"{user.get('id')}|{user.get('name')}|{self._current_month()}"
        self.is_loading = True
        self.syncing_for = token
        self.btn_refresh.configure(state="disabled", text="⏳ Sinkron...")
        self.refresh_sync_label()

        def worker():
            res = gas_service.fetch_kasir_summary(email, pwd, cashier_name)
            self.after(0, lambda: self.handle_fetch_result(res, token))

        threading.Thread(target=worker, daemon=True).start()

    def handle_fetch_result(self, res, token=None):
        """Process GAS response; abaikan jika kasir sudah ganti (stale)."""
        if token is not None and token != self.syncing_for:
            return
        self.is_loading = False
        self.syncing_for = None
        self.btn_refresh.configure(state="normal", text="↻ Muat Ulang")

        if not res or not res.get("success"):
            err_msg = res.get("message", "Gagal menghubungi server GAS") if res else "Tidak ada respon"
            if not self.cached_data:
                self.render_error_state(err_msg)
            else:
                self.lbl_kasir_info.configure(text=f"{self.lbl_kasir_info.cget('text')}  |  Gagal sinkron: {err_msg}")
            self.refresh_sync_label()
            return

        gas_data = res.get("data", [])
        n_new, n_conflict = self.merge_gas_data(gas_data)
        self.last_sync = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.save_cached_laku()
        self.update_summary(self.cached_data)
        self.render_transactions_list(self.cached_data)
        self.refresh_sync_label()

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
                box, text="Tidak ada transaksi bulan ini.",
                font=MAIN_FONT, text_color="grey"
            ).pack(pady=25)
            return

        # ponytail: terbaru paling atas; 28-31 bulan lalu = tanggal lebih tua = di bawah
        ordered = sorted(
            data,
            key=lambda it: (self._parse_date(it.get("tanggal")) if isinstance(it, dict) else None) or datetime.min.date(),
            reverse=True,
        )

        for idx, item in enumerate(ordered):
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

            if isinstance(item, dict) and "_conflict" in item:
                ctk.CTkLabel(
                    bot_line, text=" ⚠ Konflik ", font=("Segoe UI", 9, "bold"),
                    fg_color="#fee2e2", text_color="#b91c1c", corner_radius=4, height=20
                ).pack(side="left", padx=(6, 0))
                ctk.CTkButton(
                    bot_line, text="Lihat Beda", width=80, height=22,
                    fg_color="white", hover_color="#fef2f2", text_color="#b91c1c",
                    border_width=1, border_color="#fca5a5", corner_radius=4,
                    font=("Segoe UI", 9, "bold"),
                    command=lambda it=item: self.show_conflict_dialog(it)
                ).pack(side="left", padx=(6, 0))

            diff_lbl = ctk.CTkLabel(
                bot_line, text=f"Selisih: {format_rupiah(selisih_val)}",
                font=("Segoe UI", 11, "bold"), text_color=s_badge_fg
            )
            diff_lbl.pack(side="right")

    def show_conflict_dialog(self, item):
        conf = item.get("_conflict") or {}
        lokal = conf.get("lokal", {})
        gas = conf.get("gas", {})
        dialog = ctk.CTkToplevel(self)
        dialog.title("Konflik Data Laku")
        dialog.geometry("380x320")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)
        ctk.CTkLabel(
            container, text=f"⚠ Beda Data: {item.get('tanggal', '—')} / {item.get('shift', '—')} / {item.get('cabang', '—')}",
            font=("Segoe UI", 11, "bold"), text_color="#b91c1c", wraplength=340
        ).pack(anchor="w", pady=(0, 10))
        for label, src in (("Lokal (disimpan)", lokal), ("GAS (baru)", gas)):
            ctk.CTkLabel(container, text=label, font=("Segoe UI", 10, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
            ctk.CTkLabel(
                container,
                text=f"Komp: {format_rupiah(src.get('totalKomputer', 0))}  |  Fisik: {format_rupiah(src.get('uangFisik', 0))}  |  Selisih: {format_rupiah(src.get('jumlahSelisih', 0))}",
                font=SMALL_FONT, text_color="grey", wraplength=340, justify="left"
            ).pack(anchor="w", pady=(0, 8))

        def resolve(use_gas):
            key = self._tx_key(item)
            for i, it in enumerate(self.cached_data):
                if self._tx_key(it) == key:
                    if use_gas:
                        gas_item = (self.cached_data[i].get("_conflict") or {}).get("gas_item") or gas
                        clean = {k: v for k, v in gas_item.items() if k != "_conflict"}
                        self.cached_data[i] = clean
                    else:
                        self.cached_data[i].pop("_conflict", None)
                    break
            self.save_cached_laku()
            self.update_summary(self.cached_data)
            self.render_transactions_list(self.cached_data)
            self.refresh_sync_label()
            dialog.destroy()

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(
            btn_box, text="Pakai Lokal", height=34, fg_color="#6b7280", hover_color="#4b5563",
            text_color="white", corner_radius=6, font=("Segoe UI", 10, "bold"),
            command=lambda: resolve(False)
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(
            btn_box, text="Pakai GAS", height=34, fg_color="#dc2626", hover_color="#b91c1c",
            text_color="white", corner_radius=6, font=("Segoe UI", 10, "bold"),
            command=lambda: resolve(True)
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))
