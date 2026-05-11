import math
import pickle
from pathlib import Path

import pygame

from car import Car
from effects import ExplosionEffect
from pickups import ITEM_CODE, ITEM_LABELS, PickupManager, nearest_opponent_info, nearest_pickup_info
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
    pickup_spawn_points,
)


CONFIG_PATH = Path(__file__).with_name("neat_config.txt")
WINNER_PATH = Path(__file__).with_name("winner.pkl")
MAX_STEPS = 400
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


def network_inputs(
    car: Car,
    race_state: dict[str, int | bool | str | None],
    track_mask: pygame.mask.Mask,
    pickup_manager: PickupManager,
    opponents: list[tuple[str, Car, dict[str, int | bool | str | None]]],
) -> list[float]:
    target_x, target_y = next_checkpoint_center(race_state)
    sensors = car.sensor_distances(track_mask, WIDTH, HEIGHT)
    pickup_heading, pickup_distance = nearest_pickup_info(car, pickup_manager)
    opponent_heading, opponent_distance = nearest_opponent_info(car, opponents)
    current_item = race_state.get("item")
    return sensors + [
        car.speed / car.max_speed,
        heading_to_target(car, target_x, target_y),
        distance_to_target(car, target_x, target_y),
        pickup_heading,
        pickup_distance,
        1.0 if current_item is not None else 0.0,
        ITEM_CODE.get(current_item, 0.0),
        opponent_heading,
        opponent_distance,
    ]


def run_training(generations: int = 50) -> bool:
    neat = require_neat()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Training")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24, bold=True)
    track_mask = build_track_mask()
    aborted = False

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
        racer_ids = []
        pickup_manager = PickupManager(pickup_spawn_points())

        for _, genome in genomes:
            genome.fitness = 0.0
            nets.append(neat.nn.FeedForwardNetwork.create(genome, neat_config))
            cars.append(create_ai_car())
            genome_refs.append(genome)
            race_states.append(create_race_state())
            racer_ids.append(str(genome.key))

        steps = 0
        while cars and steps < MAX_STEPS:
            steps += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    nonlocal aborted
                    aborted = True
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    aborted = True
                    return

            for index in range(len(cars) - 1, -1, -1):
                car = cars[index]
                genome = genome_refs[index]
                race_state = race_states[index]
                racer_id = racer_ids[index]
                opponents = [
                    (racer_ids[opponent_index], cars[opponent_index], race_states[opponent_index])
                    for opponent_index in range(len(cars))
                    if opponent_index != index
                ]

                outputs = nets[index].activate(network_inputs(car, race_state, track_mask, pickup_manager, opponents))
                car.update_ai(outputs)
                if car.item_output(outputs):
                    if pickup_manager.use_item(racer_id, car, race_state, opponents):
                        genome.fitness += 2.0
                genome.fitness += max(car.speed, 0) * 0.02

                if car_hits_wall(car, track_mask):
                    genome.fitness -= 2.0
                    cars.pop(index)
                    nets.pop(index)
                    genome_refs.pop(index)
                    race_states.pop(index)
                    racer_ids.pop(index)
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
                    racer_ids.pop(index)

            pickup_events = pickup_manager.update(
                [(racer_ids[index], cars[index], race_states[index]) for index in range(len(cars))]
            )
            for index, racer_id in enumerate(racer_ids):
                genome_refs[index].fitness += pickup_events[racer_id]["collected"] * 8.0
                genome_refs[index].fitness += pickup_events[racer_id]["hits"] * 14.0

            draw_track(screen)
            pickup_manager.draw(screen)
            for car in cars:
                car.draw(screen)
            info = font.render(
                f"Training cars: {len(cars)}  Step: {steps}/{MAX_STEPS}",
                True,
                TEXT,
            )
            screen.blit(info, (20, 20))
            hint = font.render("Esc: menu", True, TEXT)
            screen.blit(hint, (20, 50))
            pygame.display.flip()
            clock.tick(FPS)

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())

    winner = population.run(eval_genomes, generations)
    if not aborted and winner is not None:
        WINNER_PATH.write_bytes(pickle.dumps(winner))
    pygame.quit()
    return not aborted


def watch_winner() -> bool:
    neat = require_neat()
    if not WINNER_PATH.exists():
        return True

    try:
        winner = pickle.loads(WINNER_PATH.read_bytes())
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            CONFIG_PATH,
        )
        net = neat.nn.FeedForwardNetwork.create(winner, config)
    except Exception as error:
        raise SystemExit("Saved winner is incompatible with the current pickup-aware AI. Retrain first.") from error

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NEAT Car Watch Mode")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28, bold=True)
    track_mask = build_track_mask()
    small_font = pygame.font.SysFont("arial", 20, bold=True)

    lead_car = create_ai_car(AI_COLOR)
    rival_car = create_ai_car((235, 120, 255))
    rival_car.x += 20
    rival_car.y += 18
    lead_state = create_race_state()
    rival_state = create_race_state()
    lead_explosion = ExplosionEffect()
    rival_explosion = ExplosionEffect()
    pickup_manager = PickupManager(pickup_spawn_points())

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                lead_car.reset()
                rival_car.reset()
                rival_car.x += 20
                rival_car.y += 18
                lead_state = create_race_state()
                rival_state = create_race_state()
                lead_explosion = ExplosionEffect()
                rival_explosion = ExplosionEffect()
                pickup_manager.reset()

        racers = [
            ("lead", lead_car, lead_state),
            ("rival", rival_car, rival_state),
        ]
        for racer_id, car, state in racers:
            if bool(state["crashed"]):
                continue
            opponents = [entry for entry in racers if entry[0] != racer_id]
            outputs = net.activate(network_inputs(car, state, track_mask, pickup_manager, opponents))
            car.update_ai(outputs)
            if car.item_output(outputs):
                pickup_manager.use_item(racer_id, car, state, opponents)
            if car_hits_wall(car, track_mask):
                state["crashed"] = True
                if racer_id == "lead":
                    lead_explosion.trigger((car.x, car.y), car.color)
                else:
                    rival_explosion.trigger((car.x, car.y), car.color)
            else:
                advance_race_state(car, state)

        pickup_manager.update(racers)
        lead_explosion.update()
        rival_explosion.update()

        if bool(lead_state["crashed"]) and bool(rival_state["crashed"]):
            message = font.render("Both AI cars crashed. Press R to retry.", True, GAME_OVER)
        elif bool(lead_state["crashed"]):
            message = font.render("Lead AI crashed. Press R to retry.", True, GAME_OVER)
        elif bool(rival_state["crashed"]):
            message = font.render("Rival AI crashed. Press R to retry.", True, GAME_OVER)
        else:
            lead_item = ITEM_LABELS.get(lead_state.get("item"), "None")
            rival_item = ITEM_LABELS.get(rival_state.get("item"), "None")
            message = font.render(
                f"Lead laps: {int(lead_state['laps'])}  Rival laps: {int(rival_state['laps'])}",
                True,
                TEXT,
            )
            item_text = small_font.render(f"Lead item: {lead_item}  Rival item: {rival_item}", True, TEXT)

        draw_track(screen)
        pickup_manager.draw(screen)
        lead_car.draw(screen)
        rival_car.draw(screen)
        lead_car.draw_sensors(screen, track_mask, WIDTH, HEIGHT)
        lead_explosion.draw(screen)
        rival_explosion.draw(screen)
        screen.blit(message, (20, 20))
        if not (bool(lead_state["crashed"]) or bool(rival_state["crashed"])):
            screen.blit(item_text, (20, 56))
        hint = font.render("R: retry  Esc: menu", True, TEXT)
        screen.blit(hint, (20, 88))
        pygame.display.flip()
        clock.tick(FPS)
