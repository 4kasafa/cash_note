import sys
from app import CashNoteApp

if __name__ == "__main__":
    try:
        app = CashNoteApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
