import json
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from constants import GAS_URL_KASIR

class GasService:
    def __init__(self, endpoint=GAS_URL_KASIR, timeout=20):
        self.endpoint = endpoint
        self.timeout = timeout

    def call_api(self, action, args):
        """Send a JSON-RPC styled POST request to Google Apps Script."""
        payload = json.dumps({"action": action, "args": args}).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "text/plain"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                return json.loads(content)
        except urllib.error.HTTPError as e:
            return {"success": False, "message": f"HTTP Error {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"success": False, "message": f"Koneksi gagal: {e.reason}"}
        except TimeoutError:
            return {"success": False, "message": "Request timeout (server tidak merespons)"}
        except Exception as e:
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}

    def login(self, email, password):
        """Authenticate cashier with GAS endpoint."""
        res = self.call_api(
            "checkLogin",
            [{
                "email": email.strip(),
                "password": password,
                "deviceId": "CashNoteDesktop"
            }]
        )
        if not res or not res.get("success"):
            return {
                "success": False,
                "message": res.get("message", "Email atau password salah!") if res else "Tidak ada respon server"
            }

        redirect_url = res.get("redirectUrl", "")
        token_match = re.search(r"token=([^&]+)", redirect_url)
        if token_match:
            token = urllib.parse.unquote(token_match.group(1))
        else:
            token = f"token_{int(time.time() * 1000)}"

        return {
            "success": True,
            "token": token,
            "user": res.get("user")
        }

    def get_dashboard_data(self, token, cashier_name=""):
        """Fetch 5-day transactions from GAS dashboard."""
        res = self.call_api("getDashboardData", [token, cashier_name])
        if not res or not res.get("success"):
            error_msg = res.get("error") or res.get("message") or "Gagal memuat data transaksi"
            return {
                "success": False,
                "message": error_msg,
                "data": [],
                "totalTransaksi": 0
            }

        data = res.get("data", [])
        total_transaksi = res.get("totalTransaksi", len(data))

        # Calculate totals
        total_kurang = 0
        total_lebih = 0
        for item in data:
            selisih = item.get("jumlahSelisih", 0)
            if selisih < 0:
                total_kurang += abs(selisih)
            elif selisih > 0:
                total_lebih += selisih

        return {
            "success": True,
            "total_transaksi": total_transaksi,
            "total_kurang": total_kurang,
            "total_lebih": total_lebih,
            "data": data
        }

    def fetch_kasir_summary(self, email, password, cashier_name=""):
        """High-level method: Login and then fetch 5-day dashboard data."""
        login_res = self.login(email, password)
        if not login_res.get("success"):
            return {
                "success": False,
                "stage": "login",
                "message": login_res.get("message", "Gagal login")
            }

        token = login_res["token"]
        dash_res = self.get_dashboard_data(token, cashier_name)
        if not dash_res.get("success"):
            return {
                "success": False,
                "stage": "fetch",
                "message": dash_res.get("message", "Gagal mengambil transaksi")
            }

        return {
            "success": True,
            "token": token,
            "total_transaksi": dash_res["total_transaksi"],
            "total_kurang": dash_res["total_kurang"],
            "total_lebih": dash_res["total_lebih"],
            "data": dash_res["data"]
        }

# Global singleton instance
gas_service = GasService()
