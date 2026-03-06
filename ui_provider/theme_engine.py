from PySide6.QtCore import QObject, Signal


class theme_engine(QObject):
    themeChanged = Signal(str)

    def __init__(self, initial_theme="dark"):
        super().__init__()
        # Application properties (Sizing, Spacing, Radii)
        # Using consistent naming conventions and modern spacing multiples (4, 8, 16, 24)
        self.geometry = {
            "win_title": "App Title",
            "title_bar_height": 32,
            "status_bar_height": 20,
            "border_radius_sm": 4,  # For checkboxes, tooltips
            "border_radius_md": 8,  # For buttons, text inputs
            "border_radius_lg": 12,  # For cards, main windows
            "padding": 16
        }

        # Typography (Modern UI focuses on readability and weight hierarchy)
        # Assuming format: (Font Family, Size, Weight) - common in UI frameworks
        font_family = "Segoe UI"  # You can also add fallbacks like "Inter" or "Roboto"
        self.typography = {
            "title": f"""bold 15px {font_family}""",  # Weight 600/700 equivalent
            "button": f"""normal 15px {font_family}""",  # Weight 600/700 equivalent
            "large_button": f"""normal 20px {font_family}""",  # Weight 600/700 equivalent
            "body": f"""BOLD 16px {font_family}""",  # Weight 600/700 equivalent
            "hd_line": f"""bold 20px {font_family}""",  # Weight 600/700 equivalent

        }

        # Modern Color Palettes
        self.palettes = {
            "dark_emerald": {
                "primary": "#0A0F0D",
                "secondary": "#111827",
                "secondary_hover": "#1F2937",

                "text": "#ECFDF5",
                "text_secondary": "#86EFAC",
                "text_warning": "#F87171",

                "accent_primary": "#10B981",
                "accent_hover": "#059669",

                "border": "#1F2937"
            },
            "dark": {
                "primary": "#0F172A",  # Deep slate (Main Window)
                "secondary": "#1E293B",  # Lighter slate (Cards, Panels)
                "secondary_hover": "#334155",

                "text": "#F8FAFC",  # Off-white (easy on the eyes)
                "text_secondary": "#94A3B8",  # Muted gray for subtitles
                "text_warning": "#EF4444",  # Crisp red for destructive actions

                "accent_primary": "#6366F1",  # Modern Indigo
                "accent_hover": "#4F46E5",  # Slightly darker indigo on hover

                "border": "#334155"  # Subtle borders to separate elements
            },
            "light": {
                "primary": "#F8FAFC",  # Very light cool gray
                "secondary": "#FFFFFF",  # Pure white (Cards, Panels)
                "secondary_hover": "#F1F5F9",

                "text": "#0F172A",  # Almost black
                "text_secondary": "#64748B",  # Slate gray
                "text_warning": "#DC2626",

                "accent_primary": "#4F46E5",  # Deep Indigo
                "accent_hover": "#4338CA",

                "border": "#E2E8F0"
            },
            "light_soft": {
                "primary": "#F5F7FA",
                "secondary": "#FFFFFF",
                "secondary_hover": "#EEF2F7",

                "text": "#111827",
                "text_secondary": "#6B7280",
                "text_warning": "#DC2626",

                "accent_primary": "#2563EB",
                "accent_hover": "#1D4ED8",

                "border": "#E5E7EB"
            }
        }

        self.current_theme = initial_theme

    def set_theme(self, theme_name):
        """Allows dynamic switching between 'light' and 'dark' modes."""
        if theme_name in self.palettes:
            self.current_theme = theme_name
            self.themeChanged.emit()
        else:
            raise ValueError(f"Theme '{theme_name}' not found.")

    def get(self, key):
        """Fetches a color based on the currently active theme."""
        return self.palettes[self.current_theme].get(key, "#FF00FF")  # Magenta fallback for missing keys

    def getProperty(self, key):
        """Fetches geometry/sizing properties."""
        return self.geometry.get(key, 0)

    def getFont(self, key):
        """Fetches typography settings."""
        return self.typography.get(key)
