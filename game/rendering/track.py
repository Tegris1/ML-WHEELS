import pygame

from game.config import (
    FINISH,
    FINISH_LINE,
    GRASS,
    HEIGHT,
    INNER_RECT,
    LINE,
    OUTER_RECT,
    ROAD,
    ROAD_EDGE,
    WIDTH,
)


def build_track_mask() -> pygame.mask.Mask:
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill((0, 0, 0))
    pygame.draw.rect(surface, (255, 255, 255), OUTER_RECT, border_radius=36)
    pygame.draw.rect(surface, (0, 0, 0), INNER_RECT, border_radius=20)
    return pygame.mask.from_threshold(surface, (255, 255, 255), (1, 1, 1, 255))


def draw_track(surface: pygame.Surface) -> None:
    surface.fill(GRASS)
    pygame.draw.rect(surface, ROAD, OUTER_RECT, border_radius=36)
    pygame.draw.rect(surface, GRASS, INNER_RECT, border_radius=20)
    pygame.draw.rect(surface, ROAD_EDGE, OUTER_RECT, 5, border_radius=36)
    pygame.draw.rect(surface, ROAD_EDGE, INNER_RECT, 5, border_radius=20)
    pygame.draw.rect(surface, FINISH, FINISH_LINE)
    _draw_center_lines(surface)


def _draw_center_lines(surface: pygame.Surface) -> None:
    dash_length = 26
    gap = 16

    for x in range(INNER_RECT.left + 40, INNER_RECT.right - 40, dash_length + gap):
        pygame.draw.line(surface, LINE, (x, 145), (x + dash_length, 145), 4)
        pygame.draw.line(surface, LINE, (x, 555), (x + dash_length, 555), 4)

    for y in range(INNER_RECT.top + 40, INNER_RECT.bottom - 40, dash_length + gap):
        pygame.draw.line(surface, LINE, (145, y), (145, y + dash_length), 4)
        pygame.draw.line(surface, LINE, (855, y), (855, y + dash_length), 4)
