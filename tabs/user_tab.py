import customtkinter as ctk
import json
import os
from tkinter import messagebox
from constants import HEADER_FONT, TEXT_COLOR, MAIN_FONT, CONSOLE_COLOR, BORDER_COLOR, ACCENT_COLOR, USERS_FILE, SMALL_FONT, SIDEBAR_COLOR

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
        header_area.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(header_area, text="Cashier Management", font=HEADER_FONT, text_color=TEXT_COLOR).pack(side="left")
        
        self.btn_add = ctk.CTkButton(header_area, text="+ Add Cashier", width=120, fg_color=ACCENT_COLOR, text_color="white", corner_radius=5, font=SMALL_FONT, command=self.show_add_form)
        self.btn_add.pack(side="right")
        
        self.search_entry = ctk.CTkEntry(self.list_view, placeholder_text="Search cashier name...", font=MAIN_FONT, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=0)
        self.search_entry.pack(fill="x", padx=20, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_user_list())

        self.scroll_users = ctk.CTkScrollableFrame(self.list_view, fg_color=CONSOLE_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.scroll_users.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        # --- Form View (Hidden by default) ---
        self.form_view = ctk.CTkFrame(self.content_container, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        
        self.form_title = ctk.CTkLabel(self.form_view, text="Add New Cashier", font=HEADER_FONT, text_color=ACCENT_COLOR)
        self.form_title.pack(pady=20)
        
        self.create_field("Nama Kasir:", "entry_name")
        self.create_field("ID Kasir:", "entry_id")
        self.create_field("Cabang:", "entry_branch")
        self.create_field("Shift:", "entry_shift")
        
        btn_box = ctk.CTkFrame(self.form_view, fg_color="transparent")
        btn_box.pack(fill="x", padx=40, pady=30)
        
        ctk.CTkButton(btn_box, text="Save Data", fg_color=ACCENT_COLOR, text_color="white", corner_radius=5, command=self.save_user).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_box, text="Cancel", fg_color="#666666", text_color="white", corner_radius=5, command=self.show_list_view).pack(side="left", expand=True, padx=5)

    def create_field(self, label, attr_name):
        f = ctk.CTkFrame(self.form_view, fg_color="transparent")
        f.pack(fill="x", padx=40, pady=5)
        ctk.CTkLabel(f, text=label, font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR).pack(anchor="w")
        entry = ctk.CTkEntry(f, fg_color=CONSOLE_COLOR, border_color=BORDER_COLOR, corner_radius=5)
        entry.pack(fill="x", pady=(2, 0))
        setattr(self, attr_name, entry)

    def show_add_form(self):
        self.editing_id = None
        self.form_title.configure(text="Add New Cashier")
        self.entry_name.delete(0, "end")
        self.entry_id.delete(0, "end")
        self.entry_id.configure(state="normal")
        self.entry_branch.delete(0, "end")
        self.entry_shift.delete(0, "end")
        self.list_view.pack_forget()
        self.form_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_edit_form(self, user):
        self.editing_id = user["id"]
        self.form_title.configure(text="Edit Cashier")
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, user["name"])
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, user["id"])
        self.entry_id.configure(state="disabled") # ID shouldn't be changed
        self.entry_branch.delete(0, "end")
        self.entry_branch.insert(0, user["branch"])
        self.entry_shift.delete(0, "end")
        self.entry_shift.insert(0, user["shift"])
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
        
        if not (name and uid and branch and shift):
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        if self.editing_id:
            for user in self.users:
                if user["id"] == self.editing_id:
                    user["name"] = name
                    user["branch"] = branch
                    user["shift"] = shift
                    break
        else:
            # Check for duplicate ID
            if any(u["id"] == uid for u in self.users):
                messagebox.showerror("Duplicate ID", f"ID Kasir '{uid}' already exists.")
                return
            self.users.append({"name": name, "id": uid, "branch": branch, "shift": shift})
            
        self.save_users_to_file()
        self.show_list_view()

    def delete_user(self, uid):
        if messagebox.askyesno("Confirmation", "Delete this cashier?"):
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
            ctk.CTkLabel(info_frame, text=f"ID: {user['id']} | Branch: {user['branch']} | Shift: {user['shift']}", font=("Segoe UI", 9), text_color="grey", anchor="w").pack(fill="x")
            
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=10)
            
            ctk.CTkButton(btns, text="Edit", width=50, height=25, corner_radius=5, font=SMALL_FONT, fg_color="#f5f5f5", text_color="black", command=lambda u=user: self.show_edit_form(u)).pack(side="left", padx=2)
            ctk.CTkButton(btns, text="Delete", width=50, height=25, corner_radius=5, font=SMALL_FONT, fg_color="#ffebee", text_color="#d32f2f", hover_color="#ffcdd2", command=lambda u=user: self.delete_user(u["id"])).pack(side="left", padx=2)

    def on_activate(self):
        self.show_list_view()
