from __future__ import annotations

import pygame

from game.config import GAME_OVER, HEIGHT, WIDTH
from game.logic.race import RaceState
from game.ui import theme


def draw_ui(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_one_state: RaceState,
    player_two_state: RaceState | None = None,
) -> None:
    panel_height = 78 if player_two_state is not None else 46
    panel = pygame.Rect(16, 16, 190, panel_height)
    pygame.draw.rect(surface, theme.PANEL_SHADOW, panel.move(0, 5), border_radius=14)
    pygame.draw.rect(surface, theme.PANEL, panel, border_radius=14)
    pygame.draw.rect(surface, theme.BORDER_SOFT, panel, 2, border_radius=14)

    player_one_text = font.render(f"P1 LAP {player_one_state.laps}", True, theme.TEXT)
    surface.blit(player_one_text, (32, 24))
    if player_two_state is not None:
        player_two_text = font.render(f"P2 LAP {player_two_state.laps}", True, theme.TEXT)
        surface.blit(player_two_text, (32, 58))

    messages = []
    if player_one_state.crashed:
        messages.append("P1 lost")
    if player_two_state is not None and player_two_state.crashed:
        messages.append("P2 lost")

    if messages:
        crash_font = pygame.font.SysFont("bahnschrift", 42, bold=True)
        text = " | ".join(messages) + " - Press R to restart."
        message = crash_font.render(text, True, GAME_OVER)
        rect = message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        box = rect.inflate(48, 30)
        pygame.draw.rect(surface, theme.PANEL_SHADOW, box.move(0, 7), border_radius=18)
        pygame.draw.rect(surface, theme.PANEL, box, border_radius=18)
        pygame.draw.rect(surface, theme.WARNING, box, 2, border_radius=18)
        surface.blit(message, rect)
