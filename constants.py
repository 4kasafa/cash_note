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
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CALC_HISTORY_FILE = os.path.join(DATA_DIR, "calculate_history.json")

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
