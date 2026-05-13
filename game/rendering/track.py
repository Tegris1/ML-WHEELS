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
            (
                int(path_points[(index + offset) % len(path_points)][0]),
                int(path_points[(index + offset) % len(path_points)][1]),
            )
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


def build_track_mask() -> pygame.mask.Mask:
    return track_model.ACTIVE_TRACK.mask


def draw_track(surface: pygame.Surface) -> None:
    surface.blit(track_model.ACTIVE_TRACK.surface, (0, 0))
