import random

import pygame

from game.config import FINISH, GRASS, HEIGHT, LINE, ROAD, ROAD_EDGE, TEXT, WIDTH
from game.models import track as track_model
from game.models.track import TrackLayout


def _draw_path(
    surface: pygame.Surface,
    layout: TrackLayout,
    color: tuple[int, int, int],
    width: int,
) -> None:
    path_points = track_model.layout_path_points(layout)
    pygame.draw.lines(surface, color, True, path_points, width)
    radius = max(2, width // 2)
    for x, y in path_points:
        pygame.draw.circle(surface, color, (x, y), radius)


def _layout_seed(layout: TrackLayout) -> int:
    seed = (layout.track_width * 1_009) ^ len(layout.centerline)
    step = max(1, len(layout.centerline) // 28)
    for index, (x, y) in enumerate(layout.centerline[::step]):
        seed = (seed * 1_664_525 + int(x * 10) * 101 + int(y * 10) * 313 + index) & 0xFFFFFFFF
    return seed


def _draw_grass(surface: pygame.Surface, rng: random.Random) -> None:
    surface.fill(GRASS)
    for _ in range(260):
        x = rng.randrange(0, WIDTH)
        y = rng.randrange(0, HEIGHT)
        length = rng.randrange(4, 12)
        color = rng.choice(((28, 111, 42), (42, 142, 55), (54, 124, 48), (75, 148, 64)))
        pygame.draw.line(surface, color, (x, y), (x + rng.randrange(-2, 3), y - length), 1)

    for _ in range(34):
        x = rng.randrange(-40, WIDTH + 40)
        y = rng.randrange(-40, HEIGHT + 40)
        width = rng.randrange(80, 190)
        height = rng.randrange(34, 90)
        color = rng.choice(((28, 116, 45), (39, 129, 47), (47, 118, 49)))
        pygame.draw.ellipse(surface, color, pygame.Rect(x, y, width, height))


def _track_guard_mask(layout: TrackLayout) -> pygame.mask.Mask:
    mask_surface = pygame.Surface((WIDTH, HEIGHT))
    mask_surface.fill((0, 0, 0))
    _draw_path(mask_surface, layout, (255, 255, 255), layout.track_width + 100)
    return pygame.mask.from_threshold(mask_surface, (255, 255, 255), (1, 1, 1, 255))


def _draw_bush(surface: pygame.Surface, rng: random.Random, x: int, y: int, size: int) -> None:
    pygame.draw.ellipse(
        surface,
        (15, 50, 25),
        pygame.Rect(x - size, y + size // 3, size * 2, max(4, size // 2)),
    )
    palette = ((26, 92, 38), (33, 122, 47), (53, 145, 60), (77, 158, 70))
    for _ in range(7):
        offset_x = rng.randrange(-size, size + 1)
        offset_y = rng.randrange(-size // 2, size // 2 + 1)
        radius = rng.randrange(max(3, size // 4), max(4, size // 2))
        pygame.draw.circle(surface, rng.choice(palette), (x + offset_x, y + offset_y), radius)
    pygame.draw.circle(surface, (102, 171, 76), (x - size // 4, y - size // 3), max(2, size // 5))


def _draw_rock(surface: pygame.Surface, rng: random.Random, x: int, y: int, size: int) -> None:
    rect = pygame.Rect(x - size, y - size // 2, size * 2, size)
    pygame.draw.ellipse(surface, (18, 42, 34), rect.move(2, 4))
    pygame.draw.ellipse(surface, rng.choice(((91, 97, 89), (108, 111, 101), (78, 86, 79))), rect)
    pygame.draw.arc(surface, (145, 149, 132), rect.inflate(-4, -4), 3.6, 5.8, 1)


def _draw_flower_patch(surface: pygame.Surface, rng: random.Random, x: int, y: int, size: int) -> None:
    for _ in range(6):
        flower_x = x + rng.randrange(-size, size + 1)
        flower_y = y + rng.randrange(-size, size + 1)
        pygame.draw.line(surface, (35, 105, 43), (flower_x, flower_y), (flower_x, flower_y + 5), 1)
        pygame.draw.circle(surface, rng.choice(((245, 211, 86), (232, 134, 79), (232, 220, 143))), (flower_x, flower_y), 2)


def _draw_scenery(surface: pygame.Surface, layout: TrackLayout, rng: random.Random) -> None:
    guard_mask = _track_guard_mask(layout)
    placed: list[tuple[int, int, int]] = []
    attempts = 0
    while len(placed) < 120 and attempts < 1_200:
        attempts += 1
        x = rng.randrange(18, WIDTH - 18)
        y = rng.randrange(18, HEIGHT - 18)
        if guard_mask.get_at((x, y)):
            continue
        size = rng.randrange(7, 18)
        if any((x - other_x) ** 2 + (y - other_y) ** 2 < (size + other_size + 8) ** 2 for other_x, other_y, other_size in placed):
            continue

        roll = rng.random()
        if roll < 0.62:
            _draw_bush(surface, rng, x, y, size)
        elif roll < 0.82:
            _draw_rock(surface, rng, x, y, size)
        else:
            _draw_flower_patch(surface, rng, x, y, size)
        placed.append((x, y, size))


def _draw_road_texture(surface: pygame.Surface, layout: TrackLayout, rng: random.Random) -> None:
    half_width = layout.track_width / 2
    for index in range(0, len(layout.centerline), 5):
        center = layout.point_at(index)
        normal = layout.normal_at(index)
        offset = rng.uniform(-half_width + 12, half_width - 12)
        point = center + normal * offset
        pygame.draw.circle(surface, rng.choice(((66, 67, 63), (78, 78, 73), (52, 54, 52))), (int(point.x), int(point.y)), 1)


def _lerp_point(
    start: tuple[float, float],
    end: tuple[float, float],
    ratio: float,
) -> tuple[float, float]:
    return (
        start[0] + (end[0] - start[0]) * ratio,
        start[1] + (end[1] - start[1]) * ratio,
    )


def _draw_finish_line(surface: pygame.Surface, layout: TrackLayout) -> None:
    finish_line = layout.finish_line()
    polygon = finish_line.polygon
    columns = 8
    rows = 2
    for column in range(columns):
        x0 = column / columns
        x1 = (column + 1) / columns
        start_left = _lerp_point(polygon[0], polygon[1], x0)
        start_right = _lerp_point(polygon[0], polygon[1], x1)
        end_left = _lerp_point(polygon[3], polygon[2], x0)
        end_right = _lerp_point(polygon[3], polygon[2], x1)
        for row in range(rows):
            y0 = row / rows
            y1 = (row + 1) / rows
            tile = (
                _lerp_point(start_left, end_left, y0),
                _lerp_point(start_right, end_right, y0),
                _lerp_point(start_right, end_right, y1),
                _lerp_point(start_left, end_left, y1),
            )
            color = TEXT if (column + row) % 2 == 0 else (18, 18, 18)
            pygame.draw.polygon(surface, color, tile)
    pygame.draw.polygon(surface, FINISH, finish_line.polygon, 2)


def render_layout_surface(layout: TrackLayout) -> pygame.Surface:
    surface = pygame.Surface((WIDTH, HEIGHT))
    rng = random.Random(_layout_seed(layout))
    _draw_grass(surface, rng)
    _draw_scenery(surface, layout, rng)
    _draw_path(surface, layout, (24, 55, 43), layout.edge_width + 18)
    _draw_path(surface, layout, ROAD_EDGE, layout.edge_width)
    _draw_path(surface, layout, (48, 50, 49), layout.track_width + 4)
    _draw_path(surface, layout, ROAD, layout.track_width)
    _draw_road_texture(surface, layout, rng)

    dash_span = 4
    dash_stride = 7
    path_points = layout.centerline
    for index in range(0, len(path_points), dash_stride):
        dash_points = [
            (
                int(path_points[(index + offset) % len(path_points)][0]),
                int(path_points[(index + offset) % len(path_points)][1]),
            )
            for offset in range(dash_span)
        ]
        pygame.draw.lines(surface, (28, 28, 27), False, dash_points, 6)
        pygame.draw.lines(surface, LINE, False, dash_points, 4)

    _draw_finish_line(surface, layout)
    return surface


def render_layout_mask(layout: TrackLayout) -> pygame.mask.Mask:
    mask_surface = pygame.Surface((WIDTH, HEIGHT))
    mask_surface.fill((0, 0, 0))
    _draw_path(mask_surface, layout, (255, 255, 255), layout.track_width)
    return pygame.mask.from_threshold(mask_surface, (255, 255, 255), (1, 1, 1, 255))


def build_track_mask() -> pygame.mask.Mask:
    return track_model.ACTIVE_TRACK.mask


def draw_track(surface: pygame.Surface) -> None:
    surface.blit(track_model.ACTIVE_TRACK.surface, (0, 0))
