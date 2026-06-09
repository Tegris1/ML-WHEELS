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


def _scale_color(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)


def _mix_color(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    return tuple(
        int(first[channel] + (second[channel] - first[channel]) * ratio)
        for channel in range(3)
    )


def _car_point(car: Car, local_x: float, local_y: float) -> tuple[float, float]:
    radians = math.radians(car.angle)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    return (
        car.x + local_x * cos_a - local_y * sin_a,
        car.y + local_x * sin_a + local_y * cos_a,
    )


def _local_polygon(
    car: Car,
    points: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    return [_car_point(car, x, y) for x, y in points]


def _draw_rotated_rect(
    surface: pygame.Surface,
    car: Car,
    center: tuple[float, float],
    size: tuple[float, float],
    color: tuple[int, int, int],
) -> None:
    half_x = size[0] / 2
    half_y = size[1] / 2
    cx, cy = center
    points = [
        (cx - half_x, cy - half_y),
        (cx + half_x, cy - half_y),
        (cx + half_x, cy + half_y),
        (cx - half_x, cy + half_y),
    ]
    pygame.draw.polygon(surface, color, _local_polygon(car, points))


def _draw_local_circle(
    surface: pygame.Surface,
    car: Car,
    local_x: float,
    local_y: float,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    x, y = _car_point(car, local_x, local_y)
    pygame.draw.circle(surface, color, (int(x), int(y)), radius)


def draw_car(
    car: Car,
    surface: pygame.Surface,
    color: tuple[int, int, int],
) -> None:
    half_h = car.height / 2
    half_w = car.width / 2
    body = [
        (-half_h + 3, -half_w + 2),
        (half_h - 9, -half_w),
        (half_h - 2, -half_w + 5),
        (half_h, 0),
        (half_h - 2, half_w - 5),
        (half_h - 9, half_w),
        (-half_h + 3, half_w - 2),
        (-half_h, half_w - 6),
        (-half_h, -half_w + 6),
    ]

    shadow = [(x + 2.6, y + 2.2) for x, y in _local_polygon(car, body)]
    pygame.draw.polygon(surface, (8, 10, 10), shadow)

    tire_color = (14, 15, 14)
    for wheel_x in (-half_h + 8, half_h - 11):
        _draw_rotated_rect(surface, car, (wheel_x, -half_w - 1), (8, 5), tire_color)
        _draw_rotated_rect(surface, car, (wheel_x, half_w + 1), (8, 5), tire_color)

    outline = _scale_color(color, 0.42)
    pygame.draw.polygon(surface, outline, _local_polygon(car, body))

    body_color = _mix_color(color, (255, 255, 255), 0.08)
    body_inner = [
        (-half_h + 4, -half_w + 4),
        (half_h - 10, -half_w + 2),
        (half_h - 4, -half_w + 6),
        (half_h - 2, 0),
        (half_h - 4, half_w - 6),
        (half_h - 10, half_w - 2),
        (-half_h + 4, half_w - 4),
        (-half_h + 1, half_w - 7),
        (-half_h + 1, -half_w + 7),
    ]
    pygame.draw.polygon(surface, body_color, _local_polygon(car, body_inner))

    cabin = [
        (-6, -half_w + 4),
        (6, -half_w + 5),
        (9, -3),
        (9, 3),
        (6, half_w - 5),
        (-6, half_w - 4),
        (-10, 4),
        (-10, -4),
    ]
    glass = (36, 54, 61)
    pygame.draw.polygon(surface, glass, _local_polygon(car, cabin))
    pygame.draw.polygon(surface, (106, 145, 148), _local_polygon(car, cabin), 1)

    windshield = [(7, -5), (half_h - 7, -3), (half_h - 7, 3), (7, 5)]
    rear_window = [(-half_h + 5, -4), (-11, -5), (-11, 5), (-half_h + 5, 4)]
    pygame.draw.polygon(surface, (61, 85, 91), _local_polygon(car, windshield))
    pygame.draw.polygon(surface, (33, 47, 52), _local_polygon(car, rear_window))

    stripe = _mix_color(color, (255, 255, 255), 0.35)
    pygame.draw.line(
        surface,
        stripe,
        _car_point(car, -half_h + 7, 0),
        _car_point(car, half_h - 6, 0),
        2,
    )

    _draw_local_circle(surface, car, half_h - 2, -4, 2, (255, 244, 178))
    _draw_local_circle(surface, car, half_h - 2, 4, 2, (255, 244, 178))
    _draw_local_circle(surface, car, -half_h + 1, -5, 2, (212, 38, 38))
    _draw_local_circle(surface, car, -half_h + 1, 5, 2, (212, 38, 38))


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
        pygame.draw.line(surface, (180, 232, 220), (int(car.x), int(car.y)), hit_point, 1)
        pygame.draw.circle(surface, (245, 255, 231), hit_point, 2)
