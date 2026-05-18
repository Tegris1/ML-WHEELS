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
        self.brake_force = 0.14
        self.rolling_friction = 0.025
        self.drag = 0.992
        self.turn_speed = 3.2
        self.tire_grip = 0.22
        self.max_lateral_grip = 0.28
        self.start_x = start_x
        self.start_y = start_y
        self.start_angle = start_angle
        self.reset()

    def reset(self) -> None:
        self.x = self.start_x
        self.y = self.start_y
        self.angle = self.start_angle
        self.speed = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0

    def move(self, forward: bool, backward: bool, left: bool, right: bool) -> None:
        heading_x = math.cos(math.radians(self.angle))
        heading_y = math.sin(math.radians(self.angle))
        right_x = -heading_y
        right_y = heading_x

        forward_speed = self.velocity_x * heading_x + self.velocity_y * heading_y

        if forward:
            forward_speed += self.acceleration
        if backward:
            if forward_speed > 0:
                forward_speed = max(0.0, forward_speed - self.brake_force)
            else:
                forward_speed -= self.acceleration * 0.7

        if not (forward or backward):
            forward_speed *= 1.0 - self.rolling_friction
            if abs(forward_speed) < 0.02:
                forward_speed = 0.0

        forward_speed = max(-self.max_speed / 2, min(self.max_speed, forward_speed))

        turn_input = int(right) - int(left)
        if turn_input and abs(forward_speed) > 0.15:
            speed_ratio = min(abs(forward_speed) / self.max_speed, 1.0)
            steer_scale = 0.35 + speed_ratio * 0.65
            direction = 1 if forward_speed >= 0 else -1
            self.angle += self.turn_speed * steer_scale * turn_input * direction

        heading_x = math.cos(math.radians(self.angle))
        heading_y = math.sin(math.radians(self.angle))
        right_x = -heading_y
        right_y = heading_x

        lateral_speed = self.velocity_x * right_x + self.velocity_y * right_y
        lateral_correction = -lateral_speed * self.tire_grip
        lateral_correction = max(
            -self.max_lateral_grip,
            min(self.max_lateral_grip, lateral_correction),
        )
        lateral_speed += lateral_correction

        self.velocity_x = heading_x * forward_speed + right_x * lateral_speed
        self.velocity_y = heading_y * forward_speed + right_y * lateral_speed
        self.velocity_x *= self.drag
        self.velocity_y *= self.drag

        self.x += self.velocity_x
        self.y += self.velocity_y
        self.speed = self.velocity_x * heading_x + self.velocity_y * heading_y

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
