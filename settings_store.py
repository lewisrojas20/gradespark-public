# settings_store.py
import os
import json
import logging

class SettingsStore:
    def __init__(self, filename="settings.json"):
        self.filepath = filename
        self.defaults = {
            "api_key": "",
            "show_rubric_categories": True,
            "show_rubric": True,
            "dark_mode_enabled": False,
            "window_size": [1000, 700],
            "last_selection": {"grade": "", "subject": "", "assignment": ""},
            "env_imported": False,
            "window_geometry": None,
            "tour_completed": False
        }
        self.settings = self.load()
        self._import_from_env_once()

    def load(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r') as f:
                    loaded_settings = json.load(f)
                settings = self.defaults.copy()
                settings.update(loaded_settings)
                return settings
        except Exception as e:
            logging.error(f"Failed to load settings from {self.filepath}: {e}")
        return self.defaults.copy()

    def _import_from_env_once(self):
        if self.get("env_imported"):
            return
        if os.path.exists('.env'):
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.strip().split('=', 1)[1]
                            self.set("api_key", api_key)
                            logging.info("Imported API key from .env file.")
                self.set("env_imported", True)
                self.save()
            except Exception as e:
                logging.error(f"Could not import from .env file: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
    
    def __setitem__(self, key, value):
        """Allow dictionary-style assignment"""
        self.settings[key] = value
    
    def __getitem__(self, key):
        """Allow dictionary-style access"""
        return self.settings.get(key)

    def save(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save settings to {self.filepath}: {e}")
