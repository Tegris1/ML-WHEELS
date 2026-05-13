from __future__ import annotations

import math
import pickle
from collections.abc import Sequence

import pygame

from game.config import AI_COLOR, FPS, GAME_OVER, HEIGHT, TEXT, WIDTH
from game.logic.race import RaceState, advance_race_state, car_hits_wall, next_checkpoint_center
from game.logic.sensors import read_car_sensors
from game.models.car import Car
from game.models.track import create_ai_car
from game.paths import NEAT_CONFIG_PATH, WINNER_PATH
from game.rendering.car import draw_car, draw_car_sensors
from game.rendering.track import build_track_mask, draw_track

MAX_STEPS = 300
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


def network_inputs(car: Car, race_state: RaceState, track_mask: pygame.mask.Mask) -> list[float]:
    target_x, target_y = next_checkpoint_center(race_state)
    sensors = [
        reading.normalized_distance
        for reading in read_car_sensors(car, track_mask, WIDTH, HEIGHT)
    ]
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

    neat_config = _load_neat_config(neat)

    def eval_genomes(genomes, config) -> None:
        nets = []
        cars = []
        genome_refs = []
        race_states = []

        for _, genome in genomes:
            genome.fitness = 0.0
            nets.append(neat.nn.FeedForwardNetwork.create(genome, config))
            cars.append(create_ai_car())
            genome_refs.append(genome)
            race_states.append(RaceState())

        _run_generation_loop(
            cars=cars,
            clock=clock,
            font=font,
            genome_refs=genome_refs,
            nets=nets,
            race_states=race_states,
            screen=screen,
            track_mask=track_mask,
        )

    population = neat.Population(neat_config)
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
    neat_config = _load_neat_config(neat)
    net = neat.nn.FeedForwardNetwork.create(winner, neat_config)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Watch Mode")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28, bold=True)
    track_mask = build_track_mask()

    car = create_ai_car()
    race_state = RaceState()
    crashed = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                car.reset()
                race_state = RaceState()
                crashed = False

        if not crashed:
            outputs = net.activate(network_inputs(car, race_state, track_mask))
            _apply_ai_outputs(car, outputs)
            crashed = car_hits_wall(car, track_mask)
            if not crashed:
                advance_race_state(car, race_state)

        draw_track(screen)
        draw_car(car, screen, AI_COLOR)
        draw_car_sensors(car, screen, track_mask)
        screen.blit(_watch_message(font, race_state, crashed), (20, 20))
        pygame.display.flip()
        clock.tick(FPS)


def _load_neat_config(neat):
    return neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        NEAT_CONFIG_PATH,
    )


def _run_generation_loop(
    cars: list[Car],
    clock: pygame.time.Clock,
    font: pygame.font.Font,
    genome_refs: list,
    nets: list,
    race_states: list[RaceState],
    screen: pygame.Surface,
    track_mask: pygame.mask.Mask,
) -> None:
    steps = 0
    while cars and steps < MAX_STEPS:
        steps += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        for index in range(len(cars) - 1, -1, -1):
            _update_ai_driver(index, cars, genome_refs, nets, race_states, track_mask)

        draw_track(screen)
        for car in cars:
            draw_car(car, screen, AI_COLOR)
        screen.blit(_training_message(font, len(cars), steps), (20, 20))
        pygame.display.flip()
        clock.tick(FPS)


def _update_ai_driver(
    index: int,
    cars: list[Car],
    genome_refs: list,
    nets: list,
    race_states: list[RaceState],
    track_mask: pygame.mask.Mask,
) -> None:
    car = cars[index]
    genome = genome_refs[index]
    race_state = race_states[index]

    outputs = nets[index].activate(network_inputs(car, race_state, track_mask))
    _apply_ai_outputs(car, outputs)
    genome.fitness += max(car.speed, 0) * 0.02

    if car_hits_wall(car, track_mask):
        genome.fitness -= 2.0
        _remove_ai_driver(index, cars, genome_refs, nets, race_states)
        return

    reached_checkpoint, completed_lap = advance_race_state(car, race_state)
    if reached_checkpoint:
        genome.fitness += 20.0
    if completed_lap:
        genome.fitness += 100.0
    if car.speed < 0.15:
        genome.fitness -= 0.03
    if race_state.laps >= TARGET_LAPS:
        genome.fitness += 250.0
        _remove_ai_driver(index, cars, genome_refs, nets, race_states)


def _apply_ai_outputs(car: Car, outputs: Sequence[float]) -> None:
    car.move(
        forward=outputs[0] > 0.5,
        backward=outputs[1] > 0.5,
        left=outputs[2] > 0.5,
        right=outputs[3] > 0.5,
    )


def _remove_ai_driver(
    index: int,
    cars: list[Car],
    genome_refs: list,
    nets: list,
    race_states: list[RaceState],
) -> None:
    cars.pop(index)
    genome_refs.pop(index)
    nets.pop(index)
    race_states.pop(index)


def _training_message(font: pygame.font.Font, car_count: int, steps: int) -> pygame.Surface:
    return font.render(f"Training cars: {car_count}  Step: {steps}/{MAX_STEPS}", True, TEXT)


def _watch_message(font: pygame.font.Font, race_state: RaceState, crashed: bool) -> pygame.Surface:
    if crashed:
        return font.render("Winner crashed. Press R to retry.", True, GAME_OVER)
    return font.render(f"AI laps: {race_state.laps}", True, TEXT)
