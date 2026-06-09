from __future__ import annotations

import pickle
from collections.abc import Mapping, Sequence

import pygame

from game.ai.training import network_inputs, require_neat
from game.app_result import AppResult, QUIT, RETURN_TO_MENU
from game.config import (
    AI_COLOR,
    FPS,
    HEIGHT,
    PLAYER_ONE,
    PLAYER_TWO,
    WIDTH,
)
from game.logic.race import RaceState, advance_race_state, car_hits_wall, cars_collide
from game.modes.settings import (
    PLAYER_TYPE_AI,
    PLAYER_TYPE_EMPTY,
    PLAYER_TYPE_HUMAN_1,
    PLAYER_TYPE_HUMAN_2,
    PlaySettings,
)
from game.models.track import create_ai_car, create_player_cars
from game.paths import get_winner_path, NEAT_CONFIG_PATH
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


def run_play_mode(settings: PlaySettings) -> AppResult:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 30, bold=True)
    track_mask = build_track_mask()

    drivers = _create_drivers(settings)
    if not drivers:
        return RETURN_TO_MENU

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return QUIT
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return RETURN_TO_MENU
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                for driver in drivers:
                    driver.reset()

        keys = pygame.key.get_pressed()
        for driver in drivers:
            driver.update(keys, track_mask)

        if settings.collisions_enabled:
            _handle_collisions(drivers)

        draw_track(screen)
        for driver in drivers:
            driver.draw(screen)
        draw_ui(
            screen,
            font,
            drivers[0].race_state,
            drivers[1].race_state if len(drivers) > 1 else None,
        )
        pygame.display.flip()
        clock.tick(FPS)


def _create_drivers(settings: PlaySettings) -> list[Driver]:
    drivers = []
    player_cars = create_player_cars()
    if settings.player_one_type != PLAYER_TYPE_EMPTY:
        drivers.append(
            _create_driver(
                settings.player_one_type,
                settings.player_one_ai_profile,
                PLAYER_ONE,
                PLAYER_ONE_CONTROLS,
                player_cars[0]
            )
        )
    if settings.player_two_type != PLAYER_TYPE_EMPTY:
        drivers.append(
            _create_driver(
                settings.player_two_type,
                settings.player_two_ai_profile,
                PLAYER_TWO,
                PLAYER_TWO_CONTROLS,
                player_cars[1]
            )
        )
    return drivers


def _create_driver(
    player_type: str,
    ai_profile: int | None,
    color: tuple[int, int, int],
    controls: Mapping[str, int] | None,
    car: Car,
) -> Driver:
    if player_type == PLAYER_TYPE_AI:
        return _create_ai_driver(ai_profile, color, car)
    if player_type == PLAYER_TYPE_HUMAN_1:
        return HumanDriver(car, color, controls)
    if player_type == PLAYER_TYPE_HUMAN_2:
        return HumanDriver(car, color, controls)
    raise ValueError(f"Unknown player type: {player_type}")


def _create_ai_driver(profile_index: int, color: tuple[int, int, int], car: Car) -> Driver:
    neat = require_neat()
    winner_path = get_winner_path(profile_index)
    if not winner_path.exists():
        raise SystemExit(f"No saved genome found for profile {profile_index + 1}.")

    winner = pickle.loads(winner_path.read_bytes())
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        NEAT_CONFIG_PATH,
    )
    net = neat.nn.FeedForwardNetwork.create(winner, config)
    return AIDriver(car, color, net)


def _handle_collisions(drivers: list[Driver]) -> None:
    for i in range(len(drivers)):
        for j in range(i + 1, len(drivers)):
            if cars_collide(drivers[i].car, drivers[j].car):
                drivers[i].race_state.crashed = True
                drivers[j].race_state.crashed = True


class Driver:
    def __init__(self, car: Car, color: tuple[int, int, int]):
        self.car = car
        self.color = color
        self.race_state = RaceState()

    def reset(self) -> None:
        self.car.reset()
        self.race_state = RaceState()

    def draw(self, screen: pygame.Surface) -> None:
        draw_car(self.car, screen, self.color)

    def update(self, keys: pygame.key.ScancodeWrapper, track_mask: pygame.mask.Mask) -> None:
        raise NotImplementedError


class HumanDriver(Driver):
    def __init__(
        self,
        car: Car,
        color: tuple[int, int, int],
        controls: Mapping[str, int],
    ):
        super().__init__(car, color)
        self.controls = controls

    def update(self, keys: pygame.key.ScancodeWrapper, track_mask: pygame.mask.Mask) -> None:
        if self.race_state.crashed:
            return

        self.car.move(
            forward=keys[self.controls["forward"]],
            backward=keys[self.controls["backward"]],
            left=keys[self.controls["left"]],
            right=keys[self.controls["right"]],
        )
        if car_hits_wall(self.car, track_mask):
            self.race_state.crashed = True
            return

        advance_race_state(self.car, self.race_state)


class AIDriver(Driver):
    def __init__(self, car: Car, color: tuple[int, int, int], net):
        super().__init__(car, color)
        self.net = net

    def update(self, keys: pygame.key.ScancodeWrapper, track_mask: pygame.mask.Mask) -> None:
        if self.race_state.crashed:
            return

        inputs = network_inputs(self.car, self.race_state, track_mask)
        outputs = self.net.activate(inputs)
        self._apply_ai_outputs(outputs)

        if car_hits_wall(self.car, track_mask):
            self.race_state.crashed = True
            return

        advance_race_state(self.car, self.race_state)

    def _apply_ai_outputs(self, outputs: Sequence[float]) -> None:
        self.car.move(
            forward=outputs[0] > 0.5,
            backward=outputs[1] > 0.5,
            left=outputs[2] > 0.5,
            right=outputs[3] > 0.5,
        )
