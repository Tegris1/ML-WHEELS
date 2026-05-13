from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from game.models.car import Car

DEFAULT_SENSOR_ANGLES = (-80, -40, 0, 40, 80)
DEFAULT_SENSOR_DISTANCE = 220
SENSOR_STEP = 4


@dataclass(frozen=True)
class SensorReading:
    distance: int
    normalized_distance: float
    hit_point: tuple[int, int]


def read_car_sensors(
    car: Car,
    track_mask: pygame.mask.Mask,
    world_width: int,
    world_height: int,
    ray_angles: tuple[int, ...] = DEFAULT_SENSOR_ANGLES,
    max_distance: int = DEFAULT_SENSOR_DISTANCE,
) -> list[SensorReading]:
    return [
        _cast_sensor_ray(
            car,
            track_mask,
            world_width,
            world_height,
            offset,
            max_distance,
        )
        for offset in ray_angles
    ]


def _cast_sensor_ray(
    car: Car,
    track_mask: pygame.mask.Mask,
    world_width: int,
    world_height: int,
    angle_offset: int,
    max_distance: int,
) -> SensorReading:
    ray_angle = math.radians(car.angle + angle_offset)
    distance = 0
    hit_point = (int(car.x), int(car.y))

    while distance < max_distance:
        point_x = int(car.x + math.cos(ray_angle) * distance)
        point_y = int(car.y + math.sin(ray_angle) * distance)
        if (
            point_x < 0
            or point_x >= world_width
            or point_y < 0
            or point_y >= world_height
            or track_mask.get_at((point_x, point_y)) == 0
        ):
            break

        hit_point = (point_x, point_y)
        distance += SENSOR_STEP

    return SensorReading(
        distance=distance,
        normalized_distance=distance / max_distance,
        hit_point=hit_point,
    )
