import pygame

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
