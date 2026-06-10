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
from game.models.track import create_ai_car, create_player_cars, CompiledTrack
from game.paths import get_winner_path, get_winner_name_path, NEAT_CONFIG_PATH
from game.rendering.car import draw_car
from game.rendering.track import draw_track
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


def run_play_mode(settings: PlaySettings, track: CompiledTrack) -> AppResult:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 30, bold=True)
    label_font = pygame.font.SysFont("bahnschrift", 16, bold=True)

    drivers = _create_drivers(settings, track)
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
            driver.update(keys, track)

        if settings.collisions_enabled:
            _handle_collisions(drivers)

        draw_track(screen, track)
        for driver in drivers:
            driver.draw(screen, label_font)
        draw_ui(
            screen,
            font,
            drivers[0].race_state,
            drivers[1].race_state if len(drivers) > 1 else None,
        )
        pygame.display.flip()
        clock.tick(FPS)


def _create_drivers(settings: PlaySettings, track: CompiledTrack) -> list[Driver]:
    drivers = []
    player_cars = create_player_cars(track)
    if settings.player_one_type != PLAYER_TYPE_EMPTY:
        drivers.append(
            _create_driver(
                settings.player_one_type,
                settings.player_one_ai_profile,
                PLAYER_ONE,
                PLAYER_ONE_CONTROLS,
                player_cars[0],
                track
            )
        )
    if settings.player_two_type != PLAYER_TYPE_EMPTY:
        drivers.append(
            _create_driver(
                settings.player_two_type,
                settings.player_two_ai_profile,
                PLAYER_TWO,
                PLAYER_TWO_CONTROLS,
                player_cars[1],
                track
            )
        )
    return drivers


def _create_driver(
    player_type: str,
    ai_profile: int | None,
    color: tuple[int, int, int],
    controls: Mapping[str, int] | None,
    car: Car,
    track: CompiledTrack,
) -> Driver:
    if player_type == PLAYER_TYPE_AI:
        return _create_ai_driver(ai_profile, color, car, track)
    if player_type == PLAYER_TYPE_HUMAN_1:
        return HumanDriver(car, color, "Human 1", controls)
    if player_type == PLAYER_TYPE_HUMAN_2:
        return HumanDriver(car, color, "Human 2", controls)
    raise ValueError(f"Unknown player type: {player_type}")


def _create_ai_driver(profile_index: int, color: tuple[int, int, int], car: Car, track: CompiledTrack) -> Driver:
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
    return AIDriver(car, color, _profile_label(profile_index), net)


def _profile_label(profile_index: int) -> str:
    name_path = get_winner_name_path(profile_index)
    if name_path.exists():
        name = name_path.read_text(encoding="utf-8").strip()
        if name:
            return name
    return f"Profile {profile_index + 1}"


def _handle_collisions(drivers: list[Driver]) -> None:
    for i in range(len(drivers)):
        for j in range(i + 1, len(drivers)):
            if cars_collide(drivers[i].car, drivers[j].car):
                drivers[i].race_state.crashed = True
                drivers[j].race_state.crashed = True


class Driver:
    def __init__(self, car: Car, color: tuple[int, int, int], label: str):
        self.car = car
        self.color = color
        self.label = label
        self.race_state = RaceState()

    def reset(self) -> None:
        self.car.reset()
        self.race_state = RaceState()

    def draw(self, screen: pygame.Surface, label_font: pygame.font.Font) -> None:
        draw_car(self.car, screen, self.color)
        self._draw_label(screen, label_font)

    def _draw_label(self, screen: pygame.Surface, label_font: pygame.font.Font) -> None:
        text = label_font.render(self.label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(self.car.x), int(self.car.y) - 36))
        panel_rect = text_rect.inflate(12, 6)
        panel_rect.clamp_ip(screen.get_rect())
        text_rect.center = panel_rect.center

        pygame.draw.rect(screen, (5, 8, 8), panel_rect.move(0, 3), border_radius=7)
        pygame.draw.rect(screen, (29, 39, 38), panel_rect, border_radius=7)
        pygame.draw.rect(screen, self.color, panel_rect, 1, border_radius=7)
        screen.blit(text, text_rect)

    def update(self, keys: pygame.key.ScancodeWrapper, track: CompiledTrack) -> None:
        raise NotImplementedError


class HumanDriver(Driver):
    def __init__(
        self,
        car: Car,
        color: tuple[int, int, int],
        label: str,
        controls: Mapping[str, int],
    ):
        super().__init__(car, color, label)
        self.controls = controls

    def update(self, keys: pygame.key.ScancodeWrapper, track: CompiledTrack) -> None:
        if self.race_state.crashed:
            return

        self.car.move(
            forward=keys[self.controls["forward"]],
            backward=keys[self.controls["backward"]],
            left=keys[self.controls["left"]],
            right=keys[self.controls["right"]],
        )
        if car_hits_wall(self.car, track.mask):
            self.race_state.crashed = True
            return

        advance_race_state(self.car, self.race_state, track)


class AIDriver(Driver):
    def __init__(self, car: Car, color: tuple[int, int, int], label: str, net):
        super().__init__(car, color, label)
        self.net = net

    def update(self, keys: pygame.key.ScancodeWrapper, track: CompiledTrack) -> None:
        if self.race_state.crashed:
            return

        inputs = network_inputs(self.car, self.race_state, track)
        outputs = self.net.activate(inputs)
        self._apply_ai_outputs(outputs)

        if car_hits_wall(self.car, track.mask):
            self.race_state.crashed = True
            return

        advance_race_state(self.car, self.race_state, track)

    def _apply_ai_outputs(self, outputs: Sequence[float]) -> None:
        self.car.move(
            forward=outputs[0] > 0.5,
            backward=outputs[1] > 0.5,
            left=outputs[2] > 0.5,
            right=outputs[3] > 0.5,
        )
