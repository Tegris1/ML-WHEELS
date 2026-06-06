from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.config import AI_PROFILES, FPS, HEIGHT, WIDTH
from game.modes.settings import (
    PLAYER_TYPE_AI,
    PLAYER_TYPE_EMPTY,
    PLAYER_TYPE_HUMAN_1,
    PLAYER_TYPE_HUMAN_2,
    PlaySettings,
    TrainingSettings,
    WatchSettings,
)
from game.paths import get_winner_path
from game.ui import theme
from game.ui.controls import Button, Selector, Stepper, Toggle

ACTION_START = "start"
ACTION_QUIT = "quit"

MODE_PLAY = "play"
MODE_TRAIN = "train"
MODE_WATCH = "watch"
MODE_EDIT_TRACK = "edit_track"


@dataclass
class MenuSelection:
    mode: str
    play: PlaySettings
    training: TrainingSettings
    watch: WatchSettings


class MainMenu:
    def __init__(self) -> None:
        self.mode = MODE_PLAY
        self.player_one_selector = self._create_player_selector(
            "Player 1", pygame.Rect(160, 380, 280, 58)
        )
        self.player_two_selector = self._create_player_selector(
            "Player 2", pygame.Rect(560, 380, 280, 58)
        )
        self.play_collisions = Toggle("Collisions", True, pygame.Rect(360, 465, 280, 58))

        self.training_generations = Stepper(
            "Generations", 50, 1, 500, 5, pygame.Rect(160, 380, 280, 58)
        )
        self.training_max_steps = Stepper(
            "Max steps", 1800, 300, 5000, 100, pygame.Rect(160, 465, 280, 58)
        )
        self.training_target_laps = Stepper(
            "Target laps", 3, 1, 10, 1, pygame.Rect(560, 380, 280, 58)
        )
        self.ai_profile = Stepper(
            "AI Profile", 1, 1, AI_PROFILES, 1, pygame.Rect(560, 465, 280, 58)
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
            play=self._play_settings(),
            training=TrainingSettings(
                generations=self.training_generations.value,
                max_steps=self.training_max_steps.value,
                target_laps=self.training_target_laps.value,
                profile_index=self.ai_profile.value - 1,
            ),
            watch=WatchSettings(
                show_sensors=self.watch_sensors.value,
                profile_index=self.ai_profile.value - 1,
            ),
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
                if self._can_start():
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
            if button.handle_event(event) and self._can_start():
                self._action = action

        if self.mode == MODE_PLAY:
            self.player_one_selector.handle_event(event)
            self.player_two_selector.handle_event(event)
            self.play_collisions.handle_event(event)
        elif self.mode == MODE_TRAIN:
            self.training_generations.handle_event(event)
            self.training_max_steps.handle_event(event)
            self.training_target_laps.handle_event(event)
            self.ai_profile.handle_event(event)
        elif self.mode == MODE_WATCH:
            self.watch_sensors.handle_event(event)
            self.ai_profile.handle_event(event)

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
        subtitle = text_font.render(
            "Select mode and run parameters", True, theme.TEXT_MUTED
        )
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
        screen.blit(heading, (160, 206))
        for _, button in self._mode_buttons():
            button.draw(screen, button_font)

        descriptions = {
            MODE_PLAY: "Select player types for a local race.",
            MODE_TRAIN: "NEAT training with selected generation limits.",
            MODE_WATCH: "Replay saved winner from a selected profile.",
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
        screen.blit(heading, (160, 338))

        if self.mode == MODE_PLAY:
            self.player_one_selector.draw(screen, text_font, heading_font)
            self.player_two_selector.draw(screen, text_font, heading_font)
            self.play_collisions.draw(screen, text_font, heading_font)
            if not self._can_start():
                warning = text_font.render(
                    "At least one player must be selected.", True, theme.WARNING
                )
                screen.blit(warning, warning.get_rect(center=(WIDTH // 2, 550)))
            return

        if self.mode == MODE_TRAIN:
            self.training_generations.draw(screen, text_font, heading_font)
            self.training_max_steps.draw(screen, text_font, heading_font)
            self.training_target_laps.draw(screen, text_font, heading_font)
            self.ai_profile.draw(screen, text_font, heading_font)
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
        self.ai_profile.draw(screen, text_font, heading_font)

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
        can_start = self._can_start()
        return [
            (
                ACTION_START,
                Button(
                    rect=pygame.Rect(360, HEIGHT - 68, 130, 46),
                    label="Start",
                    selected=can_start,
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

    def _can_start(self) -> bool:
        if self.mode != MODE_PLAY:
            return True
        return (
            self.player_one_selector.options[self.player_one_selector.selected_index]
            != "Empty"
            or self.player_two_selector.options[self.player_two_selector.selected_index]
            != "Empty"
        )

    def _create_player_selector(self, label: str, rect: pygame.Rect) -> Selector:
        options = ["Empty", "Human 1", "Human 2"]
        for i in range(AI_PROFILES):
            if get_winner_path(i).exists():
                options.append(f"AI {i + 1}")
        return Selector(label, options, 0, rect)

    def _play_settings(self) -> PlaySettings:
        p1_option = self.player_one_selector.options[
            self.player_one_selector.selected_index
        ]
        p2_option = self.player_two_selector.options[
            self.player_two_selector.selected_index
        ]
        return PlaySettings(
            player_one_type=self._get_player_type(p1_option),
            player_two_type=self._get_player_type(p2_option),
            player_one_ai_profile=self._get_ai_profile(p1_option),
            player_two_ai_profile=self._get_ai_profile(p2_option),
            collisions_enabled=self.play_collisions.value,
        )

    def _get_player_type(self, option: str) -> str:
        if option == "Empty":
            return PLAYER_TYPE_EMPTY
        if option == "Human 1":
            return PLAYER_TYPE_HUMAN_1
        if option == "Human 2":
            return PLAYER_TYPE_HUMAN_2
        if option.startswith("AI"):
            return PLAYER_TYPE_AI
        raise ValueError(f"Unknown player type: {option}")

    def _get_ai_profile(self, option: str) -> int | None:
        if not option.startswith("AI"):
            return None
        return int(option.split(" ")[1]) - 1
