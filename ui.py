import pygame
from config.config import FONT, WHITE, GREEN, BLUE, YELLOW, ORANGE, DARK

class UI:
    @staticmethod
    def draw_text(surface, text, pos, font=FONT, color=WHITE):
        surf = font.render(text, True, color)
        surface.blit(surf, pos)

    @staticmethod
    def draw_centered_text(surface, text, rect, font=FONT, color=WHITE):
        surf = font.render(text, True, color)
        surface.blit(surf, surf.get_rect(center=rect.center).topleft)

    @staticmethod
    def draw_bar(surface, rect, value, max_value, border_color=WHITE, fill_color=GREEN):
        pygame.draw.rect(surface, border_color, rect, 1)
        inner_w = max(0, int((rect.width - 4) * (value / max_value)))
        inner_r = pygame.Rect(rect.left + 2, rect.top + 2, inner_w, rect.height - 4)
        pygame.draw.rect(surface, fill_color, inner_r)

    @staticmethod
    def draw_character_placeholder(surface, rect, char, state="idle"):
        pygame.draw.rect(surface, DARK, rect)
        pygame.draw.rect(surface, char.color, rect.inflate(-10, -10))
        UI.draw_text(surface, char.name, (rect.left + 6, rect.top + 6))
        if state == "attack":
            pygame.draw.rect(surface, YELLOW, rect, 4)
