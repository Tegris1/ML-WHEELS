from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.config import FPS, HEIGHT, WIDTH
from game.modes.settings import TrainingSettings, WatchSettings
from game.ui import theme
from game.ui.controls import Button, Stepper, Toggle

ACTION_START = "start"
ACTION_QUIT = "quit"

MODE_PLAY = "play"
MODE_TRAIN = "train"
MODE_WATCH = "watch"
MODE_EDIT_TRACK = "edit_track"


@dataclass
class MenuSelection:
    mode: str
    training: TrainingSettings
    watch: WatchSettings


class MainMenu:
    def __init__(self) -> None:
        self.mode = MODE_PLAY
        self.training_generations = Stepper(
            "Generations",
            50,
            1,
            500,
            5,
            pygame.Rect(360, 380, 280, 58),
        )
        self.training_max_steps = Stepper(
            "Max steps",
            1800,
            300,
            5000,
            100,
            pygame.Rect(360, 465, 280, 58),
        )
        self.training_target_laps = Stepper(
            "Target laps",
            3,
            1,
            10,
            1,
            pygame.Rect(360, 550, 280, 58),
        )
        self.watch_sensors = Toggle("AI sensors", True, pygame.Rect(360, 390, 280, 58))
        self.status_message: str | None = None
        self._action: str | None = None

    def run(self, screen: pygame.Surface, clock: pygame.time.Clock) -> str:
        pygame.display.set_caption("ML-WHEELS - Main Menu")
        title_font = pygame.font.SysFont("arial", 52, bold=True)
        heading_font = pygame.font.SysFont("arial", 24, bold=True)
        text_font = pygame.font.SysFont("arial", 22)
        button_font = pygame.font.SysFont("arial", 24, bold=True)
        self._action = None

        while self._action is None:
            for event in pygame.event.get():
                self._handle_event(event)

            self._draw(screen, title_font, heading_font, text_font, button_font)
            pygame.display.flip()
            clock.tick(FPS)

        return self._action

    def selection(self) -> MenuSelection:
        return MenuSelection(
            mode=self.mode,
            training=TrainingSettings(
                generations=self.training_generations.value,
                max_steps=self.training_max_steps.value,
                target_laps=self.training_target_laps.value,
            ),
            watch=WatchSettings(show_sensors=self.watch_sensors.value),
        )

    def set_status(self, message: str) -> None:
        self.status_message = message

    def clear_status(self) -> None:
        self.status_message = None

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self._action = ACTION_QUIT
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._action = ACTION_QUIT
                return
            if event.key == pygame.K_RETURN:
                self._action = ACTION_START
                return
            if event.key in (pygame.K_1, pygame.K_KP1):
                self.mode = MODE_PLAY
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self.mode = MODE_TRAIN
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self.mode = MODE_WATCH
            elif event.key in (pygame.K_4, pygame.K_KP4):
                self.mode = MODE_EDIT_TRACK

        for mode, button in self._mode_buttons():
            if button.handle_event(event):
                self.mode = mode

        for action, button in self._action_buttons():
            if button.handle_event(event):
                self._action = action

        if self.mode == MODE_TRAIN:
            self.training_generations.handle_event(event)
            self.training_max_steps.handle_event(event)
            self.training_target_laps.handle_event(event)
        elif self.mode == MODE_WATCH:
            self.watch_sensors.handle_event(event)

    def _draw(
        self,
        screen: pygame.Surface,
        title_font: pygame.font.Font,
        heading_font: pygame.font.Font,
        text_font: pygame.font.Font,
        button_font: pygame.font.Font,
    ) -> None:
        screen.fill(theme.BACKGROUND)
        self._draw_header(screen, title_font, text_font)
        self._draw_mode_panel(screen, heading_font, text_font, button_font)
        self._draw_parameters(screen, heading_font, text_font)
        for _, button in self._action_buttons():
            button.draw(screen, button_font)

    def _draw_header(
        self,
        screen: pygame.Surface,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
    ) -> None:
        title = title_font.render("ML-WHEELS", True, theme.TEXT)
        subtitle = text_font.render("Select mode and run parameters", True, theme.TEXT_MUTED)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 94)))
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 142)))
        if self.status_message:
            status = text_font.render(self.status_message, True, theme.WARNING)
            screen.blit(status, status.get_rect(center=(WIDTH // 2, 174)))

    def _draw_mode_panel(
        self,
        screen: pygame.Surface,
        heading_font: pygame.font.Font,
        text_font: pygame.font.Font,
        button_font: pygame.font.Font,
    ) -> None:
        heading = heading_font.render("Mode", True, theme.TEXT)
        screen.blit(heading, (250, 206))
        for _, button in self._mode_buttons():
            button.draw(screen, button_font)

        descriptions = {
            MODE_PLAY: "Two local players: WASD and arrows.",
            MODE_TRAIN: "NEAT training with selected generation limits.",
            MODE_WATCH: "Replay saved winner from winner.pkl.",
            MODE_EDIT_TRACK: "Draw and save a custom track layout.",
        }
        description = text_font.render(descriptions[self.mode], True, theme.TEXT_MUTED)
        screen.blit(description, description.get_rect(center=(WIDTH // 2, 318)))

    def _draw_parameters(
        self,
        screen: pygame.Surface,
        heading_font: pygame.font.Font,
        text_font: pygame.font.Font,
    ) -> None:
        heading = heading_font.render("Parameters", True, theme.TEXT)
        screen.blit(heading, (250, 338))

        if self.mode == MODE_PLAY:
            lines = [
                "No parameters for local race.",
                "Press Start, then Esc to return to this menu.",
            ]
            for index, line in enumerate(lines):
                text = text_font.render(line, True, theme.TEXT_MUTED)
                screen.blit(text, text.get_rect(center=(WIDTH // 2, 410 + index * 34)))
            return

        if self.mode == MODE_TRAIN:
            self.training_generations.draw(screen, text_font, heading_font)
            self.training_max_steps.draw(screen, text_font, heading_font)
            self.training_target_laps.draw(screen, text_font, heading_font)
            return

        if self.mode == MODE_EDIT_TRACK:
            lines = [
                "Left-drag to sketch the track centerline.",
                "Use [ and ] to change width, Enter to save, D for default track.",
            ]
            for index, line in enumerate(lines):
                text = text_font.render(line, True, theme.TEXT_MUTED)
                screen.blit(text, text.get_rect(center=(WIDTH // 2, 410 + index * 34)))
            return

        self.watch_sensors.draw(screen, text_font, heading_font)

    def _mode_buttons(self) -> list[tuple[str, Button]]:
        labels = [
            (MODE_PLAY, "Play"),
            (MODE_TRAIN, "Train AI"),
            (MODE_WATCH, "Watch AI"),
            (MODE_EDIT_TRACK, "Edit Track"),
        ]
        return [
            (
                mode,
                Button(
                    rect=pygame.Rect(160 + index * 170, 245, 150, 52),
                    label=label,
                    selected=self.mode == mode,
                ),
            )
            for index, (mode, label) in enumerate(labels)
        ]

    def _action_buttons(self) -> list[tuple[str, Button]]:
        return [
            (
                ACTION_START,
                Button(
                    rect=pygame.Rect(360, HEIGHT - 68, 130, 46),
                    label="Start",
                    selected=True,
                ),
            ),
            (
                ACTION_QUIT,
                Button(
                    rect=pygame.Rect(510, HEIGHT - 68, 130, 46),
                    label="Quit",
                ),
            ),
        ]
