import math
import sys

import pygame


WIDTH, HEIGHT = 1000, 700
FPS = 60

GRASS = (34, 139, 34)
ROAD = (70, 70, 70)
ROAD_EDGE = (180, 180, 180)
LINE = (250, 250, 250)
FINISH = (255, 80, 80)
CAR_COLOR = (60, 170, 255)
TEXT = (255, 255, 255)
GAME_OVER = (255, 220, 220)

OUTER_RECT = pygame.Rect(100, 80, 800, 540)
INNER_RECT = pygame.Rect(280, 210, 440, 280)
FINISH_LINE = pygame.Rect((WIDTH // 2) - 8, 80, 16, 130)
CHECKPOINTS = [
    pygame.Rect(720, 210, 180, 280),  # right
    pygame.Rect(280, 490, 440, 130),  # bottom
    pygame.Rect(100, 210, 180, 280),  # left
    pygame.Rect(280, 80, 440, 130),   # top
]


class Car:
    def __init__(self) -> None:
        self.width = 22
        self.height = 38
        self.max_speed = 6.5
        self.acceleration = 0.18
        self.friction = 0.05
        self.turn_speed = 3.2
        self.reset()

    def reset(self) -> None:
        self.x = WIDTH // 2 + 70
        self.y = 145
        self.angle = -90
        self.speed = 0.0

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += self.acceleration
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= self.acceleration * 0.8

        if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s]):
            if self.speed > 0:
                self.speed = max(0, self.speed - self.friction)
            elif self.speed < 0:
                self.speed = min(0, self.speed + self.friction)

        self.speed = max(-self.max_speed / 2, min(self.max_speed, self.speed))

        if abs(self.speed) > 0.2:
            direction = 1 if self.speed >= 0 else -1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.angle -= self.turn_speed * direction
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.angle += self.turn_speed * direction

        radians = math.radians(self.angle)
        self.x += math.cos(radians) * self.speed
        self.y += math.sin(radians) * self.speed

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
        pygame.draw.polygon(surface, CAR_COLOR, self.corners())
        front = (
            self.x + math.cos(math.radians(self.angle)) * (self.height / 2 - 4),
            self.y + math.sin(math.radians(self.angle)) * (self.height / 2 - 4),
        )
        pygame.draw.circle(surface, LINE, (int(front[0]), int(front[1])), 4)


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


def car_hits_wall(car: Car, track_mask: pygame.mask.Mask) -> bool:
    for x, y in car.corners():
        px, py = int(x), int(y)
        if px < 0 or px >= WIDTH or py < 0 or py >= HEIGHT:
            return True
        if track_mask.get_at((px, py)) == 0:
            return True
    return False


def update_lap_state(
    car: Car,
    lap_count: int,
    checkpoint_index: int,
    finish_armed: bool,
    previous_in_finish: bool,
) -> tuple[int, int, bool, bool]:
    car_point = (int(car.x), int(car.y))

    if checkpoint_index < len(CHECKPOINTS) and CHECKPOINTS[checkpoint_index].collidepoint(car_point):
        checkpoint_index += 1

    in_finish = FINISH_LINE.collidepoint(car_point)
    if checkpoint_index == len(CHECKPOINTS):
        finish_armed = True

    if finish_armed and in_finish and not previous_in_finish:
        lap_count += 1
        checkpoint_index = 0
        finish_armed = False

    return lap_count, checkpoint_index, finish_armed, in_finish


def draw_ui(surface: pygame.Surface, font: pygame.font.Font, lap_count: int, crashed: bool) -> None:
    lap_text = font.render(f"Laps: {lap_count}", True, TEXT)
    hint_text = font.render("Drive: arrows or WASD", True, TEXT)
    surface.blit(lap_text, (20, 20))
    surface.blit(hint_text, (20, 55))

    if crashed:
        crash_font = pygame.font.SysFont("arial", 46, bold=True)
        message = crash_font.render("You lose! Press R to restart.", True, GAME_OVER)
        rect = message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        shadow = message.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 + 3))
        shadow_text = crash_font.render("You lose! Press R to restart.", True, (0, 0, 0))
        surface.blit(shadow_text, shadow)
        surface.blit(message, rect)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 30, bold=True)

    track_mask = build_track_mask()
    car = Car()

    lap_count = 0
    checkpoint_index = 0
    finish_armed = False
    previous_in_finish = True
    crashed = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and crashed:
                car.reset()
                lap_count = 0
                checkpoint_index = 0
                finish_armed = False
                previous_in_finish = True
                crashed = False

        keys = pygame.key.get_pressed()
        if not crashed:
            car.update(keys)
            crashed = car_hits_wall(car, track_mask)
            if not crashed:
                lap_count, checkpoint_index, finish_armed, previous_in_finish = update_lap_state(
                    car,
                    lap_count,
                    checkpoint_index,
                    finish_armed,
                    previous_in_finish,
                )

        draw_track(screen)
        car.draw(screen)
        draw_ui(screen, font, lap_count, crashed)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
