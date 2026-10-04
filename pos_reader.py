import ctypes
import os
import re
import uiautomation as auto
from constants import KETOKO_PROCESS_NAME, KETOKO_WINDOW_TITLE

# ClassName obfuscated dari field total Ketoko, fallback ke scan Edit ControlType
KETOKO_EDIT_CLASS = "l11illlII111I"
KETOKO_BUTTON_PAY_ID = "ButBayar"


def get_window_process_name(hwnd: int) -> str:
    """Nama file process pemilik hwnd (e.g. 'KetokoD.exe'), '' jika gagal."""
    try:
        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return ""
        # ponytail: QueryFullProcessImageName cukup, tanpa psutil/tambahan dependency
        hproc = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
        if not hproc:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(260)
            size = ctypes.wintypes.DWORD(260)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value)
        finally:
            ctypes.windll.kernel32.CloseHandle(hproc)
    except Exception:
        pass
    return ""


def is_ketoko_window(hwnd: int, title: str = "") -> tuple:
    """(is_ketoko, proc_name): True jika title match ATAU process KetokoD.exe.

    Menangani dialog terpisah (e.g. title='Pembayaran') milik process yang sama.
    """
    proc = get_window_process_name(hwnd)
    if title and KETOKO_WINDOW_TITLE.lower() in title.lower():
        return True, proc
    if proc.lower() == KETOKO_PROCESS_NAME.lower():
        return True, proc
    return False, proc


def _read_edit_sources(edit) -> dict:
    """Ambil semua sumber teks yang mungkin dari sebuah Edit control."""
    sources = {}
    try:
        sources["value"] = edit.GetValuePattern().Value or ""
    except Exception as e:
        sources["value_err"] = repr(e)
    try:
        sources["name"] = edit.Name or ""
    except Exception as e:
        sources["name_err"] = repr(e)
    try:
        sources["legacy"] = (edit.GetLegacyIAccessiblePattern().Value or "")[:200]
    except Exception as e:
        sources["legacy_err"] = repr(e)
    return sources


def _iter_edits(control, depth: int = 0, max_depth: int = 10):
    """Yield semua EditControl secara rekursif (GetDescendants tidak ada di lib ini)."""
    if depth > max_depth:
        return
    try:
        children = control.GetChildren()
    except Exception:
        return
    for child in children:
        try:
            if child.ControlType == auto.ControlType.EditControl:
                yield child
            else:
                yield from _iter_edits(child, depth + 1, max_depth)
        except Exception:
            continue


def _clean_amount_text(text: str) -> str:
    """Ambil digit saja dari teks nominal (e.g. 'Rp 150.000,00' -> '150000')."""
    if not text:
        return ""
    # Hapus koma desimal beserta 2 digit di belakangnya jika ada (,00)
    cleaned = re.sub(r",\d{1,2}$", "", text.strip())
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    # ponytail: abaikan jika hanya '0'
    if digits and int(digits) > 0:
        return digits
    return ""


def read_ketoko_value(hwnd: int) -> str:
    """Baca nilai nominal dari window Ketoko via UIAutomation.

    Return string digit bersih (e.g. '150000') atau '' jika gagal/kosong.
    Aman dipanggil dari thread background (tidak pernah raise).
    """
    if not hwnd:
        return ""
    try:
        with auto.UIAutomationInitializerInThread():
            window = auto.ControlFromHandle(hwnd)
            if not window or not window.Exists(1, 0.2):
                return ""

            # Prioritas 1: cari edit field dengan ClassName obfuscated yang sudah di-inspect
            edit = window.EditControl(searchDepth=10, ClassName=KETOKO_EDIT_CLASS)
            if edit.Exists(1, 0.2):
                sources = _read_edit_sources(edit)
                for key in ("value", "name", "legacy"):
                    cleaned = _clean_amount_text(sources.get(key, ""))
                    if cleaned:
                        return cleaned
                # ponytail: field nominal ketemu tapi kosong/0 -> percaya, jangan fallback
                return ""

            # Prioritas 2: fallback scan semua EditControl (nested) yang punya value > 0
            for ctrl in _iter_edits(window):
                sources = _read_edit_sources(ctrl)
                for key in ("value", "name", "legacy"):
                    raw = sources.get(key, "")
                    if "/" in raw or ":" in raw:
                        continue  # ponytail: tolak tanggal/jam (e.g. DateEdit 10/3/2026 5:11 PM)
                    cleaned = _clean_amount_text(raw)
                    if cleaned:
                        return cleaned
    except Exception:
        # ponytail: silent on UIA read failure, user can type manually
        pass
    return ""


def click_butbayar(hwnd: int) -> bool:
    """Klik tombol 'ButBayar' di window Ketoko via InvokePattern.

    Return True jika berhasil di-invoke, False jika gagal.
    """
    if not hwnd:
        return False
    try:
        with auto.UIAutomationInitializerInThread():
            window = auto.ControlFromHandle(hwnd)
            if not window or not window.Exists(1, 0.2):
                return False

            btn = window.ButtonControl(searchDepth=10, AutomationId=KETOKO_BUTTON_PAY_ID)
            if btn.Exists(1, 0.2):
                try:
                    btn.GetInvokePattern().Invoke()
                    return True
                except Exception:
                    btn.Click(simulateMove=False)
                    return True
    except Exception:
        # ponytail: silent on click failure, data in cash note is already saved
        pass
    return False
