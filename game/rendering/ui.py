from __future__ import annotations

import pygame

from game.config import GAME_OVER, HEIGHT, TEXT, WIDTH
from game.logic.race import RaceState


def draw_ui(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_one_state: RaceState,
    player_two_state: RaceState,
) -> None:
    _draw_lap_info(surface, font, player_one_state, player_two_state)
    _draw_crash_message(surface, player_one_state, player_two_state)


def _draw_lap_info(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_one_state: RaceState,
    player_two_state: RaceState,
) -> None:
    player_one_text = font.render(f"Blue laps: {player_one_state.laps}", True, TEXT)
    player_two_text = font.render(f"Gold laps: {player_two_state.laps}", True, TEXT)
    hint_one = font.render("Blue car: WASD", True, TEXT)
    hint_two = font.render("Gold car: Arrows", True, TEXT)

    surface.blit(player_one_text, (20, 20))
    surface.blit(player_two_text, (20, 55))
    surface.blit(hint_one, (20, 90))
    surface.blit(hint_two, (20, 125))


def _draw_crash_message(
    surface: pygame.Surface,
    player_one_state: RaceState,
    player_two_state: RaceState,
) -> None:
    messages = []
    if player_one_state.crashed:
        messages.append("Blue car lost")
    if player_two_state.crashed:
        messages.append("Gold car lost")

    if not messages:
        return

    crash_font = pygame.font.SysFont("arial", 42, bold=True)
    text = " | ".join(messages) + " - Press R to restart."
    message = crash_font.render(text, True, GAME_OVER)
    rect = message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    shadow = message.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 + 3))
    shadow_text = crash_font.render(text, True, (0, 0, 0))
    surface.blit(shadow_text, shadow)
    surface.blit(message, rect)
