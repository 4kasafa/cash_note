import customtkinter as ctk
import os
from datetime import datetime
from constants import ACCENT_COLOR, SMALL_FONT, SIDEBAR_COLOR, BORDER_COLOR, TEXT_COLOR, HEADER_FONT, DATA_DIR

class SystemTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.controller = controller
        
        ctk.CTkLabel(self, text="Cash Note", font=("Segoe UI", 24, "bold"), text_color=ACCENT_COLOR).pack(pady=(30, 10))
        ctk.CTkLabel(self, text="Professional Transaction Management", font=SMALL_FONT, text_color="grey").pack(pady=(0, 30))

        # Stats Section
        self.stats_frame = ctk.CTkFrame(self, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR, corner_radius=0)
        self.stats_frame.pack(fill="x", padx=50, pady=20)
        
        self.add_stat("System Health", "Operational")
        self.add_stat("Encryption", "Active (AES-256)")
        self.add_stat("Cloud Sync", "Connected")
        self.add_stat("Last Login", f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Action Prompt
        self.btn_new = ctk.CTkButton(self, text="Start New Session", font=HEADER_FONT, height=60, fg_color=ACCENT_COLOR, text_color="white", corner_radius=0, command=self.init_session)
        self.btn_new.pack(fill="x", padx=50, pady=20)
        
        ctk.CTkLabel(self, text="Press [Space] to initialize", font=SMALL_FONT, text_color="grey").pack()

    def add_stat(self, key, val):
        f = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(f, text=f"{key}:", font=("Segoe UI", 11, "bold"), text_color=TEXT_COLOR).pack(side="left")
        ctk.CTkLabel(f, text=val, font=("Segoe UI", 11), text_color=TEXT_COLOR).pack(side="right")

    def init_session(self):
        today = datetime.now().strftime("%d_%m_%Y")
        base_name = f"data_{today}"
        file_path = os.path.join(DATA_DIR, f"{base_name}.json")
        
        # Multi-session logic
        if os.path.exists(file_path):
            counter = 1
            while True:
                suffix = f"_{counter:03d}"
                file_path = os.path.join(DATA_DIR, f"{base_name}{suffix}.json")
                if not os.path.exists(file_path):
                    break
                counter += 1
                
        self.controller.current_file = file_path
        self.controller.tabs["ACT"].file_path = file_path
        self.controller.tabs["ACT"].load_session()
        self.controller.btn_act.pack(pady=5)
        self.controller.show_tab("ACT")
