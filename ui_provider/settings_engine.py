import json
import os


class settings_engine:
    def __init__(self, settings_file="app_settings.json"):
        self.file_path = settings_file
        self.default_settings = {



        }
        self.settings = self.load_settings()

    def load_settings(self):
        """Load settings from JSON, or return defaults if file missing/corrupt."""
        if not os.path.exists(self.file_path):
            self.save_settings(self.default_settings)  # Create file
            return self.default_settings

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                # Merge with defaults in case new keys were added to the app recently
                # (This ensures your app doesn't crash if a key is missing in the file)
                for key, value in self.default_settings.items():
                    if key not in data:
                        data[key] = value
                return data
        except (json.JSONDecodeError, IOError):
            print("Settings file corrupt. Using defaults.")
            return self.default_settings

    def save_settings(self, new_data=None):
        """Save current settings to disk."""
        if new_data:
            self.settings = new_data

        try:
            with open(self.file_path, "w") as f:
                json.dump(self.settings, f, indent=5)  # indent=4 makes it readable for humans
            # print("Settings saved.")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        return self.settings.get(key, self.default_settings.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()
