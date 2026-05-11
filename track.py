from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

import pygame

from car import Car


WIDTH, HEIGHT = 1000, 700
FPS = 60

GRASS = (34, 139, 34)
ROAD = (70, 70, 70)
ROAD_EDGE = (180, 180, 180)
LINE = (250, 250, 250)
FINISH = (255, 80, 80)
TEXT = (255, 255, 255)
GAME_OVER = (255, 220, 220)
PLAYER_ONE = (60, 170, 255)
PLAYER_TWO = (255, 190, 60)
AI_COLOR = (130, 230, 110)

TRACK_LAYOUT_PATH = Path(__file__).with_name("track_layout.json")
DEFAULT_TRACK_WIDTH = 80
DEFAULT_TRACK_CENTER = pygame.Vector2(WIDTH / 2, HEIGHT / 2 + 10)
DEFAULT_TRACK_SAMPLE_COUNT = 180
DEFAULT_START_INDEX = 4
CHECKPOINT_COUNT = 6
MIN_TRACK_POINTS = 24
TRACK_SPACING = 12
MIN_TRACK_WIDTH = 50
MAX_TRACK_WIDTH = 140

PLAYER_ONE_CONTROLS = {
    "forward": pygame.K_w,
    "backward": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
}
PLAYER_TWO_CONTROLS = {
    "forward": pygame.K_UP,
    "backward": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
}


@dataclass(frozen=True)
class TrackZone:
    center: tuple[float, float]
    polygon: tuple[tuple[float, float], ...]
    bounds: pygame.Rect

    def contains(self, point: tuple[int, int]) -> bool:
        return self.bounds.collidepoint(point) and _point_in_polygon(point, self.polygon)


@dataclass(frozen=True)
class TrackLayout:
    centerline: tuple[tuple[float, float], ...]
    track_width: int

    def point_at(self, index: int) -> pygame.Vector2:
        x, y = self.centerline[index % len(self.centerline)]
        return pygame.Vector2(x, y)

    def tangent_at(self, index: int) -> pygame.Vector2:
        tangent = self.point_at(index + 1) - self.point_at(index - 1)
        if tangent.length_squared() == 0:
            tangent = self.point_at(index + 1) - self.point_at(index)
        return tangent.normalize()

    def normal_at(self, index: int) -> pygame.Vector2:
        tangent = self.tangent_at(index)
        return pygame.Vector2(-tangent.y, tangent.x)

    @property
    def edge_width(self) -> int:
        return self.track_width + 12

    @property
    def start_index(self) -> int:
        return min(DEFAULT_START_INDEX, len(self.centerline) - 1)

    def zone_at(self, index: int, width: float, depth: float) -> TrackZone:
        center = self.point_at(index)
        tangent = self.tangent_at(index)
        normal = self.normal_at(index)
        half_width = width / 2
        half_depth = depth / 2
        polygon_vectors = (
            center - (normal * half_width) - (tangent * half_depth),
            center + (normal * half_width) - (tangent * half_depth),
            center + (normal * half_width) + (tangent * half_depth),
            center - (normal * half_width) + (tangent * half_depth),
        )
        polygon = tuple((point.x, point.y) for point in polygon_vectors)
        min_x = min(point[0] for point in polygon)
        max_x = max(point[0] for point in polygon)
        min_y = min(point[1] for point in polygon)
        max_y = max(point[1] for point in polygon)
        return TrackZone(
            center=(center.x, center.y),
            polygon=polygon,
            bounds=pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y).inflate(2, 2),
        )

    def finish_line(self) -> TrackZone:
        return self.zone_at(0, self.track_width + 16, 30)

    def checkpoints(self) -> tuple[TrackZone, ...]:
        step = len(self.centerline) / (CHECKPOINT_COUNT + 1)
        zones = []
        for order in range(1, CHECKPOINT_COUNT + 1):
            index = int(round(self.start_index + (step * order))) % len(self.centerline)
            zones.append(self.zone_at(index, self.track_width + 10, 26))
        return tuple(zones)

    def start_pose(self, lane_offset: float) -> tuple[float, float, float]:
        center = self.point_at(self.start_index)
        tangent = self.tangent_at(self.start_index)
        normal = self.normal_at(self.start_index)
        start = center + (normal * lane_offset)
        angle = math.degrees(math.atan2(tangent.y, tangent.x))
        return start.x, start.y, angle


@dataclass(frozen=True)
class CompiledTrack:
    layout: TrackLayout
    surface: pygame.Surface
    mask: pygame.mask.Mask
    finish_line: TrackZone
    checkpoints: tuple[TrackZone, ...]
    player_one_start: tuple[float, float, float]
    player_two_start: tuple[float, float, float]
    ai_start: tuple[float, float, float]


def _point_in_polygon(point: tuple[int, int], polygon: tuple[tuple[float, float], ...]) -> bool:
    x, y = point
    inside = False
    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        intersects = (current_y > y) != (previous_y > y)
        if intersects:
            slope_x = (previous_x - current_x) * (y - current_y) / (previous_y - current_y) + current_x
            if x < slope_x:
                inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


def _track_radius(theta: float) -> float:
    return (
        220
        + 42 * math.sin((2 * theta) + 0.6)
        + 28 * math.sin((5 * theta) - 1.1)
        - 18 * math.cos((3 * theta) + 0.3)
    )


def create_default_layout() -> TrackLayout:
    points = []
    for index in range(DEFAULT_TRACK_SAMPLE_COUNT):
        theta = (-math.pi / 2) + ((2 * math.pi * index) / DEFAULT_TRACK_SAMPLE_COUNT)
        radius = _track_radius(theta)
        points.append(
            (
                DEFAULT_TRACK_CENTER.x + math.cos(theta) * (radius * 1.12),
                DEFAULT_TRACK_CENTER.y + math.sin(theta) * (radius * 1.02),
            )
        )
    return TrackLayout(centerline=tuple(points), track_width=DEFAULT_TRACK_WIDTH)


def _sanitize_points(points: list[tuple[float, float]]) -> list[pygame.Vector2]:
    cleaned: list[pygame.Vector2] = []
    for raw_x, raw_y in points:
        point = pygame.Vector2(float(raw_x), float(raw_y))
        if not cleaned or point.distance_to(cleaned[-1]) >= 2:
            cleaned.append(point)
    return cleaned


def build_layout_from_path(points: list[tuple[float, float]], track_width: int) -> TrackLayout:
    cleaned = _sanitize_points(points)
    if len(cleaned) < 6:
        raise ValueError("Draw a longer loop before saving.")

    loop_points = cleaned[:]
    if loop_points[0].distance_to(loop_points[-1]) > max(TRACK_SPACING * 1.5, track_width * 0.6):
        loop_points.append(loop_points[0])

    segment_lengths = []
    total_length = 0.0
    for index in range(len(loop_points) - 1):
        length = loop_points[index].distance_to(loop_points[index + 1])
        if length == 0:
            continue
        segment_lengths.append(length)
        total_length += length

    if total_length < 400:
        raise ValueError("The track is too short.")

    sample_count = max(MIN_TRACK_POINTS, min(int(total_length / TRACK_SPACING), 260))
    if sample_count < MIN_TRACK_POINTS:
        raise ValueError("The track needs more detail.")

    sampled_points = []
    traversed = 0.0
    segment_index = 0
    segment_start = loop_points[0]
    segment_end = loop_points[1]
    segment_length = max(segment_start.distance_to(segment_end), 1.0)

    for sample_index in range(sample_count):
        target_distance = (total_length * sample_index) / sample_count
        while traversed + segment_length < target_distance and segment_index < len(loop_points) - 2:
            traversed += segment_length
            segment_index += 1
            segment_start = loop_points[segment_index]
            segment_end = loop_points[segment_index + 1]
            segment_length = max(segment_start.distance_to(segment_end), 1.0)
        progress = (target_distance - traversed) / segment_length
        point = segment_start.lerp(segment_end, progress)
        sampled_points.append((point.x, point.y))

    return TrackLayout(
        centerline=tuple(sampled_points),
        track_width=max(MIN_TRACK_WIDTH, min(MAX_TRACK_WIDTH, int(track_width))),
    )


def _draw_path(surface: pygame.Surface, layout: TrackLayout, color: tuple[int, int, int], width: int) -> None:
    path_points = [(int(x), int(y)) for x, y in layout.centerline]
    pygame.draw.lines(surface, color, True, path_points, width)
    radius = max(2, width // 2)
    for x, y in layout.centerline:
        pygame.draw.circle(surface, color, (int(x), int(y)), radius)


def render_layout_surface(layout: TrackLayout) -> pygame.Surface:
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill(GRASS)
    _draw_path(surface, layout, ROAD_EDGE, layout.edge_width)
    _draw_path(surface, layout, ROAD, layout.track_width)

    dash_span = 4
    dash_stride = 7
    path_points = layout.centerline
    for index in range(0, len(path_points), dash_stride):
        dash_points = [
            (int(path_points[(index + offset) % len(path_points)][0]), int(path_points[(index + offset) % len(path_points)][1]))
            for offset in range(dash_span)
        ]
        pygame.draw.lines(surface, LINE, False, dash_points, 4)

    finish_line = layout.finish_line()
    pygame.draw.polygon(surface, FINISH, finish_line.polygon)
    pygame.draw.polygon(surface, TEXT, finish_line.polygon, 2)
    return surface


def render_layout_mask(layout: TrackLayout) -> pygame.mask.Mask:
    mask_surface = pygame.Surface((WIDTH, HEIGHT))
    mask_surface.fill((0, 0, 0))
    _draw_path(mask_surface, layout, (255, 255, 255), layout.track_width)
    return pygame.mask.from_threshold(mask_surface, (255, 255, 255), (1, 1, 1, 255))


def compile_track(layout: TrackLayout) -> CompiledTrack:
    return CompiledTrack(
        layout=layout,
        surface=render_layout_surface(layout),
        mask=render_layout_mask(layout),
        finish_line=layout.finish_line(),
        checkpoints=layout.checkpoints(),
        player_one_start=layout.start_pose(-15),
        player_two_start=layout.start_pose(15),
        ai_start=layout.start_pose(0),
    )


def save_layout(layout: TrackLayout) -> None:
    payload = {
        "track_width": layout.track_width,
        "centerline": [[round(x, 2), round(y, 2)] for x, y in layout.centerline],
    }
    TRACK_LAYOUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_layout() -> TrackLayout:
    if not TRACK_LAYOUT_PATH.exists():
        return create_default_layout()

    try:
        payload = json.loads(TRACK_LAYOUT_PATH.read_text(encoding="utf-8"))
        centerline = payload["centerline"]
        track_width = int(payload["track_width"])
        return build_layout_from_path(centerline, track_width)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return create_default_layout()


ACTIVE_TRACK = compile_track(load_layout())


def current_layout() -> TrackLayout:
    return ACTIVE_TRACK.layout


def reload_active_track() -> None:
    global ACTIVE_TRACK
    ACTIVE_TRACK = compile_track(load_layout())


def use_layout(layout: TrackLayout, persist: bool = False) -> None:
    global ACTIVE_TRACK
    ACTIVE_TRACK = compile_track(layout)
    if persist:
        save_layout(layout)


def use_default_track(persist: bool = False) -> None:
    use_layout(create_default_layout(), persist=persist)


def save_track_from_path(points: list[tuple[float, float]], track_width: int) -> TrackLayout:
    layout = build_layout_from_path(points, track_width)
    use_layout(layout, persist=True)
    return layout


def pickup_spawn_points(count: int = 8) -> list[tuple[float, float]]:
    layout = ACTIVE_TRACK.layout
    points = []
    step = len(layout.centerline) / count
    for order in range(count):
        index = int(round(layout.start_index + (step * order))) % len(layout.centerline)
        points.append(layout.centerline[index])
    return points


def build_track_mask() -> pygame.mask.Mask:
    return ACTIVE_TRACK.mask


def draw_track(surface: pygame.Surface) -> None:
    surface.blit(ACTIVE_TRACK.surface, (0, 0))


def create_player_cars() -> tuple[Car, Car]:
    player_one = Car(
        color=PLAYER_ONE,
        controls=PLAYER_ONE_CONTROLS,
        start_x=ACTIVE_TRACK.player_one_start[0],
        start_y=ACTIVE_TRACK.player_one_start[1],
        start_angle=ACTIVE_TRACK.player_one_start[2],
    )
    player_two = Car(
        color=PLAYER_TWO,
        controls=PLAYER_TWO_CONTROLS,
        start_x=ACTIVE_TRACK.player_two_start[0],
        start_y=ACTIVE_TRACK.player_two_start[1],
        start_angle=ACTIVE_TRACK.player_two_start[2],
    )
    return player_one, player_two


def create_ai_car(color: tuple[int, int, int] = AI_COLOR) -> Car:
    return Car(
        color=color,
        start_x=ACTIVE_TRACK.ai_start[0],
        start_y=ACTIVE_TRACK.ai_start[1],
        start_angle=ACTIVE_TRACK.ai_start[2],
    )


def create_race_state() -> dict[str, int | bool]:
    return {
        "laps": 0,
        "checkpoint_index": 0,
        "finish_armed": False,
        "in_finish": False,
        "crashed": False,
        "item": None,
    }


def reset_race_state(state: dict[str, int | bool]) -> None:
    state["laps"] = 0
    state["checkpoint_index"] = 0
    state["finish_armed"] = False
    state["in_finish"] = False
    state["crashed"] = False
    state["item"] = None


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


def advance_race_state(car: Car, state: dict[str, int | bool]) -> tuple[bool, bool]:
    checkpoint_index = int(state["checkpoint_index"])
    finish_armed = bool(state["finish_armed"])
    previous_in_finish = bool(state["in_finish"])
    car_point = (int(car.x), int(car.y))

    reached_checkpoint = False
    completed_lap = False

    if checkpoint_index < len(ACTIVE_TRACK.checkpoints) and ACTIVE_TRACK.checkpoints[checkpoint_index].contains(car_point):
        checkpoint_index += 1
        reached_checkpoint = True

    in_finish = ACTIVE_TRACK.finish_line.contains(car_point)
    if checkpoint_index == len(ACTIVE_TRACK.checkpoints):
        finish_armed = True

    if finish_armed and in_finish and not previous_in_finish:
        state["laps"] = int(state["laps"]) + 1
        checkpoint_index = 0
        finish_armed = False
        completed_lap = True

    state["checkpoint_index"] = checkpoint_index
    state["finish_armed"] = finish_armed
    state["in_finish"] = in_finish
    return reached_checkpoint, completed_lap


def next_checkpoint_center(state: dict[str, int | bool]) -> tuple[float, float]:
    checkpoint_index = int(state["checkpoint_index"])
    if checkpoint_index >= len(ACTIVE_TRACK.checkpoints):
        target = ACTIVE_TRACK.finish_line.center
    else:
        target = ACTIVE_TRACK.checkpoints[checkpoint_index].center
    return float(target[0]), float(target[1])
