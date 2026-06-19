import urllib.request
import json
import logging
from .version import VERSION, GITHUB_USER, GITHUB_REPO

class UpdateManager:
    def __init__(self):
        self.api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
        self.latest_version = None
        self.download_url = None
        self.release_notes = ""

    def check_for_updates(self):
        """
        Returns True if a newer version is available on GitHub.
        """
        try:
            # GitHub API requires a User-Agent header
            req = urllib.request.Request(self.api_url, headers={'User-Agent': 'PoE2-Timer-App'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                # Tag names are usually "v1.0.0" or "1.0.0"
                tag = data.get("tag_name", "").replace("v", "")
                self.latest_version = tag
                self.release_notes = data.get("body", "")
                
                # Find the first asset that looks like an EXE or ZIP
                assets = data.get("assets", [])
                if assets:
                    self.download_url = assets[0].get("browser_download_url")
                else:
                    self.download_url = data.get("html_url") # Fallback to release page

                if self._is_newer(tag, VERSION):
                    return True
        except Exception as e:
            logging.error(f"Failed to check for updates: {e}")
        
        return False

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(p) for p in latest.split(".")]
            c_parts = [int(p) for p in current.split(".")]
            return l_parts > c_parts
        except:
            return latest != current

    def download_file(self, target_path, progress_callback=None):
        """
        Downloads the binary from download_url to target_path with progress feedback.
        progress_callback: function(int) - receives percentage (0-100)
        """
        if not self.download_url:
            return False
        try:
            req = urllib.request.Request(self.download_url, headers={'User-Agent': 'PoE2-Timer-App'})
            with urllib.request.urlopen(req) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                block_size = 8192
                
                with open(target_path, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        f.write(buffer)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            progress_callback(percent)
            return True
        except Exception as e:
            logging.error(f"Failed to download update: {e}")
            return False
