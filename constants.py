import customtkinter as ctk
import os

# Appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Colors (Modern Payment UI Palette)
BG_COLOR = "#f8f9fc"
SIDEBAR_COLOR = "#ffffff"
CONSOLE_COLOR = "#ffffff"
TEXT_COLOR = "#2d2d2d"
ACCENT_COLOR = "#4e73df"
BORDER_COLOR = "#d1d3e2"

# Status Colors
STATUS_TOTAL_BG = "#ffff00" # Yellow
STATUS_PAID_BG = "#90ee90"  # Light Green
STATUS_CHANGE_BG = "#ffa500" # Orange
COLOR_KURANG = "#ef4444"    # Red
COLOR_LEBIH = "#10b981"     # Green
COLOR_PAS = "#6b7280"       # Gray

# Google Apps Script Endpoint
GAS_URL_KASIR = "https://script.google.com/macros/s/AKfycbw95Qnt8U-GQWt04AeG3sBpBfcBleNLfPMSr0arOXtGDH2iZiMDVoWHyBmNpW8Shejo/exec"

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CALC_HISTORY_FILE = os.path.join(DATA_DIR, "calculate_history.json")
MODAL_FILE = os.path.join(DATA_DIR, "modal_data.json")

LAKU_FILE_PREFIX = "laku_"

def laku_file_for(user_id, month):
    safe = "".join(c.lower() if c.isalnum() or c in ("-", "_") else "_" for c in str(user_id or "anon")).strip("_") or "anon"
    return os.path.join(DATA_DIR, f"{LAKU_FILE_PREFIX}{month}_{safe}.json")

# Font Configuration
MAIN_FONT = ("Segoe UI", 11)
HEADER_FONT = ("Segoe UI", 16, "bold")
DISPLAY_FONT = ("Segoe UI", 24, "bold")
SMALL_FONT = ("Segoe UI", 10)

# Windows API Constants
SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
WM_HOTKEY = 0x0312

# POS Automation
KETOKO_WINDOW_TITLE = "Ketoko.co.id"
KETOKO_PROCESS_NAME = "KetokoD.exe"
RETURN_FOCUS_DELAY_MS = 50
BUTBAYAR_CLICK_DELAY_MS = 100

