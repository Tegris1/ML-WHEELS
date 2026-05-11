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

OUTER_RECT = pygame.Rect(100, 80, 800, 540)
INNER_RECT = pygame.Rect(280, 210, 440, 280)
FINISH_LINE = pygame.Rect((WIDTH // 2) - 8, 80, 16, 130)
CHECKPOINTS = [
    pygame.Rect(720, 210, 180, 280),
    pygame.Rect(280, 490, 440, 130),
    pygame.Rect(100, 210, 180, 280),
    pygame.Rect(280, 80, 440, 130),
]

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

    dash_length = 26
    gap = 16
    for x in range(INNER_RECT.left + 40, INNER_RECT.right - 40, dash_length + gap):
        pygame.draw.line(surface, LINE, (x, 145), (x + dash_length, 145), 4)
        pygame.draw.line(surface, LINE, (x, 555), (x + dash_length, 555), 4)
    for y in range(INNER_RECT.top + 40, INNER_RECT.bottom - 40, dash_length + gap):
        pygame.draw.line(surface, LINE, (145, y), (145, y + dash_length), 4)
        pygame.draw.line(surface, LINE, (855, y), (855, y + dash_length), 4)


def create_player_cars() -> tuple[Car, Car]:
    player_one = Car(
        color=PLAYER_ONE,
        controls=PLAYER_ONE_CONTROLS,
        start_x=WIDTH // 2 + 45,
        start_y=145,
    )
    player_two = Car(
        color=PLAYER_TWO,
        controls=PLAYER_TWO_CONTROLS,
        start_x=WIDTH // 2 + 95,
        start_y=145,
    )
    return player_one, player_two


def create_ai_car(color: tuple[int, int, int] = AI_COLOR) -> Car:
    return Car(
        color=color,
        start_x=WIDTH // 2 + 70,
        start_y=145,
    )


def create_race_state() -> dict[str, int | bool]:
    return {
        "laps": 0,
        "checkpoint_index": 0,
        "finish_armed": False,
        "in_finish": True,
        "crashed": False,
    }


def reset_race_state(state: dict[str, int | bool]) -> None:
    state["laps"] = 0
    state["checkpoint_index"] = 0
    state["finish_armed"] = False
    state["in_finish"] = True
    state["crashed"] = False


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

    if checkpoint_index < len(CHECKPOINTS) and CHECKPOINTS[checkpoint_index].collidepoint(car_point):
        checkpoint_index += 1
        reached_checkpoint = True

    in_finish = FINISH_LINE.collidepoint(car_point)
    if checkpoint_index == len(CHECKPOINTS):
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
    if checkpoint_index >= len(CHECKPOINTS):
        target = FINISH_LINE
    else:
        target = CHECKPOINTS[checkpoint_index]
    return float(target.centerx), float(target.centery)
