from __future__ import annotations

from dataclasses import dataclass
import math
import random

import pygame


EXPLOSION_COLORS = (
    (255, 245, 190),
    (255, 210, 90),
    (255, 145, 40),
    (235, 80, 30),
    (130, 130, 130),
)


@dataclass
class ExplosionParticle:
    position: pygame.Vector2
    velocity: pygame.Vector2
    radius: float
    life: int
    max_life: int
    color: tuple[int, int, int]

    def update(self) -> None:
        self.position += self.velocity
        self.velocity *= 0.92
        self.radius *= 0.97
        self.life -= 1

    @property
    def alive(self) -> bool:
        return self.life > 0 and self.radius > 0.8

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        radius = max(1, int(self.radius))
        particle_surface = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            particle_surface,
            (*self.color, alpha),
            (radius + 1, radius + 1),
            radius,
        )
        surface.blit(
            particle_surface,
            (int(self.position.x) - radius - 1, int(self.position.y) - radius - 1),
        )


class ExplosionEffect:
    def __init__(self) -> None:
        self.particles: list[ExplosionParticle] = []

    def trigger(self, position: tuple[float, float], base_color: tuple[int, int, int]) -> None:
        center = pygame.Vector2(position)
        self.particles.clear()
        for _ in range(34):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.5, 6.5)
            direction = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            color = random.choice(EXPLOSION_COLORS[:-1] if random.random() < 0.75 else EXPLOSION_COLORS)
            if random.random() < 0.18:
                color = base_color
            self.particles.append(
                ExplosionParticle(
                    position=center + (direction * 1.4),
                    velocity=direction,
                    radius=random.uniform(3.0, 8.0),
                    life=random.randint(18, 34),
                    max_life=34,
                    color=color,
                )
            )

    def update(self) -> None:
        for particle in self.particles:
            particle.update()
        self.particles = [particle for particle in self.particles if particle.alive]

    def draw(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)

    @property
    def active(self) -> bool:
        return bool(self.particles)
