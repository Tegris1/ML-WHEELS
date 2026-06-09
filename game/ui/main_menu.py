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
from game.paths import get_winner_path, get_winner_name_path
from game.ui import theme
from game.ui.controls import Button, Selector, Stepper, Toggle, TextInput

ACTION_START = "start"
ACTION_QUIT = "quit"

MODE_PLAY = "play"
MODE_TRAIN = "train"
MODE_WATCH = "watch"
MODE_EDIT_TRACK = "edit_track"

TRAIN_PROFILE_RECT = pygame.Rect(560, 465, 280, 58)
TRAIN_ADVANCED_TOGGLE_RECT = pygame.Rect(560, 550, 280, 58)
ADVANCED_REWARDS_COMPACT_RECT = pygame.Rect(680, 340, 160, 34)
MODE_PANEL_RECT = pygame.Rect(130, 196, 740, 132)
PARAMETER_PANEL_RECT = pygame.Rect(130, 344, 740, 274)
ACTION_PANEL_RECT = pygame.Rect(330, HEIGHT - 80, 340, 68)


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
        
        # AI Profile Selector
        self.ai_profile = self._create_profile_selector(
            "AI Profile", pygame.Rect(560, 465, 280, 58)
        )
        
        self.profile_name_input = TextInput(
            "Profile Name", "", pygame.Rect(160, 550, 280, 58)
        )
        self._update_profile_name_input()

        # Advanced Rewards
        self.advanced_rewards_toggle = Toggle("Advanced rewards", False, TRAIN_ADVANCED_TOGGLE_RECT.copy())
        self.speed_reward = Stepper("Speed rew (x100)", 2, 0, 10, 1, pygame.Rect(160, 380, 280, 58))
        self.wall_penalty = Stepper("Wall pen", 2, 0, 10, 1, pygame.Rect(160, 465, 280, 58))
        self.checkpoint_reward = Stepper("Checkpoint rew", 20, 0, 100, 5, pygame.Rect(160, 550, 280, 58))
        self.lap_reward = Stepper("Lap rew", 100, 0, 500, 10, pygame.Rect(560, 380, 280, 58))
        self.stuck_penalty = Stepper("Stuck pen (x100)", 3, 0, 10, 1, pygame.Rect(560, 465, 280, 58))
        self.finish_reward = Stepper("Finish rew", 250, 0, 1000, 50, pygame.Rect(560, 550, 280, 58))

        self.watch_sensors = Toggle("AI sensors", True, pygame.Rect(160, 380, 280, 58))
        self.status_message: str | None = None
        self._action: str | None = None

    def run(self, screen: pygame.Surface, clock: pygame.time.Clock) -> str:
        pygame.display.set_caption("ML-WHEELS - Main Menu")
        title_font = pygame.font.SysFont("bahnschrift", 58, bold=True)
        heading_font = pygame.font.SysFont("bahnschrift", 24, bold=True)
        text_font = pygame.font.SysFont("segoeui", 21)
        button_font = pygame.font.SysFont("bahnschrift", 24, bold=True)
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
                profile_index=self.ai_profile.selected_index,
                profile_name=self.profile_name_input.text,
                speed_reward=self.speed_reward.value / 100.0,
                wall_penalty=float(self.wall_penalty.value),
                checkpoint_reward=float(self.checkpoint_reward.value),
                lap_reward=float(self.lap_reward.value),
                stuck_penalty=self.stuck_penalty.value / 100.0,
                finish_reward=float(self.finish_reward.value),
            ),
            watch=WatchSettings(
                show_sensors=self.watch_sensors.value,
                profile_index=self.ai_profile.selected_index,
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
            if event.key == pygame.K_RETURN and not self.profile_name_input.active:
                if self._can_start():
                    self._action = ACTION_START
                return
            if event.key in (pygame.K_1, pygame.K_KP1) and not self.profile_name_input.active:
                self.mode = MODE_PLAY
                self._refresh_selectors()
            elif event.key in (pygame.K_2, pygame.K_KP2) and not self.profile_name_input.active:
                self.mode = MODE_TRAIN
                self._refresh_selectors()
            elif event.key in (pygame.K_3, pygame.K_KP3) and not self.profile_name_input.active:
                self.mode = MODE_WATCH
                self._refresh_selectors()
            elif event.key in (pygame.K_4, pygame.K_KP4) and not self.profile_name_input.active:
                self.mode = MODE_EDIT_TRACK

        for mode, button in self._mode_buttons():
            if button.handle_event(event):
                self.mode = mode
                self._refresh_selectors()
                if mode == MODE_TRAIN:
                    self._update_profile_name_input()

        for action, button in self._action_buttons():
            if button.handle_event(event) and self._can_start():
                self._action = action

        if self.mode == MODE_PLAY:
            self.player_one_selector.handle_event(event)
            self.player_two_selector.handle_event(event)
            self.play_collisions.handle_event(event)
            
        elif self.mode == MODE_TRAIN:
            if not self.advanced_rewards_toggle.value:
                self.profile_name_input.handle_event(event)
                old_index = self.ai_profile.selected_index
                
                self.training_generations.handle_event(event)
                self.training_max_steps.handle_event(event)
                self.training_target_laps.handle_event(event)
                
                # Handling AI profile in its Train rect
                original_profile_rect = self.ai_profile.rect
                self.ai_profile.rect = TRAIN_PROFILE_RECT.copy()
                self.ai_profile.handle_event(event)
                self.ai_profile.rect = original_profile_rect

                self._handle_advanced_rewards_toggle(event, TRAIN_ADVANCED_TOGGLE_RECT)
                
                if old_index != self.ai_profile.selected_index:
                    self._update_profile_name_input()
            else:
                self.speed_reward.handle_event(event)
                self.wall_penalty.handle_event(event)
                self.checkpoint_reward.handle_event(event)
                self.lap_reward.handle_event(event)
                self.stuck_penalty.handle_event(event)
                self.finish_reward.handle_event(event)
                
                self._handle_advanced_rewards_toggle(event, ADVANCED_REWARDS_COMPACT_RECT)

        elif self.mode == MODE_WATCH:
            self.watch_sensors.handle_event(event)
            
            # Handling AI profile in its Watch rect
            original_profile_rect = self.ai_profile.rect
            self.ai_profile.rect = pygame.Rect(560, 380, 280, 58)
            self.ai_profile.handle_event(event)
            self.ai_profile.rect = original_profile_rect

    def _refresh_selectors(self):
        # Keeps selected indices but refreshes names
        p1_idx = self.player_one_selector.selected_index
        p2_idx = self.player_two_selector.selected_index
        prof_idx = self.ai_profile.selected_index

        self.player_one_selector = self._create_player_selector("Player 1", self.player_one_selector.rect)
        self.player_one_selector.selected_index = min(p1_idx, len(self.player_one_selector.options) - 1)
        
        self.player_two_selector = self._create_player_selector("Player 2", self.player_two_selector.rect)
        self.player_two_selector.selected_index = min(p2_idx, len(self.player_two_selector.options) - 1)
        
        self.ai_profile = self._create_profile_selector("AI Profile", self.ai_profile.rect)
        self.ai_profile.selected_index = min(prof_idx, len(self.ai_profile.options) - 1)


    def _update_profile_name_input(self):
        name_path = get_winner_name_path(self.ai_profile.selected_index)
        if name_path.exists():
            self.profile_name_input.text = name_path.read_text().strip()
        else:
            self.profile_name_input.text = ""

    def _draw(
        self,
        screen: pygame.Surface,
        title_font: pygame.font.Font,
        heading_font: pygame.font.Font,
        text_font: pygame.font.Font,
        button_font: pygame.font.Font,
    ) -> None:
        self._draw_background(screen)
        self._draw_header(screen, title_font, text_font)
        self._draw_mode_panel(screen, heading_font, text_font, button_font)
        self._draw_parameters(screen, heading_font, text_font)
        self._draw_panel(screen, ACTION_PANEL_RECT, elevated=True)
        for _, button in self._action_buttons():
            button.draw(screen, button_font)

    def _draw_header(
        self,
        screen: pygame.Surface,
        title_font: pygame.font.Font,
        text_font: pygame.font.Font,
    ) -> None:
        title_shadow = title_font.render("ML-WHEELS", True, theme.PANEL_SHADOW)
        title = title_font.render("ML-WHEELS", True, theme.TEXT)
        subtitle = text_font.render(
            "Tune drivers, training and track tools", True, theme.TEXT_MUTED
        )
        screen.blit(title_shadow, title_shadow.get_rect(center=(WIDTH // 2 + 4, 94 + 5)))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 94)))
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 142)))
        pygame.draw.line(
            screen,
            theme.ACCENT_LIGHT,
            (WIDTH // 2 - 96, 166),
            (WIDTH // 2 + 96, 166),
            3,
        )
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
        self._draw_panel(screen, MODE_PANEL_RECT)
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
        screen.blit(description, description.get_rect(center=(WIDTH // 2, 313)))

    def _draw_parameters(
        self,
        screen: pygame.Surface,
        heading_font: pygame.font.Font,
        text_font: pygame.font.Font,
    ) -> None:
        self._draw_panel(screen, PARAMETER_PANEL_RECT, accent_line=False)
        heading = heading_font.render("Parameters", True, theme.TEXT)
        screen.blit(heading, (160, 330))

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
            if not self.advanced_rewards_toggle.value:
                self.training_generations.draw(screen, text_font, heading_font)
                self.training_max_steps.draw(screen, text_font, heading_font)
                self.training_target_laps.draw(screen, text_font, heading_font)
                
                original_profile_rect = self.ai_profile.rect
                self.ai_profile.rect = TRAIN_PROFILE_RECT.copy()
                self.ai_profile.draw(screen, text_font, heading_font)
                self.ai_profile.rect = original_profile_rect

                self.profile_name_input.draw(screen, text_font, heading_font)
                
                self.advanced_rewards_toggle.rect = TRAIN_ADVANCED_TOGGLE_RECT.copy()
                self.advanced_rewards_toggle.draw(screen, text_font, heading_font)
            else:
                self.speed_reward.draw(screen, text_font, heading_font)
                self.wall_penalty.draw(screen, text_font, heading_font)
                self.checkpoint_reward.draw(screen, text_font, heading_font)
                self.lap_reward.draw(screen, text_font, heading_font)
                self.stuck_penalty.draw(screen, text_font, heading_font)
                self.finish_reward.draw(screen, text_font, heading_font)
                
                self._draw_compact_advanced_rewards_toggle(screen, text_font)
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

        # MODE_WATCH layout
        original_profile_rect = self.ai_profile.rect
        self.ai_profile.rect = pygame.Rect(560, 380, 280, 58)
        
        self.watch_sensors.draw(screen, text_font, heading_font)
        self.ai_profile.draw(screen, text_font, heading_font)
        
        self.ai_profile.rect = original_profile_rect


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

    def _format_profile_name(self, index: int) -> str:
        name_path = get_winner_name_path(index)
        if name_path.exists():
            custom_name = name_path.read_text().strip()
            if custom_name:
                return f"Profile {index + 1} [{custom_name}]"
        if get_winner_path(index).exists():
            return f"Profile {index + 1} [Trained]"
        return f"Profile {index + 1} [Empty]"

    def _create_profile_selector(self, label: str, rect: pygame.Rect) -> Selector:
        options = [self._format_profile_name(i) for i in range(AI_PROFILES)]
        return Selector(label, options, 0, rect)

    def _create_player_selector(self, label: str, rect: pygame.Rect) -> Selector:
        options = ["Empty", "Human 1", "Human 2"]
        for i in range(AI_PROFILES):
            if get_winner_path(i).exists():
                options.append(self._format_profile_name(i))
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
        if option.startswith("Profile "):
            return PLAYER_TYPE_AI
        raise ValueError(f"Unknown player type: {option}")

    def _get_ai_profile(self, option: str) -> int | None:
        if not option.startswith("Profile "):
            return None
        # Extracts the number from "Profile X [...]"
        parts = option.split(" ")
        if len(parts) >= 2:
            try:
                return int(parts[1]) - 1
            except ValueError:
                pass
        return None

    def _handle_advanced_rewards_toggle(
        self,
        event: pygame.event.Event,
        rect: pygame.Rect,
    ) -> None:
        was_enabled = self.advanced_rewards_toggle.value
        self.advanced_rewards_toggle.rect = rect.copy()
        self.advanced_rewards_toggle.handle_event(event)
        if self.advanced_rewards_toggle.value and not was_enabled:
            self.profile_name_input.active = False

    def _draw_compact_advanced_rewards_toggle(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
    ) -> None:
        rect = ADVANCED_REWARDS_COMPACT_RECT
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = theme.ACCENT if hovered else theme.ACCENT_DARK

        pygame.draw.rect(screen, theme.PANEL_SHADOW, rect.move(0, 4), border_radius=9)
        pygame.draw.rect(screen, color, rect, border_radius=9)
        pygame.draw.rect(screen, theme.ACCENT_LIGHT, rect, 2, border_radius=9)

        text = font.render("Advanced: ON", True, theme.TEXT)
        screen.blit(text, text.get_rect(center=rect.center))

    def _draw_background(self, screen: pygame.Surface) -> None:
        for y in range(HEIGHT):
            ratio = y / max(HEIGHT - 1, 1)
            color = self._blend(theme.BACKGROUND_TOP, theme.BACKGROUND_BOTTOM, ratio)
            pygame.draw.line(screen, color, (0, y), (WIDTH, y))

        pygame.draw.circle(screen, (47, 66, 49), (90, 110), 130)
        pygame.draw.circle(screen, (23, 45, 41), (880, 92), 170)
        pygame.draw.circle(screen, (48, 43, 30), (820, 650), 210)
        pygame.draw.circle(screen, theme.BORDER_SOFT, (88, 112), 132, 2)
        pygame.draw.circle(screen, theme.BORDER_SOFT, (880, 92), 172, 2)

    def _draw_panel(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        elevated: bool = False,
        accent_line: bool = True,
    ) -> None:
        pygame.draw.rect(screen, theme.PANEL_SHADOW, rect.move(0, 8), border_radius=18)
        pygame.draw.rect(
            screen,
            theme.PANEL_ELEVATED if elevated else theme.PANEL,
            rect,
            border_radius=18,
        )
        pygame.draw.rect(screen, theme.BORDER_SOFT, rect, 2, border_radius=18)
        if accent_line:
            pygame.draw.line(
                screen,
                theme.ACCENT_DARK,
                (rect.left + 20, rect.top + 3),
                (rect.right - 20, rect.top + 3),
                2,
            )

    def _blend(
        self,
        start: tuple[int, int, int],
        end: tuple[int, int, int],
        ratio: float,
    ) -> tuple[int, int, int]:
        return tuple(
            int(start[channel] + (end[channel] - start[channel]) * ratio)
            for channel in range(3)
        )
