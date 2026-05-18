from __future__ import annotations

import pygame

from game.app_result import AppResult, QUIT, RETURN_TO_MENU
from game.config import DEFAULT_TRACK_WIDTH, FPS, HEIGHT, MAX_TRACK_WIDTH, MIN_TRACK_WIDTH, WIDTH
from game.models import track as track_model
from game.rendering.track import render_layout_surface
from game.ui import theme


def run_track_editor() -> AppResult:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ML-WHEELS - Track Editor")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 28, bold=True)
    text_font = pygame.font.SysFont("arial", 20)

    path_points: list[tuple[float, float]] = []
    drawing = False
    track_width = track_model.current_layout().track_width
    preview_surface = track_model.ACTIVE_TRACK.surface
    status_message = "Hold left mouse button and draw a closed loop."

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return QUIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return RETURN_TO_MENU
                if event.key == pygame.K_RETURN:
                    try:
                        layout = track_model.save_track_from_path(path_points, track_width)
                    except ValueError as error:
                        status_message = str(error)
                    else:
                        preview_surface = render_layout_surface(layout)
                        path_points = []
                        status_message = "Track saved. Press Esc to return or draw a new layout."
                elif event.key in (pygame.K_LEFTBRACKET, pygame.K_MINUS, pygame.K_KP_MINUS):
                    track_width = max(MIN_TRACK_WIDTH, track_width - 5)
                elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    track_width = min(MAX_TRACK_WIDTH, track_width + 5)
                elif event.key == pygame.K_c:
                    path_points = []
                    status_message = "Canvas cleared."
                elif event.key == pygame.K_d:
                    track_model.use_default_track(persist=True)
                    preview_surface = track_model.ACTIVE_TRACK.surface
                    path_points = []
                    track_width = DEFAULT_TRACK_WIDTH
                    status_message = "Default track restored."
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                drawing = True
                path_points = [event.pos]
                status_message = "Drawing track centerline."
            elif event.type == pygame.MOUSEMOTION and drawing:
                point = (float(event.pos[0]), float(event.pos[1]))
                if not path_points or pygame.Vector2(point).distance_to(path_points[-1]) >= 6:
                    path_points.append(point)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drawing = False
                if len(path_points) >= 6:
                    status_message = "Preview ready. Press Enter to save."
                else:
                    status_message = "Add a longer loop before saving."

        preview_layout = None
        if len(path_points) >= 6:
            try:
                preview_layout = track_model.build_layout_from_path(path_points, track_width)
            except ValueError:
                preview_layout = None

        if preview_layout is not None:
            screen.blit(render_layout_surface(preview_layout), (0, 0))
        else:
            screen.blit(preview_surface, (0, 0))
            if len(path_points) >= 2:
                pygame.draw.lines(screen, theme.ACCENT, False, [(int(x), int(y)) for x, y in path_points], 4)
                for point in path_points:
                    pygame.draw.circle(screen, theme.TEXT, (int(point[0]), int(point[1])), 3)

        _draw_overlay(screen, title_font, text_font, track_width, status_message, len(path_points))
        pygame.display.flip()
        clock.tick(FPS)


def _draw_overlay(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    text_font: pygame.font.Font,
    track_width: int,
    status_message: str,
    point_count: int,
) -> None:
    panel = pygame.Rect(18, 18, 964, 118)
    pygame.draw.rect(screen, theme.BACKGROUND, panel, border_radius=8)
    pygame.draw.rect(screen, theme.BORDER, panel, 2, border_radius=8)

    title = title_font.render("Track Editor", True, theme.TEXT)
    screen.blit(title, (36, 32))

    details = [
        f"Width: {track_width}px   Points: {point_count}",
        "Draw with left mouse button. Enter: save   C: clear   D: default   [: narrower   ]: wider   Esc: menu",
        status_message,
    ]
    for index, line in enumerate(details):
        color = theme.WARNING if index == 2 else theme.TEXT_MUTED
        text = text_font.render(line, True, color)
        screen.blit(text, (36, 68 + index * 22))
