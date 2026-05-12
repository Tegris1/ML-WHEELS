from __future__ import annotations

import math

import pygame

from game.config import HEIGHT, WIDTH
from game.logic.sensors import (
    DEFAULT_SENSOR_ANGLES,
    DEFAULT_SENSOR_DISTANCE,
    read_car_sensors,
)
from game.models.car import Car


def draw_car(
    car: Car,
    surface: pygame.Surface,
    color: tuple[int, int, int],
) -> None:
    pygame.draw.polygon(surface, color, car.corners())
    front = (
        car.x + math.cos(math.radians(car.angle)) * (car.height / 2 - 4),
        car.y + math.sin(math.radians(car.angle)) * (car.height / 2 - 4),
    )
    pygame.draw.circle(surface, (255, 255, 255), (int(front[0]), int(front[1])), 4)


def draw_car_sensors(
    car: Car,
    surface: pygame.Surface,
    track_mask: pygame.mask.Mask,
    ray_angles: tuple[int, ...] = DEFAULT_SENSOR_ANGLES,
    max_distance: int = DEFAULT_SENSOR_DISTANCE,
) -> None:
    for reading in read_car_sensors(
        car,
        track_mask,
        WIDTH,
        HEIGHT,
        ray_angles,
        max_distance,
    ):
        hit_point = reading.hit_point
        pygame.draw.line(surface, (255, 255, 255), (int(car.x), int(car.y)), hit_point, 1)
        pygame.draw.circle(surface, (255, 255, 255), hit_point, 2)
