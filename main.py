from __future__ import annotations

from dataclasses import dataclass
import sys

import pygame

from ai_train import WINNER_PATH, run_training, watch_winner
from effects import ExplosionEffect
from pickups import ITEM_LABELS, PickupManager
from track import (
    FPS,
    GAME_OVER,
    GRASS,
    HEIGHT,
    ROAD,
    ROAD_EDGE,
    TEXT,
    WIDTH,
    advance_race_state,
    build_layout_from_path,
    build_track_mask,
    car_hits_wall,
    cars_collide,
    create_default_layout,
    create_player_cars,
    create_race_state,
    current_layout,
    draw_track,
    pickup_spawn_points,
    render_layout_surface,
    reset_race_state,
    save_track_from_path,
)


BACKGROUND = (18, 24, 32)
PANEL = (36, 47, 61)
PANEL_ALT = (47, 62, 80)
BUTTON = (72, 97, 124)
BUTTON_HOVER = (92, 124, 157)
BUTTON_ACTIVE = (60, 170, 255)
BUTTON_WARN = (170, 78, 78)
BORDER = (130, 150, 173)


@dataclass(frozen=True)
class Button:
    label: str
    rect: pygame.Rect


def draw_button(
    surface: pygame.Surface,
    font: pygame.font.Font,
    button: Button,
    mouse_pos: tuple[int, int],
    active: bool = False,
    warn: bool = False,
) -> None:
    color = BUTTON_WARN if warn else BUTTON_ACTIVE if active else BUTTON_HOVER if button.rect.collidepoint(mouse_pos) else BUTTON
    pygame.draw.rect(surface, color, button.rect, border_radius=8)
    pygame.draw.rect(surface, BORDER, button.rect, 2, border_radius=8)
    text = font.render(button.label, True, TEXT)
    surface.blit(text, text.get_rect(center=button.rect.center))


def draw_ui(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_one_state: dict[str, int | bool],
    player_two_state: dict[str, int | bool],
) -> None:
    player_one_text = font.render(f"Blue laps: {int(player_one_state['laps'])}", True, TEXT)
    player_two_text = font.render(f"Gold laps: {int(player_two_state['laps'])}", True, TEXT)

    player_one_item = ITEM_LABELS.get(player_one_state.get("item"), "None")
    player_two_item = ITEM_LABELS.get(player_two_state.get("item"), "None")
    player_one_item_text = font.render(f"Blue item: {player_one_item}", True, TEXT)
    player_two_item_text = font.render(f"Gold item: {player_two_item}", True, TEXT)

    surface.blit(player_one_text, (20, 20))
    surface.blit(player_two_text, (20, 55))
    surface.blit(player_one_item_text, (20, 90))
    surface.blit(player_two_item_text, (20, 125))

    messages = []
    if bool(player_one_state["crashed"]):
        messages.append("Blue car lost")
    if bool(player_two_state["crashed"]):
        messages.append("Gold car lost")

    if messages:
        crash_font = pygame.font.SysFont("arial", 42, bold=True)
        text = " | ".join(messages) + " - Press R to restart."
        message = crash_font.render(text, True, GAME_OVER)
        rect = message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        shadow = message.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 + 3))
        shadow_text = crash_font.render(text, True, (0, 0, 0))
        surface.blit(shadow_text, shadow)
        surface.blit(message, rect)


def run_human_game() -> bool:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ML Wheels - Play")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 30, bold=True)

    track_mask = build_track_mask()
    player_one, player_two = create_player_cars()
    player_one_state = create_race_state()
    player_two_state = create_race_state()
    player_one_explosion = ExplosionEffect()
    player_two_explosion = ExplosionEffect()
    pickup_manager = PickupManager(pickup_spawn_points())

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                return True
            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
                and (bool(player_one_state["crashed"]) or bool(player_two_state["crashed"]))
            ):
                player_one.reset()
                player_two.reset()
                reset_race_state(player_one_state)
                reset_race_state(player_two_state)
                player_one_explosion = ExplosionEffect()
                player_two_explosion = ExplosionEffect()
                pickup_manager.reset()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f and not bool(player_one_state["crashed"]):
                pickup_manager.use_item("player_one", player_one, player_one_state, [("player_two", player_two, player_two_state)])
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RCTRL and not bool(player_two_state["crashed"]):
                pickup_manager.use_item("player_two", player_two, player_two_state, [("player_one", player_one, player_one_state)])

        keys = pygame.key.get_pressed()
        if not bool(player_one_state["crashed"]):
            player_one.update_manual(keys)
            if car_hits_wall(player_one, track_mask):
                player_one_state["crashed"] = True
                player_one_explosion.trigger((player_one.x, player_one.y), player_one.color)
            else:
                advance_race_state(player_one, player_one_state)

        if not bool(player_two_state["crashed"]):
            player_two.update_manual(keys)
            if car_hits_wall(player_two, track_mask):
                player_two_state["crashed"] = True
                player_two_explosion.trigger((player_two.x, player_two.y), player_two.color)
            else:
                advance_race_state(player_two, player_two_state)

        if (
            not bool(player_one_state["crashed"])
            and not bool(player_two_state["crashed"])
            and cars_collide(player_one, player_two)
        ):
            player_one_state["crashed"] = True
            player_two_state["crashed"] = True

        pickup_manager.update(
            [
                ("player_one", player_one, player_one_state),
                ("player_two", player_two, player_two_state),
            ]
        )
        player_one_explosion.update()
        player_two_explosion.update()

        draw_track(screen)
        pickup_manager.draw(screen)
        player_one.draw(screen)
        player_two.draw(screen)
        player_one_explosion.draw(screen)
        player_two_explosion.draw(screen)
        draw_ui(screen, font, player_one_state, player_two_state)
        pygame.display.flip()
        clock.tick(FPS)


def load_editor_points() -> tuple[list[tuple[float, float]], int]:
    layout = current_layout()
    return list(layout.centerline), layout.track_width


def run_track_editor() -> bool:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ML Wheels - Track Editor")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 28, bold=True)
    font = pygame.font.SysFont("arial", 22, bold=True)
    small_font = pygame.font.SysFont("arial", 18, bold=True)

    points, track_width = load_editor_points()
    status = "Draw a loop, then save."
    tool_mode = "draw"
    drawing = False
    erasing = False

    toolbar = pygame.Rect(0, 0, WIDTH, 86)
    buttons = {
        "draw": Button("Draw", pygame.Rect(18, 18, 92, 38)),
        "erase": Button("Erase", pygame.Rect(120, 18, 92, 38)),
        "clear": Button("Clear", pygame.Rect(222, 18, 92, 38)),
        "save": Button("Save", pygame.Rect(324, 18, 92, 38)),
        "reload": Button("Reload", pygame.Rect(426, 18, 102, 38)),
        "default": Button("Default", pygame.Rect(538, 18, 108, 38)),
        "minus": Button("-", pygame.Rect(714, 18, 38, 38)),
        "plus": Button("+", pygame.Rect(870, 18, 38, 38)),
        "back": Button("Back", pygame.Rect(918, 18, 64, 38)),
    }
    canvas_rect = pygame.Rect(0, toolbar.bottom, WIDTH, HEIGHT - toolbar.height)

    def add_point(point: tuple[int, int]) -> None:
        if not canvas_rect.collidepoint(point):
            return
        if not points or pygame.Vector2(point).distance_to(points[-1]) >= 6:
            points.append((float(point[0]), float(point[1])))

    def erase_at(point: tuple[int, int]) -> None:
        nonlocal points
        if not canvas_rect.collidepoint(point):
            return
        radius = max(20, track_width // 3)
        center = pygame.Vector2(point)
        points = [candidate for candidate in points if center.distance_to(candidate) > radius]

    while True:
        preview_surface = None
        preview_error = ""
        if len(points) >= 6:
            try:
                preview_layout = build_layout_from_path(points, track_width)
                preview_surface = render_layout_surface(preview_layout)
            except ValueError as error:
                preview_error = str(error)

        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked_button = next((name for name, button in buttons.items() if button.rect.collidepoint(event.pos)), None)
                    if clicked_button == "draw":
                        tool_mode = "draw"
                        status = "Draw mode."
                    elif clicked_button == "erase":
                        tool_mode = "erase"
                        status = "Erase mode."
                    elif clicked_button == "clear":
                        points = []
                        status = "Canvas cleared."
                    elif clicked_button == "save":
                        try:
                            save_track_from_path(points, track_width)
                            points, track_width = load_editor_points()
                            status = "Track saved."
                        except ValueError as error:
                            status = str(error)
                    elif clicked_button == "reload":
                        points, track_width = load_editor_points()
                        status = "Loaded current saved track."
                    elif clicked_button == "default":
                        default_layout = create_default_layout()
                        points = list(default_layout.centerline)
                        track_width = default_layout.track_width
                        status = "Default track loaded into editor."
                    elif clicked_button == "minus":
                        track_width = max(50, track_width - 4)
                        status = f"Track width: {track_width}"
                    elif clicked_button == "plus":
                        track_width = min(140, track_width + 4)
                        status = f"Track width: {track_width}"
                    elif clicked_button == "back":
                        pygame.quit()
                        return True
                    elif canvas_rect.collidepoint(event.pos):
                        if tool_mode == "draw":
                            drawing = True
                            add_point(event.pos)
                        else:
                            erasing = True
                            erase_at(event.pos)
                elif event.button == 3:
                    erasing = True
                    erase_at(event.pos)
                elif event.button == 4:
                    track_width = min(140, track_width + 2)
                elif event.button == 5:
                    track_width = max(50, track_width - 2)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    drawing = False
                    if tool_mode == "erase":
                        erasing = False
                if event.button == 3:
                    erasing = False
            if event.type == pygame.MOUSEMOTION:
                if drawing:
                    add_point(event.pos)
                if erasing:
                    erase_at(event.pos)

        if preview_surface is not None:
            screen.blit(preview_surface, (0, 0))
        else:
            screen.fill(GRASS)
            if len(points) >= 2:
                pygame.draw.lines(screen, ROAD_EDGE, False, [(int(x), int(y)) for x, y in points], track_width + 12)
                pygame.draw.lines(screen, ROAD, False, [(int(x), int(y)) for x, y in points], track_width)
            for point in points:
                pygame.draw.circle(screen, ROAD, (int(point[0]), int(point[1])), max(4, track_width // 2))

        pygame.draw.rect(screen, PANEL, toolbar)
        pygame.draw.line(screen, BORDER, (0, toolbar.bottom), (WIDTH, toolbar.bottom), 2)
        draw_button(screen, font, buttons["draw"], mouse_pos, active=tool_mode == "draw")
        draw_button(screen, font, buttons["erase"], mouse_pos, active=tool_mode == "erase")
        draw_button(screen, font, buttons["clear"], mouse_pos, warn=True)
        draw_button(screen, font, buttons["save"], mouse_pos)
        draw_button(screen, font, buttons["reload"], mouse_pos)
        draw_button(screen, font, buttons["default"], mouse_pos)
        draw_button(screen, font, buttons["minus"], mouse_pos)
        draw_button(screen, font, buttons["plus"], mouse_pos)
        draw_button(screen, font, buttons["back"], mouse_pos)

        title = title_font.render("Track Editor", True, TEXT)
        screen.blit(title, (18, 58))
        info = small_font.render("Left drag: draw  Right drag: erase  Mouse wheel: width", True, TEXT)
        screen.blit(info, (212, 60))
        width_text = font.render(f"Width {track_width}", True, TEXT)
        screen.blit(width_text, (764, 26))

        status_text = preview_error if preview_error else status
        status_surface = small_font.render(status_text, True, TEXT)
        status_rect = status_surface.get_rect(midbottom=(WIDTH // 2, HEIGHT - 12))
        pygame.draw.rect(screen, PANEL_ALT, status_rect.inflate(20, 12), border_radius=8)
        screen.blit(status_surface, status_rect)

        pygame.display.flip()
        clock.tick(FPS)


def run_main_menu() -> None:
    generations = 50
    notice = "Choose a mode."

    while True:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("ML Wheels")
        clock = pygame.time.Clock()
        title_font = pygame.font.SysFont("arial", 54, bold=True)
        font = pygame.font.SysFont("arial", 28, bold=True)
        small_font = pygame.font.SysFont("arial", 20, bold=True)

        buttons = {
            "play": Button("Play", pygame.Rect(110, 180, 230, 68)),
            "watch": Button("Watch AI", pygame.Rect(110, 270, 230, 68)),
            "train": Button("Train AI", pygame.Rect(110, 360, 230, 68)),
            "editor": Button("Track Editor", pygame.Rect(110, 450, 230, 68)),
            "quit": Button("Quit", pygame.Rect(110, 540, 230, 68)),
            "minus": Button("-", pygame.Rect(470, 378, 44, 44)),
            "plus": Button("+", pygame.Rect(680, 378, 44, 44)),
        }

        chosen_mode: str | None = None
        while chosen_mode is None:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = next((name for name, button in buttons.items() if button.rect.collidepoint(event.pos)), None)
                    if clicked == "minus":
                        generations = max(5, generations - 5)
                    elif clicked == "plus":
                        generations = min(300, generations + 5)
                    elif clicked == "watch" and not WINNER_PATH.exists():
                        notice = "No trained winner found. Train first."
                    elif clicked is not None:
                        chosen_mode = clicked

            screen.fill(BACKGROUND)
            panel_rect = pygame.Rect(70, 110, 860, 540)
            pygame.draw.rect(screen, PANEL, panel_rect, border_radius=10)
            pygame.draw.rect(screen, BORDER, panel_rect, 2, border_radius=10)

            title = title_font.render("ML Wheels", True, TEXT)
            subtitle = font.render("Race, train, watch, or build a custom track.", True, TEXT)
            screen.blit(title, (110, 128))
            screen.blit(subtitle, (110, 188 - 38))

            for name, button in buttons.items():
                if name == "quit":
                    draw_button(screen, font, button, mouse_pos, warn=True)
                elif name in {"minus", "plus"}:
                    draw_button(screen, font, button, mouse_pos)
                else:
                    draw_button(screen, font, button, mouse_pos)

            side_title = font.render("Training", True, TEXT)
            side_text = small_font.render("Generations", True, TEXT)
            value_text = font.render(str(generations), True, TEXT)
            helper = small_font.render("Training saves a new winner when it completes.", True, TEXT)
            track_info = small_font.render("The current saved track is used by play, watch, and train.", True, TEXT)
            screen.blit(side_title, (470, 220))
            screen.blit(side_text, (470, 330))
            screen.blit(value_text, value_text.get_rect(center=(597, 400)))
            screen.blit(helper, (470, 450))
            screen.blit(track_info, (470, 482))

            active_track = current_layout()
            preview = render_layout_surface(active_track)
            preview_rect = pygame.Rect(470, 220, 390, 180)
            preview_scaled = pygame.transform.smoothscale(preview, preview_rect.size)
            screen.blit(preview_scaled, preview_rect)
            pygame.draw.rect(screen, BORDER, preview_rect, 2, border_radius=8)

            notice_surface = small_font.render(notice, True, TEXT)
            screen.blit(notice_surface, (470, 535))

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        if chosen_mode == "play":
            if not run_human_game():
                return
            notice = "Returned from play mode."
        elif chosen_mode == "watch":
            if not WINNER_PATH.exists():
                notice = "No trained winner found. Train first."
                continue
            try:
                if not watch_winner():
                    return
            except SystemExit as error:
                notice = str(error)
                continue
            notice = "Returned from watch mode."
        elif chosen_mode == "train":
            if not run_training(generations):
                return
            notice = f"Training finished for {generations} generations."
        elif chosen_mode == "editor":
            if not run_track_editor():
                return
            notice = "Returned from track editor."
        elif chosen_mode == "quit":
            return


def main() -> None:
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "menu"
    if mode == "menu":
        run_main_menu()
        return
    if mode == "play":
        run_human_game()
        return
    if mode == "train":
        generations = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        run_training(generations)
        return
    if mode == "watch":
        if not WINNER_PATH.exists():
            raise SystemExit("No saved genome found. Train first with 'python main.py train'.")
        watch_winner()
        return
    if mode == "editor":
        run_track_editor()
        return
    raise SystemExit("Usage: python main.py [menu|play|train|watch|editor] [generations]")


if __name__ == "__main__":
    main()
