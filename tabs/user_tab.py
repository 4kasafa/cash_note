import customtkinter as ctk
import json
import os
from tkinter import messagebox
from constants import (
    HEADER_FONT, TEXT_COLOR, MAIN_FONT, CONSOLE_COLOR, BORDER_COLOR,
    ACCENT_COLOR, USERS_FILE, SMALL_FONT, SIDEBAR_COLOR, COLOR_LEBIH,
    COLOR_KURANG, COLOR_PAS
)

class UserTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        self.users = []
        self.editing_id = None # Store the ID kasir being edited
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        # Container for switching between List and Form
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)
        
        # --- List View ---
        self.list_view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.list_view.pack(fill="both", expand=True)
        
        header_area = ctk.CTkFrame(self.list_view, fg_color="transparent")
        header_area.pack(fill="x", padx=20, pady=(10, 5))
        
        # Action & Navigation Buttons Row
        actions_row = ctk.CTkFrame(header_area, fg_color="transparent")
        actions_row.pack(fill="x", pady=(0, 8))

        self.btn_to_calc = ctk.CTkButton(
            actions_row, 
            text="← Hitung", 
            width=115, 
            height=30, 
            fg_color="#666666", 
            hover_color="#555555", 
            text_color="white", 
            corner_radius=6, 
            font=("Segoe UI", 10, "bold"), 
            command=lambda: self.controller.show_tab("CAL")
        )
        self.btn_to_calc.pack(side="left", padx=(0, 6))

        self.btn_to_kasir = ctk.CTkButton(
            actions_row, 
            text="Laku →", 
            width=125, 
            height=30, 
            fg_color="#4b5563", 
            hover_color="#374151", 
            text_color="white", 
            corner_radius=6, 
            font=("Segoe UI", 10, "bold"), 
            command=lambda: self.controller.show_tab("KSR")
        )
        self.btn_to_kasir.pack(side="left")

        self.btn_add = ctk.CTkButton(
            actions_row, 
            text="+ Tambah Kasir", 
            width=110, 
            height=30, 
            fg_color=ACCENT_COLOR, 
            hover_color="#375a7f", 
            text_color="white", 
            corner_radius=6, 
            font=SMALL_FONT, 
            command=self.show_add_form
        )
        self.btn_add.pack(side="right")
        
        ctk.CTkLabel(header_area, text="Kelola Data Kasir", font=HEADER_FONT, text_color=TEXT_COLOR).pack(anchor="w")
        
        self.search_entry = ctk.CTkEntry(self.list_view, placeholder_text="Cari nama kasir...", font=MAIN_FONT, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=0)
        self.search_entry.pack(fill="x", padx=20, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_user_list())

        self.scroll_users = ctk.CTkScrollableFrame(self.list_view, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.scroll_users.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        # --- Form View (Hidden by default) ---
        self.form_view = ctk.CTkScrollableFrame(self.content_container, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        
        self.form_title = ctk.CTkLabel(self.form_view, text="Tambah Kasir Baru", font=HEADER_FONT, text_color=ACCENT_COLOR)
        self.form_title.pack(pady=(15, 10))
        
        self.create_field("Nama Kasir:", "entry_name")
        self.create_field("ID Kasir:", "entry_id")
        self.create_field("Cabang:", "entry_branch")
        self.create_field("Shift:", "entry_shift")
        self.create_field("Email (Login GAS):", "entry_email")
        self.create_password_field("Password (Login GAS):", "entry_password")
        
        btn_box = ctk.CTkFrame(self.form_view, fg_color="transparent")
        btn_box.pack(fill="x", padx=40, pady=25)
        
        ctk.CTkButton(btn_box, text="Simpan Data", fg_color=ACCENT_COLOR, text_color="white", corner_radius=5, command=self.save_user).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_box, text="Batal", fg_color="#666666", text_color="white", corner_radius=5, command=self.show_list_view).pack(side="left", expand=True, padx=5)

    def create_field(self, label, attr_name):
        f = ctk.CTkFrame(self.form_view, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=4)
        ctk.CTkLabel(f, text=label, font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
        entry = ctk.CTkEntry(f, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=5)
        entry.pack(fill="x", pady=(2, 0))
        setattr(self, attr_name, entry)

    def create_password_field(self, label, attr_name):
        f = ctk.CTkFrame(self.form_view, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=4)
        ctk.CTkLabel(f, text=label, font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", pady=(2, 0))
        entry = ctk.CTkEntry(row, show="*", fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=5)
        entry.pack(side="left", fill="x", expand=True)
        setattr(self, attr_name, entry)

        btn_toggle = ctk.CTkButton(
            row, text="👁", width=36, height=28, fg_color="#e5e7eb", hover_color="#d1d5db",
            text_color="#374151", corner_radius=5, font=("Segoe UI", 11)
        )
        btn_toggle.pack(side="left", padx=(6, 0))

        def toggle():
            if entry.cget("show") == "*":
                entry.configure(show="")
                btn_toggle.configure(text="🔒")
            else:
                entry.configure(show="*")
                btn_toggle.configure(text="👁")

        btn_toggle.configure(command=toggle)

    def show_add_form(self):
        self.editing_id = None
        self.form_title.configure(text="Tambah Kasir Baru")
        self.entry_name.delete(0, "end")
        self.entry_id.delete(0, "end")
        self.entry_id.configure(state="normal")
        self.entry_branch.delete(0, "end")
        self.entry_shift.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.list_view.pack_forget()
        self.form_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_edit_form(self, user):
        self.editing_id = user["id"]
        self.form_title.configure(text="Edit Data Kasir")
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, user.get("name", ""))
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, user.get("id", ""))
        self.entry_id.configure(state="disabled") # ID shouldn't be changed
        self.entry_branch.delete(0, "end")
        self.entry_branch.insert(0, user.get("branch", ""))
        self.entry_shift.delete(0, "end")
        self.entry_shift.insert(0, user.get("shift", ""))
        self.entry_email.delete(0, "end")
        self.entry_email.insert(0, user.get("email", ""))
        self.entry_password.delete(0, "end")
        self.entry_password.insert(0, user.get("password", ""))
        self.list_view.pack_forget()
        self.form_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_list_view(self):
        self.form_view.pack_forget()
        self.list_view.pack(fill="both", expand=True)
        self.refresh_user_list()

    def load_users(self):
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, "r") as f:
                    self.users = json.load(f)
            except: self.users = []
        else: self.users = []
        self.refresh_user_list()

    def save_users_to_file(self):
        with open(USERS_FILE, "w") as f:
            json.dump(self.users, f, indent=4)

    def save_user(self):
        name = self.entry_name.get().strip()
        uid = self.entry_id.get().strip()
        branch = self.entry_branch.get().strip()
        shift = self.entry_shift.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_password.get().strip()
        
        if not (name and uid and branch and shift):
            messagebox.showwarning("Peringatan", "Kolom Nama, ID, Cabang, dan Shift wajib diisi.")
            return

        if self.editing_id:
            for user in self.users:
                if user["id"] == self.editing_id:
                    user["name"] = name
                    user["branch"] = branch
                    user["shift"] = shift
                    user["email"] = email
                    user["password"] = password
                    break
        else:
            # Check for duplicate ID
            if any(u["id"] == uid for u in self.users):
                messagebox.showerror("ID Duplikat", f"ID Kasir '{uid}' sudah terdaftar.")
                return
            self.users.append({
                "name": name,
                "id": uid,
                "branch": branch,
                "shift": shift,
                "email": email,
                "password": password
            })
            
        self.save_users_to_file()
        self.show_list_view()

    def delete_user(self, uid):
        if messagebox.askyesno("Konfirmasi", "Hapus data kasir ini?"):
            self.users = [u for u in self.users if u["id"] != uid]
            self.save_users_to_file()
            self.refresh_user_list()

    def refresh_user_list(self):
        for w in self.scroll_users.winfo_children(): w.destroy()
        
        query = self.search_entry.get().lower()
        
        for user in self.users:
            if query and query not in user["name"].lower(): continue
            
            row = ctk.CTkFrame(self.scroll_users, fg_color="white", border_width=1, border_color=BORDER_COLOR, corner_radius=5)
            row.pack(fill="x", pady=5, padx=5)
            
            # Avatar circle (using initials)
            initials = "".join([n[0] for n in user["name"].split()[:2]]).upper()
            avatar = ctk.CTkLabel(row, text=initials, width=40, height=40, corner_radius=20, fg_color="#e0e0e0", font=("Segoe UI", 12, "bold"), text_color=ACCENT_COLOR)
            avatar.pack(side="left", padx=10, pady=10)
            
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=5)
            
            ctk.CTkLabel(info_frame, text=user["name"], font=("Segoe UI", 12, "bold"), text_color=TEXT_COLOR, anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=f"ID: {user['id']} | Cabang: {user['branch']} | Shift: {user['shift']}", font=("Segoe UI", 9), text_color="grey", anchor="w").pack(fill="x")
            
            has_gas = bool(user.get("email") and user.get("password"))
            sub_row = ctk.CTkFrame(info_frame, fg_color="transparent")
            sub_row.pack(fill="x", pady=(2, 0))

            gas_text = f"✉ {user['email']}" if user.get("email") else "Belum ada email login GAS"
            ctk.CTkLabel(sub_row, text=gas_text, font=("Segoe UI", 9), text_color=ACCENT_COLOR if has_gas else "grey", anchor="w").pack(side="left")
            
            badge_text = "GAS Siap" if has_gas else "Lokal"
            badge_bg = COLOR_LEBIH if has_gas else "#9ca3af"
            badge = ctk.CTkLabel(
                sub_row, 
                text=f" {badge_text} ", 
                font=("Segoe UI", 8, "bold"), 
                text_color="white", 
                fg_color=badge_bg, 
                corner_radius=4,
                height=16
            )
            badge.pack(side="left", padx=(6, 0))

            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=10)
            
            ctk.CTkButton(btns, text="Edit", width=50, height=25, corner_radius=5, font=SMALL_FONT, fg_color="#f5f5f5", text_color="black", command=lambda u=user: self.show_edit_form(u)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="Hapus", width=50, height=25, corner_radius=5, font=SMALL_FONT, fg_color="#ffebee", text_color="#d32f2f", hover_color="#ffcdd2", command=lambda u=user: self.delete_user(u["id"])).pack(side="left", padx=2)

    def on_activate(self):
        self.load_users()
        self.show_list_view()
