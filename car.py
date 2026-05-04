import math

import pygame


class Car:
    def __init__(
        self,
        color: tuple[int, int, int],
        start_x: float,
        start_y: float,
        start_angle: float = -90,
        controls: dict[str, int] | None = None,
    ) -> None:
        self.width = 22
        self.height = 38
        self.max_speed = 6.5
        self.acceleration = 0.18
        self.friction = 0.05
        self.turn_speed = 3.2
        self.color = color
        self.controls = controls or {}
        self.start_x = start_x
        self.start_y = start_y
        self.start_angle = start_angle
        self.reset()

    def reset(self) -> None:
        self.x = self.start_x
        self.y = self.start_y
        self.angle = self.start_angle
        self.speed = 0.0

    def update_manual(self, keys: pygame.key.ScancodeWrapper) -> None:
        self.move(
            forward=keys[self.controls["forward"]],
            backward=keys[self.controls["backward"]],
            left=keys[self.controls["left"]],
            right=keys[self.controls["right"]],
        )

    def update_ai(self, outputs: list[float] | tuple[float, ...]) -> None:
        forward = outputs[0] > 0.5
        backward = outputs[1] > 0.5
        left = outputs[2] > 0.5
        right = outputs[3] > 0.5
        self.move(forward=forward, backward=backward, left=left, right=right)

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

    def sensor_distances(
        self,
        track_mask: pygame.mask.Mask,
        world_width: int,
        world_height: int,
        ray_angles: tuple[int, ...] = (-80, -40, 0, 40, 80),
        max_distance: int = 220,
    ) -> list[float]:
        distances = []
        for offset in ray_angles:
            ray_angle = math.radians(self.angle + offset)
            distance = 0
            while distance < max_distance:
                point_x = int(self.x + math.cos(ray_angle) * distance)
                point_y = int(self.y + math.sin(ray_angle) * distance)
                if (
                    point_x < 0
                    or point_x >= world_width
                    or point_y < 0
                    or point_y >= world_height
                    or track_mask.get_at((point_x, point_y)) == 0
                ):
                    break
                distance += 4
            distances.append(distance / max_distance)
        return distances

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

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.polygon(surface, self.color, self.corners())
        front = (
            self.x + math.cos(math.radians(self.angle)) * (self.height / 2 - 4),
            self.y + math.sin(math.radians(self.angle)) * (self.height / 2 - 4),
        )
        pygame.draw.circle(surface, (255, 255, 255), (int(front[0]), int(front[1])), 4)

    def draw_sensors(
        self,
        surface: pygame.Surface,
        track_mask: pygame.mask.Mask,
        world_width: int,
        world_height: int,
        ray_angles: tuple[int, ...] = (-80, -40, 0, 40, 80),
        max_distance: int = 220,
    ) -> None:
        for offset in ray_angles:
            ray_angle = math.radians(self.angle + offset)
            distance = 0
            hit_point = (int(self.x), int(self.y))
            while distance < max_distance:
                point_x = int(self.x + math.cos(ray_angle) * distance)
                point_y = int(self.y + math.sin(ray_angle) * distance)
                if (
                    point_x < 0
                    or point_x >= world_width
                    or point_y < 0
                    or point_y >= world_height
                    or track_mask.get_at((point_x, point_y)) == 0
                ):
                    break
                hit_point = (point_x, point_y)
                distance += 4
            pygame.draw.line(surface, (255, 255, 255), (int(self.x), int(self.y)), hit_point, 1)
            pygame.draw.circle(surface, (255, 255, 255), hit_point, 2)
