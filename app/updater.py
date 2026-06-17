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
