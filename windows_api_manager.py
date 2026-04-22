import ctypes
from ctypes import wintypes
import threading
from constants import SW_RESTORE, HWND_TOPMOST, HWND_NOTOPMOST, SWP_NOMOVE, SWP_NOSIZE, WM_HOTKEY

user32 = ctypes.windll.user32

class WindowsAPIManager:
    def __init__(self, app):
        self.app = app
        self.my_hwnd = None
        self.previous_hwnd = None

    def init_windows_api(self):
        self.my_hwnd = user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(100)
        user32.GetWindowTextW(self.my_hwnd, buf, 100)
        if "Cash Note" not in buf.value:
            self.my_hwnd = user32.FindWindowW(None, "Cash Note")

    def start_hotkey_listener(self):
        def listen():
            user32.RegisterHotKey(None, 1, 0, 0x7B) # F12
            user32.RegisterHotKey(None, 2, 0, 0x79) # F10
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY:
                    self.app.after(0, self.focus_app)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def focus_app(self):
        current = user32.GetForegroundWindow()
        if self.my_hwnd and current != self.my_hwnd:
            self.previous_hwnd = current
            user32.ShowWindow(self.my_hwnd, SW_RESTORE)
            user32.SetWindowPos(self.my_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            user32.SetWindowPos(self.my_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            user32.SetForegroundWindow(self.my_hwnd)
            if self.app.active_tab == "ACT":
                self.app.tabs["ACT"].entry_amount.focus_force()

    def return_focus(self):
        if self.previous_hwnd:
            def task():
                user32.SetForegroundWindow(self.previous_hwnd)
                self.previous_hwnd = None
            self.app.after(200, task)
