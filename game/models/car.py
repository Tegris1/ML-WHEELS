from __future__ import annotations

import math


class Car:
    def __init__(
        self,
        start_x: float,
        start_y: float,
        start_angle: float = 0,
    ) -> None:
        self.width = 22
        self.height = 38
        self.max_speed = 6.5
        self.acceleration = 0.18
        self.friction = 0.05
        self.turn_speed = 3.2
        self.start_x = start_x
        self.start_y = start_y
        self.start_angle = start_angle
        self.reset()

    def reset(self) -> None:
        self.x = self.start_x
        self.y = self.start_y
        self.angle = self.start_angle
        self.speed = 0.0

    def move(self, forward: bool, backward: bool, left: bool, right: bool) -> None:
        if forward:
            self.speed += self.acceleration
        if backward:
            self.speed -= self.acceleration * 0.8

        if not (forward or backward):
            if self.speed > 0:
                self.speed = max(0, self.speed - self.friction)
            elif self.speed < 0:
                self.speed = min(0, self.speed + self.friction)

        self.speed = max(-self.max_speed / 2, min(self.max_speed, self.speed))

        if abs(self.speed) > 0.2:
            direction = 1 if self.speed >= 0 else -1
            if left:
                self.angle -= self.turn_speed * direction
            if right:
                self.angle += self.turn_speed * direction

        radians = math.radians(self.angle)
        self.x += math.cos(radians) * self.speed
        self.y += math.sin(radians) * self.speed

    def corners(self) -> list[tuple[float, float]]:
        radians = math.radians(self.angle)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)
        half_w = self.width / 2
        half_h = self.height / 2
        local_points = [
            (-half_h, -half_w),
            (half_h, -half_w),
            (half_h, half_w),
            (-half_h, half_w),
        ]

        points = []
        for local_x, local_y in local_points:
            world_x = self.x + local_x * cos_a - local_y * sin_a
            world_y = self.y + local_x * sin_a + local_y * cos_a
            points.append((world_x, world_y))
        return points
