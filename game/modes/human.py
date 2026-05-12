from __future__ import annotations

import pygame

from game.config import (
    FPS,
    HEIGHT,
    PLAYER_ONE,
    PLAYER_ONE_CONTROLS,
    PLAYER_TWO,
    PLAYER_TWO_CONTROLS,
    WIDTH,
)
from game.logic.race import RaceState, advance_race_state, car_hits_wall, cars_collide
from game.models.car import Car
from game.rendering.car import draw_car
from game.rendering.track import build_track_mask, draw_track
from game.rendering.ui import draw_ui


def create_player_cars() -> tuple[Car, Car]:
    player_one = Car(
        color=PLAYER_ONE,
        controls=PLAYER_ONE_CONTROLS,
        start_x=WIDTH // 2 + 45,
        start_y=145,
    )
    player_two = Car(
        color=PLAYER_TWO,
        controls=PLAYER_TWO_CONTROLS,
        start_x=WIDTH // 2 + 95,
        start_y=145,
    )
    return player_one, player_two


def run_human_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock() #fps
    font = pygame.font.SysFont("arial", 30, bold=True)

    track_mask = build_track_mask()
    player_one, player_two = create_player_cars()
    player_one_state = RaceState()
    player_two_state = RaceState()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if _restart_requested(event, player_one_state, player_two_state):
                player_one.reset()
                player_two.reset()
                player_one_state = RaceState()
                player_two_state = RaceState()

        keys = pygame.key.get_pressed()
        _update_player_car(player_one, player_one_state, keys, track_mask)
        _update_player_car(player_two, player_two_state, keys, track_mask)
        _handle_player_collision(player_one, player_two, player_one_state, player_two_state)

        draw_track(screen)
        draw_car(player_one, screen)
        draw_car(player_two, screen)
        draw_ui(screen, font, player_one_state, player_two_state)
        pygame.display.flip()
        clock.tick(FPS)


def _restart_requested(
    event: pygame.event.Event,
    player_one_state: RaceState,
    player_two_state: RaceState,
) -> bool:
    return (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_r
        and (player_one_state.crashed or player_two_state.crashed)
    )


def _update_player_car(
    car: Car,
    race_state: RaceState,
    keys: pygame.key.ScancodeWrapper,
    track_mask: pygame.mask.Mask,
) -> None:
    if race_state.crashed:
        return

    car.update_manual(keys)
    if car_hits_wall(car, track_mask):
        race_state.crashed = True
        return

    advance_race_state(car, race_state)


def _handle_player_collision(
    player_one: Car,
    player_two: Car,
    player_one_state: RaceState,
    player_two_state: RaceState,
) -> None:
    if player_one_state.crashed or player_two_state.crashed:
        return

    if cars_collide(player_one, player_two):
        player_one_state.crashed = True
        player_two_state.crashed = True
