from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.config import HEIGHT, WIDTH
from game.models.car import Car
from game.models.track import CompiledTrack


@dataclass
class RaceState:
    laps: int = 0
    checkpoint_index: int = 0
    finish_armed: bool = False
    in_finish: bool = False
    crashed: bool = False
    item: object | None = None

    def reset(self) -> None:
        self.laps = 0
        self.checkpoint_index = 0
        self.finish_armed = False
        self.in_finish = False
        self.crashed = False
        self.item = None


def car_hits_wall(car: Car, track_mask: pygame.mask.Mask) -> bool:
    for x, y in car.corners():
        px, py = int(x), int(y)
        if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT:
            return True
        if track_mask.get_at((px, py)) == 0:
            return True
    return False


def cars_collide(first_car: Car, second_car: Car) -> bool:
    first_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    second_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(first_surface, (255, 255, 255), [(int(x), int(y)) for x, y in first_car.corners()])
    pygame.draw.polygon(second_surface, (255, 255, 255), [(int(x), int(y)) for x, y in second_car.corners()])
    first_mask = pygame.mask.from_surface(first_surface)
    second_mask = pygame.mask.from_surface(second_surface)
    return first_mask.overlap(second_mask, (0, 0)) is not None


def advance_race_state(car: Car, state: RaceState, active_track: CompiledTrack) -> tuple[bool, bool]:
    checkpoint_index = state.checkpoint_index
    finish_armed = state.finish_armed
    previous_in_finish = state.in_finish
    car_point = (int(car.x), int(car.y))

    reached_checkpoint = False
    completed_lap = False

    if checkpoint_index < len(active_track.checkpoints) and active_track.checkpoints[checkpoint_index].contains(car_point):
        checkpoint_index += 1
        reached_checkpoint = True

    in_finish = active_track.finish_line.contains(car_point)
    if checkpoint_index == len(active_track.checkpoints):
        finish_armed = True

    if finish_armed and in_finish and not previous_in_finish:
        state.laps += 1
        checkpoint_index = 0
        finish_armed = False
        completed_lap = True

    state.checkpoint_index = checkpoint_index
    state.finish_armed = finish_armed
    state.in_finish = in_finish
    return reached_checkpoint, completed_lap


def next_checkpoint_center(state: RaceState, active_track: CompiledTrack) -> tuple[float, float]:
    if state.checkpoint_index >= len(active_track.checkpoints):
        target = active_track.finish_line.center
    else:
        target = active_track.checkpoints[state.checkpoint_index].center
    return float(target[0]), float(target[1])
