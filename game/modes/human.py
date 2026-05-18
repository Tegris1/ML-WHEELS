from __future__ import annotations

from collections.abc import Mapping

import pygame

from game.app_result import AppResult, QUIT, RETURN_TO_MENU
from game.config import (
    FPS,
    HEIGHT,
    PLAYER_ONE,
    PLAYER_TWO,
    WIDTH,
)
from game.logic.race import RaceState, advance_race_state, car_hits_wall, cars_collide
from game.models.car import Car
from game.models.track import create_player_cars
from game.rendering.car import draw_car
from game.rendering.track import build_track_mask, draw_track
from game.rendering.ui import draw_ui

PLAYER_ONE_CONTROLS = {
    "forward": pygame.K_w,
    "backward": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
}
PLAYER_TWO_CONTROLS = {
    "forward": pygame.K_UP,
    "backward": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
}


def create_player_cars() -> tuple[Car, Car]:
    player_one = Car(
        start_x=WIDTH // 2 + 45,
        start_y=145,
    )
    player_two = Car(
        start_x=WIDTH // 2 + 95,
        start_y=145,
    )
    return player_one, player_two


def run_human_game() -> AppResult:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 30, bold=True)

    track_mask = build_track_mask()
    player_one, player_two = create_player_cars()
    player_one_state = RaceState()
    player_two_state = RaceState()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return QUIT
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return RETURN_TO_MENU
            if _restart_requested(event, player_one_state, player_two_state):
                player_one.reset()
                player_two.reset()
                player_one_state = RaceState()
                player_two_state = RaceState()

        keys = pygame.key.get_pressed()
        _update_player_car(player_one, player_one_state, keys, PLAYER_ONE_CONTROLS, track_mask)
        _update_player_car(player_two, player_two_state, keys, PLAYER_TWO_CONTROLS, track_mask)
        _handle_player_collision(player_one, player_two, player_one_state, player_two_state)

        draw_track(screen)
        draw_car(player_one, screen, PLAYER_ONE)
        draw_car(player_two, screen, PLAYER_TWO)
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
    controls: Mapping[str, int],
    track_mask: pygame.mask.Mask,
) -> None:
    if race_state.crashed:
        return

    _apply_player_input(car, keys, controls)
    if car_hits_wall(car, track_mask):
        race_state.crashed = True
        return

    advance_race_state(car, race_state)


def _apply_player_input(
    car: Car,
    keys: pygame.key.ScancodeWrapper,
    controls: Mapping[str, int],
) -> None:
    car.move(
        forward=keys[controls["forward"]],
        backward=keys[controls["backward"]],
        left=keys[controls["left"]],
        right=keys[controls["right"]],
    )


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
