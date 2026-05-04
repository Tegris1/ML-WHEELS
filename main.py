import sys

import pygame

from ai_train import run_training, watch_winner
from track import (
    FPS,
    GAME_OVER,
    HEIGHT,
    TEXT,
    WIDTH,
    advance_race_state,
    build_track_mask,
    car_hits_wall,
    cars_collide,
    create_player_cars,
    create_race_state,
    draw_track,
    reset_race_state,
)


def draw_ui(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_one_state: dict[str, int | bool],
    player_two_state: dict[str, int | bool],
) -> None:
    player_one_text = font.render(f"Blue laps: {int(player_one_state['laps'])}", True, TEXT)
    player_two_text = font.render(f"Gold laps: {int(player_two_state['laps'])}", True, TEXT)
    hint_one = font.render("Blue car: WASD", True, TEXT)
    hint_two = font.render("Gold car: Arrows", True, TEXT)
    surface.blit(player_one_text, (20, 20))
    surface.blit(player_two_text, (20, 55))
    surface.blit(hint_one, (20, 90))
    surface.blit(hint_two, (20, 125))

    messages = []
    if bool(player_one_state["crashed"]):
        messages.append("Blue car lost")
    if bool(player_two_state["crashed"]):
        messages.append("Gold car lost")

    if messages:
        crash_font = pygame.font.SysFont("arial", 42, bold=True)
        text = " | ".join(messages) + " - Press R to restart."
        message = crash_font.render(text, True, GAME_OVER)
        rect = message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        shadow = message.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 + 3))
        shadow_text = crash_font.render(text, True, (0, 0, 0))
        surface.blit(shadow_text, shadow)
        surface.blit(message, rect)


def run_human_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 30, bold=True)

    track_mask = build_track_mask()
    player_one, player_two = create_player_cars()
    player_one_state = create_race_state()
    player_two_state = create_race_state()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
                and (bool(player_one_state["crashed"]) or bool(player_two_state["crashed"]))
            ):
                player_one.reset()
                player_two.reset()
                reset_race_state(player_one_state)
                reset_race_state(player_two_state)

        keys = pygame.key.get_pressed()
        if not bool(player_one_state["crashed"]):
            player_one.update_manual(keys)
            if car_hits_wall(player_one, track_mask):
                player_one_state["crashed"] = True
            else:
                advance_race_state(player_one, player_one_state)

        if not bool(player_two_state["crashed"]):
            player_two.update_manual(keys)
            if car_hits_wall(player_two, track_mask):
                player_two_state["crashed"] = True
            else:
                advance_race_state(player_two, player_two_state)

        if (
            not bool(player_one_state["crashed"])
            and not bool(player_two_state["crashed"])
            and cars_collide(player_one, player_two)
        ):
            player_one_state["crashed"] = True
            player_two_state["crashed"] = True

        draw_track(screen)
        player_one.draw(screen)
        player_two.draw(screen)
        draw_ui(screen, font, player_one_state, player_two_state)
        pygame.display.flip()
        clock.tick(FPS)


def main() -> None:
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "play"
    if mode == "play":
        run_human_game()
        return
    if mode == "train":
        generations = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        run_training(generations)
        return
    if mode == "watch":
        watch_winner()
        return
    raise SystemExit("Usage: python main.py [play|train|watch] [generations]")


if __name__ == "__main__":
    main()
