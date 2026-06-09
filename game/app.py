import pygame

from game.app_result import AppResult, QUIT
from game.ui.main_menu import ACTION_QUIT, ACTION_START, MainMenu, MenuSelection


def run_app() -> None:
    menu = MainMenu()
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    clock = pygame.time.Clock()

    while True:
        action = menu.run(screen, clock)
        if action == ACTION_QUIT:
            break
        if action == ACTION_START:
            selection = menu.selection()
            result = _run_mode(selection)
            if result == QUIT:
                break
            menu.clear_status()


def _run_mode(selection: MenuSelection) -> AppResult:
    if selection.mode == "train":
        from game.ai.training import run_training

        return run_training(selection.training)
    if selection.mode == "watch":
        from game.ai.training import watch_winner

        try:
            return watch_winner(selection.watch)
        except SystemExit as error:
            return _handle_error(error)
    if selection.mode == "edit_track":
        from game.modes.track_editor import run_track_editor

        return run_track_editor()
    if selection.mode == "play":
        from game.modes.play import run_play_mode

        try:
            return run_play_mode(selection.play)
        except SystemExit as error:
            return _handle_error(error)
    raise ValueError(f"Unknown mode: {selection.mode}")


def _handle_error(error: SystemExit) -> AppResult:
    # Here you'd ideally pass the error message back to the menu to display
    print(error)
    return AppResult.RETURN_TO_MENU
