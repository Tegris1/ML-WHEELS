from __future__ import annotations

import math

import pygame

from game.config import HEIGHT, WIDTH
from game.models.car import Car


def draw_car(car: Car, surface: pygame.Surface) -> None:
    pygame.draw.polygon(surface, car.color, car.corners())
    front = (
        car.x + math.cos(math.radians(car.angle)) * (car.height / 2 - 4),
        car.y + math.sin(math.radians(car.angle)) * (car.height / 2 - 4),
    )
    pygame.draw.circle(surface, (255, 255, 255), (int(front[0]), int(front[1])), 4)


def draw_car_sensors(
    car: Car,
    surface: pygame.Surface,
    track_mask: pygame.mask.Mask,
    ray_angles: tuple[int, ...] = (-80, -40, 0, 40, 80),
    max_distance: int = 220,
) -> None:
    for offset in ray_angles:
        hit_point = _sensor_hit_point(car, track_mask, offset, max_distance)
        pygame.draw.line(surface, (255, 255, 255), (int(car.x), int(car.y)), hit_point, 1)
        pygame.draw.circle(surface, (255, 255, 255), hit_point, 2)


def _sensor_hit_point(
    car: Car,
    track_mask: pygame.mask.Mask,
    angle_offset: int,
    max_distance: int,
) -> tuple[int, int]:
    ray_angle = math.radians(car.angle + angle_offset)
    distance = 0
    hit_point = (int(car.x), int(car.y))

    while distance < max_distance:
        point_x = int(car.x + math.cos(ray_angle) * distance)
        point_y = int(car.y + math.sin(ray_angle) * distance)
        if (
            point_x < 0
            or point_x >= WIDTH
            or point_y < 0
            or point_y >= HEIGHT
            or track_mask.get_at((point_x, point_y)) == 0
        ):
            break
        hit_point = (point_x, point_y)
        distance += 4

    return hit_point
