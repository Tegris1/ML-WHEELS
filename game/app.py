from __future__ import annotations

import pygame

from game.app_result import AppResult, RETURN_TO_MENU
from game.config import HEIGHT, WIDTH
from game.ui.main_menu import ACTION_QUIT, MODE_EDIT_TRACK, MODE_PLAY, MODE_TRAIN, MainMenu, MenuSelection


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    menu = MainMenu()

    running = True
    while running:
        action = menu.run(screen, clock)
        if action == ACTION_QUIT:
            break

        menu.clear_status()
        try:
            result = _run_selection(menu.selection())
        except SystemExit as error:
            menu.set_status(str(error))
            result = RETURN_TO_MENU

        running = result == RETURN_TO_MENU
        if running:
            screen = pygame.display.set_mode((WIDTH, HEIGHT))

    pygame.quit()


def _run_selection(selection: MenuSelection) -> AppResult:
    if selection.mode == MODE_PLAY:
        from game.modes.human import run_human_game

        return run_human_game()

    if selection.mode == MODE_TRAIN:
        from game.ai.training import run_training

        return run_training(selection.training)

    if selection.mode == MODE_EDIT_TRACK:
        from game.modes.track_editor import run_track_editor

        return run_track_editor()

    from game.ai.training import watch_winner

    return watch_winner(selection.watch)
