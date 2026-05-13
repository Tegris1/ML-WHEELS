from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.config import CHECKPOINTS, FINISH_LINE, HEIGHT, WIDTH
from game.models.car import Car


@dataclass
class RaceState:
    laps: int = 0
    checkpoint_index: int = 0
    finish_armed: bool = False
    in_finish: bool = True
    crashed: bool = False


def car_hits_wall(car: Car, track_mask: pygame.mask.Mask) -> bool:
    for x, y in car.corners():
        px, py = int(x), int(y)
        if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT:
            return True
        if track_mask.get_at((px, py)) == 0:
            return True
    return False


def cars_collide(first_car: Car, second_car: Car) -> bool:
    first_mask = _car_collision_mask(first_car)
    second_mask = _car_collision_mask(second_car)
    return first_mask.overlap(second_mask, (0, 0)) is not None


def advance_race_state(car: Car, state: RaceState) -> tuple[bool, bool]:
    car_point = (int(car.x), int(car.y))
    reached_checkpoint = False
    completed_lap = False

    if _reached_next_checkpoint(car_point, state):
        state.checkpoint_index += 1
        reached_checkpoint = True

    in_finish = FINISH_LINE.collidepoint(car_point)
    if state.checkpoint_index == len(CHECKPOINTS):
        state.finish_armed = True

    if state.finish_armed and in_finish and not state.in_finish:
        state.laps += 1
        state.checkpoint_index = 0
        state.finish_armed = False
        completed_lap = True

    state.in_finish = in_finish
    return reached_checkpoint, completed_lap


def next_checkpoint_center(state: RaceState) -> tuple[float, float]:
    if state.checkpoint_index >= len(CHECKPOINTS):
        target = FINISH_LINE
    else:
        target = CHECKPOINTS[state.checkpoint_index]
    return float(target.centerx), float(target.centery)


def _reached_next_checkpoint(car_point: tuple[int, int], state: RaceState) -> bool:
    if state.checkpoint_index >= len(CHECKPOINTS):
        return False
    return CHECKPOINTS[state.checkpoint_index].collidepoint(car_point)


def _car_collision_mask(car: Car) -> pygame.mask.Mask:
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(
        surface,
        (255, 255, 255),
        [(int(x), int(y)) for x, y in car.corners()],
    )
    return pygame.mask.from_surface(surface)
