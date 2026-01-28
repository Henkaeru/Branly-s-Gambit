class ThemeColors:
    def __init__(self, ui_manager):
        self._theme = ui_manager.get_theme()

    def colour(self, name: str, default=(255, 255, 255)):
        try:
            return self._theme.get_colour(name)
        except Exception:
            return default
