from __future__ import annotations

from dataclasses import dataclass
import math
import random

import pygame

from car import Car
from track import HEIGHT, WIDTH


PICKUP_RESPAWN_FRAMES = 280
HAZARD_DURATION_FRAMES = 180

ITEM_BOOST = "boost"
ITEM_ZAP = "zap"
ITEM_OIL = "oil"
ITEM_TYPES = (ITEM_BOOST, ITEM_ZAP, ITEM_OIL)

ITEM_LABELS = {
    ITEM_BOOST: "Turbo",
    ITEM_ZAP: "Zap",
    ITEM_OIL: "Oil",
}

ITEM_COLORS = {
    ITEM_BOOST: (90, 225, 255),
    ITEM_ZAP: (255, 235, 90),
    ITEM_OIL: (175, 90, 255),
}

ITEM_CODE = {
    None: 0.0,
    ITEM_BOOST: 0.35,
    ITEM_ZAP: 0.7,
    ITEM_OIL: 1.0,
}


@dataclass
class Pickup:
    position: pygame.Vector2
    item_type: str
    radius: int = 14
    available: bool = True
    respawn_timer: int = 0


@dataclass
class Hazard:
    position: pygame.Vector2
    owner_id: str
    timer: int = HAZARD_DURATION_FRAMES
    radius: int = 16


class PickupManager:
    def __init__(self, spawn_points: list[tuple[float, float]], seed: int = 7) -> None:
        self._rng = random.Random(seed)
        self._spawn_points = [pygame.Vector2(point) for point in spawn_points]
        self.pickups = [
            Pickup(position=point.copy(), item_type=self._rng.choice(ITEM_TYPES))
            for point in self._spawn_points
        ]
        self.hazards: list[Hazard] = []

    def reset(self) -> None:
        self.hazards.clear()
        for pickup, point in zip(self.pickups, self._spawn_points):
            pickup.position = point.copy()
            pickup.item_type = self._rng.choice(ITEM_TYPES)
            pickup.available = True
            pickup.respawn_timer = 0

    def update(self, racers: list[tuple[str, Car, dict[str, int | bool | str | None]]]) -> dict[str, dict[str, int]]:
        events = {
            racer_id: {"collected": 0, "hits": 0}
            for racer_id, _, _ in racers
        }

        for pickup in self.pickups:
            if pickup.available:
                continue
            pickup.respawn_timer -= 1
            if pickup.respawn_timer <= 0:
                pickup.available = True
                pickup.item_type = self._rng.choice(ITEM_TYPES)

        for pickup in self.pickups:
            if not pickup.available:
                continue
            for racer_id, car, state in racers:
                if bool(state.get("crashed")) or state.get("item") is not None:
                    continue
                if pickup.position.distance_to((car.x, car.y)) <= pickup.radius + (car.width / 2):
                    pickup.available = False
                    pickup.respawn_timer = PICKUP_RESPAWN_FRAMES
                    state["item"] = pickup.item_type
                    events[racer_id]["collected"] += 1
                    break

        remaining_hazards: list[Hazard] = []
        for hazard in self.hazards:
            hazard.timer -= 1
            if hazard.timer <= 0:
                continue
            triggered = False
            for racer_id, car, state in racers:
                if racer_id == hazard.owner_id or bool(state.get("crashed")):
                    continue
                if hazard.position.distance_to((car.x, car.y)) <= hazard.radius + (car.width / 2):
                    car.apply_slow(55)
                    car.skid(10)
                    events[hazard.owner_id]["hits"] += 1
                    triggered = True
                    break
            if not triggered:
                remaining_hazards.append(hazard)
        self.hazards = remaining_hazards
        return events

    def use_item(
        self,
        owner_id: str,
        car: Car,
        state: dict[str, int | bool | str | None],
        opponents: list[tuple[str, Car, dict[str, int | bool | str | None]]],
    ) -> bool:
        item_type = state.get("item")
        if item_type is None:
            return False

        if item_type == ITEM_BOOST:
            car.apply_boost(95)
            state["item"] = None
            return True

        if item_type == ITEM_ZAP:
            target = nearest_opponent(car, opponents)
            if target is None:
                return False
            _, opponent_car, opponent_state = target
            if bool(opponent_state.get("crashed")):
                return False
            if pygame.Vector2(opponent_car.x, opponent_car.y).distance_to((car.x, car.y)) > 230:
                return False
            heading = heading_to_point(car, opponent_car.x, opponent_car.y)
            if abs(heading) > 0.42:
                return False
            opponent_car.apply_slow(70)
            opponent_car.skid(12)
            state["item"] = None
            return True

        if item_type == ITEM_OIL:
            drop_offset = pygame.Vector2(
                math.cos(math.radians(car.angle)),
                math.sin(math.radians(car.angle)),
            ) * -(car.height * 0.7)
            drop_position = pygame.Vector2(car.x, car.y) + drop_offset
            clamped_position = pygame.Vector2(
                max(0, min(WIDTH - 1, drop_position.x)),
                max(0, min(HEIGHT - 1, drop_position.y)),
            )
            self.hazards.append(Hazard(position=clamped_position, owner_id=owner_id))
            state["item"] = None
            return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        for pickup in self.pickups:
            if not pickup.available:
                continue
            color = ITEM_COLORS[pickup.item_type]
            center = (int(pickup.position.x), int(pickup.position.y))
            pygame.draw.circle(surface, color, center, pickup.radius)
            pygame.draw.circle(surface, (255, 255, 255), center, pickup.radius, 2)
            icon_radius = max(2, pickup.radius // 3)
            if pickup.item_type == ITEM_BOOST:
                points = [
                    (center[0] - 4, center[1] - 2),
                    (center[0] + 1, center[1] - 2),
                    (center[0] - 1, center[1] + 5),
                    (center[0] + 5, center[1] + 1),
                    (center[0] + 1, center[1] + 1),
                    (center[0] + 3, center[1] - 5),
                ]
                pygame.draw.polygon(surface, (255, 255, 255), points)
            elif pickup.item_type == ITEM_ZAP:
                pygame.draw.line(surface, (255, 255, 255), (center[0] - 4, center[1]), (center[0] + 4, center[1]), 3)
                pygame.draw.line(surface, (255, 255, 255), (center[0], center[1] - 4), (center[0], center[1] + 4), 3)
            else:
                pygame.draw.circle(surface, (255, 255, 255), center, icon_radius)
                pygame.draw.circle(surface, color, center, max(1, icon_radius - 2))

        for hazard in self.hazards:
            center = (int(hazard.position.x), int(hazard.position.y))
            pygame.draw.circle(surface, (45, 30, 55), center, hazard.radius + 2)
            pygame.draw.circle(surface, ITEM_COLORS[ITEM_OIL], center, hazard.radius, 2)
            pygame.draw.circle(surface, (20, 20, 20), center, hazard.radius - 4)


def nearest_pickup_info(car: Car, manager: PickupManager) -> tuple[float, float]:
    available_pickups = [pickup for pickup in manager.pickups if pickup.available]
    if not available_pickups:
        return 0.0, 1.0
    target = min(
        available_pickups,
        key=lambda pickup: pickup.position.distance_squared_to((car.x, car.y)),
    )
    return heading_to_point(car, target.position.x, target.position.y), normalized_distance(car, target.position)


def nearest_opponent(
    car: Car,
    opponents: list[tuple[str, Car, dict[str, int | bool | str | None]]],
) -> tuple[str, Car, dict[str, int | bool | str | None]] | None:
    active_opponents = [entry for entry in opponents if not bool(entry[2].get("crashed"))]
    if not active_opponents:
        return None
    return min(
        active_opponents,
        key=lambda entry: pygame.Vector2(entry[1].x, entry[1].y).distance_squared_to((car.x, car.y)),
    )


def nearest_opponent_info(
    car: Car,
    opponents: list[tuple[str, Car, dict[str, int | bool | str | None]]],
) -> tuple[float, float]:
    target = nearest_opponent(car, opponents)
    if target is None:
        return 0.0, 1.0
    _, opponent_car, _ = target
    return heading_to_point(car, opponent_car.x, opponent_car.y), normalized_distance(car, (opponent_car.x, opponent_car.y))


def heading_to_point(car: Car, target_x: float, target_y: float) -> float:
    target_angle = math.degrees(math.atan2(target_y - car.y, target_x - car.x))
    delta = (target_angle - car.angle + 180) % 360 - 180
    return delta / 180.0


def normalized_distance(car: Car, point: tuple[float, float] | pygame.Vector2) -> float:
    distance = pygame.Vector2(point).distance_to((car.x, car.y))
    max_distance = math.hypot(WIDTH, HEIGHT)
    return min(distance / max_distance, 1.0)
