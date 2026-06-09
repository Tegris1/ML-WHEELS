from __future__ import annotations

import pygame

from game.config import GAME_OVER, HEIGHT, TEXT, WIDTH
from game.logic.race import RaceState


def draw_ui(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_one_state: RaceState,
    player_two_state: RaceState | None = None,
) -> None:
    player_one_text = font.render(f"P1 laps: {player_one_state.laps}", True, TEXT)
    surface.blit(player_one_text, (20, 20))

    if player_two_state is not None:
        player_two_text = font.render(f"P2 laps: {player_two_state.laps}", True, TEXT)
        surface.blit(player_two_text, (20, 55))

    messages = []
    if player_one_state.crashed:
        messages.append("P1 lost")
    if player_two_state is not None and player_two_state.crashed:
        messages.append("P2 lost")

    if messages:
        crash_font = pygame.font.SysFont("arial", 42, bold=True)
        text = " | ".join(messages) + " - Press R to restart."
        message = crash_font.render(text, True, GAME_OVER)
        rect = message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        shadow = message.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 + 3))
        shadow_text = crash_font.render(text, True, (0, 0, 0))
        surface.blit(shadow_text, shadow)
        surface.blit(message, rect)
