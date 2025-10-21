import pygame

pygame.init()
pygame.mixer.init()

# Display and performance
SCREEN_SIZE = (960, 640)
FPS = 60

# Fonts
FONT = pygame.font.SysFont("consolas", 18)
BIGFONT = pygame.font.SysFont("consolas", 36)

# Colors
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
GREY = (180, 180, 180)
RED = (200, 40, 40)
GREEN = (40, 200, 40)
BLUE = (60, 140, 200)
YELLOW = (240, 220, 80)
ORANGE = (230, 130, 40)
DARK = (30, 30, 30)

# Audio (optional)
TITLE_THEME = "title_theme.mp3"
BATTLE_THEME = "battle_theme.mp3"

# Typing alias
RollResult = tuple[int, str]
