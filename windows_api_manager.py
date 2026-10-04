import ctypes
from ctypes import wintypes
import threading
import time
from constants import (
    SW_RESTORE, HWND_TOPMOST, HWND_NOTOPMOST, SWP_NOMOVE, SWP_NOSIZE,
    WM_HOTKEY, RETURN_FOCUS_DELAY_MS, BUTBAYAR_CLICK_DELAY_MS,
)
from pos_reader import read_ketoko_value, click_butbayar, is_ketoko_window

user32 = ctypes.windll.user32


class WindowsAPIManager:
    def __init__(self, app):
        self.app = app
        self.my_hwnd = None
        self.previous_hwnd = None
        self.last_f12_time = 0

    def init_windows_api(self):
        self.my_hwnd = user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(100)
        user32.GetWindowTextW(self.my_hwnd, buf, 100)
        if "Cash Note" not in buf.value:
            self.my_hwnd = user32.FindWindowW(None, "Cash Note")

    def start_hotkey_listener(self):
        def listen():
            # Register Hotkeys
            user32.RegisterHotKey(None, 1, 0, 0x7B) # F12
            user32.RegisterHotKey(None, 2, 0, 0x79) # F10
            user32.RegisterHotKey(None, 3, 0, 0x7A) # F11
            
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    hotkey_id = msg.wParam
                    
                    if hotkey_id == 1: # F12 logic
                        current_time = time.time()
                        # Detect double tap (interval < 0.4 seconds)
                        if current_time - self.last_f12_time < 0.4:
                            self.app.after(0, self.focus_app)
                        self.last_f12_time = current_time

                    elif hotkey_id == 2: # F10 (Ketoko auto-read + focus)
                        current = user32.GetForegroundWindow()
                        buf = ctypes.create_unicode_buffer(256)
                        user32.GetWindowTextW(current, buf, 256)
                        val = ""
                        is_ketoko, _ = is_ketoko_window(current, buf.value)
                        if is_ketoko:
                            # ponytail: read in hotkey thread before Cash Note steals foreground
                            val = read_ketoko_value(current)
                        self.app.after(0, lambda v=val, k=is_ketoko: self.focus_app(prefill_value=v, from_ketoko=k))

                    else: # F11 (Single tap - normal focus)
                        self.app.after(0, self.focus_app)
                        
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def focus_app(self, prefill_value: str = "", from_ketoko: bool = False):
        current = user32.GetForegroundWindow()
        if self.my_hwnd and current != self.my_hwnd:
            self.previous_hwnd = current
            user32.ShowWindow(self.my_hwnd, SW_RESTORE)
            user32.SetWindowPos(self.my_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            user32.SetWindowPos(self.my_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            user32.SetForegroundWindow(self.my_hwnd)

            if from_ketoko and self.app.current_file and self.app.active_tab != "ACT":
                self.app.show_tab("ACT")

            act_tab = self.app.tabs.get("ACT")
            if self.app.active_tab == "ACT" and act_tab:
                act_tab.apply_ketoko_prefill(prefill_value, from_ketoko)
                act_tab.entry_amount.focus_force()

    def return_focus(self, trigger_pay: bool = False):
        target_hwnd = self.previous_hwnd
        if target_hwnd:
            def task():
                user32.SetForegroundWindow(target_hwnd)
                self.previous_hwnd = None
                if trigger_pay:
                    # ponytail: jeda kecil agar window target aktif sebelum klik UIA
                    delay = BUTBAYAR_CLICK_DELAY_MS / 1000.0
                    threading.Thread(target=lambda: (time.sleep(delay), click_butbayar(target_hwnd)), daemon=True).start()
            self.app.after(RETURN_FOCUS_DELAY_MS, task)
