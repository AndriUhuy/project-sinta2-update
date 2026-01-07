# File: core/updater.py
import requests
import webbrowser
from packaging import version

class OTAUpdater:
    def __init__(self, current_version="1.0"):
        self.current_version = current_version
        
        # --- GANTI LINK INI DENGAN LINK RAW GITHUB KAMU ---
        self.version_url = "https://raw.githubusercontent.com/AndriUhuy/project-sinta2-update/refs/heads/main/version.txt" 
        # --------------------------------------------------
        
        # Link halaman download (bisa diarahkan ke repo utama)
        self.download_url = "https://github.com/AndriUhuy/project-sinta2-update/tree/main" 

    def check_for_updates(self):
        """
        Cek ke internet apakah ada versi baru.
        Returns: (is_available: bool, new_version: str)
        """
        try:
            print(f"Checking update from cloud...")
            # Tambahkan random number biar gak di-cache sama proxy/isp
            response = requests.get(self.version_url, params={'t': 'nocache'}, timeout=5)
            
            if response.status_code == 200:
                latest_version = response.text.strip()
                print(f"Cloud Version: {latest_version} | Local: {self.current_version}")
                
                # Bandingkan versi (misal 2.0 > 1.0)
                if version.parse(latest_version) > version.parse(self.current_version):
                    return True, latest_version
                else:
                    return False, latest_version
            else:
                return False, "Error"
        except Exception as e:
            print(f"Update Check Error: {e}")
            return False, "Connection Error"

    def open_download_page(self):
        """Buka browser ke halaman download"""
        webbrowser.open(self.download_url)