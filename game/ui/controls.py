from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.ui import theme


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    selected: bool = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        return self.rect.collidepoint(event.pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)
        color = theme.ACCENT_DARK if self.selected else theme.PANEL
        if hovered:
            color = theme.ACCENT if self.selected else theme.PANEL_HOVER

        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        border = theme.ACCENT if self.selected else theme.BORDER
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=8)

        text = font.render(self.label, True, theme.TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))


@dataclass
class Stepper:
    label: str
    value: int
    min_value: int
    max_value: int
    step: int
    rect: pygame.Rect

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            minus_rect, plus_rect = self._button_rects()
            if minus_rect.collidepoint(event.pos):
                self.value = max(self.min_value, self.value - self.step)
            elif plus_rect.collidepoint(event.pos):
                self.value = min(self.max_value, self.value + self.step)

    def draw(
        self,
        surface: pygame.Surface,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
    ) -> None:
        label = label_font.render(self.label, True, theme.TEXT_MUTED)
        surface.blit(label, (self.rect.left, self.rect.top - 28))

        pygame.draw.rect(surface, theme.PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surface, theme.BORDER, self.rect, 2, border_radius=8)

        minus_rect, plus_rect = self._button_rects()
        self._draw_small_button(surface, value_font, minus_rect, "-")
        self._draw_small_button(surface, value_font, plus_rect, "+")

        value = value_font.render(str(self.value), True, theme.TEXT)
        surface.blit(value, value.get_rect(center=self.rect.center))

    def _button_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        size = self.rect.height - 12
        minus = pygame.Rect(self.rect.left + 6, self.rect.top + 6, size, size)
        plus = pygame.Rect(self.rect.right - size - 6, self.rect.top + 6, size, size)
        return minus, plus

    def _draw_small_button(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        rect: pygame.Rect,
        label: str,
    ) -> None:
        color = theme.BACKGROUND
        if rect.collidepoint(pygame.mouse.get_pos()):
            color = theme.PANEL_HOVER
        pygame.draw.rect(surface, color, rect, border_radius=6)
        text = font.render(label, True, theme.TEXT)
        surface.blit(text, text.get_rect(center=rect.center))


@dataclass
class Toggle:
    label: str
    value: bool
    rect: pygame.Rect

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.value = not self.value

    def draw(
        self,
        surface: pygame.Surface,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
    ) -> None:
        label = label_font.render(self.label, True, theme.TEXT_MUTED)
        surface.blit(label, (self.rect.left, self.rect.top - 28))

        pygame.draw.rect(surface, theme.PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surface, theme.BORDER, self.rect, 2, border_radius=8)

        knob_area = pygame.Rect(self.rect.left + 16, self.rect.centery - 14, 58, 28)
        color = theme.ACCENT_DARK if self.value else theme.BACKGROUND
        pygame.draw.rect(surface, color, knob_area, border_radius=14)
        knob_x = knob_area.right - 14 if self.value else knob_area.left + 14
        pygame.draw.circle(surface, theme.TEXT, (knob_x, knob_area.centery), 10)

        value = "ON" if self.value else "OFF"
        text = value_font.render(value, True, theme.TEXT)
        surface.blit(text, (self.rect.left + 96, self.rect.centery - text.get_height() // 2))


@dataclass
class Selector:
    label: str
    options: list[str]
    selected_index: int
    rect: pygame.Rect

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            minus_rect, plus_rect = self._button_rects()
            if minus_rect.collidepoint(event.pos):
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif plus_rect.collidepoint(event.pos):
                self.selected_index = (self.selected_index + 1) % len(self.options)

    def draw(
        self,
        surface: pygame.Surface,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
    ) -> None:
        label = label_font.render(self.label, True, theme.TEXT_MUTED)
        surface.blit(label, (self.rect.left, self.rect.top - 28))

        pygame.draw.rect(surface, theme.PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surface, theme.BORDER, self.rect, 2, border_radius=8)

        minus_rect, plus_rect = self._button_rects()
        self._draw_small_button(surface, value_font, minus_rect, "<")
        self._draw_small_button(surface, value_font, plus_rect, ">")

        value = value_font.render(self.options[self.selected_index], True, theme.TEXT)
        surface.blit(value, value.get_rect(center=self.rect.center))

    def _button_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        size = self.rect.height - 12
        minus = pygame.Rect(self.rect.left + 6, self.rect.top + 6, size, size)
        plus = pygame.Rect(self.rect.right - size - 6, self.rect.top + 6, size, size)
        return minus, plus

    def _draw_small_button(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        rect: pygame.Rect,
        label: str,
    ) -> None:
        color = theme.BACKGROUND
        if rect.collidepoint(pygame.mouse.get_pos()):
            color = theme.PANEL_HOVER
        pygame.draw.rect(surface, color, rect, border_radius=6)
        text = font.render(label, True, theme.TEXT)
        surface.blit(text, text.get_rect(center=rect.center))


@dataclass
class TextInput:
    label: str
    text: str
    rect: pygame.Rect
    active: bool = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                # Add a reasonable max length, e.g., 15 chars
                if len(self.text) < 15 and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(
        self,
        surface: pygame.Surface,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
    ) -> None:
        label = label_font.render(self.label, True, theme.TEXT_MUTED)
        surface.blit(label, (self.rect.left, self.rect.top - 28))

        color = theme.ACCENT_DARK if self.active else theme.PANEL
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        border_color = theme.ACCENT if self.active else theme.BORDER
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)

        text_surface = value_font.render(self.text + ("_" if self.active else ""), True, theme.TEXT)
        # Center the text inside the rect
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
