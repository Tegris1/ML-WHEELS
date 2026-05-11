import math
import pickle
from pathlib import Path

import pygame

from car import Car
from track import (
    AI_COLOR,
    FPS,
    GAME_OVER,
    HEIGHT,
    TEXT,
    WIDTH,
    advance_race_state,
    build_track_mask,
    car_hits_wall,
    create_ai_car,
    create_race_state,
    draw_track,
    next_checkpoint_center,
)


CONFIG_PATH = Path(__file__).with_name("neat_config.txt")
WINNER_PATH = Path(__file__).with_name("winner.pkl")
MAX_STEPS = 1800
TARGET_LAPS = 3


def require_neat():
    try:
        import neat
    except ImportError as error:
        raise SystemExit(
            "Missing dependency 'neat-python'. Install it with 'pip install neat-python'."
        ) from error
    return neat


def heading_to_target(car: Car, target_x: float, target_y: float) -> float:
    target_angle = math.degrees(math.atan2(target_y - car.y, target_x - car.x))
    delta = (target_angle - car.angle + 180) % 360 - 180
    return delta / 180.0


def distance_to_target(car: Car, target_x: float, target_y: float) -> float:
    distance = math.hypot(target_x - car.x, target_y - car.y)
    max_distance = math.hypot(WIDTH, HEIGHT)
    return min(distance / max_distance, 1.0)


def network_inputs(car: Car, race_state: dict[str, int | bool], track_mask: pygame.mask.Mask) -> list[float]:
    target_x, target_y = next_checkpoint_center(race_state)
    sensors = car.sensor_distances(track_mask, WIDTH, HEIGHT)
    return sensors + [
        car.speed / car.max_speed,
        heading_to_target(car, target_x, target_y),
        distance_to_target(car, target_x, target_y),
    ]


def run_training(generations: int = 50) -> None:
    neat = require_neat()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Training")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24, bold=True)
    track_mask = build_track_mask()

    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        CONFIG_PATH,
    )

    def eval_genomes(genomes, neat_config) -> None:
        nets = []
        cars = []
        genome_refs = []
        race_states = []

        for _, genome in genomes:
            genome.fitness = 0.0
            nets.append(neat.nn.FeedForwardNetwork.create(genome, neat_config))
            cars.append(create_ai_car())
            genome_refs.append(genome)
            race_states.append(create_race_state())

        steps = 0
        while cars and steps < MAX_STEPS:
            steps += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            for index in range(len(cars) - 1, -1, -1):
                car = cars[index]
                genome = genome_refs[index]
                race_state = race_states[index]

                outputs = nets[index].activate(network_inputs(car, race_state, track_mask))
                car.update_ai(outputs)
                genome.fitness += max(car.speed, 0) * 0.02

                if car_hits_wall(car, track_mask):
                    genome.fitness -= 2.0
                    cars.pop(index)
                    nets.pop(index)
                    genome_refs.pop(index)
                    race_states.pop(index)
                    continue

                reached_checkpoint, completed_lap = advance_race_state(car, race_state)
                if reached_checkpoint:
                    genome.fitness += 20.0
                if completed_lap:
                    genome.fitness += 100.0
                if car.speed < 0.15:
                    genome.fitness -= 0.03
                if int(race_state["laps"]) >= TARGET_LAPS:
                    genome.fitness += 250.0
                    cars.pop(index)
                    nets.pop(index)
                    genome_refs.pop(index)
                    race_states.pop(index)

            draw_track(screen)
            for car in cars:
                car.draw(screen)
            info = font.render(
                f"Training cars: {len(cars)}  Step: {steps}/{MAX_STEPS}",
                True,
                TEXT,
            )
            screen.blit(info, (20, 20))
            pygame.display.flip()
            clock.tick(FPS)

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())

    winner = population.run(eval_genomes, generations)
    WINNER_PATH.write_bytes(pickle.dumps(winner))
    pygame.quit()


def watch_winner() -> None:
    neat = require_neat()
    if not WINNER_PATH.exists():
        raise SystemExit("No saved genome found. Train first with 'python main.py train'.")

    winner = pickle.loads(WINNER_PATH.read_bytes())
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        CONFIG_PATH,
    )
    net = neat.nn.FeedForwardNetwork.create(winner, config)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Watch Mode")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28, bold=True)
    track_mask = build_track_mask()

    car = create_ai_car(AI_COLOR)
    race_state = create_race_state()
    crashed = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                car.reset()
                race_state = create_race_state()
                crashed = False

        if not crashed:
            outputs = net.activate(network_inputs(car, race_state, track_mask))
            car.update_ai(outputs)
            crashed = car_hits_wall(car, track_mask)
            if not crashed:
                advance_race_state(car, race_state)

        if crashed:
            message = font.render("Winner crashed. Press R to retry.", True, GAME_OVER)
        else:
            message = font.render(f"AI laps: {int(race_state['laps'])}", True, TEXT)

        draw_track(screen)
        car.draw(screen)
        car.draw_sensors(screen, track_mask, WIDTH, HEIGHT)
        screen.blit(message, (20, 20))
        pygame.display.flip()
        clock.tick(FPS)
